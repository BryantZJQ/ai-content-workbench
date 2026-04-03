"""AI短视频内容工作台 — 选题·脚本·分镜 一站搞定"""

import os
import json
import streamlit as st

# 页面必须在最前面设置
st.set_page_config(
    page_title="AI短视频内容工作台",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# 注入核心模块（复用MCP Server的代码）
# ============================================================
# 在导入前先设置环境变量
api_key = st.session_state.get("api_key", "")
if api_key:
    os.environ["DEEPSEEK_API_KEY"] = api_key

import topic_engine
import script_gen
import key_manager


# ============================================================
# 自定义样式
# ============================================================
st.markdown("""
<style>
    .main-title {
        text-align: center;
        padding: 1rem 0 0.5rem 0;
    }
    .main-title h1 {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem;
        font-weight: 800;
    }
    .subtitle {
        text-align: center;
        color: #666;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    .result-card {
        background: #f8f9fa;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid #667eea;
    }
    .score-badge {
        display: inline-block;
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        padding: 2px 10px;
        border-radius: 12px;
        font-weight: bold;
        font-size: 0.9rem;
    }
    .hot-badge {
        display: inline-block;
        background: #ff4757;
        color: white;
        padding: 2px 8px;
        border-radius: 8px;
        font-size: 0.75rem;
    }
    .platform-tag {
        display: inline-block;
        background: #e8e8e8;
        padding: 2px 8px;
        border-radius: 8px;
        font-size: 0.75rem;
        margin-right: 4px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 24px;
        font-size: 1rem;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# 侧边栏
# ============================================================
def _check_premium() -> bool:
    """检查是否有权使用付费功能"""
    v = st.session_state.get("key_validation")
    return v is not None and v.get("valid", False)


def _premium_gate(feature_name: str) -> bool:
    """付费功能门控，无权限时显示提示并返回False"""
    if _check_premium():
        return True
    st.warning(f"🔒 **{feature_name}** 为付费功能，请在左侧边栏输入卡密解锁")
    st.markdown("""
    **获取卡密：**
    - 体验卡（3天免费）：关注公众号回复「体验」获取
    - 周卡 ¥9.9 / 月卡 ¥29 / 年卡 ¥199
    - 联系微信：`your_wechat_id`
    """)
    return False


with st.sidebar:
    st.markdown("## ⚙️ 设置")

    # === 卡密验证 ===
    st.markdown("### 🔑 卡密")
    input_card_key = st.text_input(
        "输入卡密",
        value=st.session_state.get("card_key", ""),
        placeholder="ACP-XXXX-XXXX-XXXX",
        help="输入卡密解锁全部功能",
    )

    if input_card_key:
        st.session_state["card_key"] = input_card_key
        result = key_manager.validate_key(input_card_key)
        st.session_state["key_validation"] = result

        v = st.session_state.get("key_validation", {})
        if v.get("valid"):
            st.success(f"✅ {v.get('plan_name', '')} | {v.get('remaining_info', '')}")
            if v.get("expires_at"):
                st.caption(f"到期时间：{v['expires_at']}")
        else:
            st.error(v.get("message", "卡密无效"))
    else:
        st.info("🔓 输入卡密解锁脚本生成等付费功能")
        st.session_state["key_validation"] = None

    st.divider()

    # === API Key（纯后台自动读取，用户不可见）===
    _api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    try:
        if hasattr(st, "secrets") and "DEEPSEEK_API_KEY" in st.secrets:
            _api_key = st.secrets["DEEPSEEK_API_KEY"]
    except Exception:
        pass
    if _api_key:
        os.environ["DEEPSEEK_API_KEY"] = _api_key

    st.markdown("### 📊 功能说明")
    st.markdown("""
    - **🔥 热搜榜单** — 免费使用
    - **🎯 智能选题** — 需要卡密
    - **📝 脚本生成** — 需要卡密
    - **🎬 分镜提示词** — 需要卡密
    """)

    st.divider()

    st.markdown("""    
    **获取卡密：**  
    关注公众号回复「体验」获取3天体验卡  
    或联系微信购买：`your_wechat_id`
    """)

    st.divider()
    st.markdown("""
    <div style="text-align:center; color:#999; font-size:0.8rem;">
    Powered by DeepSeek + MCP<br>
    Made with ❤️
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# 标题
# ============================================================
st.markdown('<div class="main-title"><h1>🎬 AI短视频内容工作台</h1></div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">选题 · 脚本 · 分镜 — 一站搞定，5分钟产出一条视频的全部文案</div>', unsafe_allow_html=True)


# ============================================================
# 主体 Tabs
# ============================================================
tab1, tab2, tab3, tab4 = st.tabs(["🔥 热搜榜单", "🎯 智能选题", "📝 脚本生成", "🎬 分镜提示词"])


# ===== Tab1: 热搜 =====
with tab1:
    st.markdown("### 实时热搜榜单")
    st.caption("抓取抖音、B站、微博、百度四大平台热搜，发现当下热点")

    col1, col2 = st.columns([3, 1])
    with col1:
        platforms = st.multiselect(
            "选择平台",
            ["douyin", "bilibili", "weibo", "baidu"],
            default=["douyin", "bilibili", "weibo", "baidu"],
            format_func=lambda x: {"douyin": "🎵 抖音", "bilibili": "📺 B站", "weibo": "💬 微博", "baidu": "🔍 百度"}[x],
        )
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        fetch_btn = st.button("🔍 抓取热搜", type="primary", use_container_width=True)

    if fetch_btn:
        with st.spinner("正在抓取各平台热搜..."):
            try:
                results = topic_engine.fetch_hot_topics(platforms)
                st.session_state["hot_topics"] = results
            except Exception as e:
                st.error(f"抓取失败: {e}")

    if "hot_topics" in st.session_state and st.session_state["hot_topics"]:
        results = st.session_state["hot_topics"]

        source_map = {"douyin": "🎵 抖音", "bilibili": "📺 B站", "weibo": "💬 微博", "baidu": "🔍 百度"}
        source_colors = {"douyin": "#000000", "bilibili": "#00a1d6", "weibo": "#ff8200", "baidu": "#2932e1"}

        # 按平台分列展示
        platform_data = {}
        for item in results:
            src = item["source"]
            if src not in platform_data:
                platform_data[src] = []
            platform_data[src].append(item)

        cols = st.columns(len(platform_data))
        for idx, (src, items) in enumerate(platform_data.items()):
            with cols[idx]:
                st.markdown(f"#### {source_map.get(src, src)}")
                for i, item in enumerate(items[:15], 1):
                    hot = item.get("hot_score", 0)
                    hot_str = f"  `{hot:,}`" if hot > 0 else ""
                    if i <= 3:
                        st.markdown(f"**{i}. {item['title']}**{hot_str}")
                    else:
                        st.markdown(f"{i}. {item['title']}{hot_str}")

        st.info(f"共获取 {len(results)} 条热搜")


# ===== Tab2: 智能选题 =====
with tab2:
    st.markdown("### 智能选题推荐")
    st.caption("热搜 + AI联想扩展 + 智能打分排序，帮你找到最有潜力的选题")

    col1, col2, col3 = st.columns(3)
    with col1:
        track = st.text_input("📌 内容赛道", placeholder="如：历史、科技、美食、育儿", key="topic_track")
    with col2:
        seeds = st.text_input("🌱 种子关键词（可选）", placeholder="逗号分隔，如：朱元璋,明朝", key="topic_seeds")
    with col3:
        topic_count = st.slider("📊 推荐数量", 5, 30, 10, key="topic_count")

    col_a, col_b = st.columns([1, 1])
    with col_a:
        use_hot = st.checkbox("结合实时热搜", value=True, key="topic_use_hot")
    with col_b:
        topic_btn = st.button("🎯 开始选题", type="primary", use_container_width=True)

    if topic_btn:
        if not _premium_gate("智能选题"):
            pass
        else:
            seed_list = [k.strip() for k in seeds.split(",") if k.strip()] if seeds else None
            with st.spinner("AI正在分析选题... 需要30-60秒"):
                try:
                    results = topic_engine.auto_select(
                        seed_keywords=seed_list,
                        track=track,
                        count=topic_count,
                        use_hot=use_hot,
                    )
                    st.session_state["scored_topics"] = results
                    key_manager.consume_usage(st.session_state.get("card_key", ""))
                except Exception as e:
                    st.error(f"选题失败: {e}")

    if "scored_topics" in st.session_state and st.session_state["scored_topics"]:
        results = st.session_state["scored_topics"]
        st.markdown("---")
        st.markdown(f"#### 🏆 Top {len(results)} 选题推荐")

        for i, item in enumerate(results, 1):
            score = item.get("score", 0)
            reason = item.get("reason", "")
            topic_text = item.get("topic", "")

            if score >= 8:
                color = "#28a745"
                label = "强烈推荐"
            elif score >= 6:
                color = "#ffc107"
                label = "值得做"
            else:
                color = "#6c757d"
                label = "一般"

            with st.container():
                c1, c2 = st.columns([5, 1])
                with c1:
                    st.markdown(f"**{i}. {topic_text}**")
                    if reason:
                        st.caption(f"💡 {reason}")
                with c2:
                    st.markdown(f'<span style="background:{color};color:white;padding:4px 12px;border-radius:12px;font-weight:bold;">{score}分 {label}</span>', unsafe_allow_html=True)
                st.divider()


# ===== Tab3: 脚本生成 =====
with tab3:
    st.markdown("### 短视频脚本生成")
    st.caption("输入选题，AI自动生成完整的短视频配音脚本，支持12种风格和4个平台")

    col1, col2 = st.columns([3, 1])
    with col1:
        script_topic = st.text_input(
            "📌 输入选题",
            placeholder="如：为什么故宫屋顶没有鸟粪",
            key="script_topic",
        )
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        script_btn = st.button("📝 生成脚本", type="primary", use_container_width=True)

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        style_options = [s["name"] for s in script_gen.list_styles()]
        style_descriptions = {s["name"]: s["description"] for s in script_gen.list_styles()}
        script_style = st.selectbox(
            "🎨 脚本风格",
            style_options,
            index=0,
            help="\n".join([f"• {k}: {v}" for k, v in style_descriptions.items()]),
            key="script_style",
        )
    with col_b:
        platform_options = [p["name"] for p in script_gen.list_platforms()]
        script_platform = st.selectbox("📱 目标平台", platform_options, index=0, key="script_platform")
    with col_c:
        script_duration = st.slider("⏱️ 目标时长（秒）", 15, 300, 60, step=15, key="script_duration")

    # 如果有智能选题结果，提供快捷选择
    if "scored_topics" in st.session_state and st.session_state["scored_topics"]:
        with st.expander("💡 从智能选题结果中选择"):
            topic_names = [item.get("topic", "") for item in st.session_state["scored_topics"]]
            selected = st.radio("选择一个选题：", topic_names, key="quick_topic")
            if st.button("使用该选题", key="use_topic_btn"):
                st.session_state["script_topic"] = selected
                st.rerun()

    if script_btn:
        if not _premium_gate("脚本生成"):
            pass
        elif not script_topic:
            st.error("请输入选题")
        else:
            with st.spinner("AI正在创作脚本... 需要15-30秒"):
                try:
                    result = script_gen.generate_script(
                        topic=script_topic,
                        style=script_style,
                        duration_seconds=script_duration,
                        platform=script_platform,
                    )
                    st.session_state["generated_script"] = result
                    key_manager.consume_usage(st.session_state.get("card_key", ""))
                except Exception as e:
                    st.error(f"生成失败: {e}")

    if "generated_script" in st.session_state and st.session_state["generated_script"]:
        result = st.session_state["generated_script"]

        st.markdown("---")

        # 元信息行
        meta_cols = st.columns(4)
        meta_cols[0].metric("📌 标题", result.get("title", ""))
        meta_cols[1].metric("✍️ 字数", f"{result.get('word_count', 0)} 字")
        meta_cols[2].metric("⏱️ 预估时长", f"{result.get('estimated_duration_seconds', 0)} 秒")
        meta_cols[3].metric("🎨 风格", result.get("style", ""))

        st.markdown("#### 📄 完整脚本")

        # 分段展示
        if result.get("hook"):
            st.markdown("**🎣 开场钩子**")
            st.info(result["hook"])

        if result.get("body"):
            st.markdown("**📖 正文主体**")
            st.success(result["body"])

        if result.get("cta"):
            st.markdown("**📢 结尾引导**")
            st.warning(result["cta"])

        # 复制全文
        st.markdown("#### 📋 一键复制")
        st.code(result.get("full_script", ""), language=None)


# ===== Tab4: 分镜生成 =====
with tab4:
    st.markdown("### AI视频分镜提示词")
    st.caption("生成可直接复制到可灵/Pika/Runway使用的分镜提示词")

    if "generated_script" in st.session_state and st.session_state["generated_script"]:
        prev = st.session_state["generated_script"]
        st.info(f"检测到已生成的脚本：**{prev.get('title', '')}**（{prev.get('word_count', 0)}字）")
        use_prev = st.checkbox("使用上面生成的脚本", value=True, key="use_prev_script")
    else:
        use_prev = False

    if not use_prev:
        vc_topic = st.text_input("选题", placeholder="视频选题", key="vc_topic")
        vc_script = st.text_area("脚本内容", placeholder="粘贴你的完整脚本文案...", height=200, key="vc_script")
        vc_duration = st.number_input("时长（秒）", min_value=10, max_value=600, value=60, key="vc_duration")
        vc_platform = st.selectbox("目标平台", ["通用", "抖音", "B站", "小红书"], key="vc_platform")
    else:
        vc_topic = prev.get("topic", "")
        vc_script = prev.get("full_script", "")
        vc_duration = prev.get("estimated_duration_seconds", 60)
        vc_platform = prev.get("platform", "通用")

    vc_btn = st.button("🎬 生成分镜", type="primary", use_container_width=True)

    if vc_btn:
        if not _premium_gate("分镜生成"):
            pass
        elif not vc_script:
            st.error("请先生成或输入脚本内容")
        else:
            with st.spinner("AI正在生成分镜... 需要30-60秒"):
                try:
                    cues = script_gen.generate_visual_cues(
                        topic=vc_topic,
                        script_text=vc_script,
                        duration=vc_duration,
                        platform=vc_platform,
                    )
                    st.session_state["visual_cues"] = cues
                    key_manager.consume_usage(st.session_state.get("card_key", ""))
                except Exception as e:
                    st.error(f"生成失败: {e}")

    if "visual_cues" in st.session_state and st.session_state["visual_cues"]:
        cues = st.session_state["visual_cues"]
        st.markdown("---")
        st.markdown(f"#### 🎬 共 {len(cues)} 个分镜")

        for shot in cues:
            shot_num = shot.get("shot_number", "?")
            timestamp = shot.get("timestamp", "")

            with st.expander(f"🎞️ 镜头 {shot_num}  |  {timestamp}", expanded=True):
                if shot.get("narration"):
                    st.markdown(f"**🎙️ 配音：** {shot['narration']}")

                if shot.get("scene"):
                    st.markdown(f"**🎬 画面：** {shot['scene']}")

                if shot.get("camera"):
                    st.markdown(f"**📷 镜头：** {shot['camera']}")

                if shot.get("style"):
                    st.markdown(f"**🎨 风格：** {shot['style']}")

                col_cn, col_en = st.columns(2)
                with col_cn:
                    if shot.get("prompt_cn"):
                        st.markdown("**🇨🇳 中文提示词（可灵/Vidu）**")
                        st.code(shot["prompt_cn"], language=None)
                with col_en:
                    if shot.get("prompt_en"):
                        st.markdown("**🇺🇸 英文提示词（Pika/Runway）**")
                        st.code(shot["prompt_en"], language=None)
