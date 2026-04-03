"""AI短视频内容工作台 — 选题·脚本·分镜 一站搞定"""

import os
import json
import base64
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
import content_analyzer


# ============================================================
# 自定义样式
# ============================================================
st.markdown("""
<style>
    /* ========== 全局基础 ========== */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }

    /* ========== 主标题区 ========== */
    .main-title {
        text-align: center;
        padding: 1.5rem 0 0.3rem 0;
    }
    .main-title h1 {
        background: linear-gradient(135deg, #0ea5e9 0%, #38bdf8 50%, #7dd3fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.6rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        line-height: 1.2;
    }
    .subtitle {
        text-align: center;
        color: #94a3b8;
        font-size: 1.05rem;
        font-weight: 400;
        letter-spacing: 0.08em;
        margin-bottom: 1.8rem;
    }

    /* ========== 隐藏 Streamlit Cloud 默认UI ========== */
    [data-testid="manage-app-button"],
    .stAppDeployButton,
    #MainMenu,
    footer,
    [data-testid="stStatusWidget"],
    ._profileContainer_gzau3_53,
    ._container_gzau3_1,
    .viewerBadge_container__r5tak,
    .viewerBadge_link__qRIco,
    [data-testid="stAppViewBlockContainer"] > div:last-child > div[data-testid="stVerticalBlock"] > div:last-child iframe {
        display: none !important;
        visibility: hidden !important;
    }

    /* ========== Tab 样式 ========== */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: #f1f5f9;
        border-radius: 12px;
        padding: 4px;
        border: 1px solid #e2e8f0;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        font-size: 0.9rem;
        font-weight: 500;
        border-radius: 8px;
        color: #64748b;
        transition: all 0.2s ease;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background: #e2e8f0;
        color: #1e293b;
    }
    .stTabs [aria-selected="true"] {
        background: white !important;
        color: #0ea5e9 !important;
        font-weight: 600 !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }
    .stTabs [data-baseweb="tab-highlight"] {
        display: none;
    }
    .stTabs [data-baseweb="tab-border"] {
        display: none;
    }

    /* ========== 按钮 ========== */
    .stButton > button[kind="primary"],
    .stFormSubmitButton > button {
        background: linear-gradient(135deg, #0ea5e9 0%, #38bdf8 100%) !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.6rem 1.5rem !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        letter-spacing: 0.02em;
        box-shadow: 0 4px 14px rgba(14, 165, 233, 0.35) !important;
        transition: all 0.25s ease !important;
    }
    .stButton > button[kind="primary"]:hover,
    .stFormSubmitButton > button:hover {
        box-shadow: 0 6px 20px rgba(14, 165, 233, 0.5) !important;
        transform: translateY(-1px) !important;
    }
    .stButton > button:not([kind="primary"]) {
        border-radius: 10px !important;
        border: 1px solid #e2e8f0 !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:not([kind="primary"]):hover {
        border-color: #0ea5e9 !important;
        color: #0ea5e9 !important;
        background: #f0f9ff !important;
    }

    /* ========== 输入框/表单 ========== */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div,
    .stMultiSelect > div > div {
        border-radius: 10px !important;
        border: 1.5px solid #e2e8f0 !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #0ea5e9 !important;
        box-shadow: 0 0 0 3px rgba(14,165,233,0.1) !important;
    }

    /* ========== 指标卡片 ========== */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #f8fafc, #f1f5f9);
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1rem 1.2rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.8rem !important;
        color: #94a3b8 !important;
        font-weight: 500 !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        color: #1e293b !important;
    }

    /* ========== Expander ========== */
    .streamlit-expanderHeader {
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        border-radius: 10px !important;
        background: #f8fafc !important;
        border: 1px solid #e2e8f0 !important;
    }
    .streamlit-expanderContent {
        border: 1px solid #e2e8f0 !important;
        border-top: none !important;
        border-radius: 0 0 10px 10px !important;
    }

    /* ========== 提示框美化 ========== */
    .stAlert {
        border-radius: 10px !important;
        border: none !important;
    }
    div[data-testid="stNotification"] {
        border-radius: 10px !important;
    }

    /* ========== 侧边栏 ========== */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%) !important;
    }
    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown li,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: #e2e8f0 !important;
    }
    section[data-testid="stSidebar"] .stMarkdown strong {
        color: #f8fafc !important;
    }
    section[data-testid="stSidebar"] .stDivider {
        border-color: rgba(255,255,255,0.08) !important;
    }
    section[data-testid="stSidebar"] .stTextInput > div > div > input {
        background: rgba(255,255,255,0.06) !important;
        border: 1.5px solid rgba(255,255,255,0.12) !important;
        color: #f8fafc !important;
        border-radius: 10px !important;
    }
    section[data-testid="stSidebar"] .stTextInput > div > div > input:focus {
        border-color: #38bdf8 !important;
        box-shadow: 0 0 0 3px rgba(56,189,248,0.15) !important;
    }
    section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #38bdf8 0%, #7dd3fc 100%) !important;
        box-shadow: 0 4px 14px rgba(56, 189, 248, 0.3) !important;
    }
    section[data-testid="stSidebar"] .stButton > button:not([kind="primary"]) {
        border-color: rgba(255,255,255,0.15) !important;
        color: #e2e8f0 !important;
        background: transparent !important;
    }
    section[data-testid="stSidebar"] .stButton > button:not([kind="primary"]):hover {
        border-color: #38bdf8 !important;
        color: #38bdf8 !important;
        background: rgba(56,189,248,0.08) !important;
    }
    section[data-testid="stSidebar"] .stAlert {
        background: rgba(255,255,255,0.05) !important;
        color: #e2e8f0 !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stNotification"] p {
        color: #e2e8f0 !important;
    }

    /* ========== 分割线 ========== */
    hr {
        border: none !important;
        height: 1px !important;
        background: linear-gradient(90deg, transparent, #e2e8f0, transparent) !important;
        margin: 1.5rem 0 !important;
    }

    /* ========== 下载按钮 ========== */
    .stDownloadButton > button {
        border-radius: 10px !important;
        border: 1.5px solid #e2e8f0 !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
        background: #f8fafc !important;
    }
    .stDownloadButton > button:hover {
        border-color: #0ea5e9 !important;
        color: #0ea5e9 !important;
        background: #f0f9ff !important;
        box-shadow: 0 2px 8px rgba(14,165,233,0.12) !important;
    }

    /* ========== Code 块 ========== */
    .stCodeBlock {
        border-radius: 10px !important;
        border: 1px solid #e2e8f0 !important;
    }

    /* ========== 自定义组件 ========== */
    .score-badge {
        display: inline-block;
        background: linear-gradient(135deg, #0ea5e9, #38bdf8);
        color: white;
        padding: 3px 12px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
        letter-spacing: 0.02em;
        box-shadow: 0 2px 8px rgba(14,165,233,0.25);
    }
    .hot-badge {
        display: inline-block;
        background: linear-gradient(135deg, #ef4444, #f97316);
        color: white;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        box-shadow: 0 2px 6px rgba(239,68,68,0.25);
    }
    .platform-tag {
        display: inline-block;
        background: #f1f5f9;
        border: 1px solid #e2e8f0;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 500;
        color: #475569;
        margin-right: 4px;
    }

    /* ========== 表格 ========== */
    .stMarkdown table {
        border-collapse: separate !important;
        border-spacing: 0 !important;
        border-radius: 10px !important;
        overflow: hidden !important;
        border: 1px solid #e2e8f0 !important;
        width: 100% !important;
    }
    .stMarkdown table thead tr th {
        background: #f8fafc !important;
        font-weight: 600 !important;
        color: #475569 !important;
        padding: 0.75rem 1rem !important;
        font-size: 0.85rem !important;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        border-bottom: 2px solid #e2e8f0 !important;
    }
    .stMarkdown table tbody tr td {
        padding: 0.65rem 1rem !important;
        border-bottom: 1px solid #f1f5f9 !important;
        color: #334155 !important;
        font-size: 0.9rem !important;
    }
    .stMarkdown table tbody tr:last-child td {
        border-bottom: none !important;
    }
    .stMarkdown table tbody tr:hover td {
        background: #f8fafc !important;
    }

    /* ========== 滚动条 ========== */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: transparent;
    }
    ::-webkit-scrollbar-thumb {
        background: #cbd5e1;
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #94a3b8;
    }

    /* ========== Spinner ========== */
    .stSpinner > div {
        border-radius: 10px;
    }

    /* ========== Checkbox / Radio ========== */
    .stCheckbox label, .stRadio label {
        font-weight: 500 !important;
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
    - 试用卡（3次免费体验）
    - 体验卡（3天免费）
    - 周卡 ¥9.9 / 月卡 ¥29 / 年卡 ¥199
    """)
    return False


with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:0.5rem 0 0.2rem 0;">
        <span style="font-size:1.6rem;font-weight:800;background:linear-gradient(135deg,#38bdf8,#7dd3fc);
        -webkit-background-clip:text;-webkit-text-fill-color:transparent;">🎬 AI 工作台</span>
        <div style="font-size:0.75rem;color:#94a3b8;margin-top:2px;letter-spacing:0.1em;">SHORT VIDEO CONTENT STUDIO</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # === 卡密验证 ===
    st.markdown("### 🔑 卡密")

    # 从URL参数恢复卡密（刷新后不丢失，加密存储）
    _params = st.query_params
    if "t" in _params and not st.session_state.get("card_key"):
        try:
            st.session_state["card_key"] = base64.b64decode(_params["t"]).decode()
        except Exception:
            pass

    _is_activated = bool(st.session_state.get("card_key"))

    if _is_activated:
        # ===== 状态B：已激活 =====
        _active_key = st.session_state["card_key"]
        # 显示已激活的卡密（脱敏）
        masked = _active_key[:4] + "····" + _active_key[-4:] if len(_active_key) > 8 else "····"
        st.text_input("当前卡密", value=masked, disabled=True)

        # 实时验证
        v = key_manager.validate_key(_active_key)
        st.session_state["key_validation"] = v

        if v.get("valid"):
            st.success(f"✅ {v.get('plan_name', '')} | {v.get('remaining_info', '')}")
            # 试用卡(按次数)不显示到期时间
            if v.get("expires_at") and not v.get("total_limit"):
                st.caption(f"到期时间：{v['expires_at']}")
            # 切换按钮
            if st.button("🔄 切换卡密", use_container_width=True):
                st.session_state.pop("card_key", None)
                st.session_state.pop("key_validation", None)
                if "t" in st.query_params:
                    del st.query_params["t"]
                st.rerun()
        else:
            st.error(v.get("message", "卡密无效"))
            # 过期/失效自动解锁输入框
            if st.button("🔓 更换卡密", type="primary", use_container_width=True):
                st.session_state.pop("card_key", None)
                st.session_state.pop("key_validation", None)
                if "t" in st.query_params:
                    del st.query_params["t"]
                st.rerun()
    else:
        # ===== 状态A：未激活 =====
        input_card_key = st.text_input(
            "输入卡密",
            value="",
            placeholder="ACP-XXXX-XXXX-XXXX",
            type="password",
            help="输入卡密解锁全部功能",
        )

        if st.button("🔓 激活卡密", type="primary", use_container_width=True):
            if input_card_key:
                result = key_manager.validate_key(input_card_key)
                if result.get("valid"):
                    st.session_state["card_key"] = input_card_key
                    st.session_state["key_validation"] = result
                    st.query_params["t"] = base64.b64encode(input_card_key.encode()).decode()
                    st.rerun()
                else:
                    st.error(result.get("message", "卡密无效"))
            else:
                st.warning("请先输入卡密")

        st.session_state["key_validation"] = None
        st.info("🔓 输入卡密解锁脚本生成等付费功能")

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

    st.markdown("### 📊 功能导航")
    st.markdown("""
    <div style="font-size:0.85rem;line-height:2;">
    <span style="color:#34d399;">●</span> <b>热搜榜单</b> <span style="background:rgba(52,211,153,0.15);color:#34d399;padding:1px 8px;border-radius:10px;font-size:0.7rem;font-weight:600;">免费</span><br>
    <span style="color:#38bdf8;">●</span> <b>智能选题</b><br>
    <span style="color:#38bdf8;">●</span> <b>脚本生成</b> <span style="color:#64748b;font-size:0.75rem;">12种风格</span><br>
    <span style="color:#38bdf8;">●</span> <b>分镜提示词</b><br>
    <span style="color:#38bdf8;">●</span> <b>一键出片</b> <span style="background:rgba(251,191,36,0.15);color:#fbbf24;padding:1px 8px;border-radius:10px;font-size:0.7rem;font-weight:600;">推荐</span><br>
    <span style="color:#38bdf8;">●</span> <b>爆款拆解</b> <span style="background:rgba(251,191,36,0.15);color:#fbbf24;padding:1px 8px;border-radius:10px;font-size:0.7rem;font-weight:600;">独家</span><br>
    <span style="color:#38bdf8;">●</span> <b>标题优化</b><br>
    <span style="color:#38bdf8;">●</span> <b>脚本诊断</b> <span style="background:rgba(251,191,36,0.15);color:#fbbf24;padding:1px 8px;border-radius:10px;font-size:0.7rem;font-weight:600;">独家</span>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    st.markdown("""
    <div style="text-align:center;padding:0.3rem 0;">
        <div style="font-size:0.8rem;color:#94a3b8;">关注公众号回复「体验」</div>
        <div style="font-size:0.8rem;color:#94a3b8;">获取免费试用卡密</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    st.markdown("""
    <div style="text-align:center;padding:0.2rem 0;">
        <div style="font-size:0.7rem;color:#475569;letter-spacing:0.05em;">Powered by DeepSeek AI</div>
        <div style="font-size:0.65rem;color:#334155;margin-top:2px;">v1.0 · Made with ❤️</div>
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# 标题
# ============================================================
st.markdown('<div class="main-title"><h1>🎬 AI短视频内容工作台</h1></div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">选题 · 脚本 · 分镜 — 一站搞定，5分钟产出一条视频的全部文案</div>', unsafe_allow_html=True)

# ============================================================
# 新用户引导（未激活卡密时展示产品价值）
# ============================================================
if not _check_premium():
    st.markdown("""
<div style="background:linear-gradient(135deg,rgba(14,165,233,0.04),rgba(56,189,248,0.06));
border:1px solid rgba(14,165,233,0.15);border-radius:16px;padding:2rem 2.5rem;margin-bottom:2rem;
box-shadow:0 4px 24px rgba(14,165,233,0.06);">

<div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:1rem;">
<span style="font-size:1.3rem;">👋</span>
<span style="font-size:1.15rem;font-weight:700;color:#1e293b;">欢迎使用 AI 短视频内容工作台</span>
</div>

<div style="color:#64748b;font-size:0.92rem;margin-bottom:1.2rem;">输入卡密即可解锁以下 <b style="color:#0ea5e9;">7 项 AI 功能</b>，5分钟产出一条视频的全套文案：</div>

| 功能 | 说明 | 效果 |
|------|------|------|
| 🎯 **智能选题** | 热搜 + AI 联想 + 智能打分 | 30秒找到高潜力选题 |
| 📝 **脚本生成** | 12种风格，自动写完整配音稿 | 1分钟出完整脚本 |
| 🎬 **分镜提示词** | 自动生成可灵/Pika提示词 | 直接复制到AI视频工具 |
| 🚀 **一键出片** | 选题→脚本→分镜全自动 | 5分钟搞定全套文案 |
| 🔍 **爆款拆解** | 逆向分析爆款文案结构 | 学会"为什么能火" |
| 🏷️ **标题优化** | AI生成+对比标题点击率 | 选出最强标题 |
| 📊 **脚本诊断** | 六维评分+完播率预测 | 发布前精准优化 |

<div style="margin-top:1rem;padding:0.75rem 1rem;background:rgba(52,211,153,0.08);border-radius:10px;
border:1px solid rgba(52,211,153,0.2);font-size:0.9rem;">
🔥 <b style="color:#059669;">热搜榜单完全免费</b>，无需卡密！← 左侧输入卡密解锁全部 AI 功能
</div>

</div>
""", unsafe_allow_html=True)

# ============================================================
# 主体 Tabs
# ============================================================
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "🔥 热搜榜单", "🎯 智能选题", "📝 脚本生成", "🎬 分镜提示词",
    "🚀 一键出片", "🔍 爆款拆解", "🏷️ 标题优化", "📊 脚本诊断",
])


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
                from datetime import datetime as _dt
                st.session_state["hot_topics_time"] = _dt.now().strftime("%H:%M:%S")
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

        _fetch_time = st.session_state.get("hot_topics_time", "")
        st.info(f"共获取 {len(results)} 条热搜　|　抓取时间：{_fetch_time}")


# ===== Tab2: 智能选题 =====
with tab2:
    st.markdown("### 智能选题推荐")
    st.caption("热搜 + AI联想扩展 + 智能打分排序，帮你找到最有潜力的选题")

    with st.form("topic_form"):
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
            topic_btn = st.form_submit_button("🎯 开始选题", type="primary", use_container_width=True)

    if topic_btn:
        if not _premium_gate("智能选题"):
            pass
        else:
            seed_list = [k.strip() for k in seeds.split(",") if k.strip()] if seeds else None
            results = None
            with st.status("AI正在分析选题...", expanded=True) as status:
                try:
                    all_topics = []

                    if use_hot:
                        st.write("📡 抓取实时热搜...")
                        hot = topic_engine.fetch_hot_topics()
                        hot_titles = [h["title"] for h in hot if h["title"]]
                        all_topics.extend(hot_titles)
                        st.write(f"✅ 获取 {len(hot_titles)} 条热搜")

                    if seed_list:
                        st.write("🧠 AI联想扩展关键词...")
                        expanded = topic_engine.expand_topics(
                            seed_list, count=topic_count * 2, track=track
                        )
                        all_topics.extend(expanded)
                        st.write(f"✅ 扩展出 {len(expanded)} 个候选选题")

                    if all_topics:
                        st.write("🔄 去重过滤...")
                        unique = topic_engine.deduplicate(all_topics)
                        st.write(f"✅ 去重后 {len(unique)} 个")

                        st.write("⚖️ AI智能打分排序...")
                        scored = topic_engine.score_topics(unique[:30], track=track)
                        scored = scored[:topic_count]
                        st.write(f"✅ 筛选出 Top {len(scored)} 选题")

                        st.session_state["scored_topics"] = scored
                        results = scored
                        status.update(label="✅ 选题完成！", state="complete", expanded=False)
                    else:
                        status.update(label="⚠️ 没有获取到选题素材", state="error")
                        st.warning("请输入种子关键词或勾选结合实时热搜")
                except Exception as e:
                    status.update(label="❌ 选题失败", state="error")
                    st.error(f"选题失败: {e}")
            if results:
                key_manager.consume_usage(st.session_state.get("card_key", ""))

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

    # 如果有智能选题结果，提供快捷选择（放在form外面，因为含st.button）
    if "scored_topics" in st.session_state and st.session_state["scored_topics"]:
        with st.expander("💡 从智能选题结果中选择"):
            topic_names = [item.get("topic", "") for item in st.session_state["scored_topics"]]
            selected = st.radio("选择一个选题：", topic_names, key="quick_topic")
            if st.button("使用该选题", key="use_topic_btn"):
                st.session_state["script_topic"] = selected
                st.rerun()

    with st.form("script_form"):
        script_topic = st.text_input(
            "📌 输入选题",
            placeholder="如：为什么故宫屋顶没有鸟粪",
            key="script_topic",
        )

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

        script_btn = st.form_submit_button("📝 生成脚本", type="primary", use_container_width=True)

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
                except Exception as e:
                    st.error(f"生成失败: {e}")
                    result = None
            if result:
                key_manager.consume_usage(st.session_state.get("card_key", ""))

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

        # 复制全文 + 下载
        st.markdown("#### 📋 一键复制")
        st.code(result.get("full_script", ""), language=None)
        _script_text = result.get("full_script", "")
        _script_title = result.get("title", "脚本")
        st.download_button(
            "⬇️ 下载脚本",
            data=_script_text,
            file_name=f"{_script_title}.txt",
            mime="text/plain",
            use_container_width=True,
        )

        # 跨Tab联动：一键跳转诊断
        if st.button("🔍 立即诊断这个脚本", use_container_width=True, key="script_to_diag"):
            st.session_state["_diag_original_script"] = _script_text
            st.session_state["_diag_platform"] = result.get("platform", "通用")
            st.info("💡 请切换到「📊 脚本诊断」Tab，脚本已自动填入")


# ===== Tab4: 分镜生成 =====
with tab4:
    st.markdown("### AI视频分镜提示词")
    st.caption("生成可直接复制到可灵/Pika/Runway使用的分镜提示词")

    _has_prev_script = "generated_script" in st.session_state and st.session_state["generated_script"]

    if _has_prev_script:
        prev = st.session_state["generated_script"]
        st.info(f"检测到已生成的脚本：**{prev.get('title', '')}**（{prev.get('word_count', 0)}字）")
        use_prev = st.checkbox("使用上面生成的脚本", value=True, key="use_prev_script")
    else:
        use_prev = False

    if use_prev:
        vc_topic = prev.get("topic", "")
        vc_script = prev.get("full_script", "")
        vc_duration = prev.get("estimated_duration_seconds", 60)
        vc_platform = prev.get("platform", "通用")
        vc_btn = st.button("🎬 生成分镜", type="primary", use_container_width=True)
    else:
        with st.form("visual_cue_form"):
            vc_topic = st.text_input("选题", placeholder="视频选题", key="vc_topic")
            vc_script = st.text_area("脚本内容", placeholder="粘贴你的完整脚本文案...", height=200, key="vc_script")
            vc_col1, vc_col2 = st.columns(2)
            with vc_col1:
                vc_duration = st.number_input("⏱️ 时长（秒）", min_value=10, max_value=600, value=60, key="vc_duration")
            with vc_col2:
                vc_platform = st.selectbox("📱 目标平台", ["通用", "抖音", "B站", "小红书"], key="vc_platform")
            vc_btn = st.form_submit_button("🎬 生成分镜", type="primary", use_container_width=True)

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
                except Exception as e:
                    st.error(f"生成失败: {e}")
                    cues = None
            if cues:
                key_manager.consume_usage(st.session_state.get("card_key", ""))

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

        # 分镜一键导出
        _export_lines = []
        for shot in cues:
            _export_lines.append(f"=== 镜头 {shot.get('shot_number', '?')} | {shot.get('timestamp', '')} ===")
            if shot.get("narration"):
                _export_lines.append(f"配音：{shot['narration']}")
            if shot.get("scene"):
                _export_lines.append(f"画面：{shot['scene']}")
            if shot.get("prompt_cn"):
                _export_lines.append(f"中文提示词：{shot['prompt_cn']}")
            if shot.get("prompt_en"):
                _export_lines.append(f"英文提示词：{shot['prompt_en']}")
            _export_lines.append("")
        st.download_button(
            "⬇️ 下载全部分镜",
            data="\n".join(_export_lines),
            file_name="分镜提示词.txt",
            mime="text/plain",
            use_container_width=True,
        )

        # 使用指南
        st.markdown("---")
        st.markdown("#### 📖 下一步：用提示词生成AI视频")
        st.markdown("""
提示词已就绪！复制上方提示词，粘贴到以下任一AI视频工具即可生成画面：

| 工具 | 语言 | 特点 | 链接 |
|------|------|------|------|
| **可灵** | 🇨🇳 中文 | 国产首选，效果好 | [klingai.kuaishou.com](https://klingai.kuaishou.com) |
| **Vidu** | 🇨🇳 中文 | 生数科技出品，速度快 | [vidu.studio](https://www.vidu.studio) |
| **Pika** | 🇺🇸 英文 | 风格化强，适合创意 | [pika.art](https://pika.art) |
| **Runway** | 🇺🇸 英文 | Gen-3 Alpha，画质顶级 | [runwayml.com](https://runwayml.com) |
| **即梦** | 🇨🇳 中文 | 字节出品，免费额度多 | [jimeng.jianying.com](https://jimeng.jianying.com) |

**操作步骤：**
1. 复制对应语言的提示词（中文→可灵/Vidu/即梦，英文→Pika/Runway）
2. 打开工具网站，选择"文生视频"或"图生视频"
3. 粘贴提示词，设置时长（建议4-6秒/镜头）
4. 生成后下载，用剪映/CapCut拼接所有镜头 + 配音即完成
        """)


# ===== Tab5: 一键出片 =====
with tab5:
    st.markdown("### 🚀 一键出片")
    st.caption("输入赛道和关键词，AI自动完成 选题→脚本→分镜 全流程，一步到位")

    with st.form("oneclick_form"):
        op_col1, op_col2 = st.columns(2)
        with op_col1:
            op_track = st.text_input("📌 内容赛道", placeholder="如：历史、科技、美食", key="op_track")
        with op_col2:
            op_seeds = st.text_input("🌱 种子关键词", placeholder="逗号分隔，如：朱元璋,明朝", key="op_seeds")

        op_col_a, op_col_b, op_col_c = st.columns(3)
        with op_col_a:
            op_style_options = [s["name"] for s in script_gen.list_styles()]
            op_style = st.selectbox("🎨 脚本风格", op_style_options, index=0, key="op_style")
        with op_col_b:
            op_platform_options = [p["name"] for p in script_gen.list_platforms()]
            op_platform = st.selectbox("📱 目标平台", op_platform_options, index=0, key="op_platform")
        with op_col_c:
            op_duration = st.slider("⏱️ 目标时长（秒）", 15, 300, 60, step=15, key="op_duration")

        op_btn = st.form_submit_button("🚀 一键生成全部", type="primary", use_container_width=True)

    if op_btn:
        if not _premium_gate("一键出片"):
            pass
        elif not op_track and not op_seeds:
            st.error("请至少输入赛道或种子关键词")
        else:
            op_seed_list = [k.strip() for k in op_seeds.split(",") if k.strip()] if op_seeds else []
            # 赛道本身也作为种子词，确保生成内容与赛道相关
            if op_track and op_track not in op_seed_list:
                op_seed_list.insert(0, op_track)
            op_result = {}

            with st.status("🚀 一键出片流水线启动...", expanded=True) as op_status:
                try:
                    # Step 1: 智能选题（用户输入优先，热搜仅作补充）
                    st.write("**Step 1/3** — 📡 智能选题...")
                    all_topics = []

                    # 用户关键词优先：扩展更多候选
                    if op_seed_list:
                        st.write("  🧠 基于你的关键词AI联想扩展...")
                        expanded = topic_engine.expand_topics(
                            op_seed_list, count=25, track=op_track
                        )
                        all_topics.extend(expanded)
                        st.write(f"  ✅ 扩展出 {len(expanded)} 个相关选题")

                    # 热搜作为补充（最多取10条，避免喧宾夺主）
                    st.write("  📡 抓取热搜作为灵感补充...")
                    hot = topic_engine.fetch_hot_topics()
                    hot_titles = [h["title"] for h in hot if h["title"]][:10]
                    all_topics.extend(hot_titles)
                    st.write(f"  ✅ 补充 {len(hot_titles)} 条热搜")

                    unique = topic_engine.deduplicate(all_topics)
                    scored = topic_engine.score_topics(unique[:30], track=op_track)
                    best_topic = scored[0] if scored else None

                    if not best_topic:
                        op_status.update(label="❌ 未找到合适选题", state="error")
                        st.error("选题失败，请调整关键词重试")
                    else:
                        topic_text = best_topic["topic"]
                        st.write(f"  🏆 最佳选题：**{topic_text}**（{best_topic.get('score', 0)}分）")
                        op_result["topic"] = best_topic

                        # Step 2: 脚本生成
                        st.write(f"**Step 2/3** — 📝 生成脚本...")
                        script_result = script_gen.generate_script(
                            topic=topic_text,
                            style=op_style,
                            duration_seconds=op_duration,
                            platform=op_platform,
                        )
                        op_result["script"] = script_result
                        st.write(f"  ✅ 脚本 {script_result.get('word_count', 0)} 字")

                        # Step 3: 分镜生成
                        st.write(f"**Step 3/3** — 🎬 生成分镜...")
                        cues = script_gen.generate_visual_cues(
                            topic=topic_text,
                            script_text=script_result.get("full_script", ""),
                            duration=op_duration,
                            platform=op_platform,
                        )
                        op_result["cues"] = cues
                        st.write(f"  ✅ 共 {len(cues)} 个分镜")

                        op_status.update(label="✅ 一键出片完成！", state="complete", expanded=False)
                        st.session_state["oneclick_result"] = op_result
                        key_manager.consume_usage(st.session_state.get("card_key", ""), count=3)

                except Exception as e:
                    op_status.update(label="❌ 流水线失败", state="error")
                    st.error(f"生成失败: {e}")

    # 展示一键出片结果
    if "oneclick_result" in st.session_state and st.session_state["oneclick_result"]:
        opr = st.session_state["oneclick_result"]
        st.markdown("---")

        # 选题结果
        if opr.get("topic"):
            t = opr["topic"]
            st.markdown(f'#### 🏆 选题：{t["topic"]} <span style="background:#28a745;color:white;padding:2px 10px;border-radius:12px;">{t.get("score", 0)}分</span>', unsafe_allow_html=True)
            if t.get("reason"):
                st.caption(f"💡 {t['reason']}")

        # 脚本结果
        if opr.get("script"):
            s = opr["script"]
            st.markdown("#### 📝 脚本")
            meta_cols = st.columns(4)
            meta_cols[0].metric("📌 标题", s.get("title", ""))
            meta_cols[1].metric("✍️ 字数", f"{s.get('word_count', 0)} 字")
            meta_cols[2].metric("⏱️ 时长", f"{s.get('estimated_duration_seconds', 0)} 秒")
            meta_cols[3].metric("🎨 风格", s.get("style", ""))

            if s.get("hook"):
                st.markdown("**🎣 开场钩子**")
                st.info(s["hook"])
            if s.get("body"):
                st.markdown("**📖 正文主体**")
                st.success(s["body"])
            if s.get("cta"):
                st.markdown("**📢 结尾引导**")
                st.warning(s["cta"])

            st.code(s.get("full_script", ""), language=None)
            _op_dl_col, _op_diag_col = st.columns(2)
            with _op_dl_col:
                st.download_button(
                    "⬇️ 下载脚本",
                    data=s.get("full_script", ""),
                    file_name=f"{s.get('title', '脚本')}.txt",
                    mime="text/plain",
                    use_container_width=True,
                    key="op_dl_script",
                )
            with _op_diag_col:
                if st.button("🔍 诊断这个脚本", use_container_width=True, key="op_to_diag"):
                    st.session_state["_diag_original_script"] = s.get("full_script", "")
                    st.session_state["_diag_platform"] = s.get("platform", "通用")
                    st.info("💡 请切换到「📊 脚本诊断」Tab")

        # 分镜结果
        if opr.get("cues"):
            st.markdown(f"#### 🎬 分镜（共 {len(opr['cues'])} 个）")
            for shot in opr["cues"]:
                with st.expander(f"🎞️ 镜头 {shot.get('shot_number', '?')}  |  {shot.get('timestamp', '')}", expanded=False):
                    if shot.get("narration"):
                        st.markdown(f"**🎙️ 配音：** {shot['narration']}")
                    if shot.get("scene"):
                        st.markdown(f"**🎬 画面：** {shot['scene']}")
                    c1, c2 = st.columns(2)
                    with c1:
                        if shot.get("prompt_cn"):
                            st.markdown("**🇨🇳 中文提示词**")
                            st.code(shot["prompt_cn"], language=None)
                    with c2:
                        if shot.get("prompt_en"):
                            st.markdown("**🇺🇸 英文提示词**")
                            st.code(shot["prompt_en"], language=None)

            _op_export = []
            for shot in opr["cues"]:
                _op_export.append(f"=== 镜头 {shot.get('shot_number', '?')} | {shot.get('timestamp', '')} ===")
                if shot.get("narration"):
                    _op_export.append(f"配音：{shot['narration']}")
                if shot.get("prompt_cn"):
                    _op_export.append(f"中文提示词：{shot['prompt_cn']}")
                if shot.get("prompt_en"):
                    _op_export.append(f"英文提示词：{shot['prompt_en']}")
                _op_export.append("")
            st.download_button(
                "⬇️ 下载全部分镜",
                data="\n".join(_op_export),
                file_name="一键出片_分镜.txt",
                mime="text/plain",
                use_container_width=True,
                key="op_dl_cues",
            )

        # 一键导出完整文档（脚本+分镜合并）
        if opr.get("script") and opr.get("cues"):
            st.markdown("---")
            st.markdown("#### 📦 一键导出完整文档")
            _full_doc = []
            _s = opr["script"]
            _full_doc.append(f"{'='*60}")
            _full_doc.append(f"AI短视频内容工作台 — 一键出片完整文档")
            _full_doc.append(f"{'='*60}\n")
            if opr.get("topic"):
                _full_doc.append(f"【选题】{opr['topic'].get('topic', '')}（{opr['topic'].get('score', 0)}分）")
                if opr['topic'].get('reason'):
                    _full_doc.append(f"【推荐理由】{opr['topic']['reason']}\n")
            _full_doc.append(f"【标题】{_s.get('title', '')}")
            _full_doc.append(f"【风格】{_s.get('style', '')}  |  【时长】{_s.get('estimated_duration_seconds', 0)}秒  |  【字数】{_s.get('word_count', 0)}字\n")
            _full_doc.append(f"{'─'*40}")
            _full_doc.append(f"一、完整脚本")
            _full_doc.append(f"{'─'*40}\n")
            _full_doc.append(_s.get("full_script", ""))
            _full_doc.append(f"\n{'─'*40}")
            _full_doc.append(f"二、分镜提示词（共{len(opr['cues'])}个镜头）")
            _full_doc.append(f"{'─'*40}\n")
            for _shot in opr["cues"]:
                _full_doc.append(f"--- 镜头 {_shot.get('shot_number', '?')} | {_shot.get('timestamp', '')} ---")
                if _shot.get("narration"):
                    _full_doc.append(f"配音：{_shot['narration']}")
                if _shot.get("scene"):
                    _full_doc.append(f"画面：{_shot['scene']}")
                if _shot.get("prompt_cn"):
                    _full_doc.append(f"中文提示词：{_shot['prompt_cn']}")
                if _shot.get("prompt_en"):
                    _full_doc.append(f"英文提示词：{_shot['prompt_en']}")
                _full_doc.append("")
            _full_doc.append(f"{'='*60}")
            _full_doc.append("由 AI短视频内容工作台 生成")
            st.download_button(
                "📦 下载完整文档（脚本+分镜）",
                data="\n".join(_full_doc),
                file_name=f"{_s.get('title', '一键出片')}_完整文档.txt",
                mime="text/plain",
                use_container_width=True,
                key="op_dl_full",
            )

        # 使用指南
        st.markdown("---")
        st.markdown("#### 📖 下一步：用提示词生成AI视频")
        st.markdown("""
提示词已就绪！复制上方提示词，粘贴到以下任一AI视频工具即可生成画面：

| 工具 | 语言 | 特点 | 链接 |
|------|------|------|------|
| **可灵** | 🇨🇳 中文 | 国产首选，效果好 | [klingai.kuaishou.com](https://klingai.kuaishou.com) |
| **Vidu** | 🇨🇳 中文 | 生数科技出品，速度快 | [vidu.studio](https://www.vidu.studio) |
| **Pika** | 🇺🇸 英文 | 风格化强，适合创意 | [pika.art](https://pika.art) |
| **Runway** | 🇺🇸 英文 | Gen-3 Alpha，画质顶级 | [runwayml.com](https://runwayml.com) |
| **即梦** | 🇨🇳 中文 | 字节出品，免费额度多 | [jimeng.jianying.com](https://jimeng.jianying.com) |

**操作步骤：**
1. 复制对应语言的提示词（中文→可灵/Vidu/即梦，英文→Pika/Runway）
2. 打开工具网站，选择"文生视频"或"图生视频"
3. 粘贴提示词，设置时长（建议4-6秒/镜头）
4. 生成后下载，用剪映/CapCut拼接所有镜头 + 配音即完成
        """)


# ===== Tab6: 爆款拆解 =====
with tab6:
    st.markdown("### 🔍 爆款拆解器")
    st.caption("粘贴爆款视频文案，AI逆向拆解结构公式，学会「为什么能火」再复制到新选题")

    with st.form("viral_form"):
        viral_text = st.text_area(
            "📋 粘贴爆款视频文案",
            height=200,
            placeholder="把你看到的爆款视频的配音文案/字幕粘贴到这里...",
            key="viral_text",
        )
        viral_btn = st.form_submit_button("🔍 开始拆解", type="primary", use_container_width=True)

    if viral_btn:
        if not _premium_gate("爆款拆解"):
            pass
        elif not viral_text or len(viral_text.strip()) < 30:
            st.error("请粘贴至少30字的爆款文案")
        else:
            analysis = None
            with st.status("AI正在深度拆解...", expanded=True) as v_status:
                try:
                    st.write("🔬 分析文案结构...")
                    st.write("🧠 提取爆款公式...")
                    analysis = content_analyzer.analyze_viral(viral_text)
                    if analysis.get("error"):
                        v_status.update(label="❌ 拆解失败", state="error")
                        st.error(analysis["error"])
                        analysis = None
                    else:
                        v_status.update(label="✅ 拆解完成！", state="complete", expanded=False)
                        st.session_state["viral_analysis"] = analysis
                except Exception as e:
                    v_status.update(label="❌ 拆解失败", state="error")
                    st.error(f"分析失败: {e}")
            if analysis:
                key_manager.consume_usage(st.session_state.get("card_key", ""))

    if "viral_analysis" in st.session_state and st.session_state["viral_analysis"]:
        a = st.session_state["viral_analysis"]
        st.markdown("---")

        # 总结
        if a.get("summary"):
            st.markdown("#### 💡 核心卖点")
            st.info(a["summary"])

        # 结构拆解
        if a.get("structure"):
            s = a["structure"]
            st.markdown("#### 📐 结构拆解")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("**🎣 钩子类型**")
                st.success(s.get("hook_type", ""))
                if s.get("hook_text"):
                    st.caption(f"原文：「{s['hook_text']}」")
                if s.get("hook_analysis"):
                    st.markdown(f"_{s['hook_analysis']}_")
            with col2:
                st.markdown("**📖 正文模式**")
                st.success(s.get("body_pattern", ""))
                if s.get("body_analysis"):
                    st.markdown(f"_{s['body_analysis']}_")
            with col3:
                st.markdown("**🎯 收尾类型**")
                st.success(s.get("cta_type", ""))
                if s.get("cta_analysis"):
                    st.markdown(f"_{s['cta_analysis']}_")

        # 情绪曲线
        if a.get("emotional_arc"):
            st.markdown("#### 📈 情绪曲线")
            st.info(a["emotional_arc"])

        # 爆款因素
        if a.get("viral_factors"):
            st.markdown("#### ⚡ 爆款因素")
            for vf in a["viral_factors"]:
                score = vf.get("score", 0)
                bar_color = "🟢" if score >= 8 else "🟡" if score >= 6 else "🔴"
                st.markdown(f"{bar_color} **{vf.get('factor', '')}**（{score}/10）")
                st.caption(f"证据：{vf.get('evidence', '')}")

        # 节奏分析
        if a.get("pacing"):
            p = a["pacing"]
            st.markdown("#### 🎵 节奏分析")
            pc1, pc2, pc3 = st.columns(3)
            pc1.metric("节奏", p.get("rhythm", ""))
            pc2.metric("句长", p.get("sentence_avg_length", ""))
            pc3.metric("信息密度", p.get("info_density", ""))

        # 可复用公式（核心价值）
        if a.get("reusable_formula"):
            f = a["reusable_formula"]
            st.markdown("#### 🔑 可复用爆款公式")
            st.markdown(f"**公式名称：** {f.get('name', '')}")
            st.markdown(f"**结构模式：** {f.get('pattern', '')}")
            if f.get("steps"):
                for step in f["steps"]:
                    st.markdown(f"- {step}")
            if f.get("applicable_topics"):
                st.markdown(f"**适用选题：** {'、'.join(f['applicable_topics'])}")

            # 套用公式到新选题
            st.markdown("---")
            st.markdown("#### 🚀 套用公式到新选题")
            with st.form("apply_formula_form"):
                new_topic_for_formula = st.text_input(
                    "输入你的新选题",
                    placeholder="如：为什么年轻人不愿意生孩子",
                    key="formula_new_topic",
                )
                apply_btn = st.form_submit_button("✨ 用爆款公式生成新脚本", type="primary", use_container_width=True)

            if apply_btn and new_topic_for_formula:
                with st.spinner("AI正在套用爆款公式生成脚本..."):
                    try:
                        new_script = content_analyzer.apply_formula(f, new_topic_for_formula)
                        st.session_state["formula_script"] = new_script
                    except Exception as e:
                        st.error(f"生成失败: {e}")

            if "formula_script" in st.session_state and st.session_state["formula_script"]:
                st.markdown("##### 📝 基于爆款公式生成的新脚本")
                st.code(st.session_state["formula_script"], language=None)
                st.download_button(
                    "⬇️ 下载脚本",
                    data=st.session_state["formula_script"],
                    file_name="爆款公式脚本.txt",
                    mime="text/plain",
                    use_container_width=True,
                    key="dl_formula_script",
                )

        # 改进建议
        if a.get("improvement"):
            st.markdown("#### 💬 改进建议")
            st.warning(a["improvement"])


# ===== Tab7: 标题优化 =====
with tab7:
    st.markdown("### 🏷️ 标题A/B测试器")
    st.caption("标题决定80%的点击率 — AI生成多个标题变体并预测点击率，帮你选出最强标题")

    title_mode = st.radio(
        "选择模式",
        ["🤖 AI生成标题变体", "⚔️ 对比我的标题"],
        horizontal=True,
        key="title_mode",
    )

    if title_mode == "🤖 AI生成标题变体":
        with st.form("title_gen_form"):
            title_topic = st.text_input(
                "📌 输入选题/主题",
                placeholder="如：为什么故宫屋顶没有鸟粪",
                key="title_topic",
            )
            title_script = st.text_area(
                "📝 脚本内容（可选，提供后标题更精准）",
                height=100,
                placeholder="粘贴脚本正文，AI会根据内容优化标题...",
                key="title_script_ref",
            )
            t_col1, t_col2 = st.columns(2)
            with t_col1:
                title_platform = st.selectbox(
                    "📱 目标平台",
                    ["通用", "抖音", "B站", "小红书"],
                    key="title_platform",
                )
            with t_col2:
                title_count = st.slider("📊 生成数量", 5, 15, 8, key="title_count")
            title_gen_btn = st.form_submit_button("🏷️ 生成标题变体", type="primary", use_container_width=True)

        if title_gen_btn:
            if not _premium_gate("标题优化"):
                pass
            elif not title_topic:
                st.error("请输入选题")
            else:
                titles_result = None
                with st.spinner("AI正在生成标题变体..."):
                    try:
                        titles_result = content_analyzer.generate_title_variants(
                            topic=title_topic,
                            script_text=title_script or "",
                            platform=title_platform,
                            count=title_count,
                        )
                        st.session_state["title_variants"] = titles_result
                    except Exception as e:
                        st.error(f"生成失败: {e}")
                if titles_result:
                    key_manager.consume_usage(st.session_state.get("card_key", ""))

        if "title_variants" in st.session_state and st.session_state["title_variants"]:
            variants = st.session_state["title_variants"]
            st.markdown("---")
            st.markdown(f"#### 🏆 标题变体排行（共 {len(variants)} 个）")

            for i, v in enumerate(variants, 1):
                score = v.get("score", 0)
                if score >= 8.5:
                    medal = "🥇"
                    color = "#28a745"
                elif score >= 7:
                    medal = "🥈"
                    color = "#ffc107"
                elif score >= 5.5:
                    medal = "🥉"
                    color = "#17a2b8"
                else:
                    medal = "　"
                    color = "#6c757d"

                with st.container():
                    tc1, tc2 = st.columns([5, 1])
                    with tc1:
                        st.markdown(f"**{medal} {i}. {v.get('title', '')}**")
                        st.caption(f"策略：{v.get('type', '')} | {v.get('reasoning', '')}")
                    with tc2:
                        st.markdown(
                            f'<div style="text-align:center;"><span style="background:{color};color:white;'
                            f'padding:6px 14px;border-radius:16px;font-weight:bold;font-size:1.1rem;">'
                            f'{score}分</span></div>',
                            unsafe_allow_html=True,
                        )
                    st.divider()

    else:
        # 对比模式
        with st.form("title_compare_form"):
            st.markdown("输入你想对比的标题（每行一个）：")
            user_titles_text = st.text_area(
                "📋 输入标题（每行一个）",
                height=150,
                placeholder="标题1\n标题2\n标题3",
                key="user_titles",
            )
            cmp_platform = st.selectbox("📱 目标平台", ["通用", "抖音", "B站", "小红书"], key="cmp_platform")
            cmp_btn = st.form_submit_button("⚔️ 开始对比", type="primary", use_container_width=True)

        if cmp_btn:
            if not _premium_gate("标题优化"):
                pass
            else:
                user_titles = [t.strip() for t in user_titles_text.split("\n") if t.strip()]
                if len(user_titles) < 2:
                    st.error("请至少输入2个标题进行对比")
                else:
                    cmp_result = None
                    with st.spinner("AI正在对比评分..."):
                        try:
                            cmp_result = content_analyzer.compare_titles(user_titles, cmp_platform)
                            st.session_state["title_comparison"] = cmp_result
                        except Exception as e:
                            st.error(f"对比失败: {e}")
                    if cmp_result:
                        key_manager.consume_usage(st.session_state.get("card_key", ""))

        if "title_comparison" in st.session_state and st.session_state["title_comparison"]:
            cmp = st.session_state["title_comparison"]
            st.markdown("---")
            st.markdown("#### ⚔️ 标题对比结果")
            for i, item in enumerate(cmp, 1):
                score = item.get("score", 0)
                color = "#28a745" if score >= 8 else "#ffc107" if score >= 6 else "#6c757d"
                with st.container():
                    cc1, cc2 = st.columns([4, 1])
                    with cc1:
                        st.markdown(f"**{i}. {item.get('title', '')}**")
                        st.caption(f"✅ {item.get('strengths', '')}　|　❌ {item.get('weaknesses', '')}")
                        if item.get("improved"):
                            st.info(f"💡 优化建议：{item['improved']}")
                    with cc2:
                        st.markdown(
                            f'<div style="text-align:center;"><span style="background:{color};color:white;'
                            f'padding:6px 14px;border-radius:16px;font-weight:bold;font-size:1.1rem;">'
                            f'{score}分</span></div>',
                            unsafe_allow_html=True,
                        )
                    st.divider()


# ===== Tab8: 脚本诊断 =====
with tab8:
    st.markdown("### 📊 脚本质量诊断")
    st.caption("粘贴任意脚本，AI给出完播率预测、节奏分析、互动潜力评估和具体优化建议")

    # 从其他Tab联动过来的脚本自动填入
    _prefill_script = st.session_state.get("_diag_original_script", "")
    if _prefill_script:
        st.success("✅ 已自动填入从脚本生成/一键出片传来的脚本")

    with st.form("diagnose_form"):
        diag_script = st.text_area(
            "📋 粘贴脚本内容",
            value=_prefill_script,
            height=250,
            placeholder="粘贴你写的或AI生成的短视频脚本...",
            key="diag_script",
        )
        d_col1, d_col2 = st.columns(2)
        with d_col1:
            diag_platform = st.selectbox("📱 目标平台", ["通用", "抖音", "B站", "小红书"], key="diag_platform")
        with d_col2:
            diag_duration = st.slider("⏱️ 目标时长（秒）", 15, 300, 60, step=15, key="diag_duration")
        diag_btn = st.form_submit_button("📊 开始诊断", type="primary", use_container_width=True)

    if diag_btn:
        if not _premium_gate("脚本诊断"):
            pass
        elif not diag_script or len(diag_script.strip()) < 30:
            st.error("请粘贴至少30字的脚本内容")
        else:
            diag_result = None
            st.session_state["_diag_original_script"] = diag_script
            st.session_state["_diag_platform"] = diag_platform
            with st.status("AI正在诊断脚本质量...", expanded=True) as d_status:
                try:
                    st.write("📐 分析脚本结构...")
                    st.write("📈 评估完播率...")
                    st.write("💬 预测互动效果...")
                    diag_result = content_analyzer.diagnose_script(
                        diag_script, diag_platform, diag_duration
                    )
                    if diag_result.get("error"):
                        d_status.update(label="❌ 诊断失败", state="error")
                        st.error(diag_result["error"])
                        diag_result = None
                    else:
                        d_status.update(label="✅ 诊断完成！", state="complete", expanded=False)
                        st.session_state["diag_result"] = diag_result
                except Exception as e:
                    d_status.update(label="❌ 诊断失败", state="error")
                    st.error(f"诊断失败: {e}")
            if diag_result:
                key_manager.consume_usage(st.session_state.get("card_key", ""))

    if "diag_result" in st.session_state and st.session_state["diag_result"]:
        d = st.session_state["diag_result"]
        st.markdown("---")

        # 总评分
        overall = d.get("overall_score", 0)
        if overall >= 8:
            ov_color, ov_label = "#28a745", "优秀"
        elif overall >= 6:
            ov_color, ov_label = "#ffc107", "良好"
        elif overall >= 4:
            ov_color, ov_label = "#fd7e14", "及格"
        else:
            ov_color, ov_label = "#dc3545", "需改进"

        st.markdown(
            f'<div style="text-align:center;padding:1rem;">'
            f'<span style="background:{ov_color};color:white;padding:12px 32px;border-radius:20px;'
            f'font-size:1.5rem;font-weight:bold;">{overall}/10 {ov_label}</span></div>',
            unsafe_allow_html=True,
        )
        if d.get("overall_verdict"):
            st.markdown(f"<p style='text-align:center;color:#666;'>{d['overall_verdict']}</p>", unsafe_allow_html=True)

        # 六维评分
        if d.get("scores"):
            st.markdown("#### 📊 六维评分")
            scores = d["scores"]
            score_names = {
                "hook_power": "🎣 钩子强度",
                "info_density": "📚 信息密度",
                "pacing": "🎵 节奏起伏",
                "emotion": "❤️ 情感感染",
                "engagement": "💬 互动潜力",
                "platform_fit": "📱 平台适配",
            }
            s_cols = st.columns(3)
            for idx, (key, label) in enumerate(score_names.items()):
                if key in scores:
                    item = scores[key]
                    with s_cols[idx % 3]:
                        sc = item.get("score", 0)
                        sc_color = "#28a745" if sc >= 8 else "#ffc107" if sc >= 6 else "#dc3545"
                        st.markdown(
                            f"**{label}** "
                            f'<span style="background:{sc_color};color:white;padding:2px 10px;'
                            f'border-radius:10px;">{sc}/10</span>',
                            unsafe_allow_html=True,
                        )
                        st.caption(item.get("comment", ""))

        # 完播率预测
        if d.get("completion_rate"):
            cr = d["completion_rate"]
            st.markdown("#### 📈 完播率预测")
            st.metric("预测完播率", cr.get("predicted", "N/A"))
            if cr.get("dropoff_points"):
                st.markdown("**⚠️ 可能流失点：**")
                for dp in cr["dropoff_points"]:
                    st.warning(
                        f"📍 **{dp.get('position', '')}** — {dp.get('reason', '')}\n\n"
                        f"💡 建议：{dp.get('suggestion', '')}"
                    )

        # 预测热门评论
        if d.get("predicted_comments"):
            st.markdown("#### 💬 预测热门评论")
            for pc in d["predicted_comments"]:
                st.markdown(f"  💭 _{pc}_")

        # 置顶评论建议
        if d.get("pin_comment_suggestion"):
            st.markdown("#### 📌 建议置顶评论")
            st.success(d["pin_comment_suggestion"])

        # 具体优化建议
        if d.get("suggestions"):
            st.markdown("#### ✏️ 具体优化建议")
            for sg in d["suggestions"]:
                priority = sg.get("priority", "medium")
                p_icon = "🔴" if priority == "high" else "🟡" if priority == "medium" else "🟢"
                with st.expander(f"{p_icon} {sg.get('area', '优化项')}", expanded=(priority == "high")):
                    if sg.get("current"):
                        st.markdown(f"**当前：** {sg['current']}")
                    if sg.get("problem"):
                        st.markdown(f"**问题：** {sg['problem']}")
                    if sg.get("improved"):
                        st.markdown(f"**优化后：**")
                        st.success(sg["improved"])

        # ========== 一键重写 ==========
        st.markdown("---")
        _original_script = st.session_state.get("_diag_original_script", "")
        _diag_platform = st.session_state.get("_diag_platform", "通用")
        if _original_script and d.get("overall_score", 10) < 9:
            if st.button("🔧 一键优化脚本（AI根据诊断结果重写）", type="primary", use_container_width=True, key="rewrite_btn"):
                if not _premium_gate("一键重写"):
                    pass
                else:
                    with st.spinner("AI正在根据诊断结果重写脚本..."):
                        try:
                            rewritten = content_analyzer.rewrite_script(
                                _original_script, d, _diag_platform
                            )
                            st.session_state["rewritten_script"] = rewritten
                        except Exception as e:
                            st.error(f"重写失败: {e}")
                    if st.session_state.get("rewritten_script"):
                        key_manager.consume_usage(st.session_state.get("card_key", ""))

            if "rewritten_script" in st.session_state and st.session_state["rewritten_script"]:
                st.markdown("#### ✨ 优化后的脚本")
                _rw_col1, _rw_col2 = st.columns(2)
                with _rw_col1:
                    st.markdown("**📄 原始脚本**")
                    st.text_area("原始", _original_script, height=300, disabled=True, key="_rw_orig", label_visibility="collapsed")
                with _rw_col2:
                    st.markdown("**✨ 优化后脚本**")
                    st.text_area("优化后", st.session_state["rewritten_script"], height=300, disabled=True, key="_rw_new", label_visibility="collapsed")

                st.download_button(
                    "⬇️ 下载优化后脚本",
                    data=st.session_state["rewritten_script"],
                    file_name="优化后脚本.txt",
                    mime="text/plain",
                    use_container_width=True,
                    key="dl_rewritten",
                )
