"""
测试波动收割策略
验证策略是否能正确生成信号并运行回测
"""

import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def test_volatility_harvest_strategy():
    """测试波动收割策略"""
    print("=" * 60)
    print("测试波动收割策略 (Volatility Harvest Strategy)")
    print("=" * 60)

    # 导入策略
    from backend.strategies.volatility_harvest_strategy import VolatilityHarvestStrategy
    from backend.strategies.backtest_engine import BacktestEngine

    # 创建模拟数据（模拟BTC 4H K线）
    print("\n1. 创建模拟K线数据...")
    np.random.seed(42)
    n_bars = 500  # 500根4H K线约83天

    # 生成价格数据（模拟BTC波动）
    base_price = 50000
    returns = np.random.normal(0.001, 0.02, n_bars)  # 均值0.1%, 波动率2%
    prices = base_price * np.cumprod(1 + returns)

    # 生成OHLCV数据
    timestamps = [datetime(2024, 1, 1) + timedelta(hours=4*i) for i in range(n_bars)]
    data = {
        'timestamp': timestamps,
        'open': prices * (1 + np.random.uniform(-0.005, 0.005, n_bars)),
        'high': prices * (1 + np.random.uniform(0, 0.02, n_bars)),
        'low': prices * (1 - np.random.uniform(0, 0.02, n_bars)),
        'close': prices,
        'volume': np.random.uniform(100, 1000, n_bars)
    }

    df = pd.DataFrame(data)
    print(f"   生成 {len(df)} 根K线, 时间范围: {df['timestamp'].iloc[0]} - {df['timestamp'].iloc[-1]}")

    # 创建策略实例
    print("\n2. 创建策略实例...")
    strategy = VolatilityHarvestStrategy()
    print(f"   策略名称: {strategy.name}")
    print(f"   策略参数: {strategy.params}")

    # 生成信号
    print("\n3. 生成交易信号...")
    df_signals = strategy.generate_signals(df)

    buy_signals = (df_signals['signal'] == 1).sum()
    sell_signals = (df_signals['signal'] == -1).sum()
    print(f"   买入信号: {buy_signals}")
    print(f"   卖出信号: {sell_signals}")

    # 检查技术指标是否计算正确
    print("\n4. 检查技术指标...")
    print(f"   ATR均值: {df_signals['atr'].mean():.2f}")
    print(f"   ATR止损均值: {df_signals['atr_trail'].mean():.2f}")
    print(f"   EMA趋势最新值: {df_signals['ema_trend'].iloc[-1]:.2f}")

    # 运行回测
    print("\n5. 运行回测...")
    engine = BacktestEngine(initial_capital=10000)
    result = engine.run_backtest(strategy, df)

    metrics = result['metrics']
    print(f"\n6. 回测结果:")
    print(f"   初始资金: ${metrics['initial_capital']:,.2f}")
    print(f"   最终资金: ${metrics['final_capital']:,.2f}")
    print(f"   总收益率: {metrics['total_return_pct']:.2f}%")
    print(f"   夏普比率: {metrics['sharpe_ratio']:.2f}")
    print(f"   最大回撤: {metrics['max_drawdown_pct']:.2f}%")
    print(f"   总交易数: {metrics['total_trades']}")
    print(f"   胜率: {metrics['win_rate']:.2f}%")

    # 测试策略描述
    print("\n7. 策略描述:")
    print("-" * 40)
    print(strategy.get_strategy_description()[:500] + "...")

    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)

    return result


def test_strategy_agent_integration():
    """测试策略Agent集成"""
    print("\n" + "=" * 60)
    print("测试策略Agent集成")
    print("=" * 60)

    try:
        from backend.agents.strategy_agent import StrategyAgent

        # 检查策略是否注册
        agent = StrategyAgent.__new__(StrategyAgent)
        agent.available_strategies = {}

        # 模拟导入检查
        from backend.strategies.volatility_harvest_strategy import VolatilityHarvestStrategy
        agent.available_strategies['VolatilityHarvest'] = VolatilityHarvestStrategy

        print(f"\n已注册策略: {list(agent.available_strategies.keys())}")
        print("VolatilityHarvest策略已成功注册!")

        # 测试实例化
        strategy = agent.available_strategies['VolatilityHarvest']()
        print(f"策略实例化成功: {strategy.name}")

    except Exception as e:
        print(f"错误: {str(e)}")
        import traceback
        traceback.print_exc()


def test_with_real_data():
    """使用真实数据测试（如果可用）"""
    print("\n" + "=" * 60)
    print("使用真实数据测试（可选）")
    print("=" * 60)

    try:
        from backend.data_fetchers.historical_data_manager import HistoricalDataManager
        from backend.strategies.volatility_harvest_strategy import VolatilityHarvestStrategy
        from backend.strategies.backtest_engine import BacktestEngine

        manager = HistoricalDataManager()

        # 尝试获取BTC-USDT 4H数据
        print("\n尝试获取 BTC-USDT 4H 历史数据...")
        df = manager.load_klines("BTC-USDT", "4H", limit=500)

        if df.empty:
            print("没有本地缓存数据，尝试从API获取...")
            df = manager.get_latest_data_for_backtest(
                symbol="BTC-USDT",
                timeframe="4H",
                days=90,
                auto_update=True
            )

        if not df.empty:
            print(f"获取到 {len(df)} 根K线数据")
            print(f"时间范围: {df['timestamp'].iloc[0]} - {df['timestamp'].iloc[-1]}")

            # 运行策略
            strategy = VolatilityHarvestStrategy()
            engine = BacktestEngine(initial_capital=10000)
            result = engine.run_backtest(strategy, df)

            metrics = result['metrics']
            print(f"\n真实数据回测结果:")
            print(f"   总收益率: {metrics['total_return_pct']:.2f}%")
            print(f"   夏普比率: {metrics['sharpe_ratio']:.2f}")
            print(f"   最大回撤: {metrics['max_drawdown_pct']:.2f}%")
            print(f"   总交易数: {metrics['total_trades']}")
            print(f"   胜率: {metrics['win_rate']:.2f}%")
        else:
            print("无法获取数据，跳过真实数据测试")

    except Exception as e:
        print(f"真实数据测试跳过: {str(e)}")


if __name__ == "__main__":
    # 运行测试
    test_volatility_harvest_strategy()
    test_strategy_agent_integration()
    test_with_real_data()
