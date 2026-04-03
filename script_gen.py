"""脚本生成器 — AI生成短视频配音脚本"""

import json
import re

from llm_client import chat, parse_json_response, parse_json_array


# ============================================================
# 风格模板（内置12种，无需外部配置文件）
# ============================================================

STYLES = {
    "故事讲述": {
        "description": "沉稳、娓娓道来，适合历史/人物/事件类",
        "tone": "沉稳、有节奏感，像纪录片旁白",
        "rhythm": "长短句交替，叙事段落用长句铺垫，转折处用短句制造停顿感",
        "forbidden": "禁止使用'震惊'、'万万没想到'等夸张词汇；不要用问号轰炸",
        "hook_instruction": "用一个具体的时间+地点+人物开场，设置悬念",
        "body_instruction": "按时间线或因果链展开，每段一个关键转折",
        "cta_instruction": "抛出开放性问题，引导评论",
    },
    "震惊体": {
        "description": "反转、冲击力强，适合冷知识/揭秘类",
        "tone": "惊讶、反转、节奏快，像在分享一个不可思议的发现",
        "rhythm": "短句为主，密集输出信息点，每句话都是一个冲击",
        "forbidden": "不要过度堆砌反问句；避免虎头蛇尾，结尾要有实质内容",
        "hook_instruction": "用一个反常识的结论开场，制造认知冲突",
        "body_instruction": "层层递进揭示真相，每段一个反转点",
        "cta_instruction": "用反问收尾，激发讨论欲",
    },
    "知识科普": {
        "description": "理性、有料，适合科学/技术/生活常识类",
        "tone": "理性、清晰、有说服力，像一位耐心的老师",
        "rhythm": "中等句长，逻辑连接词清晰，信息密度高但不压迫",
        "forbidden": "不要用口水话凑字数；避免'众所周知'等空洞表述",
        "hook_instruction": "指出一个常见误区或提出一个好问题",
        "body_instruction": "用数据和事实论证，逻辑清晰，通俗易懂",
        "cta_instruction": "总结核心观点，引导收藏",
    },
    "争议辩论": {
        "description": "犀利、有态度，适合社会话题/观点输出类",
        "tone": "犀利、有态度、引战但不低俗，像一个敢说真话的朋友",
        "rhythm": "长短句穿插，观点用短句砸出来，论据用长句铺开",
        "forbidden": "不要人身攻击；避免绝对化表述",
        "hook_instruction": "抛出一个有争议的观点，明确站队",
        "body_instruction": "正反两面论证，最后给出自己的判断",
        "cta_instruction": "把问题抛给观众，引导评论区站队",
    },
    "情感共鸣": {
        "description": "走心、真挚，适合情感/亲情/成长/回忆类",
        "tone": "温暖、真诚、克制，像深夜电台主播的独白",
        "rhythm": "句子偏长，语速缓慢，多用逗号制造呼吸感",
        "forbidden": "不要用'感动中国'式煽情；避免生硬的鸡汤金句",
        "hook_instruction": "用一个私密的生活细节或画面开场，让人代入",
        "body_instruction": "用具体的故事和细节传递情感，而非空洞抒情",
        "cta_instruction": "用一句温暖的话收尾，引导分享给在乎的人",
    },
    "搞笑吐槽": {
        "description": "幽默、接地气，适合奇葩事件/日常吐槽/段子类",
        "tone": "轻松、调侃、毒舌但不恶意",
        "rhythm": "短句为主，节奏快，铺垫-抖包袱的经典结构",
        "forbidden": "不要低俗擦边；不要解释为什么好笑",
        "hook_instruction": "用一个荒诞的场景或金句直接抓住注意力",
        "body_instruction": "每30字一个笑点，层层递进，最后抖出最大的包袱",
        "cta_instruction": "用一句自嘲或反转收尾，引导评论区接梗",
    },
    "种草推荐": {
        "description": "真实体验感、有说服力，适合好物/美食/旅行/App推荐类",
        "tone": "真诚、不做作，像朋友私下安利",
        "rhythm": "口语化碎句，多用信任词，关键卖点用短句强调",
        "forbidden": "禁止使用'全网最低价'等广告词；不要罗列参数，要说体验感受",
        "hook_instruction": "用亲身使用的痛点场景开场，引发共鸣",
        "body_instruction": "按使用场景展开，每个点说感受而非参数",
        "cta_instruction": "给出适合人群建议，降低决策压力",
    },
    "新闻速递": {
        "description": "简洁、权威、信息密度高，适合热点事件/行业动态类",
        "tone": "客观、冷静、专业，像资深记者的快速通报",
        "rhythm": "短句为主，一句一个信息点，无废话",
        "forbidden": "不要掺入个人情绪；避免空洞来源词",
        "hook_instruction": "一句话说清楚发生了什么",
        "body_instruction": "按重要性递减展开背景和细节，最多3个信息层",
        "cta_instruction": "一句话点出这件事对普通人的影响",
    },
    "干货教程": {
        "description": "步骤清晰、实操性强，适合技能/教程/方法论类",
        "tone": "耐心、清晰、有条理，像手把手教你的师傅",
        "rhythm": "中等句长，多用序数词，关键操作用短句强调",
        "forbidden": "不要铺垫太长，30秒内必须进入正题",
        "hook_instruction": "直接说出学完能解决什么问题或达到什么效果",
        "body_instruction": "分3-5步展开，每步一个要点，穿插易错提醒",
        "cta_instruction": "鼓励动手实践，引导收藏备用",
    },
    "悬疑解密": {
        "description": "层层设疑、反转揭秘，适合悬案/未解之谜类",
        "tone": "神秘、低沉、克制，像在耳边讲秘密",
        "rhythm": "前慢后快，铺垫阶段用长句，揭秘阶段用短句加速",
        "forbidden": "不要开头就剧透",
        "hook_instruction": "抛出一个不合理的事实或未解的谜团",
        "body_instruction": "先给线索铺垫疑点，中间给出多个可能性，最后揭示真相",
        "cta_instruction": "留一个未解的尾巴，引导评论区讨论",
    },
    "鸡汤励志": {
        "description": "正能量、感染力强，适合励志/自律/职场/逆袭类",
        "tone": "坚定、有力量感、不说教",
        "rhythm": "中等偏短句，金句用独立短句突出",
        "forbidden": "不要喊口号；禁止空洞鼓励；要有具体故事支撑",
        "hook_instruction": "用一个低谷时刻或转折点开场",
        "body_instruction": "讲一个真实的逆袭/成长故事，强调过程而非结果",
        "cta_instruction": "给出一个可执行的小行动建议",
    },
    "吐槽盘点": {
        "description": "犀利点评、节奏明快，适合排行榜/年度盘点/对比类",
        "tone": "犀利、有主见、节奏快，像脱口秀吐槽",
        "rhythm": "短句密集，一句一个点评，善用排比和对比",
        "forbidden": "不要流水账罗列；每个条目必须有观点",
        "hook_instruction": "直接亮出要盘点的主题和数量，制造期待",
        "body_instruction": "每个条目用2-3句话：事实+吐槽/点评，由弱到强排列",
        "cta_instruction": "问观众心中的第一名是谁，引导评论",
    },
}

# 平台配置
PLATFORMS = {
    "通用": {"aspect_ratio": "16:9", "constraints": ""},
    "抖音": {
        "aspect_ratio": "9:16",
        "constraints": "开场钩子必须在3秒内抓住注意力；每句话不超过20字；结尾必须有强互动引导；总时长15-60秒最佳",
    },
    "B站": {
        "aspect_ratio": "16:9",
        "constraints": "开场可以有5-10秒铺垫；允许长句和复杂逻辑；2-5分钟是黄金时长",
    },
    "小红书": {
        "aspect_ratio": "3:4",
        "constraints": "开场必须有强烈的个人体验感；多用信任词；正文要有清单感；30-60秒最佳",
    },
}


def _count_chinese(text: str) -> int:
    return len(re.findall(r'[\u4e00-\u9fff]', text))


def _estimate_duration(text: str, wps: float = 4.2) -> float:
    return round(_count_chinese(text) / wps, 1)


def generate_script(topic: str, style: str = "故事讲述",
                    duration_seconds: int = 60,
                    platform: str = "通用") -> dict:
    """
    为单个选题生成完整脚本

    Args:
        topic: 选题关键词
        style: 风格名称（12种可选）
        duration_seconds: 目标时长（秒）
        platform: 目标平台（通用/抖音/B站/小红书）

    Returns:
        dict: 包含 title/hook/body/cta/full_script/word_count/estimated_duration 等字段
    """
    wps = 4.2
    target_words = int(duration_seconds * wps)
    style_cfg = STYLES.get(style, STYLES["故事讲述"])
    platform_cfg = PLATFORMS.get(platform, PLATFORMS["通用"])

    system_prompt = f"""你是一位顶级短视频文案写手，擅长写{style_cfg['description']}的视频脚本。

【风格要求】
- 语气：{style_cfg['tone']}
- 节奏：{style_cfg['rhythm']}
- {style_cfg['forbidden']}

【硬性规范】
- 总字数严格控制在 {target_words} 字左右（允许±15%）
- 全文口语化，像跟朋友聊天一样自然
- 禁止使用"大家好"、"今天我们来聊"等俗套开场
- 不要使用任何markdown标记符号"""

    if platform_cfg["constraints"]:
        system_prompt += f"\n\n【目标平台：{platform}】\n{platform_cfg['constraints']}"

    user_prompt = f"""请为以下选题写一条短视频配音脚本：

【选题】{topic}

请严格按以下JSON格式输出，不要输出任何其他内容：
{{
  "title": "视频标题（吸引眼球，15字以内）",
  "hook": "开场钩子（{style_cfg['hook_instruction']}，约30-50字）",
  "body": "正文主体（{style_cfg['body_instruction']}，约{target_words - 80}字）",
  "cta": "结尾引导（{style_cfg['cta_instruction']}，约20-30字）"
}}"""

    raw = chat(system_prompt, user_prompt)
    script_data = parse_json_response(raw)

    if not script_data:
        script_data = _fallback_generate(topic, style, target_words)

    full_script = f"{script_data.get('hook', '')}\n{script_data.get('body', '')}\n{script_data.get('cta', '')}"
    word_count = _count_chinese(full_script)
    duration = _estimate_duration(full_script, wps)

    return {
        "topic": topic,
        "style": style,
        "platform": platform,
        "title": script_data.get("title", topic),
        "hook": script_data.get("hook", ""),
        "body": script_data.get("body", ""),
        "cta": script_data.get("cta", ""),
        "full_script": full_script,
        "word_count": word_count,
        "estimated_duration_seconds": duration,
    }


def _fallback_generate(topic: str, style: str, target_words: int) -> dict:
    """降级方案：纯文本生成"""
    style_cfg = STYLES.get(style, STYLES["故事讲述"])

    prompt = f"""请为选题"{topic}"写一条{target_words}字左右的短视频配音脚本。

要求：
- 第一段是开场钩子（抓住注意力）
- 中间是正文（3-5个信息点）
- 最后一段是结尾引导（引导互动）
- 只输出脚本正文，不要输出任何标记或说明"""

    system = f"你是一位顶级短视频文案写手，擅长写{style_cfg['description']}的视频脚本。语气：{style_cfg['tone']}"
    text = chat(system, prompt)
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]

    if len(paragraphs) >= 3:
        return {
            "title": topic,
            "hook": paragraphs[0],
            "body": "\n".join(paragraphs[1:-1]),
            "cta": paragraphs[-1],
        }
    return {"title": topic, "hook": "", "body": text, "cta": ""}


def generate_visual_cues(topic: str, script_text: str,
                         duration: float, platform: str = "通用") -> list[dict]:
    """
    为脚本生成AI视频分镜提示词

    Returns:
        list[dict]: 分镜列表，每个包含 shot_number/timestamp/scene/camera/prompt_cn/prompt_en
    """
    aspect_ratio = PLATFORMS.get(platform, PLATFORMS["通用"])["aspect_ratio"]
    num_shots = max(4, int(duration / 12))
    shot_dur = round(duration / num_shots, 1)

    system_prompt = f"""你是一位专业的短视频分镜导演兼AI视频提示词专家。
你精通可灵(Kling)、Pika、Runway、Vidu等AI视频生成平台的提示词写法。
本次视频画面比例为 {aspect_ratio}。"""

    prompt = f"""以下是一条关于"{topic}"的短视频配音文案，时长约{duration}秒，画面比例{aspect_ratio}：

{script_text}

请生成 {num_shots} 个分镜，严格按JSON数组格式输出：
[
  {{
    "shot_number": 1,
    "timestamp": "0-{shot_dur}s",
    "narration": "对应的配音文案原文",
    "scene": "画面场景详细描述",
    "camera": "镜头运动方式",
    "style": "视觉风格",
    "prompt_cn": "可灵/Vidu中文提示词，50-80字",
    "prompt_en": "Pika/Runway英文提示词，60-120 words"
  }}
]"""

    raw = chat(system_prompt, prompt, max_tokens=8000)
    result = parse_json_array(raw)
    return result or []


def list_styles() -> list[dict]:
    """返回所有可用的脚本风格"""
    return [
        {"name": name, "description": cfg["description"]}
        for name, cfg in STYLES.items()
    ]


def list_platforms() -> list[dict]:
    """返回所有支持的目标平台"""
    return [
        {"name": name, "aspect_ratio": cfg["aspect_ratio"]}
        for name, cfg in PLATFORMS.items()
    ]
