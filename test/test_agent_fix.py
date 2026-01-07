"""
测试Agent循环修复
验证迭代计数器是否正常工作
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

print("=" * 60)
print("测试 StrategyAgent 循环修复")
print("=" * 60)

from agents.strategy_agent import StrategyAgent

# 创建Agent
print("\n[1/2] 初始化 StrategyAgent...")
agent = StrategyAgent(use_deepseek=True)

# 运行Agent（应该在5次迭代内自动停止）
print("\n[2/2] 运行策略优化（最多5次迭代）...")
print("-" * 60)

try:
    result = agent.run(symbol="BTC-USDT", timeframe="1H")

    print("\n" + "=" * 60)
    print("✅ Agent成功完成！")
    print("=" * 60)

    # 显示结果
    print(f"\n最终策略: {result.get('current_strategy')}")
    print(f"最终参数: {result.get('current_params')}")
    print(f"总迭代次数: {result.get('iteration')}")

    # 显示优化历史
    history = result.get('optimization_history', [])
    print(f"\n优化历史 (共 {len(history)} 次):")
    for h in history:
        print(f"  迭代 {h['iteration']}: 收益率={h['metrics']['total_return_pct']:.2f}%, "
              f"夏普={h['metrics']['sharpe_ratio']:.2f}")

except Exception as e:
    print("\n" + "=" * 60)
    print(f"❌ Agent运行失败: {e}")
    print("=" * 60)
    import traceback
    traceback.print_exc()
