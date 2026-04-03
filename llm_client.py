"""LLM客户端 — 封装多模型API调用（DeepSeek/Kimi/通义千问/智谱GLM）"""

import os
import json
import re
import time
import functools
from openai import OpenAI


# 支持的模型提供商配置
MODEL_PROVIDERS = {
    "deepseek": {
        "name": "DeepSeek",
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
        "secret_key": "DEEPSEEK_API_KEY",
        "free": False,
        "note": "性价比高，中文能力强",
    },
    "kimi": {
        "name": "Kimi (月之暗面)",
        "base_url": "https://api.moonshot.cn/v1",
        "model": "moonshot-v1-8k",
        "secret_key": "KIMI_API_KEY",
        "free": True,
        "note": "免费额度，长文本理解强",
    },
    "qwen": {
        "name": "通义千问 (阿里)",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen-turbo",
        "secret_key": "QWEN_API_KEY",
        "free": True,
        "note": "免费额度，阿里出品",
    },
    "glm": {
        "name": "智谱GLM (清华)",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "model": "glm-4-flash",
        "secret_key": "GLM_API_KEY",
        "free": True,
        "note": "GLM-4-Flash免费，速度快",
    },
}


def _get_client() -> tuple[OpenAI, str]:
    """获取OpenAI兼容客户端和模型名"""
    provider_id = os.environ.get("LLM_PROVIDER", "deepseek")
    provider = MODEL_PROVIDERS.get(provider_id, MODEL_PROVIDERS["deepseek"])

    api_key = os.environ.get(provider["secret_key"], "")
    base_url = os.environ.get("LLM_BASE_URL", provider["base_url"])
    model = os.environ.get("LLM_MODEL", provider["model"])

    # 兼容旧的 DEEPSEEK_API_KEY 环境变量
    if not api_key and provider_id == "deepseek":
        api_key = os.environ.get("DEEPSEEK_API_KEY", "")

    if not api_key:
        raise ValueError(
            f"未设置 {provider['secret_key']} 。"
            f"请在 Streamlit Secrets 或环境变量中配置。"
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
