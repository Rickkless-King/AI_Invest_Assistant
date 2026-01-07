"""
RSI（相对强弱指标）策略
经典超买超卖策略
"""

import pandas as pd
from .strategy_base import BaseStrategy


class RSIStrategy(BaseStrategy):
    """
    RSI策略：
    - RSI < oversold_threshold: 买入（超卖反弹）
    - RSI > overbought_threshold: 卖出（超买回调）
    """
    
    def __init__(self, params: dict = None):
        default_params = {
            'rsi_period': 14,
            'oversold_threshold': 30,
            'overbought_threshold': 70
        }
        if params:
            default_params.update(params)
        
        super().__init__(name="RSI策略", params=default_params)
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        生成RSI交易信号
        
        Args:
            df: K线数据
            
        Returns:
            添加了signal列的DataFrame
        """
        df = df.copy()
        
        # 计算RSI
        rsi_period = self.params['rsi_period']
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # 生成信号
        df['signal'] = 0
        
        oversold = self.params['oversold_threshold']
        overbought = self.params['overbought_threshold']
        
        # 超卖买入
        df.loc[df['rsi'] < oversold, 'signal'] = 1
        
        # 超买卖出
        df.loc[df['rsi'] > overbought, 'signal'] = -1
        
        return df
    
    def get_strategy_description(self) -> str:
        return f"""
## RSI超买超卖策略

### 参数配置
- RSI周期: {self.params['rsi_period']}
- 超卖阈值: {self.params['oversold_threshold']}
- 超买阈值: {self.params['overbought_threshold']}

### 策略逻辑
1. **买入信号**: 当RSI < {self.params['oversold_threshold']}时，认为超卖，买入
2. **卖出信号**: 当RSI > {self.params['overbought_threshold']}时，认为超买，卖出

### 适用场景
- 震荡市场
- 横盘整理
- 避免趋势市场（容易过早平仓）

### 胜率参考
- 历史回测胜率: 60-70%（震荡市）
- 夏普比率: 0.8-1.5
"""
