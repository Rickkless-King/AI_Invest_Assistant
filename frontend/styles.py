"""
Streamlit 自定义样式配置
提供现代化、科技感的UI样式
"""

def get_custom_css():
    """返回自定义CSS样式"""
    return """
    <style>
    /* ========== 全局样式 ========== */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

    /* 主体背景渐变 */
    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
        font-family: 'Inter', sans-serif;
    }

    /* 侧边栏样式 */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
        border-right: 2px solid rgba(74, 144, 226, 0.3);
    }

    [data-testid="stSidebar"] .element-container {
        color: #e0e0e0;
    }

    /* ========== 标题样式 ========== */
    h1 {
        color: #ffffff !important;
        font-weight: 700 !important;
        text-shadow: 0 0 20px rgba(74, 144, 226, 0.5);
        letter-spacing: -0.5px;
        margin-bottom: 2rem !important;
    }

    h2 {
        color: #4a90e2 !important;
        font-weight: 600 !important;
        margin-top: 2rem !important;
        margin-bottom: 1rem !important;
    }

    h3 {
        color: #64b5f6 !important;
        font-weight: 600 !important;
    }

    /* ========== 卡片样式 ========== */
    .stMetric {
        background: linear-gradient(135deg, rgba(26, 26, 46, 0.9) 0%, rgba(22, 33, 62, 0.9) 100%);
        padding: 1.5rem !important;
        border-radius: 15px !important;
        border: 1px solid rgba(74, 144, 226, 0.2);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
    }

    .stMetric:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(74, 144, 226, 0.3);
        border-color: rgba(74, 144, 226, 0.5);
    }

    .stMetric label {
        color: #9ca3af !important;
        font-size: 0.875rem !important;
        font-weight: 500 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .stMetric [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-size: 1.875rem !important;
        font-weight: 700 !important;
    }

    .stMetric [data-testid="stMetricDelta"] {
        font-weight: 600 !important;
    }

    /* ========== 按钮样式 ========== */
    .stButton button {
        background: linear-gradient(135deg, #4a90e2 0%, #357abd 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        box-shadow: 0 4px 15px rgba(74, 144, 226, 0.4) !important;
        transition: all 0.3s ease !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .stButton button:hover {
        background: linear-gradient(135deg, #357abd 0%, #2868a8 100%) !important;
        box-shadow: 0 6px 20px rgba(74, 144, 226, 0.6) !important;
        transform: translateY(-2px);
    }

    .stButton button:active {
        transform: translateY(0);
    }

    /* ========== 输入框样式 ========== */
    .stSelectbox, .stTextInput {
        background: rgba(26, 26, 46, 0.6) !important;
        border-radius: 10px !important;
    }

    .stSelectbox > div > div,
    .stTextInput > div > div > input {
        background: rgba(26, 26, 46, 0.8) !important;
        color: #ffffff !important;
        border: 1px solid rgba(74, 144, 226, 0.3) !important;
        border-radius: 8px !important;
        padding: 0.75rem !important;
        font-size: 1rem !important;
        transition: all 0.3s ease;
    }

    .stSelectbox > div > div:hover,
    .stTextInput > div > div > input:hover {
        border-color: rgba(74, 144, 226, 0.6) !important;
    }

    .stSelectbox > div > div:focus,
    .stTextInput > div > div > input:focus {
        border-color: #4a90e2 !important;
        box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.2) !important;
    }

    /* ========== 数据表格样式 ========== */
    .stDataFrame {
        background: rgba(26, 26, 46, 0.6) !important;
        border-radius: 10px !important;
        overflow: hidden;
    }

    .stDataFrame table {
        color: #e0e0e0 !important;
    }

    .stDataFrame th {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%) !important;
        color: #4a90e2 !important;
        font-weight: 600 !important;
        padding: 1rem !important;
        text-transform: uppercase;
        font-size: 0.875rem;
        letter-spacing: 0.5px;
    }

    .stDataFrame td {
        padding: 0.875rem !important;
        border-bottom: 1px solid rgba(74, 144, 226, 0.1) !important;
    }

    .stDataFrame tbody tr:hover {
        background: rgba(74, 144, 226, 0.1) !important;
    }

    /* ========== 信息框样式 ========== */
    .stAlert {
        background: rgba(26, 26, 46, 0.9) !important;
        border-radius: 10px !important;
        border-left: 4px solid !important;
        padding: 1rem 1.5rem !important;
        backdrop-filter: blur(10px);
    }

    .stSuccess {
        border-left-color: #10b981 !important;
        background: linear-gradient(90deg, rgba(16, 185, 129, 0.1) 0%, rgba(26, 26, 46, 0.9) 100%) !important;
    }

    .stError {
        border-left-color: #ef4444 !important;
        background: linear-gradient(90deg, rgba(239, 68, 68, 0.1) 0%, rgba(26, 26, 46, 0.9) 100%) !important;
    }

    .stInfo {
        border-left-color: #3b82f6 !important;
        background: linear-gradient(90deg, rgba(59, 130, 246, 0.1) 0%, rgba(26, 26, 46, 0.9) 100%) !important;
    }

    .stWarning {
        border-left-color: #f59e0b !important;
        background: linear-gradient(90deg, rgba(245, 158, 11, 0.1) 0%, rgba(26, 26, 46, 0.9) 100%) !important;
    }

    /* ========== 分隔线样式 ========== */
    hr {
        border: none !important;
        height: 1px !important;
        background: linear-gradient(90deg, transparent 0%, rgba(74, 144, 226, 0.3) 50%, transparent 100%) !important;
        margin: 2rem 0 !important;
    }

    /* ========== 展开器样式 ========== */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, rgba(26, 26, 46, 0.8) 0%, rgba(22, 33, 62, 0.8) 100%) !important;
        border: 1px solid rgba(74, 144, 226, 0.2) !important;
        border-radius: 10px !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        padding: 1rem !important;
        transition: all 0.3s ease;
    }

    .streamlit-expanderHeader:hover {
        background: linear-gradient(135deg, rgba(26, 26, 46, 0.9) 0%, rgba(22, 33, 62, 0.9) 100%) !important;
        border-color: rgba(74, 144, 226, 0.4) !important;
    }

    .streamlit-expanderContent {
        background: rgba(26, 26, 46, 0.5) !important;
        border: 1px solid rgba(74, 144, 226, 0.2) !important;
        border-top: none !important;
        border-radius: 0 0 10px 10px !important;
        padding: 1.5rem !important;
    }

    /* ========== 图表样式 ========== */
    .stPlotlyChart {
        background: rgba(26, 26, 46, 0.6) !important;
        border-radius: 15px !important;
        padding: 1rem !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
    }

    /* ========== 标签页样式 ========== */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background: rgba(26, 26, 46, 0.6);
        padding: 0.5rem;
        border-radius: 10px;
    }

    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: #9ca3af;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }

    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(74, 144, 226, 0.1);
        color: #4a90e2;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #4a90e2 0%, #357abd 100%) !important;
        color: white !important;
    }

    /* ========== 进度条样式 ========== */
    .stProgress > div > div {
        background: linear-gradient(90deg, #4a90e2 0%, #357abd 100%) !important;
        border-radius: 10px;
    }

    /* ========== 加载动画 ========== */
    .stSpinner > div {
        border-color: #4a90e2 transparent transparent transparent !important;
    }

    /* ========== 滚动条样式 ========== */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }

    ::-webkit-scrollbar-track {
        background: rgba(26, 26, 46, 0.5);
        border-radius: 10px;
    }

    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #4a90e2 0%, #357abd 100%);
        border-radius: 10px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(180deg, #357abd 0%, #2868a8 100%);
    }

    /* ========== 自定义卡片类 ========== */
    .custom-card {
        background: linear-gradient(135deg, rgba(26, 26, 46, 0.95) 0%, rgba(22, 33, 62, 0.95) 100%);
        padding: 2rem;
        border-radius: 15px;
        border: 1px solid rgba(74, 144, 226, 0.2);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
        margin: 1rem 0;
    }

    .glow-text {
        text-shadow: 0 0 10px rgba(74, 144, 226, 0.5),
                     0 0 20px rgba(74, 144, 226, 0.3),
                     0 0 30px rgba(74, 144, 226, 0.2);
    }

    /* ========== 动画 ========== */
    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    .fade-in {
        animation: fadeIn 0.5s ease-out;
    }

    @keyframes pulse {
        0%, 100% {
            opacity: 1;
        }
        50% {
            opacity: 0.7;
        }
    }

    .pulse {
        animation: pulse 2s ease-in-out infinite;
    }

    /* ========== 响应式设计 ========== */
    @media (max-width: 768px) {
        .stMetric {
            padding: 1rem !important;
        }

        h1 {
            font-size: 1.75rem !important;
        }

        .stButton button {
            padding: 0.625rem 1.5rem !important;
            font-size: 0.875rem !important;
        }
    }
    </style>
    """


def get_header_html(title, subtitle=""):
    """返回美化的页面标题HTML"""
    return f"""
    <div class="fade-in" style="text-align: center; padding: 2rem 0;">
        <h1 class="glow-text" style="font-size: 3rem; margin-bottom: 0.5rem;">
            {title}
        </h1>
        {f'<p style="color: #9ca3af; font-size: 1.25rem; margin-top: 0;">{subtitle}</p>' if subtitle else ''}
    </div>
    """


def get_metric_card_html(label, value, delta=None, icon="📊"):
    """返回美化的指标卡片HTML"""
    delta_html = ""
    if delta:
        delta_color = "#10b981" if "+" in str(delta) or "↑" in str(delta) else "#ef4444"
        delta_html = f'<div style="color: {delta_color}; font-size: 1rem; font-weight: 600; margin-top: 0.5rem;">{delta}</div>'

    return f"""
    <div class="custom-card fade-in" style="text-align: center;">
        <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">{icon}</div>
        <div style="color: #9ca3af; font-size: 0.875rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 0.5rem;">
            {label}
        </div>
        <div style="color: #ffffff; font-size: 2rem; font-weight: 700; margin-bottom: 0.25rem;">
            {value}
        </div>
        {delta_html}
    </div>
    """


def get_status_badge(text, status="info"):
    """返回状态徽章HTML"""
    colors = {
        "success": "#10b981",
        "error": "#ef4444",
        "warning": "#f59e0b",
        "info": "#3b82f6"
    }

    color = colors.get(status, colors["info"])

    return f"""
    <span style="
        background: linear-gradient(135deg, {color}22 0%, {color}11 100%);
        color: {color};
        padding: 0.5rem 1rem;
        border-radius: 20px;
        border: 1px solid {color}44;
        font-weight: 600;
        font-size: 0.875rem;
        display: inline-block;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    ">{text}</span>
    """
