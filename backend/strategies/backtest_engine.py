"""
回测引擎
用于评估策略表现
"""

import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime


class BacktestEngine:
    """回测引擎"""
    
    def __init__(self, initial_capital: float = 10000, commission: float = 0.001):
        """
        初始化回测引擎
        
        Args:
            initial_capital: 初始资金
            commission: 手续费率（默认0.1%）
        """
        self.initial_capital = initial_capital
        self.commission = commission
        self.results = {}
    
    def run_backtest(self, strategy, df: pd.DataFrame) -> Dict:
        """
        运行回测
        
        Args:
            strategy: 策略对象
            df: K线数据
            
        Returns:
            回测结果字典
        """
        # 生成信号
        df_signals = strategy.generate_signals(df.copy())
        
        # 计算持仓和收益
        df_result = self._simulate_trading(df_signals)
        
        # 计算性能指标
        metrics = self._calculate_metrics(df_result)
        
        # 保存结果
        result = {
            'strategy_name': strategy.name,
            'params': strategy.params,
            'data': df_result,
            'metrics': metrics,
            'timestamp': datetime.now().isoformat()
        }
        
        self.results[strategy.name] = result
        return result
    
    def _simulate_trading(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        模拟交易过程
        
        Args:
            df: 包含信号的DataFrame
            
        Returns:
            包含持仓和权益的DataFrame
        """
        df = df.copy()
        df['position'] = 0.0  # 当前持仓（币的数量）
        df['cash'] = self.initial_capital  # 现金
        df['holdings'] = 0.0  # 持仓市值
        df['capital'] = self.initial_capital  # 总权益
        df['trade'] = 0  # 交易标记（1=买入，-1=卖出）
        
        position = 0.0
        cash = self.initial_capital
        trades = []  # 交易记录
        
        for i in range(1, len(df)):
            signal = df.iloc[i]['signal']
            price = df.iloc[i]['close']
            timestamp = df.iloc[i]['timestamp']
            
            # 买入信号且无持仓
            if signal == 1 and position == 0:
                # 扣除手续费后买入
                position = cash / price * (1 - self.commission)
                cash = 0
                df.iloc[i, df.columns.get_loc('trade')] = 1
                
                trades.append({
                    'timestamp': timestamp,
                    'type': 'BUY',
                    'price': price,
                    'amount': position,
                    'value': position * price
                })
                
            # 卖出信号且有持仓
            elif signal == -1 and position > 0:
                # 扣除手续费后卖出
                cash = position * price * (1 - self.commission)
                
                # 计算这笔交易的盈亏
                buy_trade = trades[-1] if trades else None
                if buy_trade:
                    profit = cash - buy_trade['value']
                    profit_pct = (profit / buy_trade['value']) * 100
                else:
                    profit = 0
                    profit_pct = 0
                
                trades.append({
                    'timestamp': timestamp,
                    'type': 'SELL',
                    'price': price,
                    'amount': position,
                    'value': cash,
                    'profit': profit,
                    'profit_pct': profit_pct
                })
                
                position = 0
                df.iloc[i, df.columns.get_loc('trade')] = -1
            
            # 更新当前状态
            df.iloc[i, df.columns.get_loc('position')] = position
            df.iloc[i, df.columns.get_loc('cash')] = cash
            df.iloc[i, df.columns.get_loc('holdings')] = position * price
            df.iloc[i, df.columns.get_loc('capital')] = cash + position * price
        
        df['trades_history'] = [trades] * len(df)  # 保存交易历史
        return df
    
    def _calculate_metrics(self, df: pd.DataFrame) -> Dict:
        """
        计算性能指标
        
        Args:
            df: 回测结果DataFrame
            
        Returns:
            性能指标字典
        """
        # 基本统计
        final_capital = df.iloc[-1]['capital']
        total_return = (final_capital - self.initial_capital) / self.initial_capital
        total_return_pct = total_return * 100
        
        # 收益率序列
        df['returns'] = df['capital'].pct_change().fillna(0)
        
        # 夏普比率（假设加密货币365天交易）
        if len(df['returns']) > 1 and df['returns'].std() > 0:
            sharpe_ratio = (df['returns'].mean() / df['returns'].std()) * np.sqrt(365)
        else:
            sharpe_ratio = 0
        
        # 最大回撤
        cumulative_returns = (1 + df['returns']).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = drawdown.min()
        max_drawdown_pct = max_drawdown * 100
        
        # 交易统计
        trades = df[df['trade'] != 0]
        total_trades = len(trades[trades['trade'] == 1])  # 买入次数
        
        # 胜率（从交易历史中计算）
        winning_trades = 0
        losing_trades = 0
        if len(df['trades_history'].iloc[-1]) > 0:
            sell_trades = [t for t in df['trades_history'].iloc[-1] if t['type'] == 'SELL']
            winning_trades = len([t for t in sell_trades if t.get('profit', 0) > 0])
            losing_trades = len([t for t in sell_trades if t.get('profit', 0) <= 0])
            win_rate = (winning_trades / len(sell_trades) * 100) if sell_trades else 0
        else:
            win_rate = 0

        # 计算交易天数
        trading_days = (df['timestamp'].iloc[-1] - df['timestamp'].iloc[0]).days

        metrics = {
            'initial_capital': self.initial_capital,
            'final_capital': final_capital,
            'total_return': total_return,
            'total_return_pct': total_return_pct,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'max_drawdown_pct': max_drawdown_pct,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'trading_days': trading_days,
            'avg_daily_return': total_return / trading_days if trading_days > 0 else 0
        }
        
        return metrics
    
    def compare_strategies(self, results: List[Dict]) -> pd.DataFrame:
        """
        比较多个策略的表现
        
        Args:
            results: 回测结果列表
            
        Returns:
            比较结果DataFrame
        """
        comparison_data = []
        
        for result in results:
            metrics = result['metrics']
            comparison_data.append({
                '策略名称': result['strategy_name'],
                '总收益率': f"{metrics['total_return_pct']:.2f}%",
                '夏普比率': f"{metrics['sharpe_ratio']:.2f}",
                '最大回撤': f"{metrics['max_drawdown_pct']:.2f}%",
                '交易次数': metrics['total_trades'],
                '胜率': f"{metrics['win_rate']:.2f}%",
                '交易天数': metrics['trading_days']
            })
        
        return pd.DataFrame(comparison_data)
