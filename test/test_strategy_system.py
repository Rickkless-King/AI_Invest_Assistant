"""
策略系统快速测试
验证所有模块是否正常工作
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

print("=" * 60)
print("🧪 策略系统测试")
print("=" * 60)

# 测试1: 导入模块
print("\n[1/4] 测试模块导入...")
try:
    from strategies import RSIStrategy, MACDStrategy, BollingerBandsStrategy, BacktestEngine
    from data_fetchers.okx_fetcher import OKXFetcher
    print("✅ 所有策略模块导入成功")
except Exception as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)

# 测试2: 获取数据
print("\n[2/4] 测试OKX数据获取...")
try:
    fetcher = OKXFetcher()
    # 获取30天的历史数据
    df = fetcher.get_historical_candles_extended("BTC-USDT", "1H", days=30)

    if not df.empty:
        days = (df['timestamp'].iloc[-1] - df['timestamp'].iloc[0]).days
        print(f"✅ 成功获取{len(df)}条K线数据（{days}天）")
        print(f"   时间范围: {df['timestamp'].iloc[0]} 至 {df['timestamp'].iloc[-1]}")
    else:
        print("❌ 数据为空")
        sys.exit(1)
except Exception as e:
    print(f"❌ 数据获取失败: {e}")
    sys.exit(1)

# 测试3: 运行回测
print("\n[3/4] 测试回测引擎...")
try:
    # 创建策略
    strategy = RSIStrategy()
    
    # 创建回测引擎
    engine = BacktestEngine(initial_capital=10000)
    
    # 运行回测
    result = engine.run_backtest(strategy, df)
    
    metrics = result['metrics']
    
    print("✅ 回测运行成功")
    print(f"   策略: {result['strategy_name']}")
    print(f"   总收益率: {metrics['total_return_pct']:.2f}%")
    print(f"   夏普比率: {metrics['sharpe_ratio']:.2f}")
    print(f"   最大回撤: {metrics['max_drawdown_pct']:.2f}%")
    print(f"   交易次数: {metrics['total_trades']}")
    print(f"   胜率: {metrics['win_rate']:.2f}%")
    
except Exception as e:
    print(f"❌ 回测失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试4: 测试所有策略
print("\n[4/4] 测试所有策略...")
try:
    strategies = [
        RSIStrategy(),
        MACDStrategy(),
        BollingerBandsStrategy()
    ]
    
    results = []
    for strategy in strategies:
        result = engine.run_backtest(strategy, df)
        results.append(result)
        metrics = result['metrics']
        print(f"   {strategy.name}: 收益{metrics['total_return_pct']:.2f}%, 夏普{metrics['sharpe_ratio']:.2f}")
    
    # 比较策略
    comparison = engine.compare_strategies(results)
    print("\n✅ 所有策略测试完成")
    print("\n策略比较:")
    print(comparison.to_string(index=False))
    
except Exception as e:
    print(f"❌ 策略测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("🎉 所有测试通过！系统运行正常")
print("=" * 60)

print("\n💡 下一步:")
print("1. 运行 Streamlit: streamlit run frontend/streamlit_app.py")
print("2. 进入'📉 策略回测'页面")
print("3. 点击'🚀 启动Agent优化'")
print("\n或者直接测试Agent:")
print("python backend/agents/strategy_agent.py")
