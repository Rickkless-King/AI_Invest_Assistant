"""
交易模块
包含策略竞技场、模拟盘交易引擎和持久化服务
"""

from .strategy_arena import (
    StrategyArena,
    StrategyType,
    StrategyState,
    ArenaConfig,
    get_arena,
    reset_arena,
)

from .arena_persistence import (
    ArenaPersistence,
    get_persistence,
)

__all__ = [
    "StrategyArena",
    "StrategyType",
    "StrategyState",
    "ArenaConfig",
    "get_arena",
    "reset_arena",
    "ArenaPersistence",
    "get_persistence",
]
