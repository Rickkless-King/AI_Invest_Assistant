"""
策略基类
所有具体策略都需要继承此类
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np


class BaseStrategy(ABC):
    """策略基类"""
    
    def __init__(self, name: str, params: Dict = None):
        """
        初始化策略
        
        Args:
            name: 策略名称
            params: 策略参数字典
        """
        self.name = name
        self.params = params or {}
        self.signals = []  # 交易信号历史
        
    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        生成交易信号
        
        Args:
            df: K线数据DataFrame，必须包含 timestamp, open, high, low, close, volume
            
        Returns:
            添加了signal列的DataFrame，1=买入，-1=卖出，0=持有
        """
        pass
    
    @abstractmethod
    def get_strategy_description(self) -> str:
        """
        获取策略描述
        
        Returns:
            策略的文字描述
        """
        pass
    
    def calculate_positions(self, df: pd.DataFrame, initial_capital: float = 10000) -> pd.DataFrame:
        """
        根据信号计算仓位和权益
        
        Args:
            df: 包含信号的DataFrame
            initial_capital: 初始资金
            
        Returns:
            添加了position、capital、returns列的DataFrame
        """
        df = df.copy()
        df['position'] = 0.0  # 当前持仓（币的数量）
        df['capital'] = initial_capital  # 当前资金
        df['cash'] = initial_capital  # 现金
        df['holdings'] = 0.0  # 持仓市值
        
        position = 0.0
        cash = initial_capital
        
        for i in range(1, len(df)):
            signal = df.iloc[i]['signal']
            price = df.iloc[i]['close']
            
            # 买入信号且无持仓
            if signal == 1 and position == 0:
                position = cash / price * 0.99  # 99%资金买入（留1%手续费）
                cash = 0
                
            # 卖出信号且有持仓
            elif signal == -1 and position > 0:
                cash = position * price * 0.99  # 99%卖出价值（扣1%手续费）
                position = 0
            
            df.iloc[i, df.columns.get_loc('position')] = position
            df.iloc[i, df.columns.get_loc('cash')] = cash
            df.iloc[i, df.columns.get_loc('holdings')] = position * price
            df.iloc[i, df.columns.get_loc('capital')] = cash + position * price
        
        # 计算收益率
        df['returns'] = df['capital'].pct_change().fillna(0)
        
        return df
    
    def optimize_params(self, df: pd.DataFrame, param_grid: Dict) -> Tuple[Dict, float]:
        """
        网格搜索优化参数
        
        Args:
            df: K线数据
            param_grid: 参数网格，如 {'rsi_period': [7, 14, 21], 'threshold': [30, 40]}
            
        Returns:
            (最佳参数字典, 最佳夏普比率)
        """
        best_sharpe = -np.inf
        best_params = None
        
        # 生成所有参数组合
        keys = list(param_grid.keys())
        values = list(param_grid.values())
        
        import itertools
        for combo in itertools.product(*values):
            params = dict(zip(keys, combo))
            self.params = params
            
            # 生成信号并计算收益
            df_test = self.generate_signals(df.copy())
            df_test = self.calculate_positions(df_test)
            
            # 计算夏普比率
            sharpe = self._calculate_sharpe(df_test['returns'])
            
            if sharpe > best_sharpe:
                best_sharpe = sharpe
                best_params = params.copy()
        
        return best_params, best_sharpe
    
    def _calculate_sharpe(self, returns: pd.Series) -> float:
        """
        计算夏普比率
        
        Args:
            returns: 收益率序列
            
        Returns:
            夏普比率（年化）
        """
        if len(returns) < 2 or returns.std() == 0:
            return 0.0
        
        # 假设加密货币市场365天交易
        annual_return = returns.mean() * 365
        annual_std = returns.std() * np.sqrt(365)
        
        sharpe = annual_return / annual_std if annual_std > 0 else 0
        return sharpe
