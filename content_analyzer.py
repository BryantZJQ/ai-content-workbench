"""内容分析器 — 爆款拆解 / 标题A/B测试 / 脚本质量诊断"""

import json
import re

from llm_client import chat, parse_json_response, parse_json_array


# ============================================================
# 1. 爆款拆解器
# ============================================================

def analyze_viral(script_text: str) -> dict:
    """
    逆向拆解爆款视频文案，提取结构公式和可复用模板。

    Returns:
        dict: 包含 structure/hook_analysis/pacing/emotional_arc/
              viral_factors/reusable_formula/template 等字段
    """
    system_prompt = """你是一位顶级短视频内容策略师，擅长逆向拆解爆款视频的底层逻辑。
你的分析精准、深入、可操作，不说空话。"""

    user_prompt = f"""请深度拆解以下爆款短视频文案，分析它为什么能火：

--- 文案开始 ---
{script_text}
--- 文案结束 ---

请严格按以下JSON格式输出，不要输出其他内容：
{{
  "summary": "一句话概括这条视频的核心卖点",
  "structure": {{
    "hook_type": "钩子类型（如：悬念钩子/反常识钩子/痛点钩子/数字钩子/冲突钩子）",
    "hook_text": "原文中的钩子部分",
    "hook_analysis": "为什么这个开场能留住人（具体分析）",
    "body_pattern": "正文推进模式（如：层层递进/对比论证/时间线/清单式/故事弧）",
    "body_analysis": "正文的节奏和信息编排分析",
    "cta_type": "收尾类型（如：开放提问/行动号召/情感升华/反转收尾/悬念留白）",
    "cta_analysis": "收尾为什么有效"
  }},
  "viral_factors": [
    {{"factor": "爆款因素1", "evidence": "原文中的对应证据", "score": 9}},
    {{"factor": "爆款因素2", "evidence": "原文中的对应证据", "score": 8}}
  ],
  "emotional_arc": "情绪曲线描述（如：好奇→震惊→认同→行动）",
  "pacing": {{
    "rhythm": "节奏特点",
    "sentence_avg_length": "平均句长特点",
    "info_density": "信息密度评价"
  }},
  "reusable_formula": {{
    "name": "给这个公式起个名字（如：反常识三段式）",
    "pattern": "公式结构描述（用【】标注可替换部分）",
    "steps": ["步骤1：...", "步骤2：...", "步骤3：..."],
    "applicable_topics": ["适用选题类型1", "适用选题类型2", "适用选题类型3"]
  }},
  "improvement": "如果要让这条文案更好，还可以怎么改（1-2条建议）"
}}"""

    raw = chat(system_prompt, user_prompt, max_tokens=4000)
    result = parse_json_response(raw)

    if not result:
        return {"error": "分析失败，请检查输入的文案内容", "raw": raw}

    return result


def apply_formula(formula: dict, new_topic: str, style: str = "故事讲述") -> str:
    """
    将拆解出的爆款公式套用到新选题上，生成新脚本。
    """
    system_prompt = """你是一位顶级短视频文案写手。
你要参考给定的爆款公式，为新选题写一条脚本。
保留公式的结构和节奏，但内容完全围绕新选题展开。"""

    formula_desc = json.dumps(formula, ensure_ascii=False, indent=2)

    user_prompt = f"""【爆款公式】
{formula_desc}

【新选题】{new_topic}

请参考上面的爆款公式，为新选题写一条完整的短视频配音脚本。
要求：
- 严格复用公式的结构（钩子类型→正文模式→收尾类型）
- 保持相似的节奏和情绪曲线
- 内容完全围绕新选题，不要照抄原文
- 只输出脚本正文，不要输出任何标记或说明"""

    return chat(system_prompt, user_prompt, max_tokens=2000)


# ============================================================
# 2. 标题A/B测试器
# ============================================================

def generate_title_variants(topic: str, script_text: str = "",
                            platform: str = "通用",
                            count: int = 8) -> list[dict]:
    """
    为选题/脚本生成多个标题变体，并预测点击率。

    Returns:
        list[dict]: [{"title": "...", "score": 9.2, "type": "...", "reasoning": "..."}]
    """
    system_prompt = """你是一位短视频标题优化专家，深谙各平台的推荐算法和用户心理。
你知道标题决定了80%的点击率，擅长用不同策略写出高点击标题。"""

    script_hint = ""
    if script_text:
        # 截取前300字作为参考
        script_hint = f"\n\n【脚本内容参考（前300字）】\n{script_text[:300]}..."

    user_prompt = f"""【选题】{topic}
【目标平台】{platform}{script_hint}

请为这个选题生成{count}个不同策略的标题变体。

要求：
- 每个标题用不同的策略（好奇心、数字、痛点、反常识、对比、情绪、悬念、利益点等）
- 标题长度15-25字
- 给每个标题评估点击率潜力（1-10分）

请严格按JSON数组格式输出：
[
  {{
    "title": "标题文字",
    "type": "策略类型（如：好奇心驱动/数字冲击/痛点共鸣/反常识/悬念/利益承诺/对比冲突/情绪共鸣）",
    "score": 8.5,
    "reasoning": "为什么这个标题能吸引点击（一句话）"
  }}
]"""

    raw = chat(system_prompt, user_prompt, max_tokens=3000)
    result = parse_json_array(raw)

    if result:
        return sorted(result, key=lambda x: x.get("score", 0), reverse=True)

    return [{"title": topic, "type": "原始", "score": 5.0, "reasoning": "未能生成变体"}]


def compare_titles(titles: list[str], platform: str = "通用") -> list[dict]:
    """
    对用户提供的多个标题进行对比评分。
    """
    titles_text = "\n".join(f"{i+1}. {t}" for i, t in enumerate(titles))

    system_prompt = "你是一位短视频标题优化专家，擅长评估标题的点击率潜力。"

    user_prompt = f"""【目标平台】{platform}

请对以下标题进行对比评分（1-10分）：

{titles_text}

评分维度：好奇心激发、信息增量、情绪冲击力、平台适配度、完播引导力

请严格按JSON数组格式输出：
[{{"title": "原标题", "score": 8.5, "strengths": "优势", "weaknesses": "不足", "improved": "优化版本"}}]"""

    raw = chat(system_prompt, user_prompt, max_tokens=2000)
    result = parse_json_array(raw)
    if result:
        return sorted(result, key=lambda x: x.get("score", 0), reverse=True)
    return []


# ============================================================
# 3. 脚本质量诊断
# ============================================================

def diagnose_script(script_text: str, platform: str = "通用",
                    target_duration: int = 60) -> dict:
    """
    对脚本进行全方位质量诊断。

    Returns:
        dict: 包含 overall_score/hook_score/pacing_score/engagement_score/
              completion_rate/diagnosis/suggestions 等字段
    """
    word_count = len(re.findall(r'[\u4e00-\u9fff]', script_text))

    system_prompt = """你是一位短视频内容质量审核专家，拥有丰富的数据分析经验。
你擅长从文案角度预测视频的完播率、互动率，并给出可操作的优化建议。
分析要具体、犀利，不说空话套话。"""

    user_prompt = f"""请对以下短视频脚本进行全面质量诊断：

--- 脚本开始 ---
{script_text}
--- 脚本结束 ---

【基本信息】
- 字数：{word_count}字
- 目标平台：{platform}
- 目标时长：{target_duration}秒

请严格按以下JSON格式输出诊断报告：
{{
  "overall_score": 7.5,
  "overall_verdict": "一句话总评",
  "scores": {{
    "hook_power": {{
      "score": 8,
      "comment": "开场钩子强度分析（前3秒能否留住人）"
    }},
    "info_density": {{
      "score": 7,
      "comment": "信息密度是否合适（太稀薄观众划走，太密集跟不上）"
    }},
    "pacing": {{
      "score": 7,
      "comment": "节奏分析（是否有起伏、有没有尿点）"
    }},
    "emotion": {{
      "score": 6,
      "comment": "情绪感染力（能否引发共鸣或好奇）"
    }},
    "engagement": {{
      "score": 8,
      "comment": "互动潜力（能否引发评论/分享/收藏）"
    }},
    "platform_fit": {{
      "score": 7,
      "comment": "平台适配度（是否符合{platform}的算法偏好、内容调性和时长要求。抖音看完播率和前3秒钩子；B站看深度和弹幕互动；小红书看收藏率和种草感）"
    }}
  }},
  "completion_rate": {{
    "predicted": "65%",
    "dropoff_points": [
      {{"position": "第X句话", "reason": "可能流失原因", "suggestion": "怎么改"}}
    ]
  }},
  "predicted_comments": [
    "预测热门评论1",
    "预测热门评论2",
    "预测热门评论3"
  ],
  "suggestions": [
    {{
      "priority": "high",
      "area": "问题区域",
      "current": "当前原文",
      "problem": "问题描述",
      "improved": "优化后的文案"
    }}
  ],
  "pin_comment_suggestion": "建议的置顶评论内容（引导讨论方向）"
}}"""

    raw = chat(system_prompt, user_prompt, max_tokens=4000)
    result = parse_json_response(raw)

    if not result:
        return {"error": "诊断失败，请检查输入的脚本内容", "raw": raw}

    return result


# ============================================================
# 4. 诊断→一键重写
# ============================================================

def rewrite_script(original_script: str, diagnosis: dict,
                   platform: str = "通用") -> str:
    """
    根据诊断结果智能重写脚本：只修弱项，保留优点。

    Args:
        original_script: 原始脚本文本
        diagnosis: diagnose_script() 返回的诊断结果
        platform: 目标平台

    Returns:
        str: 重写后的完整脚本
    """
    # 提取诊断中的关键问题
    weak_points = []
    if diagnosis.get("scores"):
        for key, item in diagnosis["scores"].items():
            if isinstance(item, dict) and item.get("score", 10) < 7:
                weak_points.append(f"- {item.get('comment', '')}")

    suggestions_text = []
    if diagnosis.get("suggestions"):
        for sg in diagnosis["suggestions"]:
            if sg.get("problem"):
                suggestions_text.append(
                    f"- 问题：{sg['problem']}  建议改为：{sg.get('improved', '')}"
                )

    dropoff_text = []
    if diagnosis.get("completion_rate", {}).get("dropoff_points"):
        for dp in diagnosis["completion_rate"]["dropoff_points"]:
            dropoff_text.append(
                f"- {dp.get('position', '')}：{dp.get('reason', '')}→{dp.get('suggestion', '')}"
            )

    system_prompt = f"""你是一位顶级短视频文案优化师。
你的任务是根据诊断报告重写脚本，只修复弱项，保留原文的优点和风格。
目标平台：{platform}
重写原则：
1. 保留原文的核心观点和信息
2. 保留评分高的部分（钩子强度高就保留钩子结构）
3. 只重写被诊断为弱项的部分
4. 保持原文的人称和语气
5. 只输出重写后的完整脚本正文，不要输出任何标记或说明"""

    user_prompt = f"""【原始脚本】
{original_script}

【诊断发现的弱项】
{chr(10).join(weak_points) if weak_points else "无明显弱项"}

【具体优化建议】
{chr(10).join(suggestions_text) if suggestions_text else "无"}

【流失点】
{chr(10).join(dropoff_text) if dropoff_text else "无"}

【总评】{diagnosis.get('overall_verdict', '')}
【总分】{diagnosis.get('overall_score', 0)}/10

请根据以上诊断结果重写脚本。保留优点，只修复弱项。输出完整脚本正文："""

    return chat(system_prompt, user_prompt, max_tokens=3000)
