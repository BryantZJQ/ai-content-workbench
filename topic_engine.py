"""智能选题引擎 — 热搜抓取 + AI联想扩展 + 智能打分排序"""

import json
from concurrent.futures import ThreadPoolExecutor, as_completed

import httpx

from llm_client import chat, parse_json_array


# ============================================================
# 热搜抓取（4平台并发）
# ============================================================

def fetch_hot_topics(sources: list[str] | None = None) -> list[dict]:
    """
    并行抓取热搜榜单

    Args:
        sources: 来源列表，可选 ["weibo", "bilibili", "douyin", "baidu"]

    Returns:
        list[dict]: [{"title": "...", "source": "weibo", "hot_score": 12345}]
    """
    sources = sources or ["douyin", "bilibili", "weibo", "baidu"]
    fetchers = {
        "weibo": _fetch_weibo,
        "bilibili": _fetch_bilibili,
        "baidu": _fetch_baidu,
        "douyin": _fetch_douyin,
    }
    all_topics = []
    errors = []

    def _fetch_one(src):
        fn = fetchers.get(src)
        if not fn:
            return src, [], f"未知来源: {src}"
        try:
            topics = fn()
            return src, topics, None
        except Exception as e:
            return src, [], str(e)

    with ThreadPoolExecutor(max_workers=len(sources)) as ex:
        futures = [ex.submit(_fetch_one, s) for s in sources]
        for f in as_completed(futures):
            src, topics, err = f.result()
            if err:
                errors.append(f"{src}: {err}")
            else:
                all_topics.extend(topics)

    return all_topics


def _fetch_weibo() -> list[dict]:
    url = "https://weibo.com/ajax/side/hotSearch"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://weibo.com/",
        "Accept": "application/json, text/plain, */*",
    }
    resp = httpx.get(url, headers=headers, timeout=10, follow_redirects=True)
    data = resp.json()
    topics = []
    for item in data.get("data", {}).get("realtime", [])[:20]:
        word = item.get("word", "") or item.get("note", "")
        if word:
            topics.append({
                "title": word,
                "source": "weibo",
                "hot_score": item.get("num", 0),
            })
    return topics


def _fetch_bilibili() -> list[dict]:
    url = "https://api.bilibili.com/x/web-interface/wbi/search/square"
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = httpx.get(url, headers=headers, timeout=10, params={"limit": 20})
    data = resp.json()
    topics = []
    for item in data.get("data", {}).get("trending", {}).get("list", [])[:20]:
        topics.append({
            "title": item.get("keyword", ""),
            "source": "bilibili",
            "hot_score": 0,
        })
    return topics


def _fetch_baidu() -> list[dict]:
    url = "https://top.baidu.com/api/board?platform=wise&tab=realtime"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://top.baidu.com/",
    }
    resp = httpx.get(url, headers=headers, timeout=10, follow_redirects=True)
    data = resp.json()
    topics = []
    for card in data.get("data", {}).get("cards", []):
        for group in card.get("content", []):
            inner = group.get("content", []) if isinstance(group, dict) else []
            for item in inner:
                word = item.get("word", "") or item.get("query", "")
                if word:
                    topics.append({
                        "title": word,
                        "source": "baidu",
                        "hot_score": int(item.get("hotScore", 0)),
                    })
            if isinstance(group, dict) and group.get("word"):
                topics.append({
                    "title": group["word"],
                    "source": "baidu",
                    "hot_score": int(group.get("hotScore", 0)),
                })
    return topics[:20]


def _fetch_douyin() -> list[dict]:
    url = "https://v.api.aa1.cn/api/douyin-hot/index.php?aa1=hot"
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = httpx.get(url, headers=headers, timeout=10, follow_redirects=True)
    text = resp.text.strip()
    decoder = json.JSONDecoder()
    try:
        data, _ = decoder.raw_decode(text)
    except json.JSONDecodeError:
        data = {}
    topics = []
    for item in data.get("data", {}).get("word_list", [])[:20]:
        word = item.get("word", "")
        if word:
            topics.append({
                "title": word,
                "source": "douyin",
                "hot_score": item.get("hot_value", 0),
            })
    return topics


# ============================================================
# AI联想扩展
# ============================================================

def expand_topics(seed_keywords: list[str], count: int = 20,
                  track: str = "") -> list[str]:
    """基于种子关键词，让AI联想扩展更多选题"""
    seeds = "、".join(seed_keywords[:5])
    track_hint = f"，赛道方向为[{track}]" if track else ""

    prompt = f"""我有以下种子选题：{seeds}{track_hint}

请基于这些选题，联想并扩展出{count}个相关但不重复的短视频选题。

要求：
- 每个选题要有明确的切入角度，不要太宽泛
- 优先输出有话题性、有争议性、有信息增量的选题
- 直接输出JSON数组格式，不要输出其他内容
- 格式：["选题1", "选题2", ...]"""

    raw = chat("你是一位资深短视频选题策划师。", prompt)
    result = parse_json_array(raw)
    if result:
        return result

    return [line.strip().strip('"').strip("'").lstrip("0123456789.、- ")
            for line in raw.split("\n") if line.strip()][:count]


# ============================================================
# 去重 + AI打分排序
# ============================================================

def deduplicate(topics: list[str]) -> list[str]:
    """简单去重（精确匹配 + 包含关系）"""
    seen = []
    for t in topics:
        t = t.strip()
        if not t:
            continue
        is_dup = False
        for s in seen:
            if t == s or t in s or s in t:
                is_dup = True
                break
        if not is_dup:
            seen.append(t)
    return seen


def score_topics(topics: list[str], track: str = "") -> list[dict]:
    """AI对选题打分排序"""
    topics_text = "\n".join(f"{i+1}. {t}" for i, t in enumerate(topics))
    track_hint = f"赛道方向：{track}\n" if track else ""

    prompt = f"""{track_hint}以下是一批短视频选题候选，请对每个选题打分（1-10分）。

评分维度：
- 话题热度（大众是否关心）
- 争议性（是否容易引发讨论）
- 视觉表现力（是否容易配画面）
- 信息增量（是否有新鲜感）

选题列表：
{topics_text}

请严格按JSON数组格式输出，不要输出其他内容：
[{{"topic": "选题内容", "score": 8.5, "reason": "简短理由"}}]"""

    raw = chat("你是一位短视频数据分析师，擅长判断内容潜力。", prompt)
    result = parse_json_array(raw)
    if result:
        return sorted(result, key=lambda x: x.get("score", 0), reverse=True)

    return [{"topic": t, "score": 5.0, "reason": ""} for t in topics]


def auto_select(seed_keywords: list[str] | None = None, track: str = "",
                count: int = 10, use_hot: bool = True) -> list[dict]:
    """
    自动选题：热搜 + AI扩展 + 去重 + 打分 → 取TopN

    Returns:
        list[dict]: [{"topic": "...", "score": 8.5, "reason": "..."}]
    """
    all_topics = []

    if use_hot:
        hot = fetch_hot_topics()
        hot_titles = [h["title"] for h in hot if h["title"]]
        all_topics.extend(hot_titles)

    if seed_keywords:
        expanded = expand_topics(seed_keywords, count=count * 2, track=track)
        all_topics.extend(expanded)

    if not all_topics:
        return []

    unique = deduplicate(all_topics)
    scored = score_topics(unique[:30], track=track)

    return scored[:count]
