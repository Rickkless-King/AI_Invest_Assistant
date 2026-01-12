"""
波动收割策略（Volatility Harvest Strategy）
基于StrategyQuantX平台生成的Strategy 4.5.163
专为BTC-USDT 4H时间周期优化

核心逻辑：
1. 使用ATR（平均真实波幅）来识别市场波动状态
2. 在波动性确认时入场（ATR > 阈值）
3. 使用动态移动止损保护利润
4. 止损/止盈基于百分比和ATR倍数

策略特点：
- 趋势跟踪为主
- 动态止损保护利润
- 适合高波动市场（如BTC）
- 4H时间周期优化
"""

import pandas as pd
import numpy as np
from .strategy_base import BaseStrategy


class VolatilityHarvestStrategy(BaseStrategy):
    """
    波动收割策略：
    - 利用ATR识别波动区间
    - 突破前一根K线收盘价时入场
    - 动态移动止损保护利润

    原始策略参数（来自StrategyQuantX）：
    - ATRHigherPeriod1 = 20
    - ProfitTarget1 = 1.3%
    - StopLoss1 = 75 pips
    - TrailingStopCoef1 = 4.5 * ATR(185)
    """

    def __init__(self, params: dict = None):
        default_params = {
            # 核心ATR参数
            'atr_period': 20,           # ATR计算周期（信号生成）
            'atr_trail_period': 185,    # 移动止损ATR周期
            'atr_multiplier': 4.5,      # 移动止损ATR倍数

            # 入场阈值
            'entry_atr_threshold': 0.0,  # ATR入场阈值（ATR > 此值则允许入场）

            # 止损止盈
            'stop_loss_pct': 3.0,        # 止损百分比（默认3%，原75pips转换）
            'profit_target_pct': 1.3,    # 止盈百分比（原策略为1.3%）

            # 趋势判断
            'trend_ema_period': 50,      # 趋势EMA周期
            'use_trend_filter': True,    # 是否使用趋势过滤

            # 突破确认
            'breakout_bars': 1,          # 突破确认K线数
        }
        if params:
            default_params.update(params)

        super().__init__(name="波动收割策略", params=default_params)

    def _calculate_atr(self, df: pd.DataFrame, period: int) -> pd.Series:
        """
        计算ATR（平均真实波幅）

        True Range = max(High - Low, abs(High - Close_prev), abs(Low - Close_prev))
        ATR = SMA(True Range, period)
        """
        high = df['high']
        low = df['low']
        close = df['close']

        # 计算True Range
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))

        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # 计算ATR（使用指数移动平均）
        atr = true_range.ewm(span=period, adjust=False).mean()

        return atr

    def _calculate_ema(self, series: pd.Series, period: int) -> pd.Series:
        """计算EMA"""
        return series.ewm(span=period, adjust=False).mean()

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        生成波动收割交易信号

        入场逻辑：
        1. ATR[2] > entry_atr_threshold（波动性确认）
        2. 价格突破前一根K线收盘价
        3. （可选）趋势过滤：价格在EMA之上做多，之下做空

        出场逻辑：
        1. 触及止损
        2. 触及止盈
        3. 移动止损被触发

        Args:
            df: K线数据

        Returns:
            添加了signal列的DataFrame
        """
        df = df.copy()

        # 获取参数
        atr_period = self.params['atr_period']
        atr_trail_period = self.params['atr_trail_period']
        atr_multiplier = self.params['atr_multiplier']
        entry_threshold = self.params['entry_atr_threshold']
        stop_loss_pct = self.params['stop_loss_pct'] / 100
        profit_target_pct = self.params['profit_target_pct'] / 100
        trend_ema_period = self.params['trend_ema_period']
        use_trend_filter = self.params['use_trend_filter']
        breakout_bars = self.params['breakout_bars']

        # 计算技术指标
        df['atr'] = self._calculate_atr(df, atr_period)
        df['atr_trail'] = self._calculate_atr(df, atr_trail_period)
        df['ema_trend'] = self._calculate_ema(df['close'], trend_ema_period)

        # 计算ATR百分比（相对于价格）
        df['atr_pct'] = df['atr'] / df['close'] * 100

        # 计算移动止损距离
        df['trailing_stop_distance'] = df['atr_trail'] * atr_multiplier

        # 初始化信号
        df['signal'] = 0
        df['entry_price'] = np.nan
        df['stop_loss'] = np.nan
        df['take_profit'] = np.nan
        df['trailing_stop'] = np.nan

        # 持仓状态跟踪
        position = 0  # 0: 无仓位, 1: 多头, -1: 空头
        entry_price = 0
        stop_loss = 0
        take_profit = 0
        trailing_stop = 0
        highest_since_entry = 0
        lowest_since_entry = float('inf')

        for i in range(max(atr_period, atr_trail_period, trend_ema_period) + breakout_bars, len(df)):
            current_price = df.iloc[i]['close']
            high_price = df.iloc[i]['high']
            low_price = df.iloc[i]['low']
            prev_close = df.iloc[i - breakout_bars]['close']
            atr_value = df.iloc[i - 2]['atr'] if i >= 2 else df.iloc[i]['atr']  # ATR[2]
            atr_trail_value = df.iloc[i]['atr_trail']
            ema_value = df.iloc[i]['ema_trend']

            # 波动性条件（ATR > 阈值）
            volatility_ok = atr_value > entry_threshold

            # 趋势条件
            if use_trend_filter:
                bullish_trend = current_price > ema_value
                bearish_trend = current_price < ema_value
            else:
                bullish_trend = True
                bearish_trend = True

            # 如果有持仓，检查出场条件
            if position == 1:  # 多头持仓
                highest_since_entry = max(highest_since_entry, high_price)

                # 更新移动止损
                new_trailing_stop = highest_since_entry - (atr_trail_value * atr_multiplier)
                if new_trailing_stop > trailing_stop:
                    trailing_stop = new_trailing_stop

                # 检查出场条件
                if low_price <= stop_loss:
                    df.iloc[i, df.columns.get_loc('signal')] = -1
                    position = 0
                elif high_price >= take_profit:
                    df.iloc[i, df.columns.get_loc('signal')] = -1
                    position = 0
                elif low_price <= trailing_stop and trailing_stop > entry_price:
                    df.iloc[i, df.columns.get_loc('signal')] = -1
                    position = 0

            elif position == -1:  # 空头持仓
                lowest_since_entry = min(lowest_since_entry, low_price)

                # 更新移动止损
                new_trailing_stop = lowest_since_entry + (atr_trail_value * atr_multiplier)
                if new_trailing_stop < trailing_stop:
                    trailing_stop = new_trailing_stop

                # 检查出场条件
                if high_price >= stop_loss:
                    df.iloc[i, df.columns.get_loc('signal')] = 1
                    position = 0
                elif low_price <= take_profit:
                    df.iloc[i, df.columns.get_loc('signal')] = 1
                    position = 0
                elif high_price >= trailing_stop and trailing_stop < entry_price:
                    df.iloc[i, df.columns.get_loc('signal')] = 1
                    position = 0

            # 如果无持仓，检查入场条件
            if position == 0 and volatility_ok:
                # 多头入场条件：价格突破前一根K线收盘价 + 趋势向上
                if current_price > prev_close and bullish_trend:
                    df.iloc[i, df.columns.get_loc('signal')] = 1
                    position = 1
                    entry_price = current_price
                    stop_loss = entry_price * (1 - stop_loss_pct)
                    take_profit = entry_price * (1 + profit_target_pct)
                    trailing_stop = entry_price - (atr_trail_value * atr_multiplier)
                    highest_since_entry = high_price

                    df.iloc[i, df.columns.get_loc('entry_price')] = entry_price
                    df.iloc[i, df.columns.get_loc('stop_loss')] = stop_loss
                    df.iloc[i, df.columns.get_loc('take_profit')] = take_profit
                    df.iloc[i, df.columns.get_loc('trailing_stop')] = trailing_stop

                # 空头入场条件：价格跌破前一根K线收盘价 + 趋势向下
                elif current_price < prev_close and bearish_trend and not bullish_trend:
                    df.iloc[i, df.columns.get_loc('signal')] = -1
                    position = -1
                    entry_price = current_price
                    stop_loss = entry_price * (1 + stop_loss_pct)
                    take_profit = entry_price * (1 - profit_target_pct)
                    trailing_stop = entry_price + (atr_trail_value * atr_multiplier)
                    lowest_since_entry = low_price

                    df.iloc[i, df.columns.get_loc('entry_price')] = entry_price
                    df.iloc[i, df.columns.get_loc('stop_loss')] = stop_loss
                    df.iloc[i, df.columns.get_loc('take_profit')] = take_profit
                    df.iloc[i, df.columns.get_loc('trailing_stop')] = trailing_stop

        return df

    def get_strategy_description(self) -> str:
        return f"""
## 波动收割策略（Volatility Harvest）

### 策略来源
基于StrategyQuantX平台生成的Strategy 4.5.163，经过BTC-USDT 4H时间周期回测优化。

### 参数配置
- ATR周期（信号）: {self.params['atr_period']}
- ATR周期（止损）: {self.params['atr_trail_period']}
- ATR倍数: {self.params['atr_multiplier']}
- 止损: {self.params['stop_loss_pct']}%
- 止盈: {self.params['profit_target_pct']}%
- 趋势EMA: {self.params['trend_ema_period']}
- 趋势过滤: {'开启' if self.params['use_trend_filter'] else '关闭'}

### 策略逻辑
1. **入场条件**:
   - ATR > {self.params['entry_atr_threshold']}（波动性确认）
   - 价格突破前{self.params['breakout_bars']}根K线收盘价
   - （可选）价格在{self.params['trend_ema_period']}周期EMA之上做多，之下做空

2. **出场条件**:
   - 触及止损（{self.params['stop_loss_pct']}%）
   - 触及止盈（{self.params['profit_target_pct']}%）
   - 移动止损被触发（{self.params['atr_multiplier']} × ATR({self.params['atr_trail_period']})）

### 适用场景
- 高波动市场（BTC、ETH等）
- 4H及以上时间周期
- 趋势明确的市场环境

### 策略优势
- 动态止损随利润增长而收紧
- ATR自适应市场波动
- 2017-2026年BTC回测表现优异

### 风险提示
- 震荡市场可能频繁止损
- 需要较大的资金承受回撤
"""


# 简化版本：使用更激进的参数，适合趋势市场
class VolatilityHarvestAggressiveStrategy(VolatilityHarvestStrategy):
    """波动收割策略 - 激进版"""

    def __init__(self, params: dict = None):
        aggressive_params = {
            'atr_period': 14,
            'atr_trail_period': 100,
            'atr_multiplier': 3.0,
            'entry_atr_threshold': 0.0,
            'stop_loss_pct': 5.0,
            'profit_target_pct': 2.0,
            'trend_ema_period': 30,
            'use_trend_filter': True,
            'breakout_bars': 1,
        }
        if params:
            aggressive_params.update(params)

        super().__init__(params=aggressive_params)
        self.name = "波动收割策略(激进)"


# 保守版本：更保守的参数，减少回撤
class VolatilityHarvestConservativeStrategy(VolatilityHarvestStrategy):
    """波动收割策略 - 保守版"""

    def __init__(self, params: dict = None):
        conservative_params = {
            'atr_period': 20,
            'atr_trail_period': 185,
            'atr_multiplier': 5.0,
            'entry_atr_threshold': 0.0,
            'stop_loss_pct': 2.0,
            'profit_target_pct': 1.0,
            'trend_ema_period': 100,
            'use_trend_filter': True,
            'breakout_bars': 2,
        }
        if params:
            conservative_params.update(params)

        super().__init__(params=conservative_params)
        self.name = "波动收割策略(保守)"
