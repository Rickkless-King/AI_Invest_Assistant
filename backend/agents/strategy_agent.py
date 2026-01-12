"""
策略优化Agent
使用LangGraph实现自主策略优化
"""

from typing import TypedDict, Annotated, Literal, List, Dict
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
import pandas as pd
import sys

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategies.rsi_strategy import RSIStrategy
from strategies.macd_strategy import MACDStrategy
from strategies.bb_strategy import BollingerBandsStrategy
from strategies.volatility_harvest_strategy import VolatilityHarvestStrategy
from strategies.backtest_engine import BacktestEngine
from data_fetchers.okx_fetcher import OKXFetcher
from data_fetchers.historical_data_manager import HistoricalDataManager
from utils.logger import get_logger

load_dotenv()

# 初始化日志
logger = get_logger(__name__)


class StrategyAgentState(TypedDict):
    """Agent状态"""
    symbol: str
    timeframe: str
    current_strategy: str
    current_params: dict
    backtest_result: dict
    optimization_history: List[dict]
    iteration: int
    messages: Annotated[list, add_messages]
    should_continue: bool


class StrategyAgent:
    """策略优化Agent"""
    
    def __init__(self, use_deepseek: bool = True):
        if use_deepseek:
            self.llm = ChatOpenAI(
                model="deepseek-chat",
                base_url="https://api.deepseek.com",
                api_key=os.getenv("DEEPSEEK_API_KEY"),
                temperature=0.7,
            )
        else:
            self.llm = ChatOpenAI(
                model="qwen-plus",
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                api_key=os.getenv("DASHSCOPE_API_KEY"),
                temperature=0.7,
            )
        
        self.okx_fetcher = OKXFetcher()
        self.backtest_engine = BacktestEngine(initial_capital=10000)
        self.data_manager = HistoricalDataManager()  # 添加历史数据管理器
        self.available_strategies = {
            'RSI': RSIStrategy,
            'MACD': MACDStrategy,
            'BollingerBands': BollingerBandsStrategy,
            'VolatilityHarvest': VolatilityHarvestStrategy
        }
        self.app = self._build_workflow()
    
    def _build_workflow(self):
        workflow = StateGraph(StrategyAgentState)
        workflow.add_node("select_strategy", self._select_strategy_node)
        workflow.add_node("run_backtest", self._run_backtest_node)
        workflow.add_node("analyze_results", self._analyze_results_node)
        workflow.add_node("optimize_params", self._optimize_params_node)
        
        workflow.add_edge(START, "select_strategy")
        workflow.add_edge("select_strategy", "run_backtest")
        workflow.add_edge("run_backtest", "analyze_results")
        workflow.add_conditional_edges(
            "analyze_results",
            self._should_continue_optimization,
            {
                "optimize": "optimize_params",
                "end": END
            }
        )
        workflow.add_edge("optimize_params", "run_backtest")
        return workflow.compile()
    
    def _select_strategy_node(self, state: StrategyAgentState) -> dict:
        iteration = state.get('iteration', 0) + 1
        print(f"\n策略选择 [迭代 {iteration}]")
        logger.info(f"策略选择开始 - 迭代 {iteration}, 交易对: {state['symbol']}, 周期: {state['timeframe']}")

        if state.get('current_strategy'):
            return {}

        prompt = f"""为 {state['symbol']} ({state['timeframe']}) 选择策略。
可选：RSI、MACD、BollingerBands、VolatilityHarvest（波动收割，特别适合BTC-USDT的4H周期）。只回复策略名。"""

        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            strategy_name = response.content.strip()

            if 'RSI' in strategy_name:
                params = {'rsi_period': 14, 'oversold_threshold': 30, 'overbought_threshold': 70}
            elif 'MACD' in strategy_name:
                params = {'fast_period': 12, 'slow_period': 26, 'signal_period': 9}
            elif 'Volatility' in strategy_name or '波动' in strategy_name:
                params = {
                    'atr_period': 20,
                    'atr_trail_period': 185,
                    'atr_multiplier': 4.5,
                    'entry_atr_threshold': 0.0,
                    'stop_loss_pct': 3.0,
                    'profit_target_pct': 1.3,
                    'trend_ema_period': 50,
                    'use_trend_filter': True,
                    'breakout_bars': 1
                }
            else:
                params = {'bb_period': 20, 'bb_std': 2.0}

            print(f"选择策略: {strategy_name}, 参数: {params}")
            logger.info(f"策略选择完成 - 策略: {strategy_name}, 参数: {params}")

            return {
                "current_strategy": strategy_name,
                "current_params": params,
                "iteration": iteration
            }
        except Exception as e:
            logger.error(f"策略选择失败 - 错误: {str(e)}", exc_info=True)
            raise
    
    def _run_backtest_node(self, state: StrategyAgentState) -> dict:
        print(f"\n运行回测...")
        # 使用历史数据管理器获取数据（自动检测并补全）
        df = self.data_manager.get_latest_data_for_backtest(
            symbol=state['symbol'],
            timeframe=state['timeframe'],
            days=90,  # 获取90天数据
            auto_update=True  # 自动检测并更新
        )
        
        if df.empty:
            return {"backtest_result": {"error": "数据获取失败"}}
        
        strategy_class = self.available_strategies.get(state['current_strategy'].replace('策略', ''))
        if not strategy_class:
            for key in self.available_strategies.keys():
                if key in state['current_strategy']:
                    strategy_class = self.available_strategies[key]
                    break
        if not strategy_class:
            strategy_class = RSIStrategy
        
        strategy = strategy_class(params=state['current_params'])
        result = self.backtest_engine.run_backtest(strategy, df)
        metrics = result['metrics']
        
        print(f"收益率: {metrics['total_return_pct']:.2f}%, 夏普: {metrics['sharpe_ratio']:.2f}, 回撤: {metrics['max_drawdown_pct']:.2f}%")
        
        history = state.get('optimization_history', [])
        history.append({
            'iteration': state['iteration'],
            'strategy': state['current_strategy'],
            'params': state['current_params'],
            'metrics': metrics
        })
        
        return {
            "backtest_result": result,
            "optimization_history": history
        }
    
    def _analyze_results_node(self, state: StrategyAgentState) -> dict:
        print(f"\n分析结果...")
        result = state['backtest_result']
        if 'error' in result:
            return {"should_continue": False}
        
        metrics = result['metrics']
        prompt = f"""分析 {state['symbol']} {state['current_strategy']} 回测结果：
收益率: {metrics['total_return_pct']:.2f}%
夏普比率: {metrics['sharpe_ratio']:.2f}
最大回撤: {metrics['max_drawdown_pct']:.2f}%
胜率: {metrics['win_rate']:.2f}%

是否需要继续优化？回答"建议继续优化"或"建议停止优化"。"""
        
        response = self.llm.invoke([HumanMessage(content=prompt)])
        analysis = response.content
        print(f"分析: {analysis}")
        
        should_continue = "继续优化" in analysis and state['iteration'] < 5
        return {
            "messages": [AIMessage(content=analysis)],
            "should_continue": should_continue
        }
    
    def _optimize_params_node(self, state: StrategyAgentState) -> dict:
        print(f"\n优化参数...")
        import random
        new_params = state['current_params'].copy()
        for key in new_params:
            if isinstance(new_params[key], int):
                new_params[key] += random.randint(-2, 2)
            elif isinstance(new_params[key], float):
                new_params[key] += random.uniform(-0.5, 0.5)

        # 递增迭代计数器
        new_iteration = state['iteration'] + 1
        print(f"新参数: {new_params} (迭代 {new_iteration})")
        return {
            "current_params": new_params,
            "iteration": new_iteration
        }
    
    def _should_continue_optimization(self, state: StrategyAgentState) -> Literal["optimize", "end"]:
        return "optimize" if state.get('should_continue', False) else "end"
    
    def run(self, symbol: str = "BTC-USDT", timeframe: str = "1H",
            user_strategy: str = None, user_params: dict = None) -> dict:
        """
        运行策略优化Agent

        Args:
            symbol: 交易对
            timeframe: 时间周期
            user_strategy: 用户指定的策略名称（可选，如 "RSI", "MACD", "BollingerBands"）
            user_params: 用户指定的参数字典（可选）
        """
        print(f"\n策略优化Agent启动: {symbol} {timeframe}")

        initial_state = {
            "symbol": symbol,
            "timeframe": timeframe,
            "iteration": 0,
            "optimization_history": [],
            "messages": []
        }

        # 如果用户指定了策略和参数，直接使用
        if user_strategy and user_params:
            print(f"使用用户指定策略: {user_strategy}, 参数: {user_params}")
            initial_state["current_strategy"] = user_strategy
            initial_state["current_params"] = user_params
            initial_state["iteration"] = 1  # 直接从迭代1开始
        elif user_strategy:
            print(f"使用用户指定策略: {user_strategy} (使用默认参数)")
            initial_state["current_strategy"] = user_strategy
            # 使用默认参数
            if user_strategy == 'RSI':
                initial_state["current_params"] = {'rsi_period': 14, 'oversold_threshold': 30, 'overbought_threshold': 70}
            elif user_strategy == 'MACD':
                initial_state["current_params"] = {'fast_period': 12, 'slow_period': 26, 'signal_period': 9}
            elif user_strategy == 'VolatilityHarvest':
                initial_state["current_params"] = {
                    'atr_period': 20,
                    'atr_trail_period': 185,
                    'atr_multiplier': 4.5,
                    'entry_atr_threshold': 0.0,
                    'stop_loss_pct': 3.0,
                    'profit_target_pct': 1.3,
                    'trend_ema_period': 50,
                    'use_trend_filter': True,
                    'breakout_bars': 1
                }
            else:  # BollingerBands
                initial_state["current_params"] = {'bb_period': 20, 'bb_std': 2.0}
            initial_state["iteration"] = 1

        result = self.app.invoke(
            initial_state,
            config={
                "recursion_limit": 30  # 设置递归限制：5次迭代 × 3个节点 + 初始节点
            }
        )

        # 保存结果到数据库
        if result.get('backtest_result') and 'metrics' in result['backtest_result']:
            df = self.data_manager.load_klines(symbol, timeframe, limit=1000)
            self.data_manager.save_backtest_result(
                symbol=symbol,
                timeframe=timeframe,
                strategy_name=result['current_strategy'],
                params=result['current_params'],
                metrics=result['backtest_result']['metrics'],
                df=df,
                user_specified=(user_strategy is not None),
                notes=f"迭代{result.get('iteration', 0)}次优化"
            )

        return result
