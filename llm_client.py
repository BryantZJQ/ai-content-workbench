"""LLM客户端 — 封装DeepSeek/OpenAI兼容API调用"""

import os
import json
import re
import time
import functools
from openai import OpenAI


def _get_client() -> tuple[OpenAI, str]:
    """获取OpenAI兼容客户端和模型名"""
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
    model = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")

    if not api_key:
        raise ValueError(
            "未设置 DEEPSEEK_API_KEY 环境变量。"
            "请在环境变量或 Claude Desktop 配置中设置。"
        )

    client = OpenAI(api_key=api_key, base_url=base_url)
    return client, model


def retry(max_retries: int = 3, base_delay: float = 2.0):
    """指数退避重试装饰器"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    delay = base_delay * (2 ** attempt)
                    time.sleep(delay)
        return wrapper
    return decorator


@retry(max_retries=3, base_delay=2.0)
def chat(system_prompt: str, user_prompt: str,
         max_tokens: int = 4000, temperature: float = 0.8) -> str:
    """调用LLM"""
    client, model = _get_client()
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return resp.choices[0].message.content.strip()


def parse_json_response(raw: str) -> dict | None:
    """从LLM输出中提取JSON对象"""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start >= 0 and end > start:
        try:
            return json.loads(raw[start:end])
        except json.JSONDecodeError:
            pass
    return None


def parse_json_array(raw: str) -> list | None:
    """从LLM输出中提取JSON数组"""
    try:
        start = raw.find("[")
        end = raw.rfind("]") + 1
        if start >= 0 and end > start:
            return json.loads(raw[start:end])
    except (json.JSONDecodeError, ValueError):
        pass
    return None
