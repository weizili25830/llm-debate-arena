# -*- coding: utf-8 -*-
"""
@author:XuMing(xuming624@qq.com)
@description: 
工具执行模块
"""

import asyncio
import json
import os
import math
from typing import Any, List
from datetime import datetime
from loguru import logger


async def execute_tool(tool_call: dict) -> Any:
    """
    执行工具调用
    """
    tool_name = tool_call['function']['name']
    arguments = json.loads(tool_call['function']['arguments']) if isinstance(tool_call['function']['arguments'], str) else tool_call['function']['arguments']
    
    logger.debug(f"执行工具: {tool_name}, 参数: {arguments}")
    
    if tool_name == "python_interpreter":
        r = await execute_python(arguments['code'])
    elif tool_name == "calculator":
        r = await execute_calculator(arguments['expression'])
    else:
        r = {"error": f"Unknown tool: {tool_name}"}
    return r


async def execute_python(code: str, timeout: int = 30) -> dict:
    """
    执行 Python 代码 (沙盒)
    """
    import io
    import sys
    import time
    import traceback
    
    old_stdout = sys.stdout
    new_stdout = io.StringIO()
    sys.stdout = new_stdout
    
    start_time = time.time()
    result = {
        'stdout': '',
        'stderr': '',
        'time': 0,
        'success': False
    }
    
    try:
        # 受限命名空间
        safe_namespace = {
            '__builtins__': __builtins__,
            'print': print,
            'range': range,
            'len': len,
            'str': str,
            'int': int,
            'float': float,
            'list': list,
            'dict': dict,
            'set': set,
            'tuple': tuple,
            'time': __import__('time'),
            'math': __import__('math'),
        }
        
        compiled_code = compile(code, '<string>', 'exec')
        exec(compiled_code, safe_namespace)
        
        result['stdout'] = new_stdout.getvalue().strip()
        result['success'] = True
        
    except Exception as e:
        result['stderr'] = f"Error: {str(e)}\n{traceback.format_exc()}"
        result['success'] = False
    
    finally:
        sys.stdout = old_stdout
        new_stdout.close()
        result['time'] = time.time() - start_time
    logger.debug(f"execute_python result: {result}, code: {code}")
    return result


async def execute_calculator(expression: str) -> dict:
    """
    执行精确数学计算
    
    避免 LLM 的数学幻觉问题
    """
    
    result = {
        'expression': expression,
        'result': None,
        'error': None
    }
    
    try:
        # 安全的数学命名空间
        safe_math_namespace = {
            'abs': abs,
            'round': round,
            'min': min,
            'max': max,
            'sum': sum,
            'pow': pow,
            'sqrt': math.sqrt,
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'log': math.log,
            'log10': math.log10,
            'exp': math.exp,
            'pi': math.pi,
            'e': math.e,
            '__builtins__': {}  # 禁用内置函数
        }
        
        # 计算表达式
        result['result'] = eval(expression, safe_math_namespace)
        
    except Exception as e:
        result['error'] = f"计算错误: {str(e)}"
    logger.debug(f"execute_calculator result: {result}, expression: {expression}")
    return result


def get_debate_tools() -> List[dict]:
    """
    获取辩论工具集完整定义列表。
    
    包含：
    - python_interpreter: 函数工具，由后端执行
    - calculator: 函数工具，由后端执行
    
    注意：联网搜索通过 DashScope 的 enable_search 参数实现，
    不作为工具定义传递，由 llm_client 在 extra_body 中注入。
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "python_interpreter",
                "description": "执行 Python 代码验证算法、测试代码、计算复杂度",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "要执行的 Python 代码"
                        }
                    },
                    "required": ["code"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "calculator",
                "description": "执行精确的数学计算（避免 LLM 幻觉）。支持基本运算、三角函数、对数等",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "数学表达式，例如: '2 + 2', 'sqrt(16)', 'sin(pi/2)'"
                        }
                    },
                    "required": ["expression"]
                }
            }
        }
    ]


def use_dashscope_search(enabled_tools: List[str]) -> bool:
    """
    判断是否应启用 DashScope 厂商内置联网搜索（enable_search）。
    
    当 enabled_tools 包含 'web_search' 时返回 True，
    由调用方在请求参数中注入 extra_body={"enable_search": True}。
    """
    return 'web_search' in (enabled_tools or [])


def get_tools_for_enabled(enabled_tools: List[str]) -> List[dict]:
    """
    根据已启用的工具名称列表，返回对应的工具定义。
    
    工具名称到定义的映射：
    - "python_interpreter" -> function 类型工具
    - "web_search"         -> 不返回工具定义，改由 use_dashscope_search() 通过 enable_search 实现
    - "calculator"         -> function 类型工具
    """
    if not enabled_tools:
        return []
    
    result = []
    for tool in get_debate_tools():
        if tool['type'] == 'function':
            if tool['function']['name'] in enabled_tools:
                result.append(tool)
    return result
