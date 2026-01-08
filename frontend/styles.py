"""
Streamlit 自定义样式配置
提供温暖、简洁、Claude 风格的浅色 UI 样式
"""

def get_custom_css():
    """返回自定义CSS样式 - Claude 浅色温润风格"""
    return """
    <style>
    /* ========== 全局样式 ========== */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* 主体背景 - 温暖的米白 */
    .stApp {
        background-color: #FBF9F4;
        color: #343433;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* 侧边栏样式 - 浅米色 */
    [data-testid="stSidebar"] {
        background-color: #F1EDE4;
        border-right: 1px solid rgba(0, 0, 0, 0.05);
    }

    [data-testid="stSidebar"] section {
        background-color: transparent !important;
    }

    /* ========== 标题样式 ========== */
    h1 {
        color: #1A1A1A !important;
        font-weight: 700 !important;
        letter-spacing: -0.025em;
        margin-bottom: 1.5rem !important;
    }

    h2 {
        color: #343433 !important;
        font-weight: 600 !important;
        margin-top: 2rem !important;
        border-bottom: 2px solid #D97757;
        padding-bottom: 0.5rem;
        display: inline-block;
    }

    h3 {
        color: #4A4A48 !important;
        font-weight: 600 !important;
    }

    /* ========== 卡片与指标样式 ========== */
    .stMetric {
        background-color: #FFFFFF !important;
        padding: 1.5rem !important;
        border-radius: 16px !important;
        border: 1px solid rgba(0, 0, 0, 0.04);
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02), 0 4px 12px rgba(0, 0, 0, 0.03);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .stMetric:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 24px rgba(0, 0, 0, 0.06);
        border-color: rgba(217, 119, 87, 0.2);
    }

    .stMetric label {
        color: #6B6B68 !important;
        font-size: 0.9rem !important;
        font-weight: 500 !important;
        text-transform: none !important;
    }

    .stMetric [data-testid="stMetricValue"] {
        color: #1A1A1A !important;
        font-size: 1.75rem !important;
        font-weight: 700 !important;
    }

    /* ========== 按钮样式 - Claude 橙色系 ========== */
    .stButton button {
        background-color: #D97757 !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.6rem 1.5rem !important;
        font-weight: 600 !important;
        transition: all 0.2s !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05) !important;
    }

    .stButton button:hover {
        background-color: #C15F3C !important;
        box-shadow: 0 4px 12px rgba(193, 95, 60, 0.3) !important;
        transform: scale(1.02);
    }

    /* ========== 输入框样式 ========== */
    .stSelectbox div[data-baseweb="select"],
    .stTextInput input {
        background-color: #FFFFFF !important;
        color: #343433 !important;
        border: 1px solid rgba(0, 0, 0, 0.1) !important;
        border-radius: 10px !important;
    }

    /* ========== 数据表格样式 ========== */
    .stDataFrame {
        border-radius: 12px !important;
        overflow: hidden;
    }

    /* ========== 信息框样式 ========== */
    .stAlert {
        border-radius: 12px !important;
        border: none !important;
        background-color: #FFFFFF !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05) !important;
    }

    /* ========== 自定义卡片类 ========== */
    .custom-card {
        background-color: #FFFFFF;
        padding: 2rem;
        border-radius: 16px;
        border: 1px solid rgba(0, 0, 0, 0.04);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.02);
        margin: 1.5rem 0;
    }

    /* ========== 滚动条优化 ========== */
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: #FBF9F4; }
    ::-webkit-scrollbar-thumb { background: #E5E1D6; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #D1CDC1; }

    /* 隐藏默认装饰 */
    div[data-testid="stDecoration"] {
        display: none;
    }
    </style>
    """

def get_header_html(title, subtitle=""):
    """返回 Claude 风格的温润页面标题"""
    return f"""
    <div style="padding: 2.5rem 0; text-align: left; margin-bottom: 2rem;">
        <h1 style="margin: 0; color: #1A1A1A; font-size: 2.75rem; font-weight: 800;">{title}</h1>
        {f'<p style="color: #6B6B68; font-size: 1.2rem; margin-top: 1rem; max-width: 800px; line-height: 1.5;">{subtitle}</p>' if subtitle else ''}
        <div style="width: 60px; height: 4px; background-color: #D97757; margin-top: 2rem; border-radius: 2px;"></div>
    </div>
    """

def get_metric_card_html(label, value, delta=None, icon="📊", delta_type=None):
    """
    Claude 风格对比指标卡片

    Args:
        label: 标签名称
        value: 主要数值
        delta: 变化值/状态文本（纯文本，不要传入HTML）
        icon: 图标
        delta_type: 状态类型 ("success", "error", "warning", "info", None为自动判断)
    """
    delta_html = ""
    if delta:
        delta_str = str(delta).strip()

        # 确定颜色
        if delta_type:
            colors = {
                "success": ("#15803d", "#f0fdf4"),
                "error": ("#b91c1c", "#fef2f2"),
                "warning": ("#b45309", "#fffbeb"),
                "info": ("#1d4ed8", "#eff6ff")
            }
            delta_color, delta_bg = colors.get(delta_type, colors["info"])
        else:
            # 自动判断
            is_positive = "+" in delta_str or "↑" in delta_str or "盈" in delta_str or "金叉" in delta_str
            is_negative = "-" in delta_str or "↓" in delta_str or "亏" in delta_str or "死叉" in delta_str
            if is_positive:
                delta_color, delta_bg = "#15803d", "#f0fdf4"
            elif is_negative:
                delta_color, delta_bg = "#b91c1c", "#fef2f2"
            else:
                delta_color, delta_bg = "#1d4ed8", "#eff6ff"

        delta_html = f'<div style="margin-top: 10px;"><span style="color: {delta_color}; background: {delta_bg}; padding: 4px 10px; border-radius: 20px; font-size: 0.85rem; font-weight: 600;">{delta_str}</span></div>'

    return f'<div class="custom-card"><div style="color: #6B6B68; font-size: 1rem; font-weight: 500; display: flex; align-items: center; gap: 10px; margin-bottom: 15px;"><span style="font-size: 1.5rem;">{icon}</span> {label}</div><div style="color: #1A1A1A; font-size: 2rem; font-weight: 700;">{value}</div>{delta_html}</div>'

def get_status_badge(text, status="info"):
    """圆润的状态标签 - 返回紧凑的HTML"""
    colors = {
        "success": ("#15803d", "#f0fdf4"),
        "error": ("#b91c1c", "#fef2f2"),
        "warning": ("#b45309", "#fffbeb"),
        "info": ("#1d4ed8", "#eff6ff")
    }
    color, bg = colors.get(status, colors["info"])
    return f'<span style="color: {color}; background-color: {bg}; padding: 6px 14px; border-radius: 100px; border: 1px solid {color}22; font-weight: 600; font-size: 0.85rem; display: inline-block;">{text}</span>'
