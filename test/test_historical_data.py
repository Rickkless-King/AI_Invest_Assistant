"""
测试历史数据管理器
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

print("=" * 60)
print("测试历史数据管理器")
print("=" * 60)

from data_fetchers.historical_data_manager import HistoricalDataManager

# 创建管理器
manager = HistoricalDataManager()

# 测试1: 下载历史数据
print("\n[1/3] 测试下载历史数据...")
result = manager.download_historical_data(
    symbol="BTC-USDT",
    timeframe="1H",
    days=30
)
print(f"结果: {result.get('status')}")

# 测试2: 检查并填充
print("\n[2/3] 测试检查并填充数据...")
result = manager.check_and_fill_gaps(
    symbol="BTC-USDT",
    timeframe="1H",
    target_days=60
)
print(f"结果: {result.get('status')}")

# 测试3: 获取回测数据
print("\n[3/3] 测试获取回测数据...")
df = manager.get_latest_data_for_backtest(
    symbol="BTC-USDT",
    timeframe="1H",
    days=90,
    auto_update=True
)

if not df.empty:
    print(f"\n成功加载 {len(df)} 条数据")
    print(f"时间范围: {df['timestamp'].iloc[0]} 至 {df['timestamp'].iloc[-1]}")
    days = (df['timestamp'].iloc[-1] - df['timestamp'].iloc[0]).days
    print(f"实际天数: {days} 天")
    print("\n前5条数据:")
    print(df.head())
else:
    print("数据为空")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
