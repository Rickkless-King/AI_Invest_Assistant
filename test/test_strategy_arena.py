"""
测试策略竞技场
验证4种策略同时运行和对比功能
"""

import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def test_arena_initialization():
    """测试竞技场初始化"""
    print("=" * 60)
    print("测试策略竞技场初始化")
    print("=" * 60)

    from backend.trading.strategy_arena import StrategyArena, StrategyType

    arena = StrategyArena()

    print(f"\n已初始化 {len(arena.strategies)} 种策略:")
    for strategy_type, state in arena.strategies.items():
        mode = "固定参数" if not state.is_agent_controlled else "Agent优化"
        print(f"  - {state.name} ({mode})")
        print(f"    参数: {state.params}")

    print("\n✅ 初始化成功!")
    return arena


def test_capital_allocation():
    """测试资金分配"""
    print("\n" + "=" * 60)
    print("测试资金分配")
    print("=" * 60)

    from backend.trading.strategy_arena import StrategyArena

    arena = StrategyArena()

    # 模拟10000 USDT账户
    total_usdt = 10000
    allocations = arena.allocate_capital(total_usdt)

    print(f"\n总资金: ${total_usdt}")
    print(f"分配结果:")
    for strategy, amount in allocations.items():
        print(f"  - {strategy}: ${amount:.2f}")

    # 验证每个策略分配了10%
    for strategy_type, state in arena.strategies.items():
        assert state.initial_capital == 1000, f"{strategy_type} 资金分配错误"
        assert state.current_capital == 1000, f"{strategy_type} 当前资金错误"

    print("\n✅ 资金分配正确!")
    return arena


def test_signal_generation():
    """测试信号生成"""
    print("\n" + "=" * 60)
    print("测试信号生成")
    print("=" * 60)

    from backend.trading.strategy_arena import StrategyArena

    arena = StrategyArena()
    arena.allocate_capital(10000)

    # 获取信号
    print("\n获取所有策略的当前信号...")
    signals = arena.get_current_signals()

    signal_map = {1: "买入", -1: "卖出", 0: "持有"}
    for strategy_type, signal in signals.items():
        print(f"  - {strategy_type.value}: {signal_map.get(signal, '未知')} ({signal})")

    print("\n✅ 信号生成成功!")
    return signals


def test_trade_execution():
    """测试交易执行"""
    print("\n" + "=" * 60)
    print("测试交易执行（模拟）")
    print("=" * 60)

    from backend.trading.strategy_arena import StrategyArena, StrategyType

    arena = StrategyArena()
    arena.allocate_capital(10000)

    # 模拟买入交易
    current_price = 95000  # 假设当前BTC价格

    print(f"\n当前BTC价格: ${current_price}")

    # 测试RSI策略买入
    print("\n模拟RSI策略买入...")
    trade = arena.execute_trade(StrategyType.RSI, signal=1, current_price=current_price)

    if trade:
        print(f"  交易类型: {trade['type']}")
        print(f"  价格: ${trade['price']}")
        print(f"  数量: {trade['amount']:.6f} BTC")
        print(f"  成本: ${trade['cost']:.2f}")
    else:
        print("  无交易（可能信号条件不满足）")

    # 检查持仓
    rsi_state = arena.strategies[StrategyType.RSI]
    print(f"\nRSI策略状态:")
    print(f"  持仓: {rsi_state.position:.6f} BTC")
    print(f"  现金: ${rsi_state.current_capital:.2f}")
    print(f"  入场价: ${rsi_state.entry_price:.2f}")

    # 模拟卖出
    new_price = 96000  # 价格上涨
    print(f"\n价格上涨至 ${new_price}，模拟卖出...")
    trade = arena.execute_trade(StrategyType.RSI, signal=-1, current_price=new_price)

    if trade:
        print(f"  交易类型: {trade['type']}")
        print(f"  价格: ${trade['price']}")
        print(f"  收益: ${trade.get('profit', 0):.2f} ({trade.get('profit_pct', 0):.2f}%)")

    print("\n✅ 交易执行测试完成!")


def test_arena_status():
    """测试竞技场状态"""
    print("\n" + "=" * 60)
    print("测试竞技场状态获取")
    print("=" * 60)

    from backend.trading.strategy_arena import StrategyArena

    arena = StrategyArena()
    arena.allocate_capital(10000)

    status = arena.get_arena_status()

    print(f"\n交易对: {status['symbol']}")
    print(f"时间周期: {status['timeframe']}")
    print(f"当前价格: ${status['current_price']:,.2f}")
    print(f"运行状态: {'运行中' if status['is_running'] else '未运行'}")

    print(f"\n策略状态:")
    for name, s in status['strategies'].items():
        mode = "固定参数" if not s['is_agent_controlled'] else "Agent优化"
        print(f"  {name} ({mode}):")
        print(f"    初始资金: ${s['initial_capital']:.2f}")
        print(f"    当前价值: ${s['current_value']:.2f}")
        print(f"    收益率: {s['return_pct']:.2f}%")
        print(f"    交易次数: {s['trade_count']}")

    print("\n✅ 状态获取成功!")


def test_performance_comparison():
    """测试表现对比"""
    print("\n" + "=" * 60)
    print("测试策略表现对比")
    print("=" * 60)

    from backend.trading.strategy_arena import StrategyArena

    arena = StrategyArena()
    arena.allocate_capital(10000)

    comparison_df = arena.get_performance_comparison()

    print("\n策略表现对比表:")
    print(comparison_df.to_string())

    print("\n✅ 对比功能正常!")


def test_state_persistence():
    """测试状态持久化"""
    print("\n" + "=" * 60)
    print("测试状态持久化")
    print("=" * 60)

    from backend.trading.strategy_arena import StrategyArena
    import tempfile
    import os

    arena = StrategyArena()
    arena.allocate_capital(10000)

    # 保存状态
    temp_file = os.path.join(tempfile.gettempdir(), "test_arena_state.json")
    arena.save_state(temp_file)
    print(f"状态已保存到: {temp_file}")

    # 创建新实例并加载
    arena2 = StrategyArena()
    loaded = arena2.load_state(temp_file)

    if loaded:
        print("状态加载成功!")

        # 验证
        for strategy_type in arena.strategies:
            orig = arena.strategies[strategy_type]
            loaded_state = arena2.strategies[strategy_type]
            assert orig.initial_capital == loaded_state.initial_capital
            print(f"  {strategy_type.value}: 资金=${loaded_state.initial_capital}")
    else:
        print("状态加载失败")

    # 清理
    os.remove(temp_file)
    print("\n✅ 持久化测试完成!")


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("策略竞技场功能测试")
    print("=" * 60)

    try:
        test_arena_initialization()
        test_capital_allocation()
        test_signal_generation()
        test_trade_execution()
        test_arena_status()
        test_performance_comparison()
        test_state_persistence()

        print("\n" + "=" * 60)
        print("🎉 所有测试通过!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
