"""
Streamlit前端界面
功能: 加密货币分析、回测、实时监控
"""
# 正确启动streamlit的方式不是直接运行，而是cd AI_Invest_Assistant   streamlit run frontend/streamlit_app.py
# 按住Ctrl+C来终止应用

import streamlit as st
import sys
import os
from datetime import datetime, timedelta
import pandas as pd

# 添加项目根目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.data_fetchers.okx_fetcher import OKXFetcher
from backend.database.db_manager import DatabaseManager
from styles import get_custom_css, get_header_html, get_metric_card_html, get_status_badge
# from agents.crypto_analyst import CryptoAnalystAgent  # 如果有API key才能用

# 页面配置
st.set_page_config(
    page_title="🚀 AI量化交易平台",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 应用自定义样式
st.markdown(get_custom_css(), unsafe_allow_html=True)

# ========== 密码验证 ==========
# 初始化登录状态
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

# 如果未登录，显示密码输入界面
if not st.session_state.authenticated:
    st.markdown("""
        <div style="text-align: center; padding: 3rem 0 2rem 0;">
            <h1 style="font-size: 2.5rem; margin-bottom: 1rem; color: #D97757;">
                🚀 AI量化交易平台
            </h1>
            <p style="font-size: 1.2rem; color: #666; margin-bottom: 2rem;">
                欢迎访问！请输入访问密码
            </p>
        </div>
    """, unsafe_allow_html=True)

    # 居中布局
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        password = st.text_input(
            "访问密码",
            type="password",
            placeholder="请输入访问密码",
            key="password_input"
        )

        if st.button("登录", use_container_width=True, type="primary"):
            if password == "NBLQL":
                st.session_state.authenticated = True
                st.success("✅ 登录成功！正在加载应用...")
                st.rerun()
            else:
                st.error("❌ 密码错误，请重试")

        st.markdown("""
            <div style="text-align: center; margin-top: 2rem; color: #999; font-size: 0.9rem;">
                <p>💡 提示：此平台为演示项目，用于求职展示</p>
                <p>如需访问密码，请联系作者</p>
            </div>
        """, unsafe_allow_html=True)

    st.stop()  # 未登录时停止执行后续代码

# ========== 已登录，继续正常流程 ==========

# 初始化组件
@st.cache_resource
def init_components():
    """初始化OKX和数据库"""
    fetcher = OKXFetcher()
    db = DatabaseManager("crypto_trading.db")
    return fetcher, db

fetcher, db = init_components()

# 侧边栏
with st.sidebar:
    # Logo和标题
    st.markdown("""
        <div style="text-align: center; padding: 1.5rem 0 2rem 0;">
            <h1 style="font-size: 2.25rem; margin: 0; color: #D97757; font-weight: 800;">
                🚀 AI量化交易
            </h1>
            <p style="color: #6B6B68; font-size: 0.95rem; margin-top: 0.75rem; font-weight: 500;">
                智能策略 · 自动优化 · 风险控制
            </p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # 功能选择
    page = st.selectbox(
        "🎯 选择功能",
        ["📊 实时行情", "🔑 API配置与交易", "🔍 AI分析", "📈 历史数据", "💰 交易记录", "📉 策略回测"],
        label_visibility="collapsed"
    )

    st.markdown("---")

    # 系统状态
    st.markdown("### 📡 系统状态")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(get_status_badge("在线", "success"), unsafe_allow_html=True)
    with col2:
        st.markdown(get_status_badge("模拟盘", "info"), unsafe_allow_html=True)

    st.markdown("---")

    # 快速信息
    with st.expander("ℹ️ 平台信息", expanded=False):
        st.markdown("""
        **🏦 支持的交易所**
        - ✅ OKX (已集成)
        - 🔧 Bitget (开发中)

        **💰 支持的币种**
        - BTC, ETH, SOL, BNB
        - 100+ 主流币种

        **🤖 AI功能**
        - 智能策略选择
        - 参数自动优化
        - 风险评估分析
        """)

    # 底部信息
    st.markdown("---")
    st.markdown("""
        <div style="text-align: center; color: #6b7280; font-size: 0.75rem; padding: 1rem 0;">
            <p>Powered by LangGraph & DeepSeek</p>
            <p>© 2026 AI Trading Platform</p>
        </div>
    """, unsafe_allow_html=True)

# ==================== 页面1: 实时行情 ====================
if page == "📊 实时行情":
    # 页面标题
    st.markdown(get_header_html("📊 实时行情监控", "实时追踪市场动态，把握交易机会"), unsafe_allow_html=True)

    # 控制栏
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        # 交易对选择
        symbol = st.selectbox(
            "🎯 选择交易对",
            ["BTC-USDT", "ETH-USDT", "SOL-USDT", "BNB-USDT"],
            index=0
        )

    with col2:
        # 自动刷新
        auto_refresh = st.checkbox("🔄 自动刷新", value=False)

    with col3:
        # 刷新按钮
        if st.button("🔄 立即刷新", use_container_width=True):
            st.rerun()

    # 获取实时行情
    with st.spinner("正在获取行情..."):
        ticker = fetcher.get_ticker(symbol)

    if 'error' not in ticker:
        # 显示价格指标（使用美化卡片）
        st.markdown("### 💰 价格指标")
        col1, col2, col3, col4 = st.columns(4)

        # 计算涨跌幅
        change_pct = ((ticker['last'] - ticker['low_24h']) / ticker['low_24h'] * 100)
        delta_text = f"{'↑' if change_pct > 0 else '↓'} {abs(change_pct):.2f}%"

        with col1:
            st.markdown(
                get_metric_card_html(
                    "当前价格",
                    f"${ticker['last']:,.2f}",
                    delta_text,
                    "💵"
                ),
                unsafe_allow_html=True
            )

        with col2:
            st.markdown(
                get_metric_card_html(
                    "24h最高",
                    f"${ticker['high_24h']:,.2f}",
                    icon="📈"
                ),
                unsafe_allow_html=True
            )

        with col3:
            st.markdown(
                get_metric_card_html(
                    "24h最低",
                    f"${ticker['low_24h']:,.2f}",
                    icon="📉"
                ),
                unsafe_allow_html=True
            )

        with col4:
            volume_str = f"{ticker['vol_24h']:,.0f}" if ticker['vol_24h'] < 1000000 else f"{ticker['vol_24h']/1000000:.2f}M"
            st.markdown(
                get_metric_card_html(
                    "24h成交量",
                    volume_str,
                    icon="📊"
                ),
                unsafe_allow_html=True
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # 获取K线数据
        st.markdown("### 📈 K线图表")

        col1, col2 = st.columns([3, 1])
        with col1:
            timeframe = st.selectbox(
                "⏱️ 时间周期",
                ["1m", "5m", "15m", "30m", "1H", "4H", "1D"],
                index=4
            )
        with col2:
            limit = st.number_input("数据条数", min_value=50, max_value=500, value=100, step=50)

        df = fetcher.get_candles(symbol, timeframe, limit=limit)

        if not df.empty:
            # 计算技术指标
            df_indicators = fetcher.calculate_indicators(df)

            # 使用Streamlit的line_chart（带标题）
            st.markdown(f"""
                <div class="custom-card" style="padding: 1.5rem;">
                    <h4 style="color: #1A1A1A; margin-bottom: 0.5rem; font-weight: 700;">📊 {symbol} 价格走势 ({timeframe})</h4>
                    <div style="width: 40px; height: 3px; background-color: #D97757; border-radius: 2px;"></div>
                </div>
            """, unsafe_allow_html=True)

            chart_data = df_indicators.set_index('timestamp')[['close', 'sma_20', 'bb_upper', 'bb_lower']]
            st.line_chart(chart_data, height=400)

            # 技术指标
            st.markdown("### 🎯 技术指标分析")
            latest = df_indicators.iloc[-1]

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                rsi = latest['rsi']
                if rsi > 70:
                    rsi_status = "超买 🔴"
                    rsi_type = "error"
                elif rsi < 30:
                    rsi_status = "超卖 🟢"
                    rsi_type = "success"
                else:
                    rsi_status = "正常 🟡"
                    rsi_type = "warning"

                st.markdown(
                    get_metric_card_html(
                        "RSI 指标",
                        f"{rsi:.2f}",
                        rsi_status,
                        "📊",
                        rsi_type
                    ),
                    unsafe_allow_html=True
                )

            with col2:
                macd = latest['macd']
                macd_signal = latest['macd_signal']
                if macd > macd_signal:
                    macd_status_text = "金叉 🔥"
                    macd_type = "success"
                else:
                    macd_status_text = "死叉 ❄️"
                    macd_type = "info"

                st.markdown(
                    get_metric_card_html(
                        "MACD 指标",
                        f"{macd:.4f}",
                        macd_status_text,
                        "📈",
                        macd_type
                    ),
                    unsafe_allow_html=True
                )

            with col3:
                price = ticker['last']
                bb_upper = latest['bb_upper']
                bb_lower = latest['bb_lower']
                bb_mid = (bb_upper + bb_lower) / 2

                if price > bb_upper:
                    bb_position = "上轨"
                    bb_status = "上轨 ⚠️"
                    bb_type = "warning"
                elif price < bb_lower:
                    bb_position = "下轨"
                    bb_status = "下轨 💚"
                    bb_type = "success"
                else:
                    bb_position = "中间"
                    bb_status = "中间 ⚪"
                    bb_type = "info"

                st.markdown(
                    get_metric_card_html(
                        "布林带位置",
                        bb_position,
                        bb_status,
                        "📍",
                        bb_type
                    ),
                    unsafe_allow_html=True
                )

            with col4:
                # 计算成交量趋势
                vol_avg = df_indicators['volume'].tail(20).mean()
                current_vol = latest['volume']
                vol_trend = "放量" if current_vol > vol_avg * 1.5 else "缩量" if current_vol < vol_avg * 0.5 else "正常"

                if vol_trend == "放量":
                    vol_status = "放量 📊"
                    vol_type = "success"
                elif vol_trend == "缩量":
                    vol_status = "缩量 📉"
                    vol_type = "warning"
                else:
                    vol_status = "正常 📈"
                    vol_type = "info"

                st.markdown(
                    get_metric_card_html(
                        "成交量趋势",
                        vol_trend,
                        vol_status,
                        "📊",
                        vol_type
                    ),
                    unsafe_allow_html=True
                )

            # 保存数据按钮
            if st.button("💾 保存历史数据到数据库"):
                db.save_klines(df_indicators, symbol, timeframe)
                st.success(f"✅ 已保存 {len(df_indicators)} 条数据")

        else:
            st.error("❌ 无法获取K线数据")

    else:
        st.error(f"❌ {ticker['error']}")

# ==================== 页面2: API配置与交易 ====================
elif page == "🔑 API配置与交易":
    st.title("🔑 OKX API 配置与实时交易")

    # API 配置区
    st.subheader("1️⃣ API 配置")

    col1, col2 = st.columns([3, 1])

    with col1:
        st.info("""
        **如何获取 OKX API 密钥？**
        1. 登录 [OKX 官网](https://www.okx.com/)
        2. 进入 [API 管理页面](https://www.okx.com/account/my-api)
        3. 创建新的 API Key（需要权限：读取、交易）
        4. 保存 API Key、Secret Key 和 Passphrase
        """)

    with col2:
        st.metric("交易模式", "模拟盘" if st.session_state.get('demo_mode', True) else "实盘")

    # API 密钥输入
    with st.expander("📝 配置 API 密钥", expanded=False):
        api_key = st.text_input("API Key", type="password", help="从 OKX 获取的 API Key")
        secret_key = st.text_input("Secret Key", type="password", help="从 OKX 获取的 Secret Key")
        passphrase = st.text_input("Passphrase", type="password", help="创建 API 时设置的密码")
        demo_mode = st.checkbox("使用模拟盘（推荐新手）", value=True, help="模拟盘不会使用真实资金")

        if st.button("💾 保存配置"):
            if api_key and secret_key and passphrase:
                st.session_state['okx_api_key'] = api_key
                st.session_state['okx_secret_key'] = secret_key
                st.session_state['okx_passphrase'] = passphrase
                st.session_state['demo_mode'] = demo_mode
                st.success("✅ API 配置已保存！")
                st.rerun()
            else:
                st.error("❌ 请填写完整的 API 信息")

    st.markdown("---")

    # 检查是否已配置 API
    if not st.session_state.get('okx_api_key'):
        st.warning("⚠️ 请先配置 OKX API 密钥")
        st.stop()

    # 初始化带 API 的 fetcher
    api_fetcher = OKXFetcher(
        api_key=st.session_state.get('okx_api_key'),
        secret_key=st.session_state.get('okx_secret_key'),
        passphrase=st.session_state.get('okx_passphrase'),
        demo=st.session_state.get('demo_mode', True)
    )

    # 账户信息
    st.subheader("2️⃣ 账户信息")

    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("🔄 刷新账户信息"):
            with st.spinner("查询中..."):
                balance = api_fetcher.get_account_balance()

                if 'error' not in balance:
                    st.session_state['balance'] = balance
                else:
                    st.error(f"❌ {balance['error']}")

    with col2:
        if st.button("📋 查看持仓"):
            with st.spinner("查询中..."):
                positions = api_fetcher.get_positions()
                st.session_state['positions'] = positions

    # 显示账户余额
    if 'balance' in st.session_state:
        balance = st.session_state['balance']
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("总权益", f"${balance.get('total_equity', 0):,.2f}")

        with col2:
            usdt_bal = balance.get('balances', {}).get('USDT', 0)
            st.metric("USDT 余额", f"{usdt_bal:,.2f}")

        with col3:
            btc_bal = balance.get('balances', {}).get('BTC', 0)
            st.metric("BTC 余额", f"{btc_bal:.6f}")

        # 显示所有余额
        if balance.get('balances'):
            with st.expander("查看所有币种余额"):
                for currency, amount in balance['balances'].items():
                    st.write(f"**{currency}**: {amount:,.6f}")

    # 显示持仓
    if 'positions' in st.session_state and st.session_state['positions']:
        st.subheader("当前持仓")
        positions_df = pd.DataFrame(st.session_state['positions'])
        st.dataframe(positions_df)

    st.markdown("---")

    # 交易区
    st.subheader("3️⃣ 实时交易")

    # 交易提醒
    if st.session_state.get('demo_mode', True):
        st.success("✅ 当前为模拟盘模式，可以安全测试")
    else:
        st.error("⚠️ 当前为实盘模式，请谨慎操作！")

    col1, col2, col3 = st.columns(3)

    with col1:
        trade_symbol = st.selectbox("交易对", ["BTC-USDT", "ETH-USDT", "SOL-USDT", "BNB-USDT"])

    with col2:
        trade_side = st.selectbox("方向", ["buy", "sell"], format_func=lambda x: "买入" if x == "buy" else "卖出")

    with col3:
        trade_type = st.selectbox("类型", ["limit", "market"], format_func=lambda x: "限价单" if x == "limit" else "市价单")

    col1, col2 = st.columns(2)

    with col1:
        # 获取当前价格作为参考
        current_ticker = fetcher.get_ticker(trade_symbol)
        current_price = current_ticker.get('last', 0) if 'error' not in current_ticker else 0

        if trade_type == "limit":
            trade_price = st.number_input(
                "价格 (USDT)",
                min_value=0.0,
                value=float(current_price),
                format="%.2f",
                help=f"当前市场价: ${current_price:,.2f}"
            )
        else:
            st.info(f"市价单将以当前市场价格成交\n当前价格: ${current_price:,.2f}")
            trade_price = None

    with col2:
        # 根据币种设置最小数量
        min_size = 0.001 if "BTC" in trade_symbol else 0.01
        trade_size = st.number_input(
            f"数量 ({trade_symbol.split('-')[0]})",
            min_value=min_size,
            value=min_size,
            format="%.6f"
        )

    # 计算预估总额
    if trade_type == "limit" and trade_price:
        estimated_total = trade_price * trade_size
    elif current_price > 0:
        estimated_total = current_price * trade_size
    else:
        estimated_total = 0

    st.metric("预估总额", f"${estimated_total:,.2f} USDT")

    # 下单按钮
    if st.button(f"{'🟢 买入' if trade_side == 'buy' else '🔴 卖出'} {trade_symbol}", type="primary", use_container_width=True):
        with st.spinner("下单中..."):
            order_result = api_fetcher.place_order(
                symbol=trade_symbol,
                side=trade_side,
                order_type=trade_type,
                size=trade_size,
                price=trade_price
            )

            if 'error' not in order_result:
                st.success(f"✅ 订单提交成功！")
                st.json(order_result)

                # 保存到数据库
                trade_data = {
                    'symbol': trade_symbol,
                    'side': trade_side.upper(),
                    'price': order_result.get('price', current_price),
                    'quantity': trade_size,
                    'fee': 0,  # OKX会在订单完成后返回手续费
                    'strategy': 'manual',
                    'timestamp': datetime.now().isoformat()
                }
                db.save_trade(trade_data)
            else:
                st.error(f"❌ {order_result['error']}")

    st.markdown("---")

    # 订单历史
    st.subheader("4️⃣ 订单历史")

    col1, col2 = st.columns([1, 4])

    with col1:
        if st.button("🔍 查询订单"):
            with st.spinner("查询中..."):
                orders = api_fetcher.get_order_history(limit=50)
                st.session_state['orders'] = orders

    if 'orders' in st.session_state and st.session_state['orders']:
        orders_df = pd.DataFrame(st.session_state['orders'])
        st.dataframe(orders_df, use_container_width=True)
    else:
        st.info("暂无订单记录")

# ==================== 页面3: AI分析 ====================
elif page == "🔍 AI分析":
    st.title("🔍 AI驱动的市场分析")

    st.warning("⚠️ 此功能需要配置OpenAI或DeepSeek API密钥")

    # API密钥输入
    api_key = st.text_input("输入OpenAI API Key", type="password")

    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key

        symbol = st.selectbox(
            "选择交易对",
            ["BTC-USDT", "ETH-USDT", "SOL-USDT"],
            index=0
        )

        timeframe = st.selectbox(
            "时间周期",
            ["1H", "4H", "1D"],
            index=0
        )

        if st.button("🚀 开始AI分析"):
            with st.spinner("AI正在分析中..."):
                try:
                    from backend.agents.crypto_analyst import CryptoAnalystAgent

                    agent = CryptoAnalystAgent()
                    result = agent.analyze(symbol, timeframe)

                    # 显示结果
                    st.success("✅ 分析完成")

                    col1, col2 = st.columns([2, 1])

                    with col1:
                        st.subheader("技术分析")
                        st.write(result['technical_analysis'])

                    with col2:
                        st.subheader("最终建议")
                        st.info(result['final_recommendation'])

                        st.metric(
                            "置信度",
                            f"{result['confidence']:.0%}"
                        )

                except Exception as e:
                    st.error(f"❌ 分析失败: {str(e)}")
    else:
        st.info("👆 请先输入API密钥")

# ==================== 页面3: 历史数据 ====================
elif page == "📈 历史数据":
    st.title("📈 历史数据管理")

    # 查询数据
    st.subheader("查询历史K线")

    col1, col2 = st.columns(2)

    with col1:
        query_symbol = st.selectbox(
            "交易对",
            ["BTC-USDT", "ETH-USDT", "SOL-USDT"]
        )

    with col2:
        query_timeframe = st.selectbox(
            "时间周期",
            ["1H", "4H", "1D"]
        )

    if st.button("查询数据"):
        df = db.get_klines(query_symbol, query_timeframe, limit=1000)

        if not df.empty:
            st.success(f"✅ 找到 {len(df)} 条记录")

            # 显示统计
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("最早时间", df['timestamp'].min().strftime('%Y-%m-%d'))

            with col2:
                st.metric("最新时间", df['timestamp'].max().strftime('%Y-%m-%d'))

            with col3:
                st.metric("数据条数", len(df))

            # 显示图表
            st.line_chart(df.set_index('timestamp')['close'])

            # 显示数据表
            with st.expander("查看详细数据"):
                st.dataframe(df)

        else:
            st.warning("📭 数据库中暂无数据，请先从'实时行情'页面保存数据")

    # 数据库统计
    st.markdown("---")
    st.subheader("数据库统计")

    stats = db.get_statistics()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("K线数据", f"{stats.get('total_klines', 0):,}")

    with col2:
        st.metric("交易记录", f"{stats.get('total_trades', 0):,}")

    with col3:
        st.metric("分析记录", f"{stats.get('total_analysis', 0):,}")

# ==================== 页面4: 策略竞技场 ====================
elif page == "💰 交易记录":
    st.title("🏆 策略竞技场 - 模拟盘实时对决")

    st.info("""
    **策略竞技场 v2.0** - 比较Agent优化策略 vs 固定参数策略的实际表现

    - 🎯 **5种策略同时运行**: RSI / MACD / 布林带 / 波动收割 / 趋势突破
    - 💰 **资金分配**: 每种策略分配账户10%的资金（共50%）
    - 🤖 **Agent控制**: 前3种策略由AI Agent动态优化参数
    - 🔒 **固定参数**: 波动收割和趋势突破策略使用经过2017-2026年回测验证的固定参数
    - ⏱️ **时间周期**: BTC-USDT 4H
    - 📅 **统一起始**: 所有策略从 2025-01-01 开始计算表现
    - 🔄 **离线同步**: 关闭后再打开会自动同步新数据并模拟策略交易
    """)

    # 初始化竞技场和持久化服务
    try:
        from backend.trading.strategy_arena import get_arena, StrategyType
        from backend.trading.arena_persistence import get_persistence

        arena = get_arena()
        persistence = get_persistence()

        # 检查是否需要自动同步和回顾
        if 'arena_synced' not in st.session_state:
            st.session_state['arena_synced'] = False
            st.session_state['sync_result'] = None

        # 首次加载时自动同步（仅当已有资金分配时）
        if not st.session_state['arena_synced']:
            # 尝试加载之前的状态
            loaded, last_active = persistence.load_arena_state(arena)

            # 检查是否已有资金分配
            has_capital = any(s.initial_capital > 0 for s in arena.strategies.values())

            if has_capital and loaded:
                # 已有资金，执行离线同步
                with st.spinner("🔄 正在同步离线期间的数据..."):
                    sync_result = persistence.sync_and_review(arena, auto_optimize=True)
                    st.session_state['sync_result'] = sync_result
                    st.session_state['arena_synced'] = True

                    if sync_result.get('offline_hours', 0) > 1:
                        st.success(f"✅ 已同步 {sync_result['offline_hours']:.1f} 小时的离线数据")

                        if sync_result.get('strategy_performance'):
                            st.markdown("##### 📊 离线期间策略表现回顾")
                            for strategy, perf in sync_result['strategy_performance'].items():
                                mode = "🔒固定" if not perf['is_agent_controlled'] else "🤖Agent"
                                return_color = "green" if perf['simulated_return_pct'] >= 0 else "red"
                                trades = perf.get('trades_executed', 0)
                                st.markdown(f"- **{perf['name']}** ({mode}): "
                                           f"<span style='color:{return_color}'>"
                                           f"{perf['simulated_return_pct']:+.2f}%</span> "
                                           f"(新增交易:{trades})",
                                           unsafe_allow_html=True)

                        # 显示参数优化
                        if sync_result.get('optimizations'):
                            st.markdown("##### ⚙️ Agent参数自动优化")
                            for opt in sync_result['optimizations']:
                                st.info(f"**{opt['strategy']}**: {opt['reason']}")
                                st.caption(f"参数变更: {opt['old_params']} → {opt['new_params']}")
                    else:
                        st.info("📝 数据已是最新")
            else:
                # 首次运行，提示用户点击启动按钮
                st.session_state['arena_synced'] = True
                if not has_capital:
                    st.info("👋 首次运行，请点击下方「🚀 启动竞技场」按钮开始！系统将自动回测2025-01-01至今的所有策略表现。")

        # Tab布局
        arena_tab1, arena_tab2, arena_tab3, arena_tab4, arena_tab5 = st.tabs([
            "🚀 启动竞技", "📊 实时表现", "📈 策略对比", "📝 交易历史", "🔧 参数优化历史"
        ])

        # ==================== Tab 1: 启动竞技 ====================
        with arena_tab1:
            st.subheader("⚙️ 竞技场配置")

            # 获取账户余额
            balance_data = fetcher.get_account_balance()

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("##### 📍 交易设置")
                st.info(f"**交易对**: BTC-USDT | **时间周期**: 4H | **起始日期**: 2025-01-01")

                # 解析账户余额（balance_data是字典格式）
                usdt_balance = 10000  # 默认模拟资金

                if balance_data and isinstance(balance_data, dict):
                    if 'error' not in balance_data and 'balances' in balance_data:
                        # 成功获取真实余额
                        usdt_balance = balance_data.get('balances', {}).get('USDT', 0)
                        st.metric("可用USDT余额", f"${usdt_balance:,.2f}")
                        st.caption(f"总权益: ${balance_data.get('total_equity', 0):,.2f}")
                    else:
                        # API返回错误或无API Key
                        error_msg = balance_data.get('error', '未知错误')
                        st.warning(f"⚠️ {error_msg}")
                        st.info(f"使用模拟资金: ${usdt_balance:,.2f}")
                else:
                    st.warning("⚠️ 无法获取账户余额")
                    st.info(f"使用模拟资金: ${usdt_balance:,.2f}")

                # 资金分配预览
                per_strategy = usdt_balance * 0.1
                st.markdown(f"""
                **资金分配预览** (每策略10%):
                - RSI策略: ${per_strategy:,.2f}
                - MACD策略: ${per_strategy:,.2f}
                - 布林带策略: ${per_strategy:,.2f}
                - 波动收割策略: ${per_strategy:,.2f}
                - 趋势突破策略: ${per_strategy:,.2f}
                - **总投入**: ${per_strategy * 5:,.2f} (50%)
                """)

            with col2:
                st.markdown("##### 🎯 策略配置")

                # 显示5种策略的配置
                strategies_info = [
                    ("RSI", "Agent优化", "rsi_period=14, oversold=30, overbought=70"),
                    ("MACD", "Agent优化", "fast=12, slow=26, signal=9"),
                    ("布林带", "Agent优化", "period=20, std=2.0"),
                    ("波动收割", "固定参数", "ATR(20/185), 止盈1.3%, 止损3%"),
                    ("趋势突破", "固定参数", "LinReg(102), 止盈1.6%, 止损1.8%"),
                ]

                for name, mode, params in strategies_info:
                    mode_color = "🤖" if mode == "Agent优化" else "🔒"
                    st.markdown(f"**{mode_color} {name}** ({mode})")
                    st.caption(f"   参数: {params}")

            st.markdown("---")

            # 启动/停止按钮
            col1, col2, col3 = st.columns([1, 1, 1])

            with col1:
                if st.button("🚀 启动竞技场", type="primary", use_container_width=True):
                    with st.spinner("🔄 正在分配资金并回测历史数据..."):
                        # 1. 分配资金（必须在回测之前）
                        arena.allocate_capital(usdt_balance, force=True)

                        # 2. 执行从2025-01-01开始的完整回测
                        sync_result = persistence.sync_and_review(
                            arena, auto_optimize=True, force_full_backtest=True
                        )

                        # 3. 启动实时监控
                        arena.start_monitoring()

                        # 4. 保存状态
                        persistence.save_arena_state(arena)

                        # 显示回测结果
                        if sync_result.get('strategy_performance'):
                            st.success("✅ 竞技场已启动！")
                            st.markdown("##### 📊 2025-01-01至今回测结果：")
                            for strategy, perf in sync_result['strategy_performance'].items():
                                trades = perf.get('trades_executed', 0)
                                ret = perf.get('simulated_return_pct', 0)
                                color = "green" if ret >= 0 else "red"
                                st.markdown(f"- **{perf['name']}**: "
                                           f"<span style='color:{color}'>{ret:+.2f}%</span> "
                                           f"({trades}笔交易)", unsafe_allow_html=True)
                        else:
                            st.success("✅ 竞技场已启动！策略开始实时运行...")

                    st.rerun()

            with col2:
                if st.button("⏹️ 停止竞技场", use_container_width=True):
                    arena.stop_monitoring()
                    # 保存状态（下次打开时可恢复）
                    persistence.save_arena_state(arena)
                    st.warning("⏹️ 竞技场已停止（状态已保存，下次打开可恢复）")
                    st.rerun()

            with col3:
                if st.button("🔄 重置竞技场", use_container_width=True):
                    from backend.trading.strategy_arena import reset_arena
                    reset_arena()
                    # 清除数据库中的状态
                    persistence.clear_arena_state()
                    st.session_state['arena_synced'] = False
                    st.info("🔄 竞技场已重置（所有数据已清除）")
                    st.rerun()

            # 自动保存状态（每次页面加载时）
            if arena.strategies and any(s.initial_capital > 0 for s in arena.strategies.values()):
                persistence.save_arena_state(arena)

            # 当前状态
            st.markdown("---")
            status = arena.get_arena_status()

            if status["is_running"]:
                st.success(f"🟢 竞技场运行中 | 当前BTC价格: ${status['current_price']:,.2f}")
            else:
                st.info("🔴 竞技场未运行（关闭页面后，下次打开会自动同步数据并回顾表现）")

        # ==================== Tab 2: 实时表现 ====================
        with arena_tab2:
            st.subheader("📊 策略实时表现")

            # 刷新按钮
            if st.button("🔄 刷新数据"):
                st.rerun()

            status = arena.get_arena_status()

            if not status["strategies"]:
                st.info("请先启动竞技场")
            else:
                # 5种策略分两行显示：第一行3个(Agent优化)，第二行2个(固定参数)
                st.markdown("##### 🤖 Agent优化策略")
                cols_row1 = st.columns(3)
                strategy_order_row1 = ["RSI", "MACD", "BollingerBands"]

                for i, strategy_name in enumerate(strategy_order_row1):
                    if strategy_name in status["strategies"]:
                        s = status["strategies"][strategy_name]
                        with cols_row1[i]:
                            # 策略卡片
                            mode_icon = "🤖"
                            st.markdown(f"""
                            <div style="border: 2px solid {'#10B981' if s['return_pct'] >= 0 else '#EF4444'};
                                        border-radius: 10px; padding: 15px; margin-bottom: 10px;
                                        background: {'#ECFDF5' if s['return_pct'] >= 0 else '#FEF2F2'};">
                                <h4 style="margin: 0; color: #1F2937;">{mode_icon} {s['name'][:8]}</h4>
                                <p style="font-size: 24px; font-weight: bold; margin: 10px 0;
                                          color: {'#10B981' if s['return_pct'] >= 0 else '#EF4444'};">
                                    {s['return_pct']:+.2f}%
                                </p>
                                <p style="margin: 5px 0; font-size: 12px; color: #6B7280;">
                                    💰 ${s['current_value']:.2f}<br>
                                    📈 {s['trade_count']}笔 | 胜率{s['win_rate']:.0f}%
                                </p>
                            </div>
                            """, unsafe_allow_html=True)

                            # 持仓状态
                            if s["position"] > 0:
                                st.success(f"持仓: {s['position']:.6f} BTC")
                            else:
                                st.info("空仓等待信号")

                            # 最新信号
                            signal_map = {1: "🟢 买入", -1: "🔴 卖出", 0: "⚪ 持有"}
                            st.caption(f"信号: {signal_map.get(s['last_signal'], '⚪ 持有')}")

                st.markdown("##### 🔒 固定参数策略")
                cols_row2 = st.columns(2)
                strategy_order_row2 = ["VolatilityHarvest", "TrendBreakout"]

                for i, strategy_name in enumerate(strategy_order_row2):
                    if strategy_name in status["strategies"]:
                        s = status["strategies"][strategy_name]
                        with cols_row2[i]:
                            # 策略卡片
                            mode_icon = "🔒"
                            st.markdown(f"""
                            <div style="border: 2px solid {'#10B981' if s['return_pct'] >= 0 else '#EF4444'};
                                        border-radius: 10px; padding: 15px; margin-bottom: 10px;
                                        background: {'#ECFDF5' if s['return_pct'] >= 0 else '#FEF2F2'};">
                                <h4 style="margin: 0; color: #1F2937;">{mode_icon} {s['name'][:8]}</h4>
                                <p style="font-size: 24px; font-weight: bold; margin: 10px 0;
                                          color: {'#10B981' if s['return_pct'] >= 0 else '#EF4444'};">
                                    {s['return_pct']:+.2f}%
                                </p>
                                <p style="margin: 5px 0; font-size: 12px; color: #6B7280;">
                                    💰 ${s['current_value']:.2f}<br>
                                    📈 {s['trade_count']}笔 | 胜率{s['win_rate']:.0f}%
                                </p>
                            </div>
                            """, unsafe_allow_html=True)

                            # 持仓状态
                            if s["position"] > 0:
                                st.success(f"持仓: {s['position']:.6f} BTC")
                            else:
                                st.info("空仓等待信号")

                            # 最新信号
                            signal_map = {1: "🟢 买入", -1: "🔴 卖出", 0: "⚪ 持有"}
                            st.caption(f"信号: {signal_map.get(s['last_signal'], '⚪ 持有')}")

                # 总体表现
                st.markdown("---")
                st.subheader("📈 总体表现对比")

                # 收益率排名
                sorted_strategies = sorted(
                    status["strategies"].items(),
                    key=lambda x: x[1]["return_pct"],
                    reverse=True
                )

                for rank, (name, s) in enumerate(sorted_strategies, 1):
                    mode = "固定参数" if not s["is_agent_controlled"] else "Agent优化"
                    medal = "🥇" if rank == 1 else ("🥈" if rank == 2 else ("🥉" if rank == 3 else "  "))
                    st.markdown(f"{medal} **#{rank} {s['name']}** ({mode}): "
                               f"**{s['return_pct']:+.2f}%** | "
                               f"${s['current_value']:.2f} | "
                               f"{s['trade_count']}笔交易")

        # ==================== Tab 3: 策略对比 ====================
        with arena_tab3:
            st.subheader("📈 Agent优化 vs 固定参数 对比分析")

            status = arena.get_arena_status()

            if not status["strategies"]:
                st.info("请先启动竞技场以查看对比数据")
            else:
                # 计算两组平均表现
                agent_strategies = []
                fixed_strategies = []

                for name, s in status["strategies"].items():
                    if s["is_agent_controlled"]:
                        agent_strategies.append(s)
                    else:
                        fixed_strategies.append(s)

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("### 🤖 Agent优化策略")
                    if agent_strategies:
                        avg_return = sum(s["return_pct"] for s in agent_strategies) / len(agent_strategies)
                        total_trades = sum(s["trade_count"] for s in agent_strategies)
                        avg_winrate = sum(s["win_rate"] for s in agent_strategies) / len(agent_strategies)

                        st.metric("平均收益率", f"{avg_return:+.2f}%")
                        st.metric("总交易次数", total_trades)
                        st.metric("平均胜率", f"{avg_winrate:.1f}%")

                        st.markdown("**包含策略:**")
                        for s in agent_strategies:
                            st.markdown(f"- {s['name']}: {s['return_pct']:+.2f}%")

                with col2:
                    st.markdown("### 🔒 固定参数策略")
                    if fixed_strategies:
                        s = fixed_strategies[0]  # 只有一个固定参数策略

                        st.metric("收益率", f"{s['return_pct']:+.2f}%")
                        st.metric("交易次数", s["trade_count"])
                        st.metric("胜率", f"{s['win_rate']:.1f}%")

                        st.markdown("**策略参数（固定）:**")
                        for k, v in s.get("params", {}).items():
                            if k in ["atr_period", "atr_trail_period", "atr_multiplier",
                                    "stop_loss_pct", "profit_target_pct"]:
                                st.caption(f"- {k}: {v}")

                # 对比结论
                st.markdown("---")
                st.subheader("🏆 对比结论")

                if agent_strategies and fixed_strategies:
                    agent_avg = sum(s["return_pct"] for s in agent_strategies) / len(agent_strategies)
                    fixed_return = fixed_strategies[0]["return_pct"]

                    if agent_avg > fixed_return:
                        winner = "Agent优化策略"
                        diff = agent_avg - fixed_return
                        st.success(f"🤖 **{winner}** 领先! 平均收益高出 **{diff:.2f}%**")
                    elif fixed_return > agent_avg:
                        winner = "固定参数策略(波动收割)"
                        diff = fixed_return - agent_avg
                        st.success(f"🔒 **{winner}** 领先! 收益高出 **{diff:.2f}%**")
                    else:
                        st.info("🤝 两种模式表现持平")

                    # 详细对比表格
                    comparison_df = arena.get_performance_comparison()
                    st.dataframe(comparison_df, use_container_width=True)

                # ==================== 净值曲线图表 ====================
                st.markdown("---")
                st.subheader("📊 策略净值曲线 (从2026-01-01开始)")

                # 使用回测数据生成完整的历史净值曲线
                try:
                    with st.spinner("正在生成净值曲线..."):
                        net_value_df = persistence.generate_net_value_history(arena, start_date_str="2026-01-01")

                    if not net_value_df.empty:
                        import plotly.express as px

                        # 转换时间戳为datetime
                        net_value_df['timestamp'] = pd.to_datetime(net_value_df['timestamp'])

                        # 获取初始资金用于标注起点
                        initial_capital = list(arena.strategies.values())[0].initial_capital
                        if initial_capital == 0:
                            initial_capital = 478.35

                        # 创建净值曲线图
                        fig = px.line(
                            net_value_df,
                            x='timestamp',
                            y='net_value',
                            color='strategy',
                            title=f'5种策略净值曲线 (起点: ${initial_capital:.2f} USDT)',
                            labels={
                                'timestamp': '时间',
                                'net_value': '净值 (USDT)',
                                'strategy': '策略'
                            }
                        )

                        # 添加起点参考线
                        fig.add_hline(
                            y=initial_capital,
                            line_dash="dash",
                            line_color="gray",
                            annotation_text=f"起点 ${initial_capital:.2f}",
                            annotation_position="right"
                        )

                        # 更新图表样式
                        fig.update_layout(
                            xaxis_title="时间",
                            yaxis_title="净值 (USDT)",
                            legend_title="策略",
                            hovermode="x unified",
                            height=500
                        )

                        # 添加网格线
                        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
                        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')

                        st.plotly_chart(fig, use_container_width=True)

                        # 显示各策略最新净值和收益率
                        st.markdown("**各策略最新净值:**")
                        latest_values = net_value_df.groupby('strategy').last().reset_index()
                        cols = st.columns(5)
                        for idx, row in latest_values.iterrows():
                            with cols[idx % 5]:
                                profit_pct = ((row['net_value'] - initial_capital) / initial_capital) * 100
                                st.metric(
                                    label=row['strategy'],
                                    value=f"${row['net_value']:.2f}",
                                    delta=f"{profit_pct:+.2f}%"
                                )
                    else:
                        st.info("暂无净值数据。请先启动竞技场。")
                except Exception as e:
                    st.error(f"生成净值曲线失败: {str(e)}")

        # ==================== Tab 4: 交易历史 ====================
        with arena_tab4:
            st.subheader("📝 策略交易历史")

            status = arena.get_arena_status()

            # 按策略显示交易记录
            for strategy_name in ["RSI", "MACD", "BollingerBands", "VolatilityHarvest", "TrendBreakout"]:
                if strategy_name in arena.strategies:
                    state = arena.strategies[StrategyType(strategy_name)]
                    trades = state.trades

                    with st.expander(f"📊 {state.name} ({len(trades)}笔交易)", expanded=False):
                        if trades:
                            trades_df = pd.DataFrame(trades)
                            st.dataframe(trades_df, use_container_width=True)

                            # 统计
                            buy_count = len([t for t in trades if t.get('type') == 'BUY'])
                            sell_count = len([t for t in trades if t.get('type') == 'SELL'])
                            total_profit = sum(t.get('profit', 0) for t in trades if 'profit' in t)

                            st.markdown(f"买入: {buy_count}次 | 卖出: {sell_count}次 | 总盈亏: ${total_profit:.2f}")
                        else:
                            st.info("暂无交易记录")

            # 从数据库加载所有交易
            st.markdown("---")
            st.subheader("📋 全部交易记录（数据库）")

            trades_df = db.get_trades(limit=100)

            if not trades_df.empty:
                # 按策略筛选
                strategy_filter = st.selectbox(
                    "按策略筛选",
                    ["全部"] + list(trades_df['strategy'].unique()) if 'strategy' in trades_df.columns else ["全部"]
                )

                if strategy_filter != "全部" and 'strategy' in trades_df.columns:
                    trades_df = trades_df[trades_df['strategy'] == strategy_filter]

                st.dataframe(trades_df, use_container_width=True)

                # 汇总统计
                total_buy = trades_df[trades_df['side'] == 'BUY']['amount'].sum() if 'amount' in trades_df.columns else 0
                total_sell = trades_df[trades_df['side'] == 'SELL']['amount'].sum() if 'amount' in trades_df.columns else 0
                total_fee = trades_df['fee'].sum() if 'fee' in trades_df.columns else 0

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("总买入", f"${total_buy:,.2f}")
                with col2:
                    st.metric("总卖出", f"${total_sell:,.2f}")
                with col3:
                    st.metric("总手续费", f"${total_fee:,.2f}")
                with col4:
                    pnl = total_sell - total_buy - total_fee
                    st.metric("盈亏", f"${pnl:,.2f}")
            else:
                st.info("📭 暂无交易记录")

        # ==================== Tab 5: 参数优化历史 ====================
        with arena_tab5:
            st.subheader("🔧 Agent参数优化历史")

            st.markdown("""
            **说明**: 此页面显示Agent对前3种策略（RSI/MACD/布林带）的参数优化历史。
            波动收割策略使用固定参数，不会被优化。
            """)

            # 获取优化历史
            opt_history = persistence.get_optimization_history(limit=50)

            if not opt_history.empty:
                st.success(f"共有 {len(opt_history)} 条优化记录")

                # 显示优化历史表格
                display_df = opt_history.copy()
                display_df.columns = ['策略', '原参数', '新参数', '优化原因', '优化前表现', '优化时间']

                st.dataframe(display_df, use_container_width=True)

                # 分策略统计
                st.markdown("---")
                st.markdown("##### 📊 分策略优化统计")

                for strategy in opt_history['strategy_type'].unique():
                    strategy_opts = opt_history[opt_history['strategy_type'] == strategy]
                    st.markdown(f"- **{strategy}**: {len(strategy_opts)} 次优化")
            else:
                st.info("📭 暂无参数优化记录")
                st.markdown("""
                **提示**: 当满足以下条件时，Agent会自动优化参数：
                - 离线超过1小时后重新打开页面
                - 策略表现不佳（收益 < -2%）
                - 策略表现优异（收益 > 5%）时微调
                """)

    except Exception as e:
        st.error(f"❌ 策略竞技场加载失败: {str(e)}")
        st.exception(e)

# ==================== 页面5: AI策略优化 ====================
elif page == "📉 策略回测":
    st.title("🤖 AI策略优化系统")

    st.info("""
    **新功能 v2.0**:
    - 🧠 智能选择: LLM自动选择策略 或 手动指定策略
    - ⚙️ 参数优化: 自动迭代优化（最多5轮）
    - 💾 结果存储: 自动保存到数据库
    - 💬 对话分析: 多轮交流策略建议
    """)

    # 初始化session_state
    if 'chat_history' not in st.session_state:
        st.session_state['chat_history'] = []
    if 'current_result' not in st.session_state:
        st.session_state['current_result'] = None

    # Tab导航
    tab1, tab2, tab3 = st.tabs(["🚀 运行回测", "📊 历史记录", "💬 智能对话"])

    # ==================== Tab 1: 运行回测 ====================
    with tab1:
        # 配置区
        st.markdown("### ⚙️ 回测配置")

        col1, col2, col3 = st.columns(3)

        with col1:
            symbol = st.selectbox(
                "🎯 选择交易对",
                ["BTC-USDT", "ETH-USDT", "SOL-USDT"],
                key="strategy_symbol"
            )

        with col2:
            timeframe = st.selectbox(
                "⏱️ 选择时间周期",
                ["1m", "5m", "15m", "30m", "1H", "4H", "1D"],
                index=4,
                key="strategy_timeframe"
            )

        with col3:
            use_deepseek = st.checkbox("💡 使用DeepSeek（推荐）", value=True, help="使用DeepSeek LLM，成本更低")

        st.markdown("<br>", unsafe_allow_html=True)

        # 策略选择模式
        st.markdown("### 🎯 策略选择模式")

        strategy_mode = st.radio(
            "选择模式",
            ["🤖 LLM自动选择（智能推荐）", "👤 手动指定策略（自定义）"],
            horizontal=True,
            label_visibility="collapsed"
        )

        user_strategy = None
        user_params = None

        if strategy_mode == "👤 手动指定策略（自定义）":
            st.markdown("""
                <div class="custom-card" style="padding: 1.5rem;">
                    <h4 style="color: #1A1A1A; margin-bottom: 0.5rem; font-weight: 700;">📝 自定义策略配置</h4>
                    <div style="width: 40px; height: 3px; background-color: #D97757; border-radius: 2px;"></div>
                </div>
            """, unsafe_allow_html=True)

            col1, col2 = st.columns([1, 3])

            with col1:
                manual_strategy = st.selectbox(
                    "📊 选择策略",
                    ["RSI", "MACD", "BollingerBands", "VolatilityHarvest"],
                    key="manual_strategy",
                    help="VolatilityHarvest(波动收割)专为BTC-USDT 4H周期优化"
                )
                user_strategy = manual_strategy

            with col2:
                st.markdown("**⚙️ 参数设置**")

                if manual_strategy == "RSI":
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        rsi_period = st.number_input("RSI周期", min_value=5, max_value=30, value=14)
                    with col_b:
                        oversold = st.number_input("超卖阈值", min_value=10, max_value=40, value=30)
                    with col_c:
                        overbought = st.number_input("超买阈值", min_value=60, max_value=90, value=70)

                    user_params = {
                        'rsi_period': rsi_period,
                        'oversold_threshold': oversold,
                        'overbought_threshold': overbought
                    }

                elif manual_strategy == "MACD":
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        fast = st.number_input("快线周期", min_value=5, max_value=20, value=12)
                    with col_b:
                        slow = st.number_input("慢线周期", min_value=15, max_value=40, value=26)
                    with col_c:
                        signal = st.number_input("信号线周期", min_value=5, max_value=15, value=9)

                    user_params = {
                        'fast_period': fast,
                        'slow_period': slow,
                        'signal_period': signal
                    }

                elif manual_strategy == "BollingerBands":
                    col_a, col_b = st.columns(2)
                    with col_a:
                        bb_period = st.number_input("布林带周期", min_value=10, max_value=30, value=20)
                    with col_b:
                        bb_std = st.number_input("标准差倍数", min_value=1.0, max_value=3.0, value=2.0, step=0.1)

                    user_params = {
                        'bb_period': bb_period,
                        'bb_std': bb_std
                    }

                else:  # VolatilityHarvest
                    st.markdown("##### 波动收割策略参数 (专为BTC-USDT 4H优化)")

                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        atr_period = st.number_input("ATR周期(信号)", min_value=5, max_value=50, value=20, help="用于入场信号的ATR周期")
                        atr_trail_period = st.number_input("ATR周期(止损)", min_value=50, max_value=300, value=185, help="用于移动止损的ATR周期")
                    with col_b:
                        atr_multiplier = st.number_input("ATR倍数", min_value=1.0, max_value=10.0, value=4.5, step=0.5, help="移动止损 = ATR × 此倍数")
                        stop_loss_pct = st.number_input("止损%", min_value=1.0, max_value=10.0, value=3.0, step=0.5)
                    with col_c:
                        profit_target_pct = st.number_input("止盈%", min_value=0.5, max_value=5.0, value=1.3, step=0.1)
                        trend_ema_period = st.number_input("趋势EMA", min_value=20, max_value=200, value=50, help="趋势判断EMA周期")

                    use_trend_filter = st.checkbox("启用趋势过滤", value=True, help="仅在趋势方向上交易")

                    user_params = {
                        'atr_period': atr_period,
                        'atr_trail_period': atr_trail_period,
                        'atr_multiplier': atr_multiplier,
                        'entry_atr_threshold': 0.0,
                        'stop_loss_pct': stop_loss_pct,
                        'profit_target_pct': profit_target_pct,
                        'trend_ema_period': trend_ema_period,
                        'use_trend_filter': use_trend_filter,
                        'breakout_bars': 1
                    }

                st.info(f"📝 当前参数: {user_params}")

        st.markdown("<br>", unsafe_allow_html=True)

        # 运行按钮（增强视觉效果）
        st.markdown("""
            <div style="text-align: center; padding: 1rem 0;">
                <p style="color: #9ca3af; font-size: 0.875rem; margin-bottom: 0.5rem;">
                    ⏱️ 预计耗时: 30-60秒 · 🔄 最多5轮迭代优化
                </p>
            </div>
        """, unsafe_allow_html=True)

        if st.button("🚀 启动 AI 智能优化", type="primary", use_container_width=True, help="开始运行策略优化Agent"):
            with st.spinner("Agent正在工作中..."):
                try:
                    # 导入Agent
                    from backend.agents.strategy_agent import StrategyAgent

                    # 创建并运行Agent
                    agent = StrategyAgent(use_deepseek=use_deepseek)

                    # 使用容器显示过程
                    with st.status("Agent工作流", expanded=True) as status:
                        if user_strategy:
                            st.write(f"🎯 使用用户指定策略: {user_strategy}")
                            if user_params:
                                st.write(f"⚙️ 参数: {user_params}")
                        else:
                            st.write("🤖 LLM自动选择策略...")

                        st.write("📊 运行回测...")
                        st.write("🔍 分析结果...")
                        st.write("⚙️ 优化参数...")

                        # 运行Agent（传入用户参数）
                        result = agent.run(
                            symbol=symbol,
                            timeframe=timeframe,
                            user_strategy=user_strategy,
                            user_params=user_params
                        )

                        status.update(label="✅ 优化完成！", state="complete")

                    # 保存到session state
                    st.session_state['current_result'] = result
                    st.session_state['last_symbol'] = symbol
                    st.session_state['last_timeframe'] = timeframe
                    st.success("✅ Agent优化完成！结果已保存到数据库")
                    st.rerun()

                except Exception as e:
                    st.error(f"❌ Agent运行失败: {str(e)}")
                    st.exception(e)

        # 显示当前结果
        if st.session_state.get('current_result'):
            result = st.session_state['current_result']

            st.markdown("<br><br>", unsafe_allow_html=True)
            st.markdown("## 📊 优化结果")

            # 基本信息
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.markdown(
                    get_metric_card_html(
                        "策略名称",
                        result['current_strategy'],
                        None,
                        "🎯"
                    ),
                    unsafe_allow_html=True
                )

            with col2:
                st.markdown(
                    get_metric_card_html(
                        "优化迭代",
                        f"{result['iteration']}轮",
                        f"共{result['iteration']}次迭代",
                        "🔄",
                        "info"
                    ),
                    unsafe_allow_html=True
                )

            with col3:
                is_user_specified = user_strategy is not None
                mode_text = "用户指定" if is_user_specified else "LLM选择"
                mode_icon = "👤" if is_user_specified else "🤖"
                st.markdown(
                    get_metric_card_html(
                        "选择模式",
                        mode_text,
                        f"{mode_icon} {mode_text}",
                        "⚙️",
                        "warning" if is_user_specified else "success"
                    ),
                    unsafe_allow_html=True
                )

            # 参数名中文映射
            param_names_cn = {
                'rsi_period': 'RSI周期',
                'oversold_threshold': '超卖阈值',
                'overbought_threshold': '超买阈值',
                'fast_period': '快线周期',
                'slow_period': '慢线周期',
                'signal_period': '信号周期',
                'bb_period': '布林周期',
                'bb_std': '标准差',
                # 波动收割策略参数
                'atr_period': 'ATR周期',
                'atr_trail_period': 'ATR止损周期',
                'atr_multiplier': 'ATR倍数',
                'entry_atr_threshold': '入场阈值',
                'stop_loss_pct': '止损%',
                'profit_target_pct': '止盈%',
                'trend_ema_period': '趋势EMA',
                'use_trend_filter': '趋势过滤',
                'breakout_bars': '突破K线数'
            }

            with col4:
                params = result['current_params']
                param_count = len(params) if isinstance(params, dict) else 1

                st.markdown(
                    get_metric_card_html(
                        "参数配置",
                        f"共 {param_count} 个参数",
                        "点击下方查看详情",
                        "📝",
                        "info"
                    ),
                    unsafe_allow_html=True
                )

            # 在四列卡片下方显示参数详情
            if isinstance(result['current_params'], dict):
                with st.expander("📋 查看完整参数配置"):
                    param_cols = st.columns(len(result['current_params']))
                    for i, (k, v) in enumerate(result['current_params'].items()):
                        cn_name = param_names_cn.get(k, k)
                        with param_cols[i]:
                            st.metric(cn_name, v)

            # 回测指标
            if result.get('backtest_result') and 'metrics' in result['backtest_result']:
                metrics = result['backtest_result']['metrics']

                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("### 📈 回测表现")

                col1, col2, col3, col4 = st.columns(4)

                # 总收益率
                with col1:
                    return_pct = metrics['total_return_pct']
                    return_status = "📈 盈利" if return_pct > 0 else "📉 亏损"
                    return_type = "success" if return_pct > 0 else "error"
                    st.markdown(
                        get_metric_card_html(
                            "总收益率",
                            f"{return_pct:.2f}%",
                            return_status,
                            "💰",
                            return_type
                        ),
                        unsafe_allow_html=True
                    )

                # 夏普比率
                with col2:
                    sharpe = metrics['sharpe_ratio']
                    if sharpe > 1:
                        sharpe_status = "优秀 ⭐"
                        sharpe_type = "success"
                    elif sharpe > 0.5:
                        sharpe_status = "良好 👍"
                        sharpe_type = "info"
                    else:
                        sharpe_status = "一般 ⚠️"
                        sharpe_type = "warning"

                    st.markdown(
                        get_metric_card_html(
                            "夏普比率",
                            f"{sharpe:.2f}",
                            sharpe_status,
                            "📊",
                            sharpe_type
                        ),
                        unsafe_allow_html=True
                    )

                # 最大回撤
                with col3:
                    drawdown = metrics['max_drawdown_pct']
                    if abs(drawdown) < 5:
                        dd_status = "低风险 ✓"
                        dd_type = "success"
                    elif abs(drawdown) < 10:
                        dd_status = "中等 ⚠️"
                        dd_type = "warning"
                    else:
                        dd_status = "高风险 ⚠️"
                        dd_type = "error"

                    st.markdown(
                        get_metric_card_html(
                            "最大回撤",
                            f"{drawdown:.2f}%",
                            dd_status,
                            "📉",
                            dd_type
                        ),
                        unsafe_allow_html=True
                    )

                # 胜率
                with col4:
                    win_rate = metrics['win_rate']
                    if win_rate > 60:
                        wr_status = "高胜率 🎯"
                        wr_type = "success"
                    elif win_rate > 40:
                        wr_status = "中等 ✓"
                        wr_type = "info"
                    else:
                        wr_status = "偏低 ⚠️"
                        wr_type = "warning"

                    st.markdown(
                        get_metric_card_html(
                            "胜率",
                            f"{win_rate:.2f}%",
                            wr_status,
                            "🎯",
                            wr_type
                        ),
                        unsafe_allow_html=True
                    )

                # 更多指标
                with st.expander("📊 查看更多指标"):
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.metric("总交易次数", metrics.get('total_trades', 0))
                    with col2:
                        st.metric("盈利次数", metrics.get('winning_trades', 0))
                    with col3:
                        st.metric("亏损次数", metrics.get('losing_trades', 0))

                # 优化历史
                if result.get('optimization_history'):
                    st.markdown("### 📊 优化历史")

                    history_df = pd.DataFrame([
                        {
                            '迭代': h['iteration'],
                            '策略': h['strategy'],
                            '收益率(%)': f"{h['metrics']['total_return_pct']:.2f}",
                            '夏普比率': f"{h['metrics']['sharpe_ratio']:.2f}",
                            '最大回撤(%)': f"{h['metrics']['max_drawdown_pct']:.2f}",
                            '胜率(%)': f"{h['metrics']['win_rate']:.2f}",
                            '参数': str(h['params'])
                        }
                        for h in result['optimization_history']
                    ])

                    st.dataframe(history_df, use_container_width=True)

            # 清除结果
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 重新优化", use_container_width=True):
                    st.session_state['current_result'] = None
                    st.rerun()
            with col2:
                if st.button("💬 询问Agent", use_container_width=True):
                    st.info("请切换到【💬 对话】标签页与Agent交流")

        else:
            # 展示策略介绍
            st.markdown("---")
            st.markdown("### 📚 可用策略介绍")

            strategy_tab1, strategy_tab2, strategy_tab3, strategy_tab4 = st.tabs(["RSI策略", "MACD策略", "布林带策略", "波动收割策略"])

            with strategy_tab1:
                st.markdown("""
                #### RSI超买超卖策略

                **核心逻辑**:
                - RSI < 30: 超卖区域，买入信号
                - RSI > 70: 超买区域，卖出信号

                **参数**:
                - RSI周期: 通常14
                - 超卖阈值: 通常30
                - 超买阈值: 通常70

                **适用场景**:
                - ✅ 震荡市场
                - ✅ 横盘整理
                - ❌ 强趋势市场

                **历史胜率**: 60-70%
                """)

            with strategy_tab2:
                st.markdown("""
                #### MACD金叉死叉策略

                **核心逻辑**:
                - MACD上穿信号线: 买入信号（金叉）
                - MACD下穿信号线: 卖出信号（死叉）

                **参数**:
                - 快线周期: 12
                - 慢线周期: 26
                - 信号线周期: 9

                **适用场景**:
                - ✅ 趋势市场
                - ✅ 单边行情
                - ❌ 震荡市场

                **历史胜率**: 55-65%（趋势市）
                """)

            with strategy_tab3:
                st.markdown("""
                #### 布林带均值回归策略

                **核心逻辑**:
                - 价格触及下轨: 买入信号（超卖）
                - 价格触及上轨: 卖出信号（超买）

                **参数**:
                - 布林带周期: 20
                - 标准差倍数: 2.0

                **适用场景**:
                - ✅ 震荡市场
                - ✅ 区间交易
                - ❌ 强趋势突破

                **历史胜率**: 65-75%
                """)

            with strategy_tab4:
                st.markdown("""
                #### 波动收割策略 (Volatility Harvest)

                **策略来源**: 基于StrategyQuantX平台生成的Strategy 4.5.163，经过BTC-USDT 4H时间周期回测优化（2017-2026年数据）

                **核心逻辑**:
                - 使用ATR（平均真实波幅）识别市场波动状态
                - 价格突破前一根K线收盘价时入场
                - 动态移动止损保护利润
                - 趋势过滤（可选）：价格在EMA之上做多，之下做空

                **参数**:
                - ATR周期（信号）: 20
                - ATR周期（止损）: 185
                - ATR倍数: 4.5（移动止损 = ATR × 4.5）
                - 止损: 3%
                - 止盈: 1.3%
                - 趋势EMA: 50

                **出场条件**:
                - 触及固定止损
                - 触及固定止盈
                - 移动止损被触发（随利润增长而收紧）

                **适用场景**:
                - ✅ BTC-USDT 4H时间周期（回测优化）
                - ✅ 高波动市场
                - ✅ 趋势明确的市场
                - ❌ 低波动横盘市场

                **策略优势**:
                - 动态止损保护利润
                - ATR自适应市场波动
                - 2017-2026年BTC回测表现优异

                **风险提示**:
                - 震荡市场可能频繁止损
                - 需要较大资金承受回撤
                """)

    # ==================== Tab 2: 历史记录 ====================
    with tab2:
        st.subheader("📊 历史回测记录")

        try:
            from backend.data_fetchers.historical_data_manager import HistoricalDataManager

            manager = HistoricalDataManager()

            # 筛选器
            col1, col2, col3 = st.columns(3)

            with col1:
                filter_symbol = st.selectbox(
                    "筛选交易对",
                    ["全部", "BTC-USDT", "ETH-USDT", "SOL-USDT"],
                    key="filter_symbol"
                )

            with col2:
                filter_strategy = st.selectbox(
                    "筛选策略",
                    ["全部", "RSI", "MACD", "BollingerBands", "VolatilityHarvest"],
                    key="filter_strategy"
                )

            with col3:
                limit = st.number_input("显示条数", min_value=5, max_value=50, value=20)

            # 获取历史记录
            history_df = manager.get_backtest_history(
                symbol=None if filter_symbol == "全部" else filter_symbol,
                strategy_name=None if filter_strategy == "全部" else filter_strategy,
                limit=limit
            )

            if not history_df.empty:
                st.success(f"找到 {len(history_df)} 条历史记录")

                # 显示表格
                display_df = history_df[[
                    'id', 'symbol', 'timeframe', 'strategy_name',
                    'total_return_pct', 'sharpe_ratio', 'max_drawdown_pct', 'win_rate',
                    'total_trades', 'user_specified', 'created_at'
                ]].copy()

                display_df['user_specified'] = display_df['user_specified'].map({0: '🤖 LLM', 1: '👤 用户'})
                display_df.columns = [
                    'ID', '交易对', '周期', '策略',
                    '收益率(%)', '夏普', '回撤(%)', '胜率(%)',
                    '交易次数', '模式', '创建时间'
                ]

                st.dataframe(display_df, use_container_width=True)

                # 最佳策略推荐
                st.markdown("---")
                st.subheader("🏆 最佳策略推荐")

                best_sharpe = manager.get_best_strategy(
                    symbol=st.session_state.get('last_symbol', 'BTC-USDT'),
                    timeframe=st.session_state.get('last_timeframe', '1H'),
                    metric='sharpe_ratio'
                )

                best_return = manager.get_best_strategy(
                    symbol=st.session_state.get('last_symbol', 'BTC-USDT'),
                    timeframe=st.session_state.get('last_timeframe', '1H'),
                    metric='total_return_pct'
                )

                col1, col2 = st.columns(2)

                with col1:
                    if best_sharpe:
                        st.info(f"""
                        **最佳夏普比率策略** (风险调整后收益最高)

                        - 策略: {best_sharpe['strategy_name']}
                        - 参数: {best_sharpe['params']}
                        - 夏普比率: {best_sharpe['sharpe_ratio']:.2f}
                        - 收益率: {best_sharpe['total_return_pct']:.2f}%
                        """)

                with col2:
                    if best_return:
                        st.success(f"""
                        **最佳收益率策略** (绝对收益最高)

                        - 策略: {best_return['strategy_name']}
                        - 参数: {best_return['params']}
                        - 收益率: {best_return['total_return_pct']:.2f}%
                        - 夏普比率: {best_return['sharpe_ratio']:.2f}
                        """)

            else:
                st.warning("暂无历史记录，请先运行回测")

        except Exception as e:
            st.error(f"加载历史记录失败: {str(e)}")

    # ==================== Tab 3: 多轮对话（集成RAG） ====================
    with tab3:
        st.subheader("💬 与策略Agent对话（RAG增强）")

        # ========== RAG知识库管理 ==========
        st.markdown("### 📚 RAG知识库")
        st.info("""
        **RAG（检索增强生成）**：Agent会先从交易书籍中检索相关内容，再基于这些内容回答你的问题。
        这样回答更有理论依据，可以引用《海龟交易法则》、《以交易为生》等经典书籍。
        """)

        # 初始化RAG服务
        try:
            from backend.rag.rag_service import get_rag_service, reset_rag_service

            # 使用session_state缓存RAG服务状态
            if 'rag_initialized' not in st.session_state:
                st.session_state['rag_initialized'] = False
                st.session_state['rag_stats'] = None

            col_rag1, col_rag2, col_rag3 = st.columns([1, 1, 1])

            with col_rag1:
                if st.button("📖 索引书籍", use_container_width=True, help="解析PDF并建立向量索引"):
                    with st.spinner("正在索引书籍（首次可能需要下载模型，请耐心等待）..."):
                        try:
                            rag_service = get_rag_service()
                            results = rag_service.index_documents()
                            st.session_state['rag_initialized'] = True
                            st.session_state['rag_stats'] = rag_service.get_stats()

                            if results['processed']:
                                st.success(f"✅ 成功索引 {len(results['processed'])} 本书，共 {results['total_chunks']} 个文本块")
                            elif results['skipped']:
                                st.info(f"📚 所有书籍已索引，无需重复处理")
                            if results['failed']:
                                st.warning(f"⚠️ {len(results['failed'])} 本书解析失败")
                        except Exception as e:
                            st.error(f"索引失败: {str(e)}")

            with col_rag2:
                if st.button("🔄 强制重建索引", use_container_width=True, help="删除旧索引，重新解析所有书籍"):
                    with st.spinner("正在重建索引..."):
                        try:
                            reset_rag_service()
                            rag_service = get_rag_service()
                            results = rag_service.index_documents(force_reindex=True)
                            st.session_state['rag_initialized'] = True
                            st.session_state['rag_stats'] = rag_service.get_stats()
                            st.success(f"✅ 重建完成，共 {results['total_chunks']} 个文本块")
                        except Exception as e:
                            st.error(f"重建失败: {str(e)}")

            with col_rag3:
                if st.button("📊 查看状态", use_container_width=True):
                    try:
                        rag_service = get_rag_service()
                        stats = rag_service.get_stats()
                        st.session_state['rag_stats'] = stats
                        st.session_state['rag_initialized'] = stats['total_chunks'] > 0
                    except Exception as e:
                        st.error(f"获取状态失败: {str(e)}")

            # 显示知识库状态
            if st.session_state.get('rag_stats'):
                stats = st.session_state['rag_stats']
                col_s1, col_s2 = st.columns(2)
                with col_s1:
                    st.metric("文本块总数", stats['total_chunks'])
                with col_s2:
                    st.metric("已索引书籍", len(stats['processed_files']))

                if stats['processed_files']:
                    with st.expander("📚 已索引的书籍"):
                        for f in stats['processed_files']:
                            st.markdown(f"- {f}")

        except Exception as e:
            st.error(f"⚠️ RAG模块加载失败: {type(e).__name__}: {str(e)}")
            st.caption("如果是依赖问题，请运行: pip install pypdf sentence-transformers chromadb")
            st.session_state['rag_initialized'] = False

        st.markdown("---")

        # ========== 对话功能（无需先运行回测） ==========
        st.markdown("### 💬 与交易知识库对话")

        # 获取回测结果（如果有的话）
        result = st.session_state.get('current_result')
        has_backtest = result is not None

        if has_backtest:
            st.success("✅ 已有回测结果，对话将结合回测数据和书籍知识")
        else:
            st.info("💡 你可以直接询问交易相关问题，Agent会从书籍中检索答案。运行回测后还能结合回测数据回答。")

        # 显示对话历史
        for msg in st.session_state['chat_history']:
            if msg['role'] == 'user':
                st.markdown(f"**👤 You:** {msg['content']}")
            else:
                st.markdown(f"**🤖 Agent:** {msg['content']}")
            st.markdown("---")

        # 输入框
        user_question = st.text_input(
            "你的问题",
            placeholder="例如：止损应该怎么设置？什么是趋势跟踪？海龟交易法则的核心是什么？",
            key="chat_input"
        )

        # RAG开关
        use_rag = st.checkbox(
            "🔍 启用RAG检索（从交易书籍中检索相关内容）",
            value=st.session_state.get('rag_initialized', False),
            disabled=not st.session_state.get('rag_initialized', False),
            help="启用后，Agent会先检索书籍内容，回答更有理论依据"
        )

        col1, col2 = st.columns([4, 1])

        with col1:
            if st.button("📤 发送", type="primary", use_container_width=True):
                if user_question:
                    with st.spinner("Agent思考中..."):
                        try:
                            from langchain_openai import ChatOpenAI
                            from langchain_core.messages import HumanMessage, SystemMessage
                            import os

                            use_deepseek = st.session_state.get('use_deepseek', True)

                            if use_deepseek:
                                llm = ChatOpenAI(
                                    model="deepseek-chat",
                                    base_url="https://api.deepseek.com",
                                    api_key=os.getenv("DEEPSEEK_API_KEY"),
                                    temperature=0.7,
                                )
                            else:
                                llm = ChatOpenAI(
                                    model="qwen-plus",
                                    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                                    api_key=os.getenv("DASHSCOPE_API_KEY"),
                                    temperature=0.7,
                                )

                            # ========== RAG检索 ==========
                            rag_context = ""
                            retrieved_sources = []

                            if use_rag and st.session_state.get('rag_initialized'):
                                try:
                                    from backend.rag.rag_service import get_rag_service
                                    rag_service = get_rag_service()

                                    # 检索相关文档
                                    rag_context = rag_service.get_context_for_llm(user_question, top_k=3)
                                    docs = rag_service.retrieve(user_question, top_k=3)
                                    retrieved_sources = [doc['source'] for doc in docs]

                                    if rag_context:
                                        st.info(f"📚 已从以下书籍检索到相关内容: {', '.join(set(retrieved_sources))}")
                                except Exception as e:
                                    st.warning(f"RAG检索失败: {str(e)}")

                            # ========== 构建上下文 ==========
                            context = "我是量化交易策略Agent，擅长策略分析、参数优化和交易知识解答。\n\n"

                            # 如果有回测结果，添加到上下文
                            if has_backtest:
                                metrics = result.get('backtest_result', {}).get('metrics', {})
                                context += f"""========== 当前回测结果 ==========
策略: {result['current_strategy']}
参数: {result['current_params']}
总收益率: {metrics.get('total_return_pct', 0):.2f}%
夏普比率: {metrics.get('sharpe_ratio', 0):.2f}
最大回撤: {metrics.get('max_drawdown_pct', 0):.2f}%
胜率: {metrics.get('win_rate', 0):.2f}%
========================================

"""

                            # 如果有RAG检索结果，添加到上下文
                            if rag_context:
                                context += f"""========== 交易书籍参考资料 ==========
{rag_context}
========================================

"""

                            context += f"""历史对话:
{chr(10).join([f"{m['role']}: {m['content']}" for m in st.session_state['chat_history'][-3:]])}

用户问题: {user_question}

请基于以上信息回答用户问题。
{"如果参考资料中有相关内容，请在回答中引用具体来源（如：根据《海龟交易法则》...）。" if rag_context else ""}
{"如果用户询问如何调整参数，请结合回测结果给出具体建议。" if has_backtest else ""}
"""

                            response = llm.invoke([
                                SystemMessage(content="你是一个专业的量化交易策略Agent，擅长策略分析、参数优化和交易知识解答。如果提供了交易书籍的参考资料，请在回答中恰当引用书名。回答要专业、有理有据。"),
                                HumanMessage(content=context)
                            ])

                            # 保存到历史（如果启用了RAG，记录来源）
                            user_msg = user_question
                            agent_msg = response.content
                            if retrieved_sources:
                                agent_msg += f"\n\n📚 *本回答参考了: {', '.join(set(retrieved_sources))}*"

                            st.session_state['chat_history'].append({
                                'role': 'user',
                                'content': user_msg
                            })
                            st.session_state['chat_history'].append({
                                'role': 'agent',
                                'content': agent_msg
                            })

                            st.rerun()

                        except Exception as e:
                            st.error(f"询问失败: {str(e)}")
                else:
                    st.warning("请输入问题")

        with col2:
            if st.button("🗑️ 清空", use_container_width=True):
                st.session_state['chat_history'] = []
                st.rerun()

# 页脚
st.sidebar.markdown("---")
st.sidebar.markdown("""
<small>
**60天求职冲刺项目**
Tech Stack: Python, Streamlit, LangGraph, OKX API
Version: 2.0.0 (支持手动调参、历史记录、多轮对话)
</small>
""", unsafe_allow_html=True)
