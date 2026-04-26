# -*- coding: utf-8 -*-
"""
@author:XuMing(xuming624@qq.com)
@description: LLM 客户端 - 兼容 OpenAI SDK，支持多 base_url 自动遍历及重试"""

import asyncio
from openai import (
    AsyncOpenAI,
    APIError,
    APIConnectionError,
    RateLimitError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError
)
import json
from typing import List, Dict, AsyncGenerator, Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.log import logger
from backend.config import LLM_CONFIG, LLM_BASE_URL_CONFIGS

# 构建多 base_url 客户端列表
_clients: List[AsyncOpenAI] = []
for _cfg in LLM_BASE_URL_CONFIGS:
    _client = AsyncOpenAI(
        api_key=_cfg['api_key'],
        base_url=_cfg['url'],
        timeout=_cfg['timeout']
    )
    _clients.append(_client)
    logger.info(f"LLM client 初始化: base_url={_cfg['url']}, api_key={str(_cfg.get('api_key', ''))[:6]}...")

# 向后兼容：保留单 client 引用（指向第一个）
client = _clients[0] if _clients else None

# API 超时/连接错误可重试，BadRequestError/model not found 触发切换 base_url
_RETRYABLE_ERRORS = (APITimeoutError, APIConnectionError, RateLimitError)
_MAX_RETRIES = 3          # 每个 base_url 的最大重试次数
_RETRY_DELAY = 1.0        # 重试间隔（秒）


def _is_model_not_found(exc: Exception) -> bool:
    """判断异常是否属于模型在当前 endpoint 不可用（触发切换 base_url）"""
    if isinstance(exc, BadRequestError):
        msg = str(exc).lower()
        return any(kw in msg for kw in ('model', 'not found', 'does not exist', 'invalid model', 'no such model'))
    if isinstance(exc, APIError):
        # 404 通常表示模型不存在
        if hasattr(exc, 'status_code') and exc.status_code == 404:
            return True
    return False


async def query_model_stream(
    model_id: str, 
    messages: List[Dict], 
    temperature: float = 0.7,
    tools: Optional[List[Dict]] = None
) -> AsyncGenerator[Dict, None]:
    """
    流式查询 LLM (支持工具调用)，自动遍历多 base_url，并对每个 base_url 重试最多 3 次。
    
    Yields:
        {"type": "content", "delta": "..."}
        {"type": "tool_call", "tool_call": {...}}
        {"type": "done", "content": "...", "tool_calls": [...]}
        {"type": "error", "error": "...", "error_type": "..."}
    """
    logger.info(f"开始流式调用模型: {model_id}, 消息数: {len(messages)}")

    # 格式化消息（公共逻辑）
    formatted_messages = _format_messages(messages)

    request_params = {
        "model": model_id,
        "messages": formatted_messages,
        "temperature": temperature,
        "stream": True
    }
    if tools:
        request_params["tools"] = tools
        logger.debug(f"使用工具: {[t['function']['name'] for t in tools]}")

    last_error = None

    for client_idx, cur_client in enumerate(_clients):
        for attempt in range(_MAX_RETRIES):
            try:
                stream = await cur_client.chat.completions.create(**request_params)

                accumulated_content = ""
                accumulated_tool_calls = []
                tool_call_buffer = {}

                async for chunk in stream:
                    if not hasattr(chunk, 'choices') or not chunk.choices:
                        continue

                    choice = chunk.choices[0]

                    if hasattr(choice, 'delta') and choice.delta:
                        delta = choice.delta

                        if hasattr(delta, 'content') and delta.content:
                            accumulated_content += delta.content
                            yield {"type": "content", "delta": delta.content}

                        if hasattr(delta, 'tool_calls') and delta.tool_calls:
                            for tc_delta in delta.tool_calls:
                                idx = tc_delta.index
                                if idx not in tool_call_buffer:
                                    tool_call_buffer[idx] = {
                                        "id": "",
                                        "type": "function",
                                        "function": {"name": "", "arguments": ""}
                                    }
                                if hasattr(tc_delta, 'id') and tc_delta.id:
                                    tool_call_buffer[idx]["id"] = tc_delta.id
                                if hasattr(tc_delta, 'function') and tc_delta.function:
                                    if hasattr(tc_delta.function, 'name') and tc_delta.function.name:
                                        tool_call_buffer[idx]["function"]["name"] = tc_delta.function.name
                                    if hasattr(tc_delta.function, 'arguments') and tc_delta.function.arguments:
                                        tool_call_buffer[idx]["function"]["arguments"] += tc_delta.function.arguments

                if tool_call_buffer:
                    accumulated_tool_calls = [tool_call_buffer[i] for i in sorted(tool_call_buffer.keys())]
                    logger.info(f"检测到工具调用: {[tc['function']['name'] for tc in accumulated_tool_calls]}")
                    for tc in accumulated_tool_calls:
                        yield {"type": "tool_call", "tool_call": tc}

                yield {
                    "type": "done",
                    "content": accumulated_content,
                    "tool_calls": accumulated_tool_calls
                }
                return  # 成功，退出所有重试

            except _RETRYABLE_ERRORS as e:
                last_error = e
                logger.warning(
                    f"流式调用 [{model_id}] base_url={LLM_BASE_URL_CONFIGS[client_idx]['url']} "
                    f"第 {attempt + 1}/{_MAX_RETRIES} 次重试: {type(e).__name__}: {e}"
                )
                if attempt < _MAX_RETRIES - 1:
                    await asyncio.sleep(_RETRY_DELAY * (attempt + 1))
                    continue
                # 耗尽重试次数，尝试下一个 base_url
                break

            except Exception as e:
                last_error = e
                if _is_model_not_found(e):
                    logger.warning(
                        f"流式调用 [{model_id}] base_url={LLM_BASE_URL_CONFIGS[client_idx]['url']} "
                        f"模型不可用，切换下一个 base_url: {e}"
                    )
                    break  # 切换 base_url
                # 其他错误，直接报错（不切换 base_url）
                yield _make_error_event(e, model_id)
                return

    # 所有 base_url 均失败
    yield _make_error_event(last_error, model_id)


async def query_model(model_id: str, messages: List[Dict], temperature: float = 0.7) -> Dict:
    """
    查询 LLM (非流式，用于裁判评分等场景)，自动遍历多 base_url，并对每个 base_url 重试最多 3 次。
    
    返回: {"content": "...", "tool_calls": [...]}
    """
    logger.info(f"调用模型 (非流式): {model_id}")

    formatted_messages = _format_messages(messages)
    last_error = None

    for client_idx, cur_client in enumerate(_clients):
        for attempt in range(_MAX_RETRIES):
            try:
                response = await cur_client.chat.completions.create(
                    model=model_id,
                    messages=formatted_messages,
                    temperature=temperature,
                    stream=False
                )

                choice = response.choices[0]
                result = {
                    "content": choice.message.content or "",
                    "tool_calls": []
                }

                if hasattr(choice.message, 'tool_calls') and choice.message.tool_calls:
                    result["tool_calls"] = [
                        {
                            "id": tc.id,
                            "type": tc.type,
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        }
                        for tc in choice.message.tool_calls
                    ]

                logger.info(f"模型调用成功，内容长度: {len(result['content'])}, result: {result}")
                return result

            except _RETRYABLE_ERRORS as e:
                last_error = e
                logger.warning(
                    f"非流式调用 [{model_id}] base_url={LLM_BASE_URL_CONFIGS[client_idx]['url']} "
                    f"第 {attempt + 1}/{_MAX_RETRIES} 次重试: {type(e).__name__}: {e}"
                )
                if attempt < _MAX_RETRIES - 1:
                    await asyncio.sleep(_RETRY_DELAY * (attempt + 1))
                    continue
                break  # 耗尽重试，切换 base_url

            except Exception as e:
                last_error = e
                if _is_model_not_found(e):
                    logger.warning(
                        f"非流式调用 [{model_id}] base_url={LLM_BASE_URL_CONFIGS[client_idx]['url']} "
                        f"模型不可用，切换下一个 base_url: {e}"
                    )
                    break  # 切换 base_url
                # 其他错误直接返回
                return _make_error_result(e, model_id)

    # 所有 base_url 均失败
    return _make_error_result(last_error, model_id)


# ========== 辅助函数 ==========

def _format_messages(messages: List[Dict]) -> List[Dict]:
    """统一格式化消息列表"""
    formatted = []
    for msg in messages:
        if isinstance(msg, dict):
            formatted_msg = {'role': msg['role'], 'content': msg.get('content', '')}
            if 'tool_calls' in msg and msg['tool_calls']:
                formatted_msg['tool_calls'] = msg['tool_calls']
            if 'tool_call_id' in msg:
                formatted_msg['tool_call_id'] = msg['tool_call_id']
        else:
            formatted_msg = {'role': msg.role, 'content': msg.content or ''}
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                formatted_msg['tool_calls'] = [
                    {
                        'id': tc.id,
                        'type': tc.type,
                        'function': {
                            'name': tc.function.name,
                            'arguments': tc.function.arguments
                        }
                    }
                    for tc in msg.tool_calls
                ]
            if hasattr(msg, 'tool_call_id'):
                formatted_msg['tool_call_id'] = msg.tool_call_id
        formatted.append(formatted_msg)
    return formatted


def _make_error_event(exc: Optional[Exception], model_id: str) -> Dict:
    """将异常转换为错误事件 dict"""
    if isinstance(exc, RateLimitError):
        error_msg = f"API 限流错误 (QPM/RPM 超限): {exc}"
        error_type = "rate_limit"
    elif isinstance(exc, APITimeoutError):
        error_msg = f"API 超时错误: {exc}"
        error_type = "timeout"
    elif isinstance(exc, APIConnectionError):
        error_msg = f"API 连接错误 (网络问题): {exc}"
        error_type = "connection"
    elif isinstance(exc, AuthenticationError):
        error_msg = f"API 认证错误 (API Key 无效): {exc}"
        error_type = "auth"
    elif isinstance(exc, BadRequestError):
        error_msg = f"API 请求错误 (参数无效): {exc}"
        error_type = "bad_request"
    elif isinstance(exc, APIError):
        error_msg = f"API 通用错误: {exc}"
        error_type = "api_error"
    elif exc is None:
        error_msg = "未知错误（无异常信息）"
        error_type = "unknown"
    else:
        error_msg = f"未知错误: {type(exc).__name__} - {exc}"
        error_type = "unknown"
    logger.error(f"流式调用失败 [{model_id}]: {error_msg}", exc_info=True)
    return {"type": "error", "error": error_msg, "error_type": error_type}


def _make_error_result(exc: Exception, model_id: str) -> Dict:
    """将异常转换为错误结果 dict"""
    event = _make_error_event(exc, model_id)
    return {"content": f"Error: {event['error']}", "tool_calls": [], "error_type": event['error_type']}


# add demo
async def main():
    print("=" * 60)
    print("工具调用完整流程演示：搜索故宫并基于结果回答")
    print("=" * 60)
    
    from backend.tools import get_debate_tools, execute_tool
    
    # 从 tools.py 获取工具列表，只使用 web_search 工具
    all_tools = get_debate_tools()
    search_tool = [tool for tool in all_tools if tool['function']['name'] == 'web_search']
    
    # 初始化消息列表
    messages = [{'role': 'user', 'content': '搜索故宫,基于搜索结果回答故宫成立时间'}]
    
    # 第一次调用：模型决定使用工具
    print("\n[第一步] 模型分析问题并决定调用工具...")
    print("-" * 60)
    
    accumulated_content = ""
    tool_calls = []
    
    async for chunk in query_model_stream(
        model_id='gpt-4o-mini', 
        messages=messages, 
        tools=search_tool
    ):
        if chunk['type'] == 'content':
            accumulated_content += chunk['delta']
            print(chunk['delta'], end='', flush=True)
        elif chunk['type'] == 'tool_call':
            tool_calls.append(chunk['tool_call'])
            print(f"\n\n[工具调用] {chunk['tool_call']['function']['name']}")
            print(f"参数: {chunk['tool_call']['function']['arguments']}")
        elif chunk['type'] == 'done':
            if chunk.get('tool_calls'):
                tool_calls = chunk['tool_calls']
    
    print("\n")
    
    if tool_calls:
        print("\n[第二步] 执行工具调用...")
        print("-" * 60)
        
        assistant_message = {
            'role': 'assistant',
            'content': accumulated_content if accumulated_content else "",
            'tool_calls': [
                {
                    'id': tc['id'],
                    'type': tc['type'],
                    'function': {
                        'name': tc['function']['name'],
                        'arguments': tc['function']['arguments']
                    }
                }
                for tc in tool_calls
            ]
        }
        messages.append(assistant_message)
        
        for tool_call in tool_calls:
            print(f"\n执行工具: {tool_call['function']['name']}")
            print(f"参数: {tool_call['function']['arguments']}")
            
            try:
                result = await execute_tool(tool_call)
                print(f"工具执行结果类型: {type(result)}")
                
                if isinstance(result, dict):
                    tool_result_content = result.get('response', json.dumps(result, ensure_ascii=False))
                else:
                    tool_result_content = str(result)
                
                tool_result_message = {
                    'role': 'tool',
                    'content': tool_result_content,
                    'tool_call_id': tool_call['id']
                }
                messages.append(tool_result_message)
                print(f"✓ 工具执行成功 (结果长度: {len(tool_result_content)} 字符)")
                
            except Exception as e:
                error_msg = f"工具执行失败: {str(e)}"
                print(f"✗ {error_msg}")
                messages.append({
                    'role': 'tool',
                    'content': error_msg,
                    'tool_call_id': tool_call['id']
                })
        
        print("\n[第三步] 模型基于工具结果回答问题...")
        print("-" * 60)
        
        async for chunk in query_model_stream(
            model_id='gpt-4o-mini', 
            messages=messages, 
            tools=search_tool
        ):
            if chunk['type'] == 'content':
                print(chunk['delta'], end='', flush=True)
            elif chunk['type'] == 'done':
                final_content = chunk.get('content', '')
                print(f"\n\n[完成] 最终回答长度: {len(final_content)} 字符")
    else:
        print("\n[注意] 模型没有调用工具，直接返回了答案")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
