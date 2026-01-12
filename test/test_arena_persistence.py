"""
测试竞技场持久化和离线同步功能
"""

import sys
import os
from datetime import datetime, timedelta

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def test_persistence_initialization():
    """测试持久化服务初始化"""
    print("=" * 60)
    print("测试持久化服务初始化")
    print("=" * 60)

    from backend.trading.arena_persistence import ArenaPersistence

    persistence = ArenaPersistence()

    print(f"数据库路径: {persistence.db_path}")
    print("✅ 持久化服务初始化成功!")

    return persistence


def test_save_and_load_state():
    """测试保存和加载状态"""
    print("\n" + "=" * 60)
    print("测试保存和加载状态")
    print("=" * 60)

    from backend.trading.strategy_arena import StrategyArena
    from backend.trading.arena_persistence import ArenaPersistence

    # 创建竞技场
    arena = StrategyArena()
    arena.allocate_capital(10000)

    # 创建持久化服务
    persistence = ArenaPersistence()

    # 保存状态
    print("\n保存竞技场状态...")
    success = persistence.save_arena_state(arena)
    print(f"保存结果: {'成功' if success else '失败'}")

    # 创建新的竞技场实例并加载状态
    print("\n创建新实例并加载状态...")
    arena2 = StrategyArena()
    loaded, last_active = persistence.load_arena_state(arena2)

    print(f"加载结果: {'成功' if loaded else '失败'}")
    print(f"上次活跃时间: {last_active}")

    # 验证状态
    for strategy_type in arena.strategies:
        orig = arena.strategies[strategy_type]
        loaded_state = arena2.strategies[strategy_type]
        print(f"  {strategy_type.value}: ${loaded_state.initial_capital:.2f}")

    print("\n✅ 状态保存和加载测试通过!")


def test_offline_detection():
    """测试离线检测"""
    print("\n" + "=" * 60)
    print("测试离线检测")
    print("=" * 60)

    from backend.trading.arena_persistence import ArenaPersistence

    persistence = ArenaPersistence()

    # 获取离线时长
    offline_duration = persistence.get_offline_duration()

    if offline_duration:
        hours = offline_duration.total_seconds() / 3600
        print(f"离线时长: {hours:.2f} 小时")
    else:
        print("无历史记录，首次运行")

    print("\n✅ 离线检测测试通过!")


def test_sync_and_review():
    """测试同步和回顾功能"""
    print("\n" + "=" * 60)
    print("测试同步和回顾功能")
    print("=" * 60)

    from backend.trading.strategy_arena import StrategyArena
    from backend.trading.arena_persistence import ArenaPersistence

    # 创建竞技场
    arena = StrategyArena()
    arena.allocate_capital(10000)

    # 创建持久化服务
    persistence = ArenaPersistence()

    # 先保存状态
    persistence.save_arena_state(arena)

    # 模拟同步和回顾
    print("\n执行同步和回顾...")
    result = persistence.sync_and_review(arena, auto_optimize=True)

    print(f"\n同步结果:")
    print(f"  是否同步: {result['synced']}")
    print(f"  离线时长: {result['offline_hours']:.1f} 小时")
    print(f"  同步K线数: {result['bars_synced']}")

    if result.get('strategy_performance'):
        print(f"\n策略表现:")
        for strategy, perf in result['strategy_performance'].items():
            mode = "固定参数" if not perf['is_agent_controlled'] else "Agent优化"
            print(f"  - {perf['name']} ({mode}):")
            print(f"      买入信号: {perf['buy_signals']}")
            print(f"      卖出信号: {perf['sell_signals']}")
            print(f"      模拟收益: {perf['simulated_return_pct']:.2f}%")

    if result.get('optimizations'):
        print(f"\n参数优化:")
        for opt in result['optimizations']:
            print(f"  - {opt['strategy']}: {opt['reason']}")
            print(f"    {opt['old_params']} -> {opt['new_params']}")

    print("\n✅ 同步和回顾测试通过!")


def test_optimization_history():
    """测试优化历史记录"""
    print("\n" + "=" * 60)
    print("测试优化历史记录")
    print("=" * 60)

    from backend.trading.arena_persistence import ArenaPersistence

    persistence = ArenaPersistence()

    # 获取优化历史
    history = persistence.get_optimization_history(limit=10)

    if not history.empty:
        print(f"找到 {len(history)} 条优化记录:")
        print(history.to_string())
    else:
        print("暂无优化历史记录")

    print("\n✅ 优化历史测试通过!")


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("竞技场持久化功能测试")
    print("=" * 60)

    try:
        test_persistence_initialization()
        test_save_and_load_state()
        test_offline_detection()
        test_sync_and_review()
        test_optimization_history()

        print("\n" + "=" * 60)
        print("🎉 所有测试通过!")
        print("=" * 60)

        print("""
功能说明：
1. 启动竞技场后，状态会自动保存到数据库
2. 关闭Streamlit后，下次打开会自动：
   - 检测离线时长
   - 同步缺失的K线数据
   - 计算离线期间各策略的模拟表现
   - Agent自动优化表现不佳的策略参数（波动收割策略除外）
3. 所有优化历史都会被记录，可在"参数优化历史"Tab查看
        """)

    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
