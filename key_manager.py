"""卡密管理系统 — 生成/验证/限额控制"""

import json
import hashlib
import secrets
import string
from datetime import datetime, timedelta
from pathlib import Path


# 卡密类型配置
KEY_PLANS = {
    "demo": {"name": "试用卡", "days": 999, "daily_limit": 999, "total_limit": 3, "price": "免费"},
    "trial": {"name": "体验卡", "days": 3, "daily_limit": 10, "total_limit": 0, "price": "免费"},
    "weekly": {"name": "周卡", "days": 7, "daily_limit": 50, "total_limit": 0, "price": "¥9.9"},
    "monthly": {"name": "月卡", "days": 30, "daily_limit": 200, "total_limit": 0, "price": "¥29"},
    "yearly": {"name": "年卡", "days": 365, "daily_limit": 999, "total_limit": 0, "price": "¥199"},
}

# 卡密数据文件路径
_DATA_FILE = Path(__file__).parent / "data" / "keys.json"


def _load_keys() -> dict:
    """加载卡密数据"""
    if _DATA_FILE.exists():
        with open(_DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_keys(keys: dict):
    """保存卡密数据"""
    _DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(keys, f, ensure_ascii=False, indent=2)


def generate_keys(plan: str, count: int = 1, prefix: str = "ACP") -> list[str]:
    """
    批量生成卡密

    Args:
        plan: 卡密类型 (trial/weekly/monthly/yearly)
        count: 生成数量
        prefix: 卡密前缀

    Returns:
        list[str]: 生成的卡密列表
    """
    if plan not in KEY_PLANS:
        raise ValueError(f"未知的卡密类型: {plan}，可选: {list(KEY_PLANS.keys())}")

    keys_data = _load_keys()
    generated = []

    for _ in range(count):
        # 格式: ACP-XXXX-XXXX-XXXX（纯大写字母+数字）
        chars = string.ascii_uppercase + string.digits
        parts = ["".join(secrets.choice(chars) for _ in range(4)) for _ in range(3)]
        key_code = f"{prefix}-{'-'.join(parts)}"

        keys_data[key_code] = {
            "plan": plan,
            "plan_name": KEY_PLANS[plan]["name"],
            "daily_limit": KEY_PLANS[plan]["daily_limit"],
            "total_limit": KEY_PLANS[plan]["total_limit"],
            "total_used": 0,
            "created_at": datetime.now().isoformat(),
            "activated_at": None,
            "expires_at": None,
            "status": "unused",  # unused / active / expired / exhausted
            "usage_log": {},     # {"2026-04-03": 5}
        }
        generated.append(key_code)

    _save_keys(keys_data)
    return generated


def validate_key(key_code: str) -> dict:
    """
    验证卡密是否有效

    Returns:
        dict: {
            "valid": True/False,
            "message": "验证信息",
            "plan_name": "月卡",
            "remaining_today": 195,
            "expires_at": "2026-05-03",
        }
    """
    keys_data = _load_keys()

    # 也尝试从 Streamlit secrets 加载（云端部署用）
    cloud_keys = _load_cloud_keys()
    keys_data.update(cloud_keys)

    if key_code not in keys_data:
        return {"valid": False, "message": "卡密不存在"}

    key_info = keys_data[key_code]
    today = datetime.now().strftime("%Y-%m-%d")
    now = datetime.now()

    # 首次使用：激活
    if key_info["status"] == "unused":
        plan = key_info["plan"]
        days = KEY_PLANS[plan]["days"]
        key_info["activated_at"] = now.isoformat()
        key_info["expires_at"] = (now + timedelta(days=days)).isoformat()
        key_info["status"] = "active"
        # 保存回文件（仅本地生效）
        if key_code in keys_data:
            _save_keys(keys_data)

    # 检查是否过期
    if key_info.get("expires_at"):
        expires = datetime.fromisoformat(key_info["expires_at"])
        if now > expires:
            key_info["status"] = "expired"
            if key_code in _load_keys():
                keys_data_local = _load_keys()
                if key_code in keys_data_local:
                    keys_data_local[key_code]["status"] = "expired"
                    _save_keys(keys_data_local)
            return {
                "valid": False,
                "message": f"卡密已过期（{expires.strftime('%Y-%m-%d')}）",
            }

    # 检查总次数限制（demo试用卡）
    total_limit = key_info.get("total_limit", 0)
    total_used = key_info.get("total_used", 0)
    if total_limit > 0 and total_used >= total_limit:
        key_info["status"] = "exhausted"
        if key_code in _load_keys():
            keys_data_local = _load_keys()
            if key_code in keys_data_local:
                keys_data_local[key_code]["status"] = "exhausted"
                _save_keys(keys_data_local)
        return {
            "valid": False,
            "message": f"试用次数已用完（共{total_limit}次），请购买正式卡密解锁无限使用",
        }

    # 检查今日用量
    usage_today = key_info.get("usage_log", {}).get(today, 0)
    daily_limit = key_info.get("daily_limit", 0)
    remaining = max(0, daily_limit - usage_today)

    if remaining <= 0:
        return {
            "valid": False,
            "message": f"今日额度已用完（{daily_limit}次/天），明天再来",
        }

    expires_str = ""
    if key_info.get("expires_at"):
        expires_str = datetime.fromisoformat(key_info["expires_at"]).strftime("%Y-%m-%d")

    # 构建剩余次数信息
    if total_limit > 0:
        remaining_total = total_limit - total_used
        remaining_info = f"剩余 {remaining_total}/{total_limit} 次"
    else:
        remaining_info = f"今日剩余 {remaining} 次"

    return {
        "valid": True,
        "message": "✅ 卡密有效",
        "plan_name": key_info.get("plan_name", ""),
        "remaining_today": remaining,
        "remaining_info": remaining_info,
        "daily_limit": daily_limit,
        "total_limit": total_limit,
        "total_used": total_used,
        "expires_at": expires_str,
    }


def consume_usage(key_code: str, count: int = 1):
    """消耗一次使用额度"""
    keys_data = _load_keys()
    if key_code not in keys_data:
        return

    today = datetime.now().strftime("%Y-%m-%d")
    if "usage_log" not in keys_data[key_code]:
        keys_data[key_code]["usage_log"] = {}
    keys_data[key_code]["usage_log"][today] = (
        keys_data[key_code]["usage_log"].get(today, 0) + count
    )
    # 累加总使用次数
    keys_data[key_code]["total_used"] = keys_data[key_code].get("total_used", 0) + count
    _save_keys(keys_data)


def _load_cloud_keys() -> dict:
    """从Streamlit secrets加载卡密（云端部署用）"""
    try:
        import streamlit as st
        if hasattr(st, "secrets") and "keys" in st.secrets:
            cloud = {}
            for key_code, info in st.secrets["keys"].items():
                cloud[key_code] = {
                    "plan": info.get("plan", "monthly"),
                    "plan_name": KEY_PLANS.get(info.get("plan", "monthly"), {}).get("name", ""),
                    "daily_limit": KEY_PLANS.get(info.get("plan", "monthly"), {}).get("daily_limit", 50),
                    "created_at": info.get("created_at", datetime.now().isoformat()),
                    "activated_at": info.get("activated_at"),
                    "expires_at": info.get("expires_at"),
                    "status": info.get("status", "unused"),
                    "usage_log": {},
                }
            return cloud
    except Exception:
        pass
    return {}


# ============================================================
# 命令行工具：生成卡密
# ============================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="卡密生成工具")
    parser.add_argument("--plan", choices=KEY_PLANS.keys(), default="trial", help="卡密类型")
    parser.add_argument("--count", type=int, default=5, help="生成数量")
    parser.add_argument("--prefix", default="ACP", help="卡密前缀")
    parser.add_argument("--list", action="store_true", help="列出所有卡密")

    args = parser.parse_args()

    if args.list:
        data = _load_keys()
        if not data:
            print("暂无卡密")
        else:
            print(f"\n{'卡密':<25} {'类型':<8} {'状态':<8} {'到期时间':<12}")
            print("-" * 60)
            for code, info in data.items():
                exp = info.get("expires_at", "未激活")
                if exp and exp != "未激活":
                    exp = datetime.fromisoformat(exp).strftime("%Y-%m-%d")
                print(f"{code:<25} {info.get('plan_name', ''):<8} {info['status']:<8} {exp or '未激活':<12}")
            print(f"\n共 {len(data)} 个卡密")
    else:
        plan_info = KEY_PLANS[args.plan]
        print(f"\n生成 {args.count} 个 [{plan_info['name']}] 卡密")
        print(f"有效期: {plan_info['days']}天 | 每日限额: {plan_info['daily_limit']}次 | 建议售价: {plan_info['price']}")
        print("-" * 50)

        keys = generate_keys(args.plan, args.count, args.prefix)
        for k in keys:
            print(f"  {k}")

        print(f"\n✅ 已生成 {len(keys)} 个卡密，保存在 {_DATA_FILE}")
