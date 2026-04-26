# -*- coding: utf-8 -*-
"""
@author:XuMing(xuming624@qq.com)
@description: 
Configuration for LLM Debate Arena
"""

import os
import json
from dotenv import load_dotenv

load_dotenv()

# OpenRouter API key
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# OpenRouter API endpoint
OPENROUTER_API_URL = os.getenv("OPENROUTER_API_URL")

LLM_CONFIG = {
    'api_key': OPENROUTER_API_KEY,
    'base_url': OPENROUTER_API_URL,
    'timeout': float(os.getenv("LLM_TIMEOUT", "300.0"))
}

# ========== 多 Base URL 配置 ==========
# LLM_BASE_URLS 支持两种格式：
# 1. JSON 数组: [{"url": "https://api1.com/v1", "api_key": "sk-..."}, ...]
# 2. 逗号分隔的 URL 列表（共用 OPENROUTER_API_KEY）: "https://api1.com/v1,https://api2.com/v1"
LLM_BASE_URL_CONFIGS = []

_raw = os.getenv("LLM_BASE_URLS")
if _raw:
    try:
        _parsed = json.loads(_raw)
        for item in _parsed:
            LLM_BASE_URL_CONFIGS.append({
                'url': item['url'],
                'api_key': item.get('api_key', OPENROUTER_API_KEY),
                'timeout': float(item.get('timeout', LLM_CONFIG['timeout']))
            })
    except (json.JSONDecodeError, TypeError):
        import logging as _logging
        _logging.warning("LLM_BASE_URLS 不是合法的 JSON，降级为逗号分隔解析")
        for _url in _raw.split(','):
            _url = _url.strip()
            if _url:
                LLM_BASE_URL_CONFIGS.append({
                    'url': _url,
                    'api_key': OPENROUTER_API_KEY,
                    'timeout': LLM_CONFIG['timeout']
                })

# 若未设置多 base_url，则退回单 base_url
if not LLM_BASE_URL_CONFIGS:
    LLM_BASE_URL_CONFIGS = [{
        'url': OPENROUTER_API_URL,
        'api_key': OPENROUTER_API_KEY,
        'timeout': LLM_CONFIG['timeout']
    }]

AVAILABLE_MODELS = os.getenv("AVAILABLE_MODELS", "gpt-4o,gpt-4o-mini,gpt-5")

# ========== Bing Search 配置 ==========
BING_API_KEY = os.getenv("BING_API_KEY")

# ========== 裁判团配置 ==========

JUDGE_PANEL = [
    "gpt-4o",
    "gpt-4o-mini",
]

# ========== 数据库配置 ==========

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./debate_arena.db")

# ========== 辩论配置 ==========

DEBATE_CONFIG = {
    "max_rounds": 3,
    "enable_tools": True,
    "tools": ["python_interpreter", "web_search", "calculator"]
}

# ========== ELO 配置 ==========

ELO_CONFIG = {
    "initial_rating": 1200,
    "k_factor_new": 64,      # 新手期 (< 10 场)
    "k_factor_mid": 32,      # 成长期 (10-30 场)
    "k_factor_stable": 16,   # 成熟期 (> 30 场)
}

# tools
SERPER_API_KEY = os.getenv("SERPER_API_KEY")