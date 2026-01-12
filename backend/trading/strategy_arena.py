"""
策略竞技场（Strategy Arena）
管理多个策略在模拟盘上的实时交易对比

功能：
1. 将账户资金分为10份，5种策略各分配1份（共50%）
2. 前三种策略（RSI/MACD/BB）由Agent控制参数
3. 第四种策略（波动收割）使用固定参数
4. 第五种策略（趋势突破）使用固定参数
5. 实时监控各策略表现并记录交易
"""

import os
import sys
import json
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import pandas as pd
import numpy as np

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_fetchers.okx_fetcher import OKXFetcher
from data_fetchers.historical_data_manager import HistoricalDataManager
from strategies.rsi_strategy import RSIStrategy
from strategies.macd_strategy import MACDStrategy
from strategies.bb_strategy import BollingerBandsStrategy
from strategies.volatility_harvest_strategy import VolatilityHarvestStrategy
from strategies.trend_breakout_strategy import TrendBreakoutStrategy
from database.db_manager import DatabaseManager
from utils.logger import get_logger

logger = get_logger(__name__)


class StrategyType(Enum):
    """策略类型"""
    RSI = "RSI"
    MACD = "MACD"
    BOLLINGER = "BollingerBands"
    VOLATILITY_HARVEST = "VolatilityHarvest"
    TREND_BREAKOUT = "TrendBreakout"


@dataclass
class StrategyState:
    """单个策略的状态"""
    strategy_type: StrategyType
    name: str
    initial_capital: float  # 初始资金（USDT）
    current_capital: float  # 当前资金
    position: float = 0.0  # 当前持仓（BTC数量）
    entry_price: float = 0.0  # 入场价格
    params: Dict = field(default_factory=dict)
    is_agent_controlled: bool = True  # 是否由Agent控制
    trades: List[Dict] = field(default_factory=list)  # 交易记录
    last_signal: int = 0  # 最后信号（1=买入, -1=卖出, 0=持有）
    total_return_pct: float = 0.0  # 总收益率
    win_count: int = 0  # 盈利次数
    loss_count: int = 0  # 亏损次数
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> Dict:
        """转换为字典"""
        d = asdict(self)
        d['strategy_type'] = self.strategy_type.value
        return d


@dataclass
class ArenaConfig:
    """竞技场配置"""
    symbol: str = "BTC-USDT"
    timeframe: str = "4H"
    total_capital_ratio: float = 0.5  # 使用总资金的50%（5种策略各10%）
    per_strategy_ratio: float = 0.1  # 每种策略占总资金的10%
    commission: float = 0.001  # 手续费率0.1%
    check_interval: int = 60  # 信号检查间隔（秒）
    auto_optimize_interval: int = 3600 * 4  # Agent优化间隔（秒）= 4小时
    # 策略竞技场统一起始日期：2026年1月1日0点
    start_date: str = "2026-01-01 00:00:00"


class StrategyArena:
    """策略竞技场"""

    def __init__(self, config: ArenaConfig = None):
        self.config = config or ArenaConfig()
        self.okx = OKXFetcher()
        self.data_manager = HistoricalDataManager()
        self.db = DatabaseManager()

        # 策略状态
        self.strategies: Dict[StrategyType, StrategyState] = {}

        # 运行状态
        self.is_running = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.last_bar_time: Optional[datetime] = None

        # 初始化策略
        self._init_strategies()

        logger.info("策略竞技场初始化完成")

    def _init_strategies(self):
        """初始化5种策略"""
        now = datetime.now().isoformat()

        # 策略配置
        strategy_configs = {
            StrategyType.RSI: {
                "name": "RSI超买超卖策略",
                "params": {"rsi_period": 14, "oversold_threshold": 30, "overbought_threshold": 70},
                "is_agent_controlled": True,
            },
            StrategyType.MACD: {
                "name": "MACD金叉死叉策略",
                "params": {"fast_period": 12, "slow_period": 26, "signal_period": 9},
                "is_agent_controlled": True,
            },
            StrategyType.BOLLINGER: {
                "name": "布林带均值回归策略",
                "params": {"bb_period": 20, "bb_std": 2.0},
                "is_agent_controlled": True,
            },
            StrategyType.VOLATILITY_HARVEST: {
                "name": "波动收割策略（固定参数）",
                "params": {
                    "atr_period": 20,
                    "atr_trail_period": 185,
                    "atr_multiplier": 4.5,
                    "entry_atr_threshold": 0.0,
                    "stop_loss_pct": 3.0,
                    "profit_target_pct": 1.3,
                    "trend_ema_period": 50,
                    "use_trend_filter": True,
                    "breakout_bars": 1,
                },
                "is_agent_controlled": False,  # 固定参数，不需要Agent
            },
            StrategyType.TREND_BREAKOUT: {
                "name": "趋势突破策略（固定参数）",
                "params": {
                    "linreg_period": 102,
                    "price_entry_mult": 0.5,
                    "biggest_range_period": 157,
                    "bars_valid": 6,
                    "stop_loss_pct": 1.8,
                    "profit_target_pct": 1.6,
                    "use_trend_filter": True,
                    "trend_lookback": 2,
                    "daily_lookback": 3,
                },
                "is_agent_controlled": False,  # 固定参数，不需要Agent
            },
        }

        for strategy_type, config in strategy_configs.items():
            self.strategies[strategy_type] = StrategyState(
                strategy_type=strategy_type,
                name=config["name"],
                initial_capital=0,  # 稍后设置
                current_capital=0,
                params=config["params"],
                is_agent_controlled=config["is_agent_controlled"],
                created_at=now,
                updated_at=now,
            )

    def allocate_capital(self, total_usdt: float, force: bool = False) -> Dict[str, float]:
        """
        分配资金到各策略

        Args:
            total_usdt: 账户总USDT余额
            force: 是否强制重新分配（会覆盖现有持仓和资金）

        Returns:
            各策略分配的资金
        """
        per_strategy = total_usdt * self.config.per_strategy_ratio

        allocations = {}
        already_allocated = 0
        newly_allocated = 0

        for strategy_type, state in self.strategies.items():
            # 如果已经有资金分配且不是强制重分配，保持现有状态
            if state.initial_capital > 0 and not force:
                allocations[strategy_type.value] = state.initial_capital
                already_allocated += 1
                continue

            state.initial_capital = per_strategy
            state.current_capital = per_strategy
            state.position = 0
            state.entry_price = 0
            allocations[strategy_type.value] = per_strategy
            newly_allocated += 1

        if newly_allocated > 0:
            logger.info(f"资金分配完成: 新分配{newly_allocated}个策略，每策略 {per_strategy:.2f} USDT")
        if already_allocated > 0:
            logger.info(f"已有{already_allocated}个策略保持原有资金状态（如需重分配请使用重置功能）")

        return allocations

    def get_strategy_instance(self, strategy_type: StrategyType):
        """获取策略实例"""
        state = self.strategies[strategy_type]
        params = state.params

        if strategy_type == StrategyType.RSI:
            return RSIStrategy(params=params)
        elif strategy_type == StrategyType.MACD:
            return MACDStrategy(params=params)
        elif strategy_type == StrategyType.BOLLINGER:
            return BollingerBandsStrategy(params=params)
        elif strategy_type == StrategyType.VOLATILITY_HARVEST:
            return VolatilityHarvestStrategy(params=params)
        elif strategy_type == StrategyType.TREND_BREAKOUT:
            return TrendBreakoutStrategy(params=params)

    def get_current_signals(self) -> Dict[StrategyType, int]:
        """
        获取所有策略的当前信号

        Returns:
            {策略类型: 信号值}，信号值：1=买入, -1=卖出, 0=持有
        """
        # 获取最新K线数据
        df = self.data_manager.get_latest_data_for_backtest(
            symbol=self.config.symbol,
            timeframe=self.config.timeframe,
            days=30,  # 获取30天数据用于计算指标
            auto_update=True
        )

        if df.empty:
            logger.warning("无法获取K线数据")
            return {}

        signals = {}
        current_bar_time = df['timestamp'].iloc[-1]

        for strategy_type in self.strategies:
            strategy = self.get_strategy_instance(strategy_type)
            df_signals = strategy.generate_signals(df.copy())

            # 获取最新信号
            latest_signal = int(df_signals['signal'].iloc[-1])
            signals[strategy_type] = latest_signal

            # 更新状态
            self.strategies[strategy_type].last_signal = latest_signal
            self.strategies[strategy_type].updated_at = datetime.now().isoformat()

        self.last_bar_time = current_bar_time
        return signals

    def execute_trade(self, strategy_type: StrategyType, signal: int, current_price: float) -> Optional[Dict]:
        """
        执行交易

        Args:
            strategy_type: 策略类型
            signal: 交易信号
            current_price: 当前价格

        Returns:
            交易记录
        """
        state = self.strategies[strategy_type]
        trade = None
        now = datetime.now()

        # 买入信号且无持仓
        if signal == 1 and state.position == 0 and state.current_capital > 0:
            # 计算买入数量
            amount = (state.current_capital * (1 - self.config.commission)) / current_price
            cost = state.current_capital

            state.position = amount
            state.entry_price = current_price
            state.current_capital = 0

            trade = {
                "strategy": strategy_type.value,
                "type": "BUY",
                "price": current_price,
                "amount": amount,
                "cost": cost,
                "timestamp": now.isoformat(),
            }
            state.trades.append(trade)
            logger.info(f"[{strategy_type.value}] 买入 {amount:.6f} BTC @ {current_price:.2f}")

        # 卖出信号且有持仓
        elif signal == -1 and state.position > 0:
            # 计算卖出收益
            sell_value = state.position * current_price * (1 - self.config.commission)
            profit = sell_value - (state.position * state.entry_price)
            profit_pct = (profit / (state.position * state.entry_price)) * 100

            trade = {
                "strategy": strategy_type.value,
                "type": "SELL",
                "price": current_price,
                "amount": state.position,
                "value": sell_value,
                "profit": profit,
                "profit_pct": profit_pct,
                "timestamp": now.isoformat(),
            }

            # 更新统计
            if profit > 0:
                state.win_count += 1
            else:
                state.loss_count += 1

            state.current_capital = sell_value
            state.position = 0
            state.entry_price = 0

            state.trades.append(trade)
            logger.info(f"[{strategy_type.value}] 卖出 @ {current_price:.2f}, 收益: {profit:.2f} ({profit_pct:.2f}%)")

        # 更新总收益率
        if state.position > 0:
            current_value = state.position * current_price
        else:
            current_value = state.current_capital

        state.total_return_pct = ((current_value - state.initial_capital) / state.initial_capital) * 100
        state.updated_at = now.isoformat()

        return trade

    def check_and_execute(self) -> List[Dict]:
        """
        检查信号并执行交易

        Returns:
            执行的交易列表
        """
        # 获取当前价格
        ticker = self.okx.get_ticker(self.config.symbol)
        if not ticker:
            logger.warning("无法获取当前价格")
            return []

        current_price = float(ticker.get('last', 0))
        if current_price == 0:
            return []

        # 获取所有信号
        signals = self.get_current_signals()

        # 执行交易
        trades = []
        for strategy_type, signal in signals.items():
            trade = self.execute_trade(strategy_type, signal, current_price)
            if trade:
                trades.append(trade)
                # 保存到数据库
                self.db.save_trade(
                    symbol=self.config.symbol,
                    side=trade['type'],
                    price=trade['price'],
                    quantity=trade['amount'],
                    amount=trade.get('cost', trade.get('value', 0)),
                    fee=trade['price'] * trade['amount'] * self.config.commission,
                    strategy=trade['strategy']
                )

        return trades

    def get_arena_status(self) -> Dict:
        """获取竞技场状态"""
        ticker = self.okx.get_ticker(self.config.symbol)
        current_price = float(ticker.get('last', 0)) if ticker else 0

        status = {
            "symbol": self.config.symbol,
            "timeframe": self.config.timeframe,
            "current_price": current_price,
            "is_running": self.is_running,
            "last_bar_time": self.last_bar_time.isoformat() if self.last_bar_time else None,
            "strategies": {},
        }

        for strategy_type, state in self.strategies.items():
            # 计算当前价值
            if state.position > 0:
                current_value = state.position * current_price
            else:
                current_value = state.current_capital

            # 更新收益率
            if state.initial_capital > 0:
                return_pct = ((current_value - state.initial_capital) / state.initial_capital) * 100
            else:
                return_pct = 0

            status["strategies"][strategy_type.value] = {
                "name": state.name,
                "initial_capital": state.initial_capital,
                "current_value": current_value,
                "position": state.position,
                "entry_price": state.entry_price,
                "return_pct": return_pct,
                "params": state.params,
                "is_agent_controlled": state.is_agent_controlled,
                "trade_count": len(state.trades),
                "win_count": state.win_count,
                "loss_count": state.loss_count,
                "win_rate": (state.win_count / (state.win_count + state.loss_count) * 100)
                           if (state.win_count + state.loss_count) > 0 else 0,
                "last_signal": state.last_signal,
                "updated_at": state.updated_at,
            }

        return status

    def get_performance_comparison(self) -> pd.DataFrame:
        """获取策略表现对比"""
        status = self.get_arena_status()
        data = []

        for strategy_name, strategy_status in status["strategies"].items():
            data.append({
                "策略": strategy_status["name"],
                "类型": "固定参数" if not strategy_status["is_agent_controlled"] else "Agent优化",
                "初始资金": f"${strategy_status['initial_capital']:.2f}",
                "当前价值": f"${strategy_status['current_value']:.2f}",
                "收益率": f"{strategy_status['return_pct']:.2f}%",
                "交易次数": strategy_status["trade_count"],
                "胜率": f"{strategy_status['win_rate']:.1f}%",
                "持仓": f"{strategy_status['position']:.6f}" if strategy_status['position'] > 0 else "-",
            })

        return pd.DataFrame(data)

    def start_monitoring(self):
        """开始监控（后台线程）"""
        if self.is_running:
            logger.warning("监控已在运行")
            return

        self.is_running = True

        def monitor_loop():
            while self.is_running:
                try:
                    trades = self.check_and_execute()
                    if trades:
                        logger.info(f"执行了 {len(trades)} 笔交易")
                except Exception as e:
                    logger.error(f"监控循环错误: {str(e)}")

                time.sleep(self.config.check_interval)

        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("策略监控已启动")

    def stop_monitoring(self):
        """停止监控"""
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("策略监控已停止")

    def update_strategy_params(self, strategy_type: StrategyType, new_params: Dict):
        """
        更新策略参数（仅Agent控制的策略）

        Args:
            strategy_type: 策略类型
            new_params: 新参数
        """
        state = self.strategies.get(strategy_type)
        if not state:
            return

        if not state.is_agent_controlled:
            logger.warning(f"{strategy_type.value} 是固定参数策略，不允许更新")
            return

        state.params.update(new_params)
        state.updated_at = datetime.now().isoformat()
        logger.info(f"[{strategy_type.value}] 参数已更新: {new_params}")

    def save_state(self, filepath: str = "arena_state.json"):
        """保存竞技场状态到文件"""
        state_data = {
            "config": asdict(self.config),
            "strategies": {k.value: v.to_dict() for k, v in self.strategies.items()},
            "saved_at": datetime.now().isoformat(),
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(state_data, f, ensure_ascii=False, indent=2)

        logger.info(f"状态已保存到 {filepath}")

    def load_state(self, filepath: str = "arena_state.json") -> bool:
        """从文件加载竞技场状态"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                state_data = json.load(f)

            # 恢复策略状态
            for strategy_name, strategy_data in state_data.get("strategies", {}).items():
                strategy_type = StrategyType(strategy_name)
                if strategy_type in self.strategies:
                    state = self.strategies[strategy_type]
                    state.initial_capital = strategy_data.get("initial_capital", 0)
                    state.current_capital = strategy_data.get("current_capital", 0)
                    state.position = strategy_data.get("position", 0)
                    state.entry_price = strategy_data.get("entry_price", 0)
                    state.params = strategy_data.get("params", {})
                    state.trades = strategy_data.get("trades", [])
                    state.win_count = strategy_data.get("win_count", 0)
                    state.loss_count = strategy_data.get("loss_count", 0)
                    state.updated_at = strategy_data.get("updated_at", "")

            logger.info(f"状态已从 {filepath} 加载")
            return True

        except FileNotFoundError:
            logger.info(f"状态文件 {filepath} 不存在")
            return False
        except Exception as e:
            logger.error(f"加载状态失败: {str(e)}")
            return False


# 全局竞技场实例
_arena_instance: Optional[StrategyArena] = None


def get_arena() -> StrategyArena:
    """获取全局竞技场实例"""
    global _arena_instance
    if _arena_instance is None:
        _arena_instance = StrategyArena()
    return _arena_instance


def reset_arena():
    """重置竞技场"""
    global _arena_instance
    if _arena_instance:
        _arena_instance.stop_monitoring()
    _arena_instance = None
