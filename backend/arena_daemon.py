#!/usr/bin/env python3
"""
策略竞技场后台守护进程
持续运行在 AWS 上，自动同步数据并执行交易逻辑
"""

import sys
import time
import signal
import logging
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.trading.strategy_arena import StrategyArena, ArenaConfig
from backend.trading.arena_persistence import ArenaPersistence
from backend.utils.logger import get_logger

# 配置日志
logger = get_logger('arena_daemon')

# 全局变量
arena = None
persistence = None
is_running = True


def signal_handler(signum, frame):
    """处理终止信号"""
    global is_running
    logger.info(f"收到信号 {signum}，准备优雅退出...")
    is_running = False


def initialize_arena():
    """初始化竞技场"""
    global arena, persistence

    try:
        logger.info("=" * 60)
        logger.info("🚀 策略竞技场守护进程启动")
        logger.info("=" * 60)

        # 创建竞技场配置
        config = ArenaConfig(
            symbol="BTC-USDT",
            timeframe="4H",
            check_interval=60  # 60秒检查一次
        )

        # 创建竞技场实例
        arena = StrategyArena(config)
        persistence = ArenaPersistence()

        # 尝试加载已有状态
        loaded, last_active = persistence.load_arena_state(arena)

        if loaded:
            logger.info(f"✅ 加载已有竞技场状态 (上次活跃: {last_active})")

            # 检查是否有资金分配
            status = arena.get_arena_status()
            has_capital = any(s.get('capital', 0) > 0 for s in status['strategies'].values())

            if has_capital:
                # 自动同步离线数据
                logger.info("🔄 检测并同步离线数据...")
                sync_result = persistence.sync_and_review(
                    arena,
                    auto_optimize=True
                )

                if sync_result:
                    offline_hours = sync_result.get('offline_hours', 0)
                    if offline_hours > 1:
                        logger.info(f"📊 已同步离线 {offline_hours:.1f} 小时的数据")
                        logger.info(f"   离线期间表现: {sync_result.get('summary', {})}")
            else:
                logger.warning("⚠️ 竞技场未分配资金，请在网页界面启动竞技场")
                return False
        else:
            logger.warning("⚠️ 未找到已有竞技场状态，请先在网页界面启动竞技场")
            return False

        logger.info("✅ 竞技场初始化成功")
        return True

    except Exception as e:
        logger.error(f"❌ 初始化失败: {str(e)}", exc_info=True)
        return False


def monitor_and_trade():
    """主监控循环 - 持续运行"""
    global arena, persistence, is_running

    check_count = 0
    last_optimize_time = datetime.now()

    logger.info("🔍 开始监控循环...")

    while is_running:
        try:
            check_count += 1
            current_time = datetime.now()

            logger.info(f"\n{'=' * 60}")
            logger.info(f"🔄 第 {check_count} 次检查 ({current_time.strftime('%Y-%m-%d %H:%M:%S')})")
            logger.info(f"{'=' * 60}")

            # 1. 检查并执行交易
            trades = arena.check_and_execute()

            if trades:
                logger.info(f"✅ 执行了 {len(trades)} 笔交易:")
                for trade in trades:
                    logger.info(
                        f"   {trade['strategy']} | "
                        f"{trade['action']} | "
                        f"价格: ${trade['price']:.2f} | "
                        f"数量: {trade.get('amount', 0):.6f} | "
                        f"金额: ${trade.get('value', 0):.2f}"
                    )

                # 保存状态
                persistence.save_arena_state(arena)
                logger.info("💾 已保存竞技场状态")
            else:
                logger.info("⏸️ 无新交易信号")

            # 2. 显示当前状态
            status = arena.get_arena_status()
            logger.info(f"\n📊 当前竞技场状态:")
            logger.info(f"   总资产: ${status['total_value']:.2f} USDT")
            logger.info(f"   总收益率: {status['total_return']:.2%}")

            # 显示各策略简要状态
            for strategy_name, strategy_info in status['strategies'].items():
                profit_pct = strategy_info.get('profit_pct', 0)
                position = strategy_info.get('position', 0)
                logger.info(
                    f"   {strategy_name}: "
                    f"收益 {profit_pct:+.2%} | "
                    f"持仓 {position:.6f} BTC"
                )

            # 3. 定期优化 Agent 参数（每4小时）
            hours_since_optimize = (current_time - last_optimize_time).total_seconds() / 3600
            if hours_since_optimize >= 4:
                logger.info("\n🤖 开始 Agent 参数优化...")
                sync_result = persistence.sync_and_review(
                    arena,
                    auto_optimize=True,
                    force_full_backtest=False
                )
                if sync_result:
                    logger.info(f"✅ Agent 优化完成")
                last_optimize_time = current_time

            # 4. 休眠
            sleep_seconds = arena.config.check_interval
            logger.info(f"\n💤 休眠 {sleep_seconds} 秒...")
            time.sleep(sleep_seconds)

        except KeyboardInterrupt:
            logger.info("⚠️ 收到 Ctrl+C，准备退出...")
            is_running = False
            break

        except Exception as e:
            logger.error(f"❌ 监控循环出错: {str(e)}", exc_info=True)
            logger.info("⏳ 等待60秒后重试...")
            time.sleep(60)

    logger.info("\n🛑 监控循环已停止")


def cleanup():
    """清理并保存最终状态"""
    global arena, persistence

    try:
        if arena and persistence:
            logger.info("💾 保存最终状态...")
            persistence.save_arena_state(arena)
            logger.info("✅ 状态已保存")
    except Exception as e:
        logger.error(f"❌ 清理失败: {str(e)}", exc_info=True)


def main():
    """主函数"""
    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # 初始化竞技场
        if not initialize_arena():
            logger.error("❌ 初始化失败，退出程序")
            return 1

        # 开始监控
        monitor_and_trade()

    except Exception as e:
        logger.error(f"❌ 程序异常: {str(e)}", exc_info=True)
        return 1

    finally:
        # 清理
        cleanup()
        logger.info("👋 守护进程已退出")

    return 0


if __name__ == "__main__":
    sys.exit(main())
