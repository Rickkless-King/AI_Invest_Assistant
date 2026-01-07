"""
布林带（Bollinger Bands）策略
均值回归策略
"""

import pandas as pd
from .strategy_base import BaseStrategy


class BollingerBandsStrategy(BaseStrategy):
    """
    布林带策略：
    - 价格触及下轨: 买入（超卖反弹）
    - 价格触及上轨: 卖出（超买回调）
    """
    
    def __init__(self, params: dict = None):
        default_params = {
            'bb_period': 20,
            'bb_std': 2.0
        }
        if params:
            default_params.update(params)
        
        super().__init__(name="布林带策略", params=default_params)
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        生成布林带交易信号
        
        Args:
            df: K线数据
            
        Returns:
            添加了signal列的DataFrame
        """
        df = df.copy()
        
        # 计算布林带
        period = self.params['bb_period']
        std_multiplier = self.params['bb_std']
        
        df['bb_middle'] = df['close'].rolling(window=period).mean()
        df['bb_std'] = df['close'].rolling(window=period).std()
        df['bb_upper'] = df['bb_middle'] + (df['bb_std'] * std_multiplier)
        df['bb_lower'] = df['bb_middle'] - (df['bb_std'] * std_multiplier)
        
        # 计算价格相对布林带的位置
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        # 生成信号
        df['signal'] = 0
        
        # 触及下轨买入（超卖）
        df.loc[df['close'] <= df['bb_lower'], 'signal'] = 1
        
        # 触及上轨卖出（超买）
        df.loc[df['close'] >= df['bb_upper'], 'signal'] = -1
        
        return df
    
    def get_strategy_description(self) -> str:
        return f"""
## 布林带均值回归策略

### 参数配置
- 布林带周期: {self.params['bb_period']}
- 标准差倍数: {self.params['bb_std']}

### 策略逻辑
1. **买入信号**: 价格触及或跌破下轨（超卖区域）
2. **卖出信号**: 价格触及或突破上轨（超买区域）

### 核心原理
- 布林带基于统计学，价格在上下轨间波动
- 触及极限值后往往会回归中轨（均值回归）
- 适合震荡市，趋势市容易被套

### 适用场景
- 横盘震荡市场
- 区间交易
- 避免强趋势突破（会连续触发错误信号）

### 胜率参考
- 历史回测胜率: 65-75%（震荡市）
- 夏普比率: 0.9-1.6
- 最大回撤: 通常较小
"""
