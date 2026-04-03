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
import cloud_db
import content_analyzer


# ============================================================
# 自定义样式
# ============================================================
st.markdown("""
<style>
    /* ========== 全局基础 ========== */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI',
                     'PingFang SC', 'Microsoft YaHei', 'Noto Sans SC', sans-serif !important;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
        background: linear-gradient(180deg, #ffffff 0%, #f8fafc 30%, #f1f5f9 100%) !important;
    }
    /* 继承字体到子元素，但排除图标字体 */
    .stApp p, .stApp div, .stApp label, .stApp input, .stApp textarea,
    .stApp button, .stApp select, .stApp h1, .stApp h2, .stApp h3, .stApp h4,
    .stApp li, .stApp td, .stApp th, .stApp a, .stApp code, .stApp pre {
        font-family: inherit !important;
    }
    /* span 不做强制覆盖，避免破坏 Streamlit 内部 Material Icons 图标字体 */

    /* ========== 主标题区 ========== */
    .hero-banner {
        position: relative;
        text-align: center;
        padding: 2.2rem 2rem 1.6rem;
        margin: 0 -1rem 1.5rem;
        background: linear-gradient(135deg, rgba(14,165,233,0.06) 0%, rgba(56,189,248,0.03) 50%, rgba(125,211,252,0.06) 100%);
        border-radius: 18px;
        border: 1px solid rgba(14,165,233,0.08);
        overflow: hidden;
    }
    .hero-banner::before {
        content: '';
        position: absolute;
        top: -40px;
        right: -40px;
        width: 140px;
        height: 140px;
        background: radial-gradient(circle, rgba(14,165,233,0.1) 0%, transparent 70%);
        border-radius: 50%;
        pointer-events: none;
    }
    .hero-banner::after {
        content: '';
        position: absolute;
        bottom: -30px;
        left: -30px;
        width: 100px;
        height: 100px;
        background: radial-gradient(circle, rgba(56,189,248,0.08) 0%, transparent 70%);
        border-radius: 50%;
        pointer-events: none;
    }
    .hero-banner h1 {
        position: relative;
        background: linear-gradient(135deg, #0c4a6e 0%, #0369a1 30%, #0ea5e9 60%, #38bdf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: 0.06em;
        line-height: 1.3;
        margin: 0 0 0.6rem 0;
    }
    .hero-divider {
        width: 40px;
        height: 3px;
        background: linear-gradient(90deg, #0ea5e9, #7dd3fc);
        border-radius: 2px;
        margin: 0 auto 0.8rem;
    }
    .hero-sub {
        position: relative;
        color: #475569;
        font-size: 0.9rem;
        font-weight: 400;
        letter-spacing: 0.15em;
        line-height: 1.6;
    }
    .hero-sub .dot {
        display: inline-block;
        width: 3px;
        height: 3px;
        background: #94a3b8;
        border-radius: 50%;
        margin: 0 0.6em;
        vertical-align: middle;
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
        gap: 0;
        background: linear-gradient(180deg, rgba(241,245,249,0.6) 0%, rgba(248,250,252,0.3) 100%);
        border-radius: 12px 12px 0 0;
        padding: 0.3rem 0.5rem 0;
        border: none;
        border-bottom: 2px solid #e2e8f0;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 18px;
        font-size: 0.88rem;
        font-weight: 500;
        border-radius: 0;
        color: #64748b;
        border-bottom: 2px solid transparent;
        margin-bottom: -2px;
        transition: color 0.15s ease, border-color 0.15s ease;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background: transparent;
        color: #1e293b;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(14,165,233,0.08) !important;
        color: #0ea5e9 !important;
        font-weight: 700 !important;
        border-bottom: 3px solid #0ea5e9 !important;
        box-shadow: none;
    }
    /* 一键出片 Tab 高亮（第5个） */
    .stTabs [data-baseweb="tab-list"] > button:nth-child(5) {
        color: #0369a1;
        font-weight: 600;
        position: relative;
    }
    .stTabs [data-baseweb="tab-list"] > button:nth-child(5)::after {
        content: "主推";
        position: absolute;
        top: 2px;
        right: 2px;
        font-size: 0.55rem;
        background: #0ea5e9;
        color: white;
        padding: 1px 5px;
        border-radius: 3px;
        font-weight: 700;
        line-height: 1.3;
        letter-spacing: 0.04em;
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
        background: linear-gradient(135deg, rgba(14,165,233,0.85) 0%, rgba(56,189,248,0.8) 100%) !important;
        border: 1px solid rgba(14,165,233,0.3) !important;
        border-radius: 10px !important;
        padding: 0.55rem 1.4rem !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        letter-spacing: 0.03em;
        box-shadow: 0 2px 10px rgba(14,165,233,0.2) !important;
        backdrop-filter: blur(6px) !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button[kind="primary"]:hover,
    .stFormSubmitButton > button:hover {
        background: linear-gradient(135deg, rgba(2,132,199,0.9) 0%, rgba(14,165,233,0.85) 100%) !important;
        box-shadow: 0 4px 16px rgba(14,165,233,0.3) !important;
        transform: translateY(-1px) !important;
    }
    .stButton > button:not([kind="primary"]) {
        border-radius: 8px !important;
        border: 1px solid rgba(203,213,225,0.8) !important;
        font-weight: 500 !important;
        transition: all 0.15s ease !important;
        background: rgba(255,255,255,0.7) !important;
    }
    .stButton > button:not([kind="primary"]):hover {
        border-color: #0ea5e9 !important;
        color: #0ea5e9 !important;
        background: rgba(255,255,255,0.9) !important;
    }

    /* ========== 输入框/表单 ========== */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div,
    .stMultiSelect > div > div {
        border-radius: 8px !important;
        border: 1px solid rgba(203,213,225,0.8) !important;
        background: rgba(255,255,255,0.7) !important;
        transition: all 0.15s ease !important;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #0ea5e9 !important;
        box-shadow: 0 0 0 3px rgba(14,165,233,0.06) !important;
        background: #ffffff !important;
        outline: none !important;
    }

    /* ========== MultiSelect 标签 ========== */
    .stMultiSelect [data-baseweb="tag"] {
        background: linear-gradient(135deg, rgba(14,165,233,0.75), rgba(56,189,248,0.7)) !important;
        border: 1px solid rgba(14,165,233,0.2) !important;
        border-radius: 6px !important;
        color: #ffffff !important;
        font-weight: 500 !important;
        font-size: 0.82rem !important;
        padding: 2px 8px !important;
        box-shadow: 0 1px 4px rgba(14,165,233,0.15);
        backdrop-filter: blur(4px);
    }
    .stMultiSelect [data-baseweb="tag"] span {
        color: #ffffff !important;
    }
    .stMultiSelect [data-baseweb="tag"] [role="presentation"] {
        color: rgba(255,255,255,0.8) !important;
    }
    .stMultiSelect [data-baseweb="tag"] [role="presentation"]:hover {
        color: #ffffff !important;
    }

    /* ========== 指标卡片 ========== */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, rgba(248,250,252,0.8) 0%, rgba(241,245,249,0.5) 100%);
        border: 1px solid rgba(226,232,240,0.8);
        border-left: 3px solid #0ea5e9;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        backdrop-filter: blur(4px);
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
        border-radius: 8px 8px 0 0 !important;
        background: linear-gradient(135deg, rgba(240,249,255,0.5), rgba(248,250,252,0.8)) !important;
        border: 1px solid rgba(226,232,240,0.6) !important;
        border-left: 3px solid #0ea5e9 !important;
    }
    .streamlit-expanderContent {
        border: 1px solid rgba(226,232,240,0.6) !important;
        border-top: none !important;
        border-radius: 0 0 8px 8px !important;
        background: rgba(255,255,255,0.6) !important;
    }

    /* ========== 提示框美化 ========== */
    .stAlert {
        border-radius: 10px !important;
        border: none !important;
        backdrop-filter: blur(4px);
    }
    div[data-testid="stNotification"] {
        border-radius: 10px !important;
    }

    /* ========== 侧边栏 ========== */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f0f9ff 0%, #e0f2fe 40%, #f1f5f9 100%) !important;
        border-right: 1px solid #e2e8f0 !important;
    }
    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown li,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: #334155 !important;
    }
    section[data-testid="stSidebar"] .stMarkdown strong {
        color: #1e293b !important;
    }
    section[data-testid="stSidebar"] .stDivider {
        border-color: #cbd5e1 !important;
    }
    section[data-testid="stSidebar"] .stTextInput > div > div > input {
        background: #ffffff !important;
        border: 1.5px solid #cbd5e1 !important;
        color: #1e293b !important;
        border-radius: 4px !important;
    }
    section[data-testid="stSidebar"] .stTextInput > div > div > input:focus {
        border-color: #0ea5e9 !important;
        box-shadow: 0 0 0 2px rgba(14,165,233,0.1) !important;
    }
    section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background: #0ea5e9 !important;
        color: #ffffff !important;
        box-shadow: none !important;
    }
    section[data-testid="stSidebar"] .stButton > button:not([kind="primary"]) {
        border-color: #cbd5e1 !important;
        color: #475569 !important;
        background: #ffffff !important;
    }
    section[data-testid="stSidebar"] .stButton > button:not([kind="primary"]):hover {
        border-color: #0ea5e9 !important;
        color: #0ea5e9 !important;
        background: #f0f9ff !important;
    }
    section[data-testid="stSidebar"] .stAlert {
        background: #ffffff !important;
        color: #334155 !important;
        border: 1px solid #e2e8f0 !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stNotification"] p {
        color: #334155 !important;
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
        border-radius: 4px !important;
        border: 1px solid #cbd5e1 !important;
        font-weight: 500 !important;
        transition: all 0.15s ease !important;
        background: white !important;
    }
    .stDownloadButton > button:hover {
        border-color: #0ea5e9 !important;
        color: #0ea5e9 !important;
        background: white !important;
    }

    /* ========== Code 块 ========== */
    .stCodeBlock {
        border-radius: 2px !important;
        border: 1px solid #e2e8f0 !important;
    }

    /* ========== 自定义组件 ========== */
    .score-badge {
        display: inline-block;
        background: #0ea5e9;
        color: white;
        padding: 3px 12px;
        border-radius: 2px;
        font-weight: 600;
        font-size: 0.85rem;
        letter-spacing: 0.02em;
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
        border-radius: 2px !important;
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
    st.warning(f"**{feature_name}** 为付费功能，请在左侧边栏输入卡密解锁")
    st.markdown("""
    **获取卡密：**
    - 试用卡（3次免费体验）
    - 体验卡（3天免费）
    - 周卡 ¥9.9 / 月卡 ¥29 / 年卡 ¥199
    """)
    return False


_SITE_URL = "https://ai-content-workbench-6ivhtqpkcsnphcvjpru5hx.streamlit.app"


def _render_share_banner(feature_name: str):
    """在结果区底部渲染分享引导"""
    share_text = f"推荐一个AI短视频工具，{feature_name}功能很好用，输入关键词就能自动生成脚本和分镜。免费体验：{_SITE_URL}"
    st.markdown(f"""
<div style="margin-top:1.5rem;padding:1rem 1.2rem;background:linear-gradient(135deg,rgba(14,165,233,0.04),rgba(56,189,248,0.06));
border:1px solid rgba(14,165,233,0.12);border-radius:12px;">
<div style="font-size:0.88rem;color:#475569;margin-bottom:0.5rem;">觉得好用？分享给做短视频的朋友</div>
</div>""", unsafe_allow_html=True)
    st.code(share_text, language=None)


with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:0.5rem 0 0.2rem 0;">
        <span style="font-size:1.6rem;font-weight:800;background:linear-gradient(135deg,#0369a1,#0ea5e9);
        -webkit-background-clip:text;-webkit-text-fill-color:transparent;">AI 工作台</span>
        <div style="font-size:0.75rem;color:#64748b;margin-top:2px;letter-spacing:0.1em;">SHORT VIDEO CONTENT STUDIO</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # === 卡密验证 ===
    st.markdown("### 卡密")

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
            # 切换按钮（带确认提示）
            with st.popover("切换卡密", use_container_width=True):
                st.markdown("**确认切换卡密？**")
                st.caption("当前卡密将被移除，你需要重新输入新的卡密才能继续使用付费功能。")
                if st.button("确认切换", type="primary", use_container_width=True, key="confirm_switch"):
                    st.session_state.pop("card_key", None)
                    st.session_state.pop("key_validation", None)
                    if "t" in st.query_params:
                        del st.query_params["t"]
                    st.rerun()
        else:
            st.error(v.get("message", "卡密无效"))
            # 过期/失效自动解锁输入框
            if st.button("更换卡密", type="primary", use_container_width=True):
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

        if st.button("激活卡密", type="primary", use_container_width=True):
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
        st.info("输入卡密解锁脚本生成等付费功能")

    st.divider()

    # === 模型API Key（从Secrets自动读取所有provider）===
    from llm_client import MODEL_PROVIDERS as _MP
    _available_providers = []
    for _pid, _pcfg in _MP.items():
        _sk = _pcfg["secret_key"]
        _kv = os.environ.get(_sk, "")
        try:
            if hasattr(st, "secrets") and _sk in st.secrets:
                _kv = st.secrets[_sk]
        except Exception:
            pass
        if _kv:
            os.environ[_sk] = _kv
            _available_providers.append(_pid)

    # 兼容旧配置
    if "deepseek" in _available_providers and "DEEPSEEK_API_KEY" not in os.environ:
        os.environ["DEEPSEEK_API_KEY"] = os.environ.get(_MP["deepseek"]["secret_key"], "")

    # === 模型选择 ===
    if len(_available_providers) > 1:
        st.markdown("### AI 模型")
        _provider_labels = {p: f"{_MP[p]['name']}" for p in _available_providers}
        _default_idx = _available_providers.index(st.session_state.get("llm_provider", _available_providers[0])) if st.session_state.get("llm_provider") in _available_providers else 0
        _sel_provider = st.selectbox(
            "选择模型",
            _available_providers,
            index=_default_idx,
            format_func=lambda p: _provider_labels[p],
            key="llm_provider_select",
            help="切换不同的AI模型，效果和速度各有差异",
        )
        st.session_state["llm_provider"] = _sel_provider
        os.environ["LLM_PROVIDER"] = _sel_provider
        st.caption(f"{_MP[_sel_provider]['note']}")
        st.divider()
    elif _available_providers:
        os.environ["LLM_PROVIDER"] = _available_providers[0]

    st.markdown("### 功能导航")
    st.markdown("""
    <div style="font-size:0.85rem;line-height:2.2;">
    <span style="color:#0ea5e9;font-size:0.5rem;vertical-align:middle;">●</span> <b>热搜榜单</b> <span style="color:#94a3b8;font-size:0.72rem;margin-left:4px;">免费</span><br>
    <span style="color:#0ea5e9;font-size:0.5rem;vertical-align:middle;">●</span> <b>智能选题</b><br>
    <span style="color:#0ea5e9;font-size:0.5rem;vertical-align:middle;">●</span> <b>脚本生成</b> <span style="color:#94a3b8;font-size:0.72rem;margin-left:4px;">12种风格</span><br>
    <span style="color:#0ea5e9;font-size:0.5rem;vertical-align:middle;">●</span> <b>分镜提示词</b><br>
    <span style="color:#0ea5e9;font-size:0.5rem;vertical-align:middle;">●</span> <b>一键出片</b> <span style="color:#94a3b8;font-size:0.72rem;margin-left:4px;">★</span><br>
    <span style="color:#0ea5e9;font-size:0.5rem;vertical-align:middle;">●</span> <b>爆款拆解</b><br>
    <span style="color:#0ea5e9;font-size:0.5rem;vertical-align:middle;">●</span> <b>标题优化</b><br>
    <span style="color:#0ea5e9;font-size:0.5rem;vertical-align:middle;">●</span> <b>脚本诊断</b>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    st.markdown("""
    <div style="text-align:center;padding:0.3rem 0;">
        <div style="font-size:0.8rem;color:#64748b;">关注公众号回复「体验」</div>
        <div style="font-size:0.8rem;color:#64748b;">获取免费试用卡密</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    st.markdown("""
    <div style="text-align:center;padding:0.2rem 0;">
        <div style="font-size:0.7rem;color:#475569;letter-spacing:0.05em;">Powered by DeepSeek AI</div>
        <div style="font-size:0.65rem;color:#334155;margin-top:2px;">v1.0</div>
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# 标题
# ============================================================
st.markdown('''
<div class="hero-banner">
    <h1>AI短视频内容工作台</h1>
    <div class="hero-divider"></div>
    <div class="hero-sub">选题<span class="dot"></span>脚本<span class="dot"></span>分镜 — 一站搞定，5分钟产出一条视频的全部文案</div>
</div>
''', unsafe_allow_html=True)

# ============================================================
# 新用户引导（未激活卡密时展示产品价值）
# ============================================================
if not _check_premium():
    st.markdown("""
<div style="background:linear-gradient(135deg,rgba(14,165,233,0.04),rgba(56,189,248,0.06));
border:1px solid rgba(14,165,233,0.15);border-radius:16px;padding:2rem 2.5rem;margin-bottom:2rem;
box-shadow:0 4px 24px rgba(14,165,233,0.06);">

<div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:1rem;">
<span style="font-size:1.15rem;font-weight:700;color:#1e293b;">欢迎使用 AI 短视频内容工作台</span>
</div>

<div style="color:#64748b;font-size:0.92rem;margin-bottom:1.2rem;">输入卡密即可解锁以下 <b style="color:#0ea5e9;">7 项 AI 功能</b>，5分钟产出一条视频的全套文案：</div>

| 功能 | 说明 | 效果 |
|------|------|------|
| **智能选题** | 热搜 + AI 联想 + 智能打分 | 30秒找到高潜力选题 |
| **脚本生成** | 12种风格，自动写完整配音稿 | 1分钟出完整脚本 |
| **分镜提示词** | 自动生成可灵/Pika提示词 | 直接复制到AI视频工具 |
| **一键出片** | 选题→脚本→分镜全自动 | 5分钟搞定全套文案 |
| **爆款拆解** | 逆向分析爆款文案结构 | 学会"为什么能火" |
| **标题优化** | AI生成+对比标题点击率 | 选出最强标题 |
| **脚本诊断** | 六维评分+完播率预测 | 发布前精准优化 |

<div style="margin-top:1rem;padding:0.75rem 1rem;background:rgba(52,211,153,0.08);border-radius:10px;
border:1px solid rgba(52,211,153,0.2);font-size:0.9rem;">
<b style="color:#059669;">热搜榜单完全免费</b>，无需卡密！← 左侧输入卡密解锁全部 AI 功能
</div>

</div>
""", unsafe_allow_html=True)

# ============================================================
# 管理员模式（URL加 ?ak=<密钥> 进入，密钥存储在Secrets中）
# ============================================================
_admin_key_cfg = ""
if hasattr(st, "secrets"):
    _admin_key_cfg = st.secrets.get("ADMIN_KEY", "")
_is_admin = bool(_admin_key_cfg and st.query_params.get("ak") == _admin_key_cfg)

# ============================================================
# 主体 Tabs
# ============================================================
_tab_names = ["热搜榜单", "智能选题", "脚本生成", "分镜提示词",
              "一键出片", "爆款拆解", "标题优化", "脚本诊断"]
if _is_admin:
    _tab_names += ["卡密管理", "发帖助手"]
_tabs = st.tabs(_tab_names)
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = _tabs[:8]
if _is_admin:
    tab_keys = _tabs[8]
    tab_admin = _tabs[9]


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
            format_func=lambda x: {"douyin": "抖音", "bilibili": "B站", "weibo": "微博", "baidu": "百度"}[x],
        )
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        fetch_btn = st.button("抓取热搜", type="primary", use_container_width=True)

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

        source_map = {"douyin": "抖音", "bilibili": "B站", "weibo": "微博", "baidu": "百度"}
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
            track = st.text_input("内容赛道", placeholder="如：历史、科技、美食、育儿", key="topic_track")
        with col2:
            seeds = st.text_input("种子关键词（可选）", placeholder="逗号分隔，如：朱元璐,明朝", key="topic_seeds")
        with col3:
            topic_count = st.slider("推荐数量", 5, 30, 10, key="topic_count")

        col_a, col_b = st.columns([1, 1])
        with col_a:
            use_hot = st.checkbox("结合实时热搜", value=True, key="topic_use_hot")
        with col_b:
            topic_btn = st.form_submit_button("开始选题", type="primary", use_container_width=True)

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
                        st.write("抓取实时热搜...")
                        hot = topic_engine.fetch_hot_topics()
                        hot_titles = [h["title"] for h in hot if h["title"]]
                        all_topics.extend(hot_titles)
                        st.write(f"✅ 获取 {len(hot_titles)} 条热搜")

                    if seed_list:
                        st.write("AI联想扩展关键词...")
                        expanded = topic_engine.expand_topics(
                            seed_list, count=topic_count * 2, track=track
                        )
                        all_topics.extend(expanded)
                        st.write(f"✅ 扩展出 {len(expanded)} 个候选选题")

                    if all_topics:
                        st.write("去重过滤...")
                        unique = topic_engine.deduplicate(all_topics)
                        st.write(f"✅ 去重后 {len(unique)} 个")

                        st.write("AI智能打分排序...")
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
        st.markdown(f"#### Top {len(results)} 选题推荐")

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
                        st.caption(reason)
                with c2:
                    st.markdown(f'<span style="background:{color};color:white;padding:4px 12px;border-radius:12px;font-weight:bold;">{score}分 {label}</span>', unsafe_allow_html=True)
                st.divider()


# ===== Tab3: 脚本生成 =====
with tab3:
    st.markdown("### 短视频脚本生成")
    st.caption("输入选题，AI自动生成完整的短视频配音脚本，支持12种风格和4个平台")

    # 如果有智能选题结果，提供快捷选择（放在form外面，因为含st.button）
    if "scored_topics" in st.session_state and st.session_state["scored_topics"]:
        with st.expander("从智能选题结果中选择"):
            topic_names = [item.get("topic", "") for item in st.session_state["scored_topics"]]
            selected = st.radio("选择一个选题：", topic_names, key="quick_topic")
            if st.button("使用该选题", key="use_topic_btn"):
                st.session_state["script_topic"] = selected
                st.rerun()

    with st.form("script_form"):
        script_topic = st.text_input(
            "输入选题",
            placeholder="如：为什么故宫屋顶没有鸟粪",
            key="script_topic",
        )

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            style_options = [s["name"] for s in script_gen.list_styles()]
            style_descriptions = {s["name"]: s["description"] for s in script_gen.list_styles()}
            script_style = st.selectbox(
                "脚本风格",
                style_options,
                index=0,
                help="\n".join([f"• {k}: {v}" for k, v in style_descriptions.items()]),
                key="script_style",
            )
        with col_b:
            platform_options = [p["name"] for p in script_gen.list_platforms()]
            script_platform = st.selectbox("目标平台", platform_options, index=0, key="script_platform")
        with col_c:
            script_duration = st.slider("目标时长（秒）", 15, 300, 60, step=15, key="script_duration")

        script_btn = st.form_submit_button("生成脚本", type="primary", use_container_width=True)

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
        meta_cols[0].metric("标题", result.get("title", ""))
        meta_cols[1].metric("字数", f"{result.get('word_count', 0)} 字")
        meta_cols[2].metric("预估时长", f"{result.get('estimated_duration_seconds', 0)} 秒")
        meta_cols[3].metric("风格", result.get("style", ""))

        st.markdown("#### 完整脚本")

        # 分段展示
        if result.get("hook"):
            st.markdown("**开场钩子**")
            st.info(result["hook"])

        if result.get("body"):
            st.markdown("**正文主体**")
            st.success(result["body"])

        if result.get("cta"):
            st.markdown("**结尾引导**")
            st.warning(result["cta"])

        # 复制全文 + 下载
        st.markdown("#### 一键复制")
        st.code(result.get("full_script", ""), language=None)
        _script_text = result.get("full_script", "")
        _script_title = result.get("title", "脚本")
        st.download_button(
            "下载脚本",
            data=_script_text,
            file_name=f"{_script_title}.txt",
            mime="text/plain",
            use_container_width=True,
        )

        # 跨Tab联动：一键跳转诊断
        if st.button("立即诊断这个脚本", use_container_width=True, key="script_to_diag"):
            st.session_state["_diag_original_script"] = _script_text
            st.session_state["_diag_platform"] = result.get("platform", "通用")
            st.info("请切换到「脚本诊断」Tab，脚本已自动填入")

        _render_share_banner("脚本生成")


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
        vc_btn = st.button("生成分镜", type="primary", use_container_width=True)
    else:
        with st.form("visual_cue_form"):
            vc_topic = st.text_input("选题", placeholder="视频选题", key="vc_topic")
            vc_script = st.text_area("脚本内容", placeholder="粘贴你的完整脚本文案...", height=200, key="vc_script")
            vc_col1, vc_col2 = st.columns(2)
            with vc_col1:
                vc_duration = st.number_input("时长（秒）", min_value=10, max_value=600, value=60, key="vc_duration")
            with vc_col2:
                vc_platform = st.selectbox("目标平台", ["通用", "抖音", "B站", "小红书"], key="vc_platform")
            vc_btn = st.form_submit_button("生成分镜", type="primary", use_container_width=True)

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
        st.markdown(f"#### 共 {len(cues)} 个分镜")

        for shot in cues:
            shot_num = shot.get("shot_number", "?")
            timestamp = shot.get("timestamp", "")

            with st.expander(f"镜头 {shot_num}  |  {timestamp}", expanded=True):
                if shot.get("narration"):
                    st.markdown(f"**配音：** {shot['narration']}")

                if shot.get("scene"):
                    st.markdown(f"**画面：** {shot['scene']}")

                if shot.get("camera"):
                    st.markdown(f"**镜头：** {shot['camera']}")

                if shot.get("style"):
                    st.markdown(f"**风格：** {shot['style']}")

                col_cn, col_en = st.columns(2)
                with col_cn:
                    if shot.get("prompt_cn"):
                        st.markdown("**中文提示词（可灵/Vidu）**")
                        st.code(shot["prompt_cn"], language=None)
                with col_en:
                    if shot.get("prompt_en"):
                        st.markdown("**英文提示词（Pika/Runway）**")
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
            "下载全部分镜",
            data="\n".join(_export_lines),
            file_name="分镜提示词.txt",
            mime="text/plain",
            use_container_width=True,
        )

        # 使用指南
        st.markdown("---")
        st.markdown("#### 下一步：用提示词生成AI视频")
        st.markdown("""
提示词已就绪！复制上方提示词，粘贴到以下任一AI视频工具即可生成画面：

| 工具 | 语言 | 特点 | 链接 |
|------|------|------|------|
| **可灵** | 中文 | 国产首选，效果好 | [klingai.kuaishou.com](https://klingai.kuaishou.com) |
| **Vidu** | 中文 | 生数科技出品，速度快 | [vidu.studio](https://www.vidu.studio) |
| **Pika** | 英文 | 风格化强，适合创意 | [pika.art](https://pika.art) |
| **Runway** | 英文 | Gen-3 Alpha，画质顶级 | [runwayml.com](https://runwayml.com) |
| **即梦** | 中文 | 字节出品，免费额度多 | [jimeng.jianying.com](https://jimeng.jianying.com) |

**操作步骤：**
1. 复制对应语言的提示词（中文→可灵/Vidu/即梦，英文→Pika/Runway）
2. 打开工具网站，选择"文生视频"或"图生视频"
3. 粘贴提示词，设置时长（建议4-6秒/镜头）
4. 生成后下载，用剪映/CapCut拼接所有镜头 + 配音即完成
        """)


# ===== Tab5: 一键出片 =====
with tab5:
    st.markdown("""
<div style="background:#f0f9ff;border-left:4px solid #0ea5e9;padding:1.2rem 1.5rem;margin-bottom:1.2rem;">
<div style="font-size:1.1rem;font-weight:700;color:#0c4a6e;">一键出片 — 全自动流水线</div>
<div style="color:#64748b;font-size:0.88rem;margin-top:4px;">输入赛道 + 关键词 → AI 自动完成 <b style="color:#0369a1;">选题 → 脚本 → 分镜</b> 全流程，一步到位</div>
<div style="display:flex;gap:1.5rem;margin-top:0.6rem;font-size:0.78rem;color:#94a3b8;">
<span>Step 1 智能选题</span><span style="color:#cbd5e1;">→</span>
<span>Step 2 脚本生成</span><span style="color:#cbd5e1;">→</span>
<span>Step 3 分镜提示词</span>
</div>
</div>
""", unsafe_allow_html=True)

    with st.form("oneclick_form"):
        op_col1, op_col2 = st.columns(2)
        with op_col1:
            op_track = st.text_input("内容赛道", placeholder="如：历史、科技、美食", key="op_track")
        with op_col2:
            op_seeds = st.text_input("种子关键词", placeholder="逗号分隔，如：朱元璋,明朝", key="op_seeds")

        op_col_a, op_col_b, op_col_c = st.columns(3)
        with op_col_a:
            op_style_options = [s["name"] for s in script_gen.list_styles()]
            op_style = st.selectbox("脚本风格", op_style_options, index=0, key="op_style")
        with op_col_b:
            op_platform_options = [p["name"] for p in script_gen.list_platforms()]
            op_platform = st.selectbox("目标平台", op_platform_options, index=0, key="op_platform")
        with op_col_c:
            op_duration = st.slider("目标时长（秒）", 15, 300, 60, step=15, key="op_duration")

        op_btn = st.form_submit_button("一键生成全部", type="primary", use_container_width=True)

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

            with st.status("一键出片流水线启动...", expanded=True) as op_status:
                try:
                    # Step 1: 智能选题（用户输入优先，热搜仅作补充）
                    st.write("**Step 1/3** 智能选题...")
                    all_topics = []

                    # 用户关键词优先：扩展更多候选
                    if op_seed_list:
                        st.write("基于关键词AI联想扩展...")
                        expanded = topic_engine.expand_topics(
                            op_seed_list, count=25, track=op_track
                        )
                        all_topics.extend(expanded)
                        st.write(f"  ✅ 扩展出 {len(expanded)} 个相关选题")

                    # 热搜作为补充（最多取10条，避免喧宾夺主）
                    st.write("抓取热搜作为灵感补充...")
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
                        st.write(f"最佳选题：**{topic_text}**（{best_topic.get('score', 0)}分）")
                        op_result["topic"] = best_topic

                        # Step 2: 脚本生成
                        st.write(f"**Step 2/3** 生成脚本...")
                        script_result = script_gen.generate_script(
                            topic=topic_text,
                            style=op_style,
                            duration_seconds=op_duration,
                            platform=op_platform,
                        )
                        op_result["script"] = script_result
                        st.write(f"  ✅ 脚本 {script_result.get('word_count', 0)} 字")

                        # Step 3: 分镜生成
                        st.write(f"**Step 3/3** 生成分镜...")
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
            st.markdown(f'#### 选题：{t["topic"]} <span style="background:#28a745;color:white;padding:2px 10px;border-radius:12px;">{t.get("score", 0)}分</span>', unsafe_allow_html=True)
            if t.get("reason"):
                st.caption(t['reason'])

        # 脚本结果
        if opr.get("script"):
            s = opr["script"]
            st.markdown("#### 脚本")
            meta_cols = st.columns(4)
            meta_cols[0].metric("标题", s.get("title", ""))
            meta_cols[1].metric("字数", f"{s.get('word_count', 0)} 字")
            meta_cols[2].metric("时长", f"{s.get('estimated_duration_seconds', 0)} 秒")
            meta_cols[3].metric("风格", s.get("style", ""))

            if s.get("hook"):
                st.markdown("**开场钩子**")
                st.info(s["hook"])
            if s.get("body"):
                st.markdown("**正文主体**")
                st.success(s["body"])
            if s.get("cta"):
                st.markdown("**结尾引导**")
                st.warning(s["cta"])

            st.code(s.get("full_script", ""), language=None)
            _op_dl_col, _op_diag_col = st.columns(2)
            with _op_dl_col:
                st.download_button(
                    "下载脚本",
                    data=s.get("full_script", ""),
                    file_name=f"{s.get('title', '脚本')}.txt",
                    mime="text/plain",
                    use_container_width=True,
                    key="op_dl_script",
                )
            with _op_diag_col:
                if st.button("诊断这个脚本", use_container_width=True, key="op_to_diag"):
                    st.session_state["_diag_original_script"] = s.get("full_script", "")
                    st.session_state["_diag_platform"] = s.get("platform", "通用")
                    st.info("请切换到「脚本诊断」Tab")

        # 分镜结果
        if opr.get("cues"):
            st.markdown(f"#### 分镜（共 {len(opr['cues'])} 个）")
            for shot in opr["cues"]:
                with st.expander(f"镜头 {shot.get('shot_number', '?')}  |  {shot.get('timestamp', '')}", expanded=False):
                    if shot.get("narration"):
                        st.markdown(f"**配音：** {shot['narration']}")
                    if shot.get("scene"):
                        st.markdown(f"**画面：** {shot['scene']}")
                    c1, c2 = st.columns(2)
                    with c1:
                        if shot.get("prompt_cn"):
                            st.markdown("**中文提示词**")
                            st.code(shot["prompt_cn"], language=None)
                    with c2:
                        if shot.get("prompt_en"):
                            st.markdown("**英文提示词**")
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
                "下载全部分镜",
                data="\n".join(_op_export),
                file_name="一键出片_分镜.txt",
                mime="text/plain",
                use_container_width=True,
                key="op_dl_cues",
            )

        # 一键导出完整文档（脚本+分镜合并）
        if opr.get("script") and opr.get("cues"):
            st.markdown("---")
            st.markdown("#### 一键导出完整文档")
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
                "下载完整文档（脚本+分镜）",
                data="\n".join(_full_doc),
                file_name=f"{_s.get('title', '一键出片')}_完整文档.txt",
                mime="text/plain",
                use_container_width=True,
                key="op_dl_full",
            )

        # 使用指南
        st.markdown("---")
        st.markdown("#### 下一步：用提示词生成AI视频")
        st.markdown("""
提示词已就绪！复制上方提示词，粘贴到以下任一AI视频工具即可生成画面：

| 工具 | 语言 | 特点 | 链接 |
|------|------|------|------|
| **可灵** | 中文 | 国产首选，效果好 | [klingai.kuaishou.com](https://klingai.kuaishou.com) |
| **Vidu** | 中文 | 生数科技出品，速度快 | [vidu.studio](https://www.vidu.studio) |
| **Pika** | 英文 | 风格化强，适合创意 | [pika.art](https://pika.art) |
| **Runway** | 英文 | Gen-3 Alpha，画质顶级 | [runwayml.com](https://runwayml.com) |
| **即梦** | 中文 | 字节出品，免费额度多 | [jimeng.jianying.com](https://jimeng.jianying.com) |

**操作步骤：**
1. 复制对应语言的提示词（中文→可灵/Vidu/即梦，英文→Pika/Runway）
2. 打开工具网站，选择"文生视频"或"图生视频"
3. 粘贴提示词，设置时长（建议4-6秒/镜头）
4. 生成后下载，用剪映/CapCut拼接所有镜头 + 配音即完成
        """)

        _render_share_banner("一键出片")


# ===== Tab6: 爆款拆解 =====
with tab6:
    st.markdown("### 爆款拆解器")
    st.caption("粘贴爆款视频文案，AI逆向拆解结构公式，学会「为什么能火」再复制到新选题")

    with st.form("viral_form"):
        viral_text = st.text_area(
            "粘贴爆款视频文案",
            height=200,
            placeholder="把你看到的爆款视频的配音文案/字幕粘贴到这里...",
            key="viral_text",
        )
        viral_btn = st.form_submit_button("开始拆解", type="primary", use_container_width=True)

    if viral_btn:
        if not _premium_gate("爆款拆解"):
            pass
        elif not viral_text or len(viral_text.strip()) < 30:
            st.error("请粘贴至少30字的爆款文案")
        else:
            analysis = None
            with st.status("AI正在深度拆解...", expanded=True) as v_status:
                try:
                    st.write("分析文案结构...")
                    st.write("提取爆款公式...")
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
            st.markdown("#### 核心卖点")
            st.info(a["summary"])

        # 结构拆解
        if a.get("structure"):
            s = a["structure"]
            st.markdown("#### 结构拆解")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("**钩子类型**")
                st.success(s.get("hook_type", ""))
                if s.get("hook_text"):
                    st.caption(f"原文：「{s['hook_text']}」")
                if s.get("hook_analysis"):
                    st.markdown(f"_{s['hook_analysis']}_")
            with col2:
                st.markdown("**正文模式**")
                st.success(s.get("body_pattern", ""))
                if s.get("body_analysis"):
                    st.markdown(f"_{s['body_analysis']}_")
            with col3:
                st.markdown("**收尾类型**")
                st.success(s.get("cta_type", ""))
                if s.get("cta_analysis"):
                    st.markdown(f"_{s['cta_analysis']}_")

        # 情绪曲线
        if a.get("emotional_arc"):
            st.markdown("#### 情绪曲线")
            st.info(a["emotional_arc"])

        # 爆款因素
        if a.get("viral_factors"):
            st.markdown("#### 爆款因素")
            for vf in a["viral_factors"]:
                score = vf.get("score", 0)
                bar_color = "■" if score >= 8 else "■" if score >= 6 else "■"
                sc_color = "#28a745" if score >= 8 else "#ffc107" if score >= 6 else "#dc3545"
                st.markdown(f'<span style="color:{sc_color}">{bar_color}</span> **{vf.get("factor", "")}**（{score}/10）', unsafe_allow_html=True)
                st.caption(f"证据：{vf.get('evidence', '')}")

        # 节奏分析
        if a.get("pacing"):
            p = a["pacing"]
            st.markdown("#### 节奏分析")
            pc1, pc2, pc3 = st.columns(3)
            pc1.metric("节奏", p.get("rhythm", ""))
            pc2.metric("句长", p.get("sentence_avg_length", ""))
            pc3.metric("信息密度", p.get("info_density", ""))

        # 可复用公式（核心价值）
        if a.get("reusable_formula"):
            f = a["reusable_formula"]
            st.markdown("#### 可复用爆款公式")
            st.markdown(f"**公式名称：** {f.get('name', '')}")
            st.markdown(f"**结构模式：** {f.get('pattern', '')}")
            if f.get("steps"):
                for step in f["steps"]:
                    st.markdown(f"- {step}")
            if f.get("applicable_topics"):
                st.markdown(f"**适用选题：** {'、'.join(f['applicable_topics'])}")

            # 套用公式到新选题
            st.markdown("---")
            st.markdown("#### 套用公式到新选题")
            with st.form("apply_formula_form"):
                new_topic_for_formula = st.text_input(
                    "输入你的新选题",
                    placeholder="如：为什么年轻人不愿意生孩子",
                    key="formula_new_topic",
                )
                apply_btn = st.form_submit_button("用爆款公式生成新脚本", type="primary", use_container_width=True)

            if apply_btn and new_topic_for_formula:
                with st.spinner("AI正在套用爆款公式生成脚本..."):
                    try:
                        new_script = content_analyzer.apply_formula(f, new_topic_for_formula)
                        st.session_state["formula_script"] = new_script
                    except Exception as e:
                        st.error(f"生成失败: {e}")

            if "formula_script" in st.session_state and st.session_state["formula_script"]:
                st.markdown("##### 基于爆款公式生成的新脚本")
                st.code(st.session_state["formula_script"], language=None)
                st.download_button(
                    "下载脚本",
                    data=st.session_state["formula_script"],
                    file_name="爆款公式脚本.txt",
                    mime="text/plain",
                    use_container_width=True,
                    key="dl_formula_script",
                )

        # 改进建议
        if a.get("improvement"):
            st.markdown("#### 改进建议")
            st.warning(a["improvement"])

        _render_share_banner("爆款拆解")


# ===== Tab7: 标题优化 =====
with tab7:
    st.markdown("### 标题A/B测试器")
    st.caption("标题决定80%的点击率 — AI生成多个标题变体并预测点击率，帮你选出最强标题")

    title_mode = st.radio(
        "选择模式",
        ["AI生成标题变体", "对比我的标题"],
        horizontal=True,
        key="title_mode",
    )

    if title_mode == "AI生成标题变体":
        with st.form("title_gen_form"):
            title_topic = st.text_input(
                "输入选题/主题",
                placeholder="如：为什么故宫屋顶没有鸟粪",
                key="title_topic",
            )
            title_script = st.text_area(
                "脚本内容（可选，提供后标题更精准）",
                height=100,
                placeholder="粘贴脚本正文，AI会根据内容优化标题...",
                key="title_script_ref",
            )
            t_col1, t_col2 = st.columns(2)
            with t_col1:
                title_platform = st.selectbox(
                    "目标平台",
                    ["通用", "抖音", "B站", "小红书"],
                    key="title_platform",
                )
            with t_col2:
                title_count = st.slider("生成数量", 5, 15, 8, key="title_count")
            title_gen_btn = st.form_submit_button("生成标题变体", type="primary", use_container_width=True)

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
            st.markdown(f"#### 标题变体排行（共 {len(variants)} 个）")

            for i, v in enumerate(variants, 1):
                score = v.get("score", 0)
                if score >= 8.5:
                    medal = "#1"
                    color = "#28a745"
                elif score >= 7:
                    medal = "#2"
                    color = "#ffc107"
                elif score >= 5.5:
                    medal = "#3"
                    color = "#17a2b8"
                else:
                    medal = ""
                    color = "#6c757d"

                with st.container():
                    tc1, tc2 = st.columns([5, 1])
                    with tc1:
                        st.markdown(f"**{i}. {v.get('title', '')}**")
                        st.caption(f"策略：{v.get('type', '')} | {v.get('reasoning', '')}")
                    with tc2:
                        st.markdown(
                            f'<div style="text-align:center;"><span style="background:{color};color:white;'
                            f'padding:6px 14px;border-radius:16px;font-weight:bold;font-size:1.1rem;">'
                            f'{score}分</span></div>',
                            unsafe_allow_html=True,
                        )
                    st.divider()

            _render_share_banner("标题优化")

    else:
        # 对比模式
        with st.form("title_compare_form"):
            st.markdown("输入你想对比的标题（每行一个）：")
            user_titles_text = st.text_area(
                "输入标题（每行一个）",
                height=150,
                placeholder="标题1\n标题2\n标题3",
                key="user_titles",
            )
            cmp_platform = st.selectbox("目标平台", ["通用", "抖音", "B站", "小红书"], key="cmp_platform")
            cmp_btn = st.form_submit_button("开始对比", type="primary", use_container_width=True)

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
            st.markdown("#### 标题对比结果")
            for i, item in enumerate(cmp, 1):
                score = item.get("score", 0)
                color = "#28a745" if score >= 8 else "#ffc107" if score >= 6 else "#6c757d"
                with st.container():
                    cc1, cc2 = st.columns([4, 1])
                    with cc1:
                        st.markdown(f"**{i}. {item.get('title', '')}**")
                        st.caption(f"优势：{item.get('strengths', '')} | 弱点：{item.get('weaknesses', '')}")
                        if item.get("improved"):
                            st.info(f"优化建议：{item['improved']}")
                    with cc2:
                        st.markdown(
                            f'<div style="text-align:center;"><span style="background:{color};color:white;'
                            f'padding:6px 14px;border-radius:16px;font-weight:bold;font-size:1.1rem;">'
                            f'{score}分</span></div>',
                            unsafe_allow_html=True,
                        )
                    st.divider()

            _render_share_banner("标题优化")


# ===== Tab8: 脚本诊断 =====
with tab8:
    st.markdown("### 脚本质量诊断")
    st.caption("粘贴任意脚本，AI给出完播率预测、节奏分析、互动潜力评估和具体优化建议")

    # 从其他Tab联动过来的脚本自动填入
    _prefill_script = st.session_state.get("_diag_original_script", "")
    if _prefill_script:
        st.success("✅ 已自动填入从脚本生成/一键出片传来的脚本")

    with st.form("diagnose_form"):
        diag_script = st.text_area(
            "粘贴脚本内容",
            value=_prefill_script,
            height=250,
            placeholder="粘贴你写的或AI生成的短视频脚本...",
            key="diag_script",
        )
        d_col1, d_col2 = st.columns(2)
        with d_col1:
            diag_platform = st.selectbox("目标平台", ["通用", "抖音", "B站", "小红书"], key="diag_platform")
        with d_col2:
            diag_duration = st.slider("目标时长（秒）", 15, 300, 60, step=15, key="diag_duration")
        diag_btn = st.form_submit_button("开始诊断", type="primary", use_container_width=True)

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
                    st.write("分析脚本结构...")
                    st.write("评估完播率...")
                    st.write("预测互动效果...")
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
            st.markdown("#### 六维评分")
            scores = d["scores"]
            score_names = {
                "hook_power": "钩子强度",
                "info_density": "信息密度",
                "pacing": "节奏起伏",
                "emotion": "情感感染",
                "engagement": "互动潜力",
                "platform_fit": "平台适配",
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
            st.markdown("#### 完播率预测")
            st.metric("预测完播率", cr.get("predicted", "N/A"))
            if cr.get("dropoff_points"):
                st.markdown("**可能流失点：**")
                for dp in cr["dropoff_points"]:
                    st.warning(
                        f"**{dp.get('position', '')}** — {dp.get('reason', '')}\n\n"
                        f"建议：{dp.get('suggestion', '')}"
                    )

        # 预测热门评论
        if d.get("predicted_comments"):
            st.markdown("#### 预测热门评论")
            for pc in d["predicted_comments"]:
                st.markdown(f"  _{pc}_")

        # 置顶评论建议
        if d.get("pin_comment_suggestion"):
            st.markdown("#### 建议置顶评论")
            st.success(d["pin_comment_suggestion"])

        # 具体优化建议
        if d.get("suggestions"):
            st.markdown("#### 具体优化建议")
            for sg in d["suggestions"]:
                priority = sg.get("priority", "medium")
                p_label = "[高]" if priority == "high" else "[中]" if priority == "medium" else "[低]"
                with st.expander(f"{p_label} {sg.get('area', '优化项')}", expanded=(priority == "high")):
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
            if st.button("一键优化脚本", type="primary", use_container_width=True, key="rewrite_btn"):
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
                st.markdown("#### 优化后的脚本")
                _rw_col1, _rw_col2 = st.columns(2)
                with _rw_col1:
                    st.markdown("**原始脚本**")
                    st.text_area("原始", _original_script, height=300, disabled=True, key="_rw_orig", label_visibility="collapsed")
                with _rw_col2:
                    st.markdown("**优化后脚本**")
                    st.text_area("优化后", st.session_state["rewritten_script"], height=300, disabled=True, key="_rw_new", label_visibility="collapsed")

                st.download_button(
                    "下载优化后脚本",
                    data=st.session_state["rewritten_script"],
                    file_name="优化后脚本.txt",
                    mime="text/plain",
                    use_container_width=True,
                    key="dl_rewritten",
                )

        _render_share_banner("脚本诊断")


# ===== Tab Keys: 卡密管理（仅管理员可见）=====
if _is_admin:
    with tab_keys:
        st.markdown("### 卡密管理")
        st.caption("管理员专用 — 所有卡密状态一览")

        # 加载全部卡密
        _all_keys = {}
        _all_keys.update(key_manager._load_keys())
        _all_keys.update(key_manager._load_cloud_keys())

        if not _all_keys:
            st.info("暂无卡密数据")
        else:
            from datetime import datetime as _dt

            # 云端用量缓存
            _cloud_usage_cache = {}
            if cloud_db.is_available():
                for _kc in _all_keys:
                    try:
                        _cr = cloud_db.get_usage(_kc)
                        if _cr:
                            _cloud_usage_cache[_kc] = _cr
                    except Exception:
                        pass

            # 统计
            _cnt_total = len(_all_keys)
            _cnt_unused = 0
            _cnt_active = 0
            _cnt_expired = 0
            _cnt_exhausted = 0
            _cnt_disabled = 0

            _rows = []
            _now = _dt.now()

            for _kc, _ki in _all_keys.items():
                _plan = _ki.get("plan", "")
                _plan_name = _ki.get("plan_name", key_manager.KEY_PLANS.get(_plan, {}).get("name", _plan))
                _status = _ki.get("status", "unused")

                # 云端状态优先
                _cloud_rec = _cloud_usage_cache.get(_kc, {})
                if _cloud_rec.get("status") == "disabled":
                    _status = "disabled"

                # 真实用量（云端优先）
                _total_used = _cloud_rec.get("total_used", _ki.get("total_used", 0))
                _plan_cfg = key_manager.KEY_PLANS.get(_plan, {})
                _total_limit = _ki.get("total_limit", _plan_cfg.get("total_limit", 0))
                _daily_limit = _ki.get("daily_limit", _plan_cfg.get("daily_limit", 0))

                # 过期时间
                _exp_str = _ki.get("expires_at")
                _exp_display = "—"
                _remaining_time = "—"
                if _exp_str:
                    try:
                        _exp_dt = _dt.fromisoformat(_exp_str)
                        _exp_display = _exp_dt.strftime("%Y-%m-%d")
                        if _now > _exp_dt:
                            _status = "expired"
                            _remaining_time = "已过期"
                        else:
                            _delta = _exp_dt - _now
                            if _delta.days > 0:
                                _remaining_time = f"{_delta.days}天"
                            else:
                                _remaining_time = f"{_delta.seconds // 3600}小时"
                    except Exception:
                        pass

                # 次数限制卡判断耗尽
                if _total_limit > 0 and _total_used >= _total_limit:
                    _status = "exhausted"

                # 剩余次数
                if _total_limit > 0:
                    _remaining_uses = f"{max(0, _total_limit - _total_used)}/{_total_limit}"
                else:
                    _remaining_uses = f"已用{_total_used}次 | {_daily_limit}/天"

                # 激活时间
                _act_str = _ki.get("activated_at")
                _act_display = "—"
                if _act_str:
                    try:
                        _act_display = _dt.fromisoformat(_act_str).strftime("%Y-%m-%d %H:%M")
                    except Exception:
                        pass

                # 统计
                if _status == "unused":
                    _cnt_unused += 1
                elif _status == "active":
                    _cnt_active += 1
                elif _status == "expired":
                    _cnt_expired += 1
                elif _status == "exhausted":
                    _cnt_exhausted += 1
                elif _status == "disabled":
                    _cnt_disabled += 1

                _status_map = {
                    "unused": "未激活",
                    "active": "使用中",
                    "expired": "已过期",
                    "exhausted": "已用完",
                    "disabled": "已禁用",
                }

                _rows.append({
                    "key": _kc,
                    "plan_name": _plan_name,
                    "status": _status,
                    "status_cn": _status_map.get(_status, _status),
                    "total_used": _total_used,
                    "remaining_uses": _remaining_uses,
                    "expires_at": _exp_display,
                    "remaining_time": _remaining_time,
                    "activated_at": _act_display,
                })

            # 概览指标
            _m1, _m2, _m3, _m4, _m5 = st.columns(5)
            _m1.metric("总计", _cnt_total)
            _m2.metric("未激活", _cnt_unused)
            _m3.metric("使用中", _cnt_active)
            _m4.metric("已过期", _cnt_expired)
            _m5.metric("已用完/禁用", _cnt_exhausted + _cnt_disabled)

            st.markdown("---")

            # 筛选
            _filter = st.radio(
                "筛选状态", ["全部", "未激活", "使用中", "已过期", "已用完", "已禁用"],
                horizontal=True, key="key_filter"
            )
            _filter_map = {"未激活": "unused", "使用中": "active", "已过期": "expired", "已用完": "exhausted", "已禁用": "disabled"}
            if _filter != "全部":
                _rows = [r for r in _rows if r["status"] == _filter_map[_filter]]

            # 排序：使用中 > 未激活 > 已过期 > 已用完 > 已禁用
            _sort_order = {"active": 0, "unused": 1, "expired": 2, "exhausted": 3, "disabled": 4}
            _rows.sort(key=lambda r: _sort_order.get(r["status"], 9))

            if not _rows:
                st.info("该筛选条件下没有卡密")
            else:
                for _r in _rows:
                    _color = {"unused": "#64748b", "active": "#059669", "expired": "#dc2626", "exhausted": "#d97706", "disabled": "#6b7280"}
                    _bg = {"unused": "rgba(100,116,139,0.08)", "active": "rgba(5,150,105,0.08)", "expired": "rgba(220,38,38,0.08)", "exhausted": "rgba(217,119,6,0.08)", "disabled": "rgba(107,114,128,0.08)"}
                    _sc = _r["status"]
                    _cols_row = st.columns([3, 1, 1, 1.2, 1.2, 1, 1.2])
                    _cols_row[0].markdown(f"<code style='font-size:0.82rem;font-weight:600;'>{_r['key']}</code>", unsafe_allow_html=True)
                    _cols_row[1].markdown(f"<span style='font-size:0.82rem;color:#475569;'>{_r['plan_name']}</span>", unsafe_allow_html=True)
                    _cols_row[2].markdown(f"<span style='background:{_color.get(_sc,'#999')};color:#fff;padding:2px 8px;border-radius:4px;font-size:0.73rem;font-weight:600;'>{_r['status_cn']}</span>", unsafe_allow_html=True)
                    _cols_row[3].markdown(f"<span style='font-size:0.82rem;color:#475569;'>剩余: {_r['remaining_uses']}</span>", unsafe_allow_html=True)
                    _cols_row[4].markdown(f"<span style='font-size:0.82rem;color:#475569;'>到期: {_r['expires_at']}</span>", unsafe_allow_html=True)
                    _cols_row[5].markdown(f"<span style='font-size:0.82rem;color:#475569;'>{_r['remaining_time']}</span>", unsafe_allow_html=True)
                    # 操作按钮
                    with _cols_row[6]:
                        if _sc == "disabled":
                            if st.button("启用", key=f"enable_{_r['key']}", type="primary"):
                                _cloud_rec = _cloud_usage_cache.get(_r['key'], {})
                                _tu = _cloud_rec.get("total_used", 0)
                                cloud_db.update_usage(_r['key'], _tu, "active")
                                st.rerun()
                        elif _sc in ("unused", "active"):
                            if st.button("禁用", key=f"disable_{_r['key']}"):
                                _cloud_rec = _cloud_usage_cache.get(_r['key'], {})
                                _tu = _cloud_rec.get("total_used", 0)
                                cloud_db.update_usage(_r['key'], _tu, "disabled")
                                st.rerun()

            # 导出
            if _rows:
                _csv_lines = ["卡密,类型,状态,已用次数,剩余额度,到期时间,剩余时间,激活时间"]
                for _r in _rows:
                    _csv_lines.append(f"{_r['key']},{_r['plan_name']},{_r['status_cn']},{_r['total_used']},{_r['remaining_uses']},{_r['expires_at']},{_r['remaining_time']},{_r['activated_at']}")
                st.download_button("导出CSV", data="\n".join(_csv_lines), file_name="卡密总览.csv", mime="text/csv")


# ===== Tab Admin: 发帖助手（仅管理员可见）=====
if _is_admin:
    with tab_admin:
        st.markdown("### 发帖助手")
        st.caption("管理员专用 — 获客文案一键复制 + 发布状态追踪")

        # 初始化发布状态
        if "post_status" not in st.session_state:
            st.session_state["post_status"] = {}

        # 预置文案库
        _POSTS = {
            "小红书": [
                {
                    "id": "xhs_a1",
                    "title": "选题焦虑帖",
                    "tags": "#短视频选题 #自媒体副业 #短视频脚本 #AI工具",
                    "content": """做短视频最崩溃的事，不是拍摄，是每天想"今天拍什么"

每天下班打开电脑，第一件事不是拍视频
而是对着空白文档发呆半小时：今天到底拍什么？

刷热搜 → 50条都跟我赛道无关
看同行 → 人家能火的我写出来就是四不像
硬想 → 终于想到一个，写完脚本发现逻辑不通

一晚上过去了，啥也没拍。

后来我换了个思路：不自己想选题，让AI帮我从热搜里筛。

它做的事很简单——
· 同时看抖音/B站/微博/百度四个平台的热搜
· 结合我的赛道关键词，推荐最适合我拍的选题
· 每个选题还带爆款潜力评分，高分的优先拍

现在我的流程是：打开工具 → 选最高分的选题 → 一键生成脚本 → 开拍
全程20分钟，剩下的时间全花在拍摄和剪辑上。

想试试的评论"选题"，私信发你免费体验码""",
                },
                {
                    "id": "xhs_a2",
                    "title": "写稿低效帖",
                    "tags": "#短视频脚本怎么写 #完播率 #短视频教程 #自媒体",
                    "content": """短视频脚本写了3小时，发出去播放量83

不是选题不行，是写出来的东西不行。

你有没有过这种情况：
想到一个不错的选题，信心满满打开文档
写了半天发现：开场不够吸引人、中间逻辑散、结尾不知道怎么收

改了又改，3个小时过去
发出去一看数据——83。

大部分人的脚本败在两个地方：
① 开场前3秒没有钩子（观众直接划走）
② 中间节奏平，没有信息密度起伏（看到一半就走了）

我现在的方法是：
· 先用AI生成一版脚本（它会自动加钩子+控制节奏）
· 然后让AI诊断一遍（它会告诉我观众可能在第几秒划走）
· 哪里弱改哪里，一键优化

从"写3小时播放83"变成"写20分钟播放稳定破千"

想要这个方法的评论"脚本\"""",
                },
                {
                    "id": "xhs_a3",
                    "title": "时间不够帖",
                    "tags": "#副业 #上班族副业 #短视频副业 #时间管理",
                    "content": """上班族做短视频副业，每天只有1小时怎么分配？

很多人问我：白天上班，晚上回来只有1-2小时，做短视频够吗？

够，但前提是你不能把时间花在想选题和写稿上。

我见过太多人的时间分配：
想选题 40分钟 + 写脚本 60分钟 + 拍摄 30分钟 + 剪辑 30分钟
总共 2小时40分钟 → 下班后根本做不完

我现在的分配：
AI选题+生成脚本 10分钟 + 拍摄 30分钟 + 剪辑 20分钟
总共 60分钟 → 每天下班后稳定产出一条

省下来的关键就是：把选题和写稿交给AI。
· 它从实时热搜里挑出适合你赛道的选题
· 你选一个觉得不错的
· 它自动生成完整脚本（开场钩子+正文+结尾引导都写好了）
· 你调整几句话就能直接拍

评论"效率"，送你3次免费体验""",
                },
                {
                    "id": "xhs_a4",
                    "title": "学不来爆款帖",
                    "tags": "#爆款视频 #短视频运营 #自媒体涨粉 #内容创作",
                    "content": """研究了半年爆款视频，还是不知道为什么别人能火

你有没有做过这种事：
看到一条百万播放的视频，反复看了5遍
试着分析"它为什么火"
但分析来分析去就一个感觉：确实厉害，但我学不来

问题不是你笨，是你没有分析框架。

一条爆款视频能火，无非几个维度：
· 钩子类型（是悬念开场还是反常识开场？）
· 正文节奏（信息密度是递增还是波浪式？）
· 情绪曲线（从好奇→震惊→认同→行动？）
· 结尾设计（开放提问还是行动号召？）

我现在的做法是：
把爆款文案丢给AI拆解，它会把这几个维度全部量化分析
然后直接给你一个可复用的公式
你拿这个公式套自己的选题，就能写出类似结构的脚本

想试试爆款拆解的评论"拆解\"""",
                },
                {
                    "id": "xhs_b1",
                    "title": "脚本公式教程帖",
                    "tags": "#脚本结构 #短视频教程 #完播率提升 #内容创作",
                    "content": """短视频脚本只有3个部分，90%的人第1个就写错了

写了上百条脚本之后，我发现所有高完播率的视频
结构都可以拆成3个部分：

① 钩子（前3秒）
决定观众是看下去还是划走
常见错误：用"大家好，今天给大家分享..."开场
正确做法：直接抛出反常识结论/痛点/悬念

② 正文（主体）
决定观众能不能看到最后
关键：每5-8秒要有一个新信息点或情绪转折

③ 收尾（最后5秒）
决定观众会不会评论/关注
关键：不要"感谢观看"，要抛出问题/争议/行动号召

这3个部分，我现在都让AI先生成一版
然后用诊断工具检查每个部分的质量评分

想看完整演示的评论"公式\"""",
                },
                {
                    "id": "xhs_b2",
                    "title": "标题A/B测试帖",
                    "tags": "#短视频标题 #点击率 #爆款标题 #运营技巧",
                    "content": """同一条视频换个标题，播放量差了10倍

上周做了个测试：
同样的视频内容，发了两次
第一次标题："分享3个提高效率的方法"
第二次标题："上班摸鱼2小时，靠这3招没人发现"

第一次：播放量 400
第二次：播放量 4200

好标题的3个要素：
① 有具体数字（"3个方法"比"一些方法"强10倍）
② 有情绪触发词（"震惊""居然""竟然""后悔"）
③ 有利益承诺或好奇缺口

我现在的做法：
一个选题让AI生成10个标题
每个标题都带点击率预测评分
选最高分的那个发

想试试AI标题生成的评论"标题\"""",
                },
            ],
            "知乎": [
                {
                    "id": "zh_1",
                    "title": "短视频脚本怎么写",
                    "tags": "适用问题：短视频脚本怎么写 / 新手怎么写短视频文案",
                    "content": f"""写短视频脚本这件事，核心就3件事：开场要留人，中间要有料，结尾要有互动。

**一、开场前3秒——决定生死**
5种高效开场公式：
1. 反常识："你以为的XX，其实完全是错的"
2. 痛点直击："你是不是也遇到过..."
3. 数字冲击："99%的人都不知道..."
4. 悬念制造："看完这条视频你会感谢我"
5. 利益承诺："学会这招，每月多赚XXX"

**二、正文主体——控制节奏**
最常犯的错误是"平铺直叙"。解决方案：每5-8秒要有一个新刺激点。

**三、结尾——引导互动**
有效结尾的3种写法：
1. 开放提问："你觉得哪个最有用？评论告诉我"
2. 争议制造："你同意我的看法吗？"
3. 行动号召："收藏这条，下次写脚本的时候翻出来"

实际操作中，我自己的流程是用AI工具辅助完成初稿，然后用诊断功能检查完播率。
工具是免费体验的：{_SITE_URL}""",
                },
            ],
            "即刻": [
                {
                    "id": "jk_1",
                    "title": "产品介绍帖",
                    "tags": "",
                    "content": f"""做了一个AI短视频内容工具，来聊聊

背景：自己做短视频的时候发现，选题和写稿占了80%的时间。于是做了这个工具。

它不是一个简单的"AI写文案"工具，而是把整个内容生产流程串起来了：

→ 实时热搜聚合（四平台）
→ AI选题推荐+爆款潜力评分
→ 12种风格自动写脚本（适配抖音/B站/小红书算法）
→ 自动生成AI视频工具的分镜提示词
→ 爆款视频逆向拆解
→ 脚本质量诊断（预测完播率）
→ 诊断完一键重写

目前定价：月卡¥29，有免费体验。
地址：{_SITE_URL}

欢迎试用和反馈～""",
                },
            ],
            "朋友圈": [
                {
                    "id": "pyq_1",
                    "title": "展示效果",
                    "tags": "",
                    "content": f"""自从用了AI选题写稿，做短视频的效率翻了5倍
以前：想选题1小时+写稿1小时
现在：AI选题+生成脚本，全程10分钟
多出来的时间全花在拍摄和剪辑上，数据反而更好了
（配工具截图）
{_SITE_URL}""",
                },
                {
                    "id": "pyq_2",
                    "title": "社交证明",
                    "tags": "",
                    "content": """又帮一个朋友省了2小时写稿时间
他做美食赛道的，每天最头疼的就是选题
用了我推荐的AI工具，输入"美食探店"
30秒出来的脚本比他自己写的还好
现在天天催我问有没有折扣码""",
                },
                {
                    "id": "pyq_3",
                    "title": "稀缺引导",
                    "tags": "",
                    "content": """手上还有几个免费体验码
做短视频的朋友私我
3次免费，试完觉得好用再说
（不做短视频的就别来了，用不上）""",
                },
            ],
        }

        # 平台选择
        _admin_platform = st.selectbox(
            "选择平台", list(_POSTS.keys()), key="admin_platform"
        )

        posts = _POSTS.get(_admin_platform, [])

        if not posts:
            st.info("该平台暂无预置文案")
        else:
            for post in posts:
                pid = post["id"]
                is_published = st.session_state["post_status"].get(pid, False)
                status_label = "已发布" if is_published else "未发布"
                status_color = "#28a745" if is_published else "#94a3b8"

                with st.expander(
                    f"{'[已发]' if is_published else '[待发]'} {post['title']}",
                    expanded=not is_published,
                ):
                    if post.get("tags"):
                        st.caption(post["tags"])
                    st.code(post["content"], language=None)

                    bc1, bc2 = st.columns(2)
                    with bc1:
                        if not is_published:
                            if st.button(
                                "标记为已发布",
                                key=f"mark_{pid}",
                                use_container_width=True,
                            ):
                                st.session_state["post_status"][pid] = True
                                st.rerun()
                        else:
                            if st.button(
                                "撤销已发布",
                                key=f"unmark_{pid}",
                                use_container_width=True,
                            ):
                                st.session_state["post_status"][pid] = False
                                st.rerun()
                    with bc2:
                        st.download_button(
                            "下载文案",
                            data=post["content"],
                            file_name=f"{_admin_platform}_{post['title']}.txt",
                            mime="text/plain",
                            use_container_width=True,
                            key=f"dl_{pid}",
                        )

            # 发布进度统计
            total = len(posts)
            published = sum(
                1 for p in posts if st.session_state["post_status"].get(p["id"], False)
            )
            st.markdown("---")
            st.markdown(
                f"**{_admin_platform} 发布进度：{published}/{total}**"
            )
            st.progress(published / total if total > 0 else 0)
