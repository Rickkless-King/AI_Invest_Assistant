"""
Streamlit前端界面
功能: 加密货币分析、回测、实时监控
"""
# 正确启动streamlit的方式不是直接运行，而是使用streamlit run d:/XiaZai/【1018】Final_Oppotunity/AI_Invest_Assistant/frontend/streamlit_app.py
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
        <div style="text-align: center; padding: 1rem 0 2rem 0;">
            <h1 style="font-size: 2rem; margin: 0; background: linear-gradient(135deg, #4a90e2 0%, #64b5f6 100%);
                       -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 700;">
                🚀 AI量化交易
            </h1>
            <p style="color: #9ca3af; font-size: 0.875rem; margin-top: 0.5rem;">
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
                <div class="custom-card">
                    <h4 style="color: #4a90e2; margin-bottom: 1rem;">📊 {symbol} 价格走势 ({timeframe})</h4>
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
                    rsi_status = "超买"
                    rsi_badge = get_status_badge("超买 🔴", "error")
                elif rsi < 30:
                    rsi_status = "超卖"
                    rsi_badge = get_status_badge("超卖 🟢", "success")
                else:
                    rsi_status = "正常"
                    rsi_badge = get_status_badge("正常 🟡", "warning")

                st.markdown(
                    get_metric_card_html(
                        "RSI 指标",
                        f"{rsi:.2f}",
                        rsi_badge,
                        "📊"
                    ),
                    unsafe_allow_html=True
                )

            with col2:
                macd = latest['macd']
                macd_signal = latest['macd_signal']
                if macd > macd_signal:
                    macd_status_text = "金叉"
                    macd_badge = get_status_badge("金叉 🔥", "success")
                else:
                    macd_status_text = "死叉"
                    macd_badge = get_status_badge("死叉 ❄️", "info")

                st.markdown(
                    get_metric_card_html(
                        "MACD 指标",
                        f"{macd:.4f}",
                        macd_badge,
                        "📈"
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
                    bb_badge = get_status_badge("上轨 ⚠️", "warning")
                elif price < bb_lower:
                    bb_position = "下轨"
                    bb_badge = get_status_badge("下轨 💚", "success")
                else:
                    bb_position = "中间"
                    bb_badge = get_status_badge("中间 ⚪", "info")

                st.markdown(
                    get_metric_card_html(
                        "布林带位置",
                        bb_position,
                        bb_badge,
                        "📍"
                    ),
                    unsafe_allow_html=True
                )

            with col4:
                # 计算成交量趋势
                vol_avg = df_indicators['volume'].tail(20).mean()
                current_vol = latest['volume']
                vol_trend = "放量" if current_vol > vol_avg * 1.5 else "缩量" if current_vol < vol_avg * 0.5 else "正常"

                if vol_trend == "放量":
                    vol_badge = get_status_badge("放量 📊", "success")
                elif vol_trend == "缩量":
                    vol_badge = get_status_badge("缩量 📉", "warning")
                else:
                    vol_badge = get_status_badge("正常 📈", "info")

                st.markdown(
                    get_metric_card_html(
                        "成交量趋势",
                        vol_trend,
                        vol_badge,
                        "📊"
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

# ==================== 页面4: 交易记录 ====================
elif page == "💰 交易记录":
    st.title("💰 交易记录管理")

    # 手动添加交易
    st.subheader("添加交易记录")

    col1, col2, col3 = st.columns(3)

    with col1:
        trade_symbol = st.selectbox("交易对", ["BTC-USDT", "ETH-USDT", "SOL-USDT"])
        trade_side = st.selectbox("方向", ["BUY", "SELL"])

    with col2:
        trade_price = st.number_input("价格", min_value=0.0, value=42000.0)
        trade_quantity = st.number_input("数量", min_value=0.0, value=0.01, format="%.4f")

    with col3:
        trade_fee = st.number_input("手续费", min_value=0.0, value=0.42)
        trade_strategy = st.text_input("策略名称", value="manual")

    if st.button("💾 保存交易"):
        trade_data = {
            'symbol': trade_symbol,
            'side': trade_side,
            'price': trade_price,
            'quantity': trade_quantity,
            'fee': trade_fee,
            'strategy': trade_strategy,
            'timestamp': datetime.now().isoformat()
        }
        db.save_trade(trade_data)
        st.success("✅ 交易记录已保存")
        st.rerun()

    # 显示交易记录
    st.markdown("---")
    st.subheader("交易历史")

    trades_df = db.get_trades(limit=100)

    if not trades_df.empty:
        # 计算总盈亏（简化）
        total_buy = trades_df[trades_df['side'] == 'BUY']['amount'].sum()
        total_sell = trades_df[trades_df['side'] == 'SELL']['amount'].sum()
        total_fee = trades_df['fee'].sum()

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("总买入", f"${total_buy:,.2f}")

        with col2:
            st.metric("总卖出", f"${total_sell:,.2f}")

        with col3:
            st.metric("总手续费", f"${total_fee:,.2f}")

        with col4:
            pnl = total_sell - total_buy - total_fee
            st.metric("盈亏", f"${pnl:,.2f}", delta=f"{(pnl/total_buy*100):.2f}%" if total_buy > 0 else "0%")

        # 显示交易表格
        st.dataframe(trades_df[['symbol', 'side', 'price', 'quantity', 'amount', 'timestamp']])

    else:
        st.info("📭 暂无交易记录")

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
                <div class="custom-card">
                    <h4 style="color: #4a90e2; margin-bottom: 1rem;">📝 自定义策略配置</h4>
                </div>
            """, unsafe_allow_html=True)

            col1, col2 = st.columns([1, 3])

            with col1:
                manual_strategy = st.selectbox(
                    "📊 选择策略",
                    ["RSI", "MACD", "BollingerBands"],
                    key="manual_strategy"
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

                else:  # BollingerBands
                    col_a, col_b = st.columns(2)
                    with col_a:
                        bb_period = st.number_input("布林带周期", min_value=10, max_value=30, value=20)
                    with col_b:
                        bb_std = st.number_input("标准差倍数", min_value=1.0, max_value=3.0, value=2.0, step=0.1)

                    user_params = {
                        'bb_period': bb_period,
                        'bb_std': bb_std
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
                        icon="🎯"
                    ),
                    unsafe_allow_html=True
                )

            with col2:
                iteration_badge = get_status_badge(f"{result['iteration']}轮", "info")
                st.markdown(
                    get_metric_card_html(
                        "优化迭代",
                        f"{result['iteration']}",
                        iteration_badge,
                        "🔄"
                    ),
                    unsafe_allow_html=True
                )

            with col3:
                is_user_specified = user_strategy is not None
                mode_text = "用户指定" if is_user_specified else "LLM选择"
                mode_badge = get_status_badge(f"👤 {mode_text}" if is_user_specified else f"🤖 {mode_text}",
                                             "warning" if is_user_specified else "success")
                st.markdown(
                    get_metric_card_html(
                        "选择模式",
                        mode_text,
                        mode_badge,
                        "⚙️"
                    ),
                    unsafe_allow_html=True
                )

            with col4:
                params_str = str(result['current_params'])
                st.markdown(
                    get_metric_card_html(
                        "参数配置",
                        "查看详情 →",
                        f"<code style='font-size: 0.75rem; color: #64b5f6;'>{params_str[:30]}...</code>",
                        "📝"
                    ),
                    unsafe_allow_html=True
                )

            # 回测指标
            if result.get('backtest_result') and 'metrics' in result['backtest_result']:
                metrics = result['backtest_result']['metrics']

                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("### 📈 回测表现")

                col1, col2, col3, col4 = st.columns(4)

                # 总收益率
                with col1:
                    return_pct = metrics['total_return_pct']
                    return_status = "success" if return_pct > 0 else "error"
                    return_badge = get_status_badge(
                        f"{'📈 盈利' if return_pct > 0 else '📉 亏损'}",
                        return_status
                    )
                    st.markdown(
                        get_metric_card_html(
                            "总收益率",
                            f"{return_pct:.2f}%",
                            return_badge,
                            "💰"
                        ),
                        unsafe_allow_html=True
                    )

                # 夏普比率
                with col2:
                    sharpe = metrics['sharpe_ratio']
                    if sharpe > 1:
                        sharpe_badge = get_status_badge("优秀 ⭐", "success")
                    elif sharpe > 0.5:
                        sharpe_badge = get_status_badge("良好 👍", "info")
                    else:
                        sharpe_badge = get_status_badge("一般 ⚠️", "warning")

                    st.markdown(
                        get_metric_card_html(
                            "夏普比率",
                            f"{sharpe:.2f}",
                            sharpe_badge,
                            "📊"
                        ),
                        unsafe_allow_html=True
                    )

                # 最大回撤
                with col3:
                    drawdown = metrics['max_drawdown_pct']
                    if abs(drawdown) < 5:
                        dd_badge = get_status_badge("低风险 ✓", "success")
                    elif abs(drawdown) < 10:
                        dd_badge = get_status_badge("中等 ⚠️", "warning")
                    else:
                        dd_badge = get_status_badge("高风险 ⚠️", "error")

                    st.markdown(
                        get_metric_card_html(
                            "最大回撤",
                            f"{drawdown:.2f}%",
                            dd_badge,
                            "📉"
                        ),
                        unsafe_allow_html=True
                    )

                # 胜率
                with col4:
                    win_rate = metrics['win_rate']
                    if win_rate > 60:
                        wr_badge = get_status_badge("高胜率 🎯", "success")
                    elif win_rate > 40:
                        wr_badge = get_status_badge("中等 ✓", "info")
                    else:
                        wr_badge = get_status_badge("偏低 ⚠️", "warning")

                    st.markdown(
                        get_metric_card_html(
                            "胜率",
                            f"{win_rate:.2f}%",
                            wr_badge,
                            "🎯"
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

            strategy_tab1, strategy_tab2, strategy_tab3 = st.tabs(["RSI策略", "MACD策略", "布林带策略"])

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
                    ["全部", "RSI", "MACD", "BollingerBands"],
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

    # ==================== Tab 3: 多轮对话 ====================
    with tab3:
        st.subheader("💬 与策略Agent对话")

        if not st.session_state.get('current_result'):
            st.info("请先运行回测，然后可以询问Agent关于策略的问题")
        else:
            result = st.session_state['current_result']
            metrics = result.get('backtest_result', {}).get('metrics', {})

            # 显示对话历史
            st.markdown("### 对话历史")

            for msg in st.session_state['chat_history']:
                if msg['role'] == 'user':
                    st.markdown(f"**👤 You:** {msg['content']}")
                else:
                    st.markdown(f"**🤖 Agent:** {msg['content']}")
                st.markdown("---")

            # 输入框
            user_question = st.text_input(
                "你的问题",
                placeholder="例如：为什么选择这个策略？如何进一步优化？参数应该怎么调整？",
                key="chat_input"
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

                                # 构建上下文
                                context = f"""
我是策略优化Agent。以下是我的优化结果：

策略: {result['current_strategy']}
参数: {result['current_params']}
总收益率: {metrics.get('total_return_pct', 0):.2f}%
夏普比率: {metrics.get('sharpe_ratio', 0):.2f}
最大回撤: {metrics.get('max_drawdown_pct', 0):.2f}%
胜率: {metrics.get('win_rate', 0):.2f}%

优化过程:
{chr(10).join([f"迭代{h['iteration']}: 收益{h['metrics']['total_return_pct']:.2f}%, 夏普{h['metrics']['sharpe_ratio']:.2f}" for h in result.get('optimization_history', [])])}

历史对话:
{chr(10).join([f"{m['role']}: {m['content']}" for m in st.session_state['chat_history'][-3:]])}

用户问题: {user_question}

请基于以上信息回答用户问题。如果用户询问如何调整参数，请给出具体的参数建议。
"""

                                response = llm.invoke([
                                    SystemMessage(content="你是一个专业的量化交易策略Agent，擅长策略分析和参数优化"),
                                    HumanMessage(content=context)
                                ])

                                # 保存到历史
                                st.session_state['chat_history'].append({
                                    'role': 'user',
                                    'content': user_question
                                })
                                st.session_state['chat_history'].append({
                                    'role': 'agent',
                                    'content': response.content
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
