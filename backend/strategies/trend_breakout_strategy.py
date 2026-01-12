"""
趋势突破策略（Trend Breakout Strategy）
基于StrategyQuantX平台生成的Strategy 3.9.147
专为BTC-USDT 4H时间周期优化

核心逻辑：
1. 使用线性回归（Linear Regression）判断趋势方向
2. 使用BiggestRange指标计算波动范围
3. 在价格突破关键水平时入场
4. 使用固定百分比止盈止损

策略特点：
- 趋势跟踪策略
- 突破确认入场
- 适合趋势明确的市场
- 4H时间周期优化
"""

import pandas as pd
import numpy as np
from typing import Tuple
from .strategy_base import BaseStrategy


class TrendBreakoutStrategy(BaseStrategy):
    """
    趋势突破策略：
    - 使用线性回归判断趋势方向
    - BiggestRange计算入场价位
    - 日线高低点作为参考

    原始策略参数（来自StrategyQuantX Strategy 3.9.147）：
    - LinRegBarClosesPrd1 = 102
    - PriceEntryMult1 = 0.5
    - ProfitTarget1 = 1.6%
    - StopLoss1 = 45 pips
    - BiggestRange period = 157
    - BarsValid = 6
    """

    def __init__(self, params: dict = None):
        default_params = {
            # 线性回归参数
            'linreg_period': 102,           # 线性回归周期

            # 入场参数
            'price_entry_mult': 0.5,        # 入场价格乘数
            'biggest_range_period': 157,    # BiggestRange周期
            'bars_valid': 6,                # 入场有效K线数

            # 止损止盈
            'stop_loss_pct': 1.8,           # 止损百分比（45 pips转换约1.8%）
            'profit_target_pct': 1.6,       # 止盈百分比

            # 趋势过滤
            'use_trend_filter': True,       # 使用趋势过滤
            'trend_lookback': 2,            # 趋势判断回溯K线数

            # 日线参数
            'daily_lookback': 3,            # 日线高低点回溯天数
        }
        if params:
            default_params.update(params)

        super().__init__(name="趋势突破策略", params=default_params)

    def _calculate_linear_regression(self, series: pd.Series, period: int) -> pd.Series:
        """
        计算线性回归值

        使用最小二乘法计算线性回归线的当前值
        """
        def linreg(x):
            if len(x) < period:
                return np.nan
            y = x.values
            x_axis = np.arange(len(y))

            # 最小二乘法
            n = len(y)
            sum_x = np.sum(x_axis)
            sum_y = np.sum(y)
            sum_xy = np.sum(x_axis * y)
            sum_x2 = np.sum(x_axis ** 2)

            # 斜率和截距
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
            intercept = (sum_y - slope * sum_x) / n

            # 返回最后一个点的回归值
            return intercept + slope * (n - 1)

        return series.rolling(window=period).apply(linreg, raw=False)

    def _calculate_biggest_range(self, df: pd.DataFrame, period: int) -> pd.Series:
        """
        计算BiggestRange指标

        返回过去period根K线中最大的单根K线振幅（High - Low）
        """
        high_low_range = df['high'] - df['low']
        return high_low_range.rolling(window=period).max()

    def _calculate_daily_levels(self, df: pd.DataFrame, lookback: int) -> Tuple[pd.Series, pd.Series]:
        """
        计算日线高低点

        由于我们使用4H数据，需要聚合计算日线高低点
        每天6根4H K线
        """
        bars_per_day = 6  # 4H时间周期，每天6根K线

        # 计算日线高点
        daily_high = df['high'].rolling(window=bars_per_day * lookback).max()
        # 计算日线低点
        daily_low = df['low'].rolling(window=bars_per_day * lookback).min()

        return daily_high, daily_low

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        生成趋势突破交易信号

        入场逻辑（做多）：
        1. Close[2] > LinReg(102)[2]（价格在回归线上方）
        2. 入场价 = HighDaily[3] + (0.5 * BiggestRange(157)[2])
        3. 当价格突破入场价时入场

        入场逻辑（做空）：
        1. Close[2] < LinReg(102)[2]（价格在回归线下方）
        2. 入场价 = LowDaily[3] - (0.5 * BiggestRange(157)[2])
        3. 当价格跌破入场价时入场

        出场逻辑：
        1. 触及止损
        2. 触及止盈

        Args:
            df: K线数据

        Returns:
            添加了signal列的DataFrame
        """
        df = df.copy()

        # 获取参数
        linreg_period = self.params['linreg_period']
        price_entry_mult = self.params['price_entry_mult']
        biggest_range_period = self.params['biggest_range_period']
        bars_valid = self.params['bars_valid']
        stop_loss_pct = self.params['stop_loss_pct'] / 100
        profit_target_pct = self.params['profit_target_pct'] / 100
        trend_lookback = self.params['trend_lookback']
        daily_lookback = self.params['daily_lookback']
        use_trend_filter = self.params['use_trend_filter']

        # 计算技术指标
        df['linreg'] = self._calculate_linear_regression(df['close'], linreg_period)
        df['biggest_range'] = self._calculate_biggest_range(df, biggest_range_period)

        # 计算日线高低点
        daily_high, daily_low = self._calculate_daily_levels(df, daily_lookback)
        df['daily_high'] = daily_high
        df['daily_low'] = daily_low

        # 计算入场价位
        # 做多入场价 = DailyHigh[lookback] + (mult * BiggestRange[2])
        df['long_entry_price'] = df['daily_high'].shift(1) + (price_entry_mult * df['biggest_range'].shift(trend_lookback))
        # 做空入场价 = DailyLow[lookback] - (mult * BiggestRange[2])
        df['short_entry_price'] = df['daily_low'].shift(1) - (price_entry_mult * df['biggest_range'].shift(trend_lookback))

        # 初始化信号
        df['signal'] = 0
        df['entry_price'] = np.nan
        df['stop_loss'] = np.nan
        df['take_profit'] = np.nan

        # 持仓状态跟踪
        position = 0  # 0: 无仓位, 1: 多头, -1: 空头
        entry_price = 0
        stop_loss = 0
        take_profit = 0
        entry_bar = 0  # 入场K线索引
        pending_long = False
        pending_short = False
        pending_bar = 0

        # 需要足够的历史数据来计算指标
        start_idx = max(linreg_period, biggest_range_period, daily_lookback * 6) + trend_lookback + 5

        for i in range(start_idx, len(df)):
            current_price = df.iloc[i]['close']
            high_price = df.iloc[i]['high']
            low_price = df.iloc[i]['low']

            # 获取回溯值
            linreg_value = df.iloc[i - trend_lookback]['linreg'] if i >= trend_lookback else np.nan
            close_lookback = df.iloc[i - trend_lookback]['close'] if i >= trend_lookback else current_price

            # 趋势判断
            if use_trend_filter and not np.isnan(linreg_value):
                bullish_trend = close_lookback > linreg_value
                bearish_trend = close_lookback < linreg_value
            else:
                bullish_trend = True
                bearish_trend = True

            # 入场价位
            long_entry = df.iloc[i]['long_entry_price']
            short_entry = df.iloc[i]['short_entry_price']

            # 如果有持仓，检查出场条件
            if position == 1:  # 多头持仓
                # 检查止损
                if low_price <= stop_loss:
                    df.iloc[i, df.columns.get_loc('signal')] = -1
                    position = 0
                # 检查止盈
                elif high_price >= take_profit:
                    df.iloc[i, df.columns.get_loc('signal')] = -1
                    position = 0

            elif position == -1:  # 空头持仓
                # 检查止损
                if high_price >= stop_loss:
                    df.iloc[i, df.columns.get_loc('signal')] = 1
                    position = 0
                # 检查止盈
                elif low_price <= take_profit:
                    df.iloc[i, df.columns.get_loc('signal')] = 1
                    position = 0

            # 如果无持仓，检查入场条件
            if position == 0:
                # 处理待定订单
                if pending_long and (i - pending_bar) <= bars_valid:
                    # 检查是否突破做多入场价
                    if high_price >= long_entry and not np.isnan(long_entry):
                        df.iloc[i, df.columns.get_loc('signal')] = 1
                        position = 1
                        entry_price = long_entry
                        stop_loss = entry_price * (1 - stop_loss_pct)
                        take_profit = entry_price * (1 + profit_target_pct)
                        entry_bar = i
                        pending_long = False

                        df.iloc[i, df.columns.get_loc('entry_price')] = entry_price
                        df.iloc[i, df.columns.get_loc('stop_loss')] = stop_loss
                        df.iloc[i, df.columns.get_loc('take_profit')] = take_profit

                elif pending_short and (i - pending_bar) <= bars_valid:
                    # 检查是否跌破做空入场价
                    if low_price <= short_entry and not np.isnan(short_entry):
                        df.iloc[i, df.columns.get_loc('signal')] = -1
                        position = -1
                        entry_price = short_entry
                        stop_loss = entry_price * (1 + stop_loss_pct)
                        take_profit = entry_price * (1 - profit_target_pct)
                        entry_bar = i
                        pending_short = False

                        df.iloc[i, df.columns.get_loc('entry_price')] = entry_price
                        df.iloc[i, df.columns.get_loc('stop_loss')] = stop_loss
                        df.iloc[i, df.columns.get_loc('take_profit')] = take_profit

                # 检查新的入场信号
                if not pending_long and not pending_short:
                    # 做多条件：价格在回归线上方
                    if bullish_trend and not np.isnan(long_entry):
                        pending_long = True
                        pending_bar = i
                    # 做空条件：价格在回归线下方
                    elif bearish_trend and not bullish_trend and not np.isnan(short_entry):
                        pending_short = True
                        pending_bar = i

                # 重置过期的待定订单
                if pending_long and (i - pending_bar) > bars_valid:
                    pending_long = False
                if pending_short and (i - pending_bar) > bars_valid:
                    pending_short = False

        return df

    def get_strategy_description(self) -> str:
        return f"""
## 趋势突破策略（Trend Breakout）

### 策略来源
基于StrategyQuantX平台生成的Strategy 3.9.147，经过BTC-USDT 4H时间周期回测优化。

### 参数配置
- 线性回归周期: {self.params['linreg_period']}
- BiggestRange周期: {self.params['biggest_range_period']}
- 入场价格乘数: {self.params['price_entry_mult']}
- 入场有效K线: {self.params['bars_valid']}
- 止损: {self.params['stop_loss_pct']}%
- 止盈: {self.params['profit_target_pct']}%
- 日线回溯: {self.params['daily_lookback']}天
- 趋势过滤: {'开启' if self.params['use_trend_filter'] else '关闭'}

### 策略逻辑
1. **趋势判断**:
   - 使用{self.params['linreg_period']}周期线性回归判断趋势方向
   - Close[{self.params['trend_lookback']}] > LinReg[{self.params['trend_lookback']}] 为上升趋势
   - Close[{self.params['trend_lookback']}] < LinReg[{self.params['trend_lookback']}] 为下降趋势

2. **入场条件（做多）**:
   - 价格在回归线上方（上升趋势）
   - 入场价 = DailyHigh + ({self.params['price_entry_mult']} × BiggestRange)
   - 价格突破入场价时入场
   - 入场订单在{self.params['bars_valid']}根K线内有效

3. **入场条件（做空）**:
   - 价格在回归线下方（下降趋势）
   - 入场价 = DailyLow - ({self.params['price_entry_mult']} × BiggestRange)
   - 价格跌破入场价时入场

4. **出场条件**:
   - 触及止损（{self.params['stop_loss_pct']}%）
   - 触及止盈（{self.params['profit_target_pct']}%）

### 适用场景
- 趋势明确的市场
- 波动性适中的市场
- 4H及以上时间周期

### 策略优势
- 使用线性回归捕捉趋势
- BiggestRange自适应市场波动
- 突破确认减少假信号
- 2017-2026年BTC回测表现优异

### 风险提示
- 震荡市场可能频繁止损
- 突破后回调可能触发止损
"""
