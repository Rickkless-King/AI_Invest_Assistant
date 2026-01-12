"""
策略竞技场持久化服务
支持离线后重新打开时自动同步数据并回顾策略表现

功能：
1. 保存/加载竞技场完整状态
2. 检测离线时间并自动同步缺失数据
3. 回顾离线期间的策略表现（模拟交易）
4. Agent根据表现自动优化参数（仅前3种策略）
"""

import os
import sys
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_fetchers.historical_data_manager import HistoricalDataManager
from data_fetchers.okx_fetcher import OKXFetcher
from strategies.rsi_strategy import RSIStrategy
from strategies.macd_strategy import MACDStrategy
from strategies.bb_strategy import BollingerBandsStrategy
from strategies.volatility_harvest_strategy import VolatilityHarvestStrategy
from utils.logger import get_logger

logger = get_logger(__name__)

# 数据库路径
ARENA_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data", "arena_state.db"
)


class ArenaPersistence:
    """竞技场持久化服务"""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or ARENA_DB_PATH
        self.data_manager = HistoricalDataManager()
        self.okx = OKXFetcher()

        # 确保目录存在
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        # 初始化数据库
        self._init_database()

    def _init_database(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 竞技场状态表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS arena_state (
                id INTEGER PRIMARY KEY,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                last_active_time TEXT NOT NULL,
                is_running INTEGER DEFAULT 0,
                config_json TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)

        # 策略状态表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS strategy_state (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                arena_id INTEGER,
                strategy_type TEXT NOT NULL,
                name TEXT NOT NULL,
                initial_capital REAL DEFAULT 0,
                current_capital REAL DEFAULT 0,
                position REAL DEFAULT 0,
                entry_price REAL DEFAULT 0,
                params_json TEXT,
                is_agent_controlled INTEGER DEFAULT 1,
                total_return_pct REAL DEFAULT 0,
                win_count INTEGER DEFAULT 0,
                loss_count INTEGER DEFAULT 0,
                updated_at TEXT,
                FOREIGN KEY (arena_id) REFERENCES arena_state(id)
            )
        """)

        # 交易记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS arena_trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                arena_id INTEGER,
                strategy_type TEXT NOT NULL,
                trade_type TEXT NOT NULL,
                price REAL NOT NULL,
                amount REAL NOT NULL,
                value REAL,
                profit REAL,
                profit_pct REAL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (arena_id) REFERENCES arena_state(id)
            )
        """)

        # 参数优化历史表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS param_optimization_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                arena_id INTEGER,
                strategy_type TEXT NOT NULL,
                old_params_json TEXT,
                new_params_json TEXT,
                reason TEXT,
                performance_before REAL,
                performance_after REAL,
                optimized_at TEXT,
                FOREIGN KEY (arena_id) REFERENCES arena_state(id)
            )
        """)

        conn.commit()
        conn.close()
        logger.info(f"竞技场数据库初始化完成: {self.db_path}")

    def save_arena_state(self, arena) -> bool:
        """
        保存竞技场完整状态

        Args:
            arena: StrategyArena实例
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            now = datetime.now().isoformat()

            # 检查是否已有记录
            cursor.execute("SELECT id FROM arena_state WHERE id = 1")
            exists = cursor.fetchone()

            config_json = json.dumps({
                "symbol": arena.config.symbol,
                "timeframe": arena.config.timeframe,
                "commission": arena.config.commission,
            })

            if exists:
                cursor.execute("""
                    UPDATE arena_state SET
                        symbol = ?, timeframe = ?, last_active_time = ?,
                        is_running = ?, config_json = ?, updated_at = ?
                    WHERE id = 1
                """, (
                    arena.config.symbol, arena.config.timeframe, now,
                    1 if arena.is_running else 0, config_json, now
                ))
            else:
                cursor.execute("""
                    INSERT INTO arena_state (id, symbol, timeframe, last_active_time,
                        is_running, config_json, created_at, updated_at)
                    VALUES (1, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    arena.config.symbol, arena.config.timeframe, now,
                    1 if arena.is_running else 0, config_json, now, now
                ))

            # 保存各策略状态
            for strategy_type, state in arena.strategies.items():
                cursor.execute("SELECT id FROM strategy_state WHERE arena_id = 1 AND strategy_type = ?",
                              (strategy_type.value,))
                strategy_exists = cursor.fetchone()

                params_json = json.dumps(state.params)

                if strategy_exists:
                    cursor.execute("""
                        UPDATE strategy_state SET
                            name = ?, initial_capital = ?, current_capital = ?,
                            position = ?, entry_price = ?, params_json = ?,
                            is_agent_controlled = ?, total_return_pct = ?,
                            win_count = ?, loss_count = ?, updated_at = ?
                        WHERE arena_id = 1 AND strategy_type = ?
                    """, (
                        state.name, state.initial_capital, state.current_capital,
                        state.position, state.entry_price, params_json,
                        1 if state.is_agent_controlled else 0, state.total_return_pct,
                        state.win_count, state.loss_count, now, strategy_type.value
                    ))
                else:
                    cursor.execute("""
                        INSERT INTO strategy_state (arena_id, strategy_type, name,
                            initial_capital, current_capital, position, entry_price,
                            params_json, is_agent_controlled, total_return_pct,
                            win_count, loss_count, updated_at)
                        VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        strategy_type.value, state.name,
                        state.initial_capital, state.current_capital,
                        state.position, state.entry_price, params_json,
                        1 if state.is_agent_controlled else 0, state.total_return_pct,
                        state.win_count, state.loss_count, now
                    ))

                # 保存新交易记录
                for trade in state.trades:
                    # 检查是否已存在
                    cursor.execute("""
                        SELECT id FROM arena_trades
                        WHERE arena_id = 1 AND strategy_type = ? AND timestamp = ?
                    """, (strategy_type.value, trade.get('timestamp')))

                    if not cursor.fetchone():
                        cursor.execute("""
                            INSERT INTO arena_trades (arena_id, strategy_type, trade_type,
                                price, amount, value, profit, profit_pct, timestamp)
                            VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            strategy_type.value, trade.get('type'),
                            trade.get('price'), trade.get('amount'),
                            trade.get('value', trade.get('cost')),
                            trade.get('profit'), trade.get('profit_pct'),
                            trade.get('timestamp')
                        ))

            conn.commit()
            conn.close()
            logger.info("竞技场状态已保存")
            return True

        except Exception as e:
            logger.error(f"保存竞技场状态失败: {str(e)}")
            return False

    def load_arena_state(self, arena) -> Tuple[bool, Optional[datetime]]:
        """
        加载竞技场状态

        Args:
            arena: StrategyArena实例

        Returns:
            (是否成功, 上次活跃时间)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 加载竞技场基本状态
            cursor.execute("SELECT * FROM arena_state WHERE id = 1")
            arena_row = cursor.fetchone()

            if not arena_row:
                conn.close()
                return False, None

            last_active_time = datetime.fromisoformat(arena_row[3])

            # 加载各策略状态
            from backend.trading.strategy_arena import StrategyType

            cursor.execute("SELECT * FROM strategy_state WHERE arena_id = 1")
            strategy_rows = cursor.fetchall()

            for row in strategy_rows:
                strategy_type = StrategyType(row[2])
                if strategy_type in arena.strategies:
                    state = arena.strategies[strategy_type]
                    state.initial_capital = row[4]
                    state.current_capital = row[5]
                    state.position = row[6]
                    state.entry_price = row[7]
                    state.params = json.loads(row[8]) if row[8] else {}
                    state.total_return_pct = row[10]
                    state.win_count = row[11]
                    state.loss_count = row[12]

                    # 加载交易记录
                    cursor.execute("""
                        SELECT * FROM arena_trades
                        WHERE arena_id = 1 AND strategy_type = ?
                        ORDER BY timestamp
                    """, (strategy_type.value,))

                    state.trades = []
                    for trade_row in cursor.fetchall():
                        state.trades.append({
                            'strategy': trade_row[2],
                            'type': trade_row[3],
                            'price': trade_row[4],
                            'amount': trade_row[5],
                            'value': trade_row[6],
                            'profit': trade_row[7],
                            'profit_pct': trade_row[8],
                            'timestamp': trade_row[9],
                        })

            conn.close()
            logger.info(f"竞技场状态已加载，上次活跃: {last_active_time}")
            return True, last_active_time

        except Exception as e:
            logger.error(f"加载竞技场状态失败: {str(e)}")
            return False, None

    def get_offline_duration(self) -> Optional[timedelta]:
        """获取离线时长"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT last_active_time FROM arena_state WHERE id = 1")
            row = cursor.fetchone()
            conn.close()

            if row:
                last_active = datetime.fromisoformat(row[0])
                return datetime.now() - last_active

            return None
        except:
            return None

    def sync_and_review(self, arena, auto_optimize: bool = True, force_full_backtest: bool = False) -> Dict:
        """
        同步数据并回顾策略表现

        两种模式：
        1. 首次运行：从 start_date (2026-01-01) 开始回测所有历史数据
        2. 离线恢复：从上次活跃时间开始，同步新数据并模拟交易

        Args:
            arena: StrategyArena实例
            auto_optimize: 是否自动优化Agent控制的策略参数
            force_full_backtest: 是否强制从start_date回测并重置策略状态

        Returns:
            回顾结果
        """
        result = {
            "synced": False,
            "offline_hours": 0,
            "bars_synced": 0,
            "is_initial_backtest": False,
            "strategy_performance": {},
            "optimizations": [],
        }

        # 获取离线时长和上次活跃时间
        offline_duration = self.get_offline_duration()
        _, last_active = self.load_arena_state(arena)

        if force_full_backtest:
            last_active = None
            offline_duration = None
            # 强制全量回测时重置策略状态，避免历史交易叠加
            for state in arena.strategies.values():
                state.trades = []
                state.position = 0
                state.entry_price = 0
                state.current_capital = state.initial_capital
                state.total_return_pct = 0
                state.win_count = 0
                state.loss_count = 0
                state.last_signal = 0

        # 确定起始时间点
        start_date = datetime.strptime(arena.config.start_date, "%Y-%m-%d %H:%M:%S")

        # 判断是否为首次运行（没有任何历史状态，或者策略没有资金）
        is_first_run = force_full_backtest or (not last_active) or all(
            s.initial_capital == 0 for s in arena.strategies.values()
        )

        if is_first_run:
            logger.info(f"首次运行，将从 {arena.config.start_date} 开始回测所有策略")
            result["is_initial_backtest"] = True
            backtest_start = start_date
        else:
            result["offline_hours"] = offline_duration.total_seconds() / 3600 if offline_duration else 0
            logger.info(f"离线时长: {result['offline_hours']:.1f} 小时")

            # 如果离线时间小于1小时，不需要回顾
            if result["offline_hours"] < 1:
                logger.info("离线时间较短，跳过回顾")
                return result

            backtest_start = last_active

        # 计算需要获取的天数
        days_from_start = (datetime.now() - start_date).days + 2
        days_needed = max(days_from_start, 30)

        # 获取K线数据
        df = self.data_manager.get_latest_data_for_backtest(
            symbol=arena.config.symbol,
            timeframe=arena.config.timeframe,
            days=days_needed,
            auto_update=True
        )

        if df.empty:
            logger.warning("无法获取K线数据")
            return result

        result["bars_synced"] = len(df)
        result["synced"] = True

        # 筛选需要回测的数据
        df_backtest = df[df['timestamp'] >= backtest_start].copy()

        if df_backtest.empty:
            logger.info("无需要回测的新数据")
            return result

        if is_first_run:
            logger.info(f"首次回测: 从 {start_date} 到现在，共 {len(df_backtest)} 根K线")
        else:
            logger.info(f"离线期间有 {len(df_backtest)} 根新K线")

        # 为每个策略计算表现并模拟交易
        from backend.trading.strategy_arena import StrategyType

        # 获取当前价格
        ticker = self.okx.get_ticker(arena.config.symbol)
        current_price = float(ticker.get('last', 0)) if ticker else 0

        for strategy_type, state in arena.strategies.items():
            strategy = arena.get_strategy_instance(strategy_type)

            # 使用完整数据生成信号（需要历史数据计算指标）
            df_with_signals = strategy.generate_signals(df.copy())

            # 筛选回测期间的信号
            df_signals = df_with_signals[df_with_signals['timestamp'] >= backtest_start]

            # 统计信号数量
            buy_signals = (df_signals['signal'] == 1).sum()
            sell_signals = (df_signals['signal'] == -1).sum()

            # 模拟交易执行
            trades_executed = 0
            commission = arena.config.commission

            for idx, row in df_signals.iterrows():
                signal = row['signal']
                price = row['close']

                # 买入信号且无持仓
                if signal == 1 and state.position == 0 and state.current_capital > 0:
                    amount = (state.current_capital * (1 - commission)) / price
                    state.position = amount
                    state.entry_price = price
                    state.current_capital = 0
                    trades_executed += 1

                    # 记录交易
                    trade = {
                        "strategy": strategy_type.value,
                        "type": "BUY",
                        "price": price,
                        "amount": amount,
                        "cost": amount * price,
                        "timestamp": row['timestamp'].isoformat() if hasattr(row['timestamp'], 'isoformat') else str(row['timestamp']),
                    }
                    state.trades.append(trade)
                    if not is_first_run:  # 首次回测时不逐条打印，太多了
                        logger.info(f"[{strategy_type.value}] 买入 {amount:.6f} @ {price:.2f}")

                # 卖出信号且有持仓
                elif signal == -1 and state.position > 0:
                    sell_value = state.position * price * (1 - commission)
                    profit = sell_value - (state.position * state.entry_price)
                    profit_pct = (profit / (state.position * state.entry_price)) * 100

                    trade = {
                        "strategy": strategy_type.value,
                        "type": "SELL",
                        "price": price,
                        "amount": state.position,
                        "value": sell_value,
                        "profit": profit,
                        "profit_pct": profit_pct,
                        "timestamp": row['timestamp'].isoformat() if hasattr(row['timestamp'], 'isoformat') else str(row['timestamp']),
                    }

                    if profit > 0:
                        state.win_count += 1
                    else:
                        state.loss_count += 1

                    state.current_capital = sell_value
                    state.position = 0
                    state.entry_price = 0
                    trades_executed += 1

                    state.trades.append(trade)
                    if not is_first_run:
                        logger.info(f"[{strategy_type.value}] 卖出 @ {price:.2f}, 收益: {profit:.2f} ({profit_pct:.2f}%)")

            # 计算当前总收益率
            if state.initial_capital > 0:
                if state.position > 0 and current_price > 0:
                    current_value = state.position * current_price
                else:
                    current_value = state.current_capital
                simulated_return = ((current_value - state.initial_capital) / state.initial_capital) * 100
                state.total_return_pct = simulated_return
            else:
                simulated_return = 0

            result["strategy_performance"][strategy_type.value] = {
                "name": state.name,
                "buy_signals": int(buy_signals),
                "sell_signals": int(sell_signals),
                "trades_executed": trades_executed,
                "simulated_return_pct": simulated_return,
                "is_agent_controlled": state.is_agent_controlled,
            }

            logger.info(f"[{strategy_type.value}] 买入信号:{buy_signals}, 卖出信号:{sell_signals}, "
                       f"执行交易:{trades_executed}, 总收益:{simulated_return:.2f}%")

        # Agent自动优化参数（仅对Agent控制的策略）
        if auto_optimize:
            optimizations = self._auto_optimize_params(arena, result["strategy_performance"])
            result["optimizations"] = optimizations

        # 保存同步后的状态（包括离线期间执行的模拟交易）
        self.save_arena_state(arena)
        logger.info("离线期间模拟交易已同步并保存")

        return result

    def _auto_optimize_params(self, arena, performance: Dict) -> List[Dict]:
        """
        Agent自动优化参数

        只对is_agent_controlled=True的策略进行优化
        波动收割策略保持固定参数不变
        """
        optimizations = []
        from backend.trading.strategy_arena import StrategyType

        for strategy_type, perf in performance.items():
            if not perf["is_agent_controlled"]:
                # 固定参数策略，跳过
                logger.info(f"[{strategy_type}] 固定参数策略，跳过优化")
                continue

            state = arena.strategies[StrategyType(strategy_type)]
            old_params = state.params.copy()

            # 根据表现调整参数
            simulated_return = perf["simulated_return_pct"]

            # 如果表现不好（收益 < -2%），尝试调整参数
            if simulated_return < -2:
                new_params = self._suggest_param_adjustment(strategy_type, old_params, "poor")
                reason = f"表现不佳(收益{simulated_return:.2f}%)，调整参数"
            elif simulated_return > 5:
                # 表现很好，小幅微调
                new_params = self._suggest_param_adjustment(strategy_type, old_params, "good")
                reason = f"表现良好(收益{simulated_return:.2f}%)，微调参数"
            else:
                # 表现一般，保持不变
                new_params = old_params
                reason = None

            if reason and new_params != old_params:
                # 应用新参数
                state.params = new_params
                optimizations.append({
                    "strategy": strategy_type,
                    "old_params": old_params,
                    "new_params": new_params,
                    "reason": reason,
                    "timestamp": datetime.now().isoformat(),
                })

                # 保存优化历史
                self._save_optimization_history(strategy_type, old_params, new_params,
                                               reason, simulated_return)

                logger.info(f"[{strategy_type}] 参数已优化: {old_params} -> {new_params}")

        return optimizations

    def _suggest_param_adjustment(self, strategy_type: str, params: Dict, performance: str) -> Dict:
        """根据策略类型和表现建议参数调整"""
        new_params = params.copy()
        import random

        if strategy_type == "RSI":
            if performance == "poor":
                # 表现差，放宽阈值
                new_params["oversold_threshold"] = max(20, params.get("oversold_threshold", 30) - 5)
                new_params["overbought_threshold"] = min(80, params.get("overbought_threshold", 70) + 5)
            else:
                # 微调
                new_params["rsi_period"] = params.get("rsi_period", 14) + random.randint(-2, 2)
                new_params["rsi_period"] = max(7, min(21, new_params["rsi_period"]))

        elif strategy_type == "MACD":
            if performance == "poor":
                # 调整周期
                new_params["fast_period"] = max(8, params.get("fast_period", 12) - 2)
                new_params["slow_period"] = min(30, params.get("slow_period", 26) + 2)
            else:
                new_params["signal_period"] = params.get("signal_period", 9) + random.randint(-1, 1)
                new_params["signal_period"] = max(5, min(12, new_params["signal_period"]))

        elif strategy_type == "BollingerBands":
            if performance == "poor":
                # 调整标准差
                new_params["bb_std"] = min(2.5, params.get("bb_std", 2.0) + 0.2)
            else:
                new_params["bb_period"] = params.get("bb_period", 20) + random.randint(-2, 2)
                new_params["bb_period"] = max(15, min(25, new_params["bb_period"]))

        return new_params

    def _save_optimization_history(self, strategy_type: str, old_params: Dict,
                                   new_params: Dict, reason: str, performance: float):
        """保存参数优化历史"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO param_optimization_history
                (arena_id, strategy_type, old_params_json, new_params_json,
                 reason, performance_before, optimized_at)
                VALUES (1, ?, ?, ?, ?, ?, ?)
            """, (
                strategy_type, json.dumps(old_params), json.dumps(new_params),
                reason, performance, datetime.now().isoformat()
            ))

            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"保存优化历史失败: {str(e)}")

    def get_optimization_history(self, limit: int = 20) -> pd.DataFrame:
        """获取参数优化历史"""
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query(f"""
                SELECT strategy_type, old_params_json, new_params_json,
                       reason, performance_before, optimized_at
                FROM param_optimization_history
                ORDER BY optimized_at DESC
                LIMIT {limit}
            """, conn)
            conn.close()
            return df
        except:
            return pd.DataFrame()

    def clear_arena_state(self) -> bool:
        """
        清除所有竞技场状态（重置时使用）

        Returns:
            是否成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 清除所有表的数据
            cursor.execute("DELETE FROM arena_trades")
            cursor.execute("DELETE FROM strategy_state")
            cursor.execute("DELETE FROM arena_state")
            # 保留参数优化历史作为参考
            # cursor.execute("DELETE FROM param_optimization_history")

            conn.commit()
            conn.close()
            logger.info("竞技场状态已清除")
            return True
        except Exception as e:
            logger.error(f"清除竞技场状态失败: {str(e)}")
            return False


# 全局持久化服务实例
_persistence_instance: Optional[ArenaPersistence] = None


def get_persistence() -> ArenaPersistence:
    """获取全局持久化服务实例"""
    global _persistence_instance
    if _persistence_instance is None:
        _persistence_instance = ArenaPersistence()
    return _persistence_instance
