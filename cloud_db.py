"""云端数据库 — 使用Supabase持久化卡密使用记录"""

import os
import httpx

_SUPABASE_URL = ""
_SUPABASE_KEY = ""


def _get_config():
    """获取Supabase配置（优先从Streamlit secrets读取）"""
    global _SUPABASE_URL, _SUPABASE_KEY
    if _SUPABASE_URL and _SUPABASE_KEY:
        return _SUPABASE_URL, _SUPABASE_KEY

    # 尝试从 Streamlit secrets 读取
    try:
        import streamlit as st
        if hasattr(st, "secrets"):
            _SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
            _SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")
    except Exception:
        pass

    # fallback 到环境变量
    if not _SUPABASE_URL:
        _SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
    if not _SUPABASE_KEY:
        _SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

    return _SUPABASE_URL, _SUPABASE_KEY


def is_available() -> bool:
    """检查云端数据库是否可用"""
    url, key = _get_config()
    return bool(url and key)


def _headers():
    _, key = _get_config()
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def get_usage(key_code: str) -> dict | None:
    """查询卡密使用记录"""
    url, _ = _get_config()
    if not url:
        return None

    try:
        resp = httpx.get(
            f"{url}/rest/v1/key_usage?key_code=eq.{key_code}&select=*",
            headers=_headers(),
            timeout=10,
        )
        if resp.status_code == 200:
            rows = resp.json()
            return rows[0] if rows else None
    except Exception:
        pass
    return None


def update_usage(key_code: str, total_used: int, status: str = "active"):
    """更新或创建卡密使用记录"""
    url, _ = _get_config()
    if not url:
        return

    existing = get_usage(key_code)

    try:
        if existing:
            # 更新
            httpx.patch(
                f"{url}/rest/v1/key_usage?key_code=eq.{key_code}",
                headers=_headers(),
                json={"total_used": total_used, "status": status},
                timeout=10,
            )
        else:
            # 新建
            httpx.post(
                f"{url}/rest/v1/key_usage",
                headers=_headers(),
                json={
                    "key_code": key_code,
                    "total_used": total_used,
                    "status": status,
                },
                timeout=10,
            )
    except Exception:
        pass


def consume(key_code: str, count: int = 1) -> int:
    """
    消耗使用次数并返回新的 total_used

    Returns:
        int: 更新后的总使用次数，失败返回 -1
    """
    existing = get_usage(key_code)
    current = existing["total_used"] if existing else 0
    new_total = current + count
    update_usage(key_code, new_total)
    return new_total
