"""
加密货币分析Agent
使用LangGraph实现多步骤分析流程
"""

from typing import TypedDict, Annotated, Literal
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
import os
import sys
from datetime import datetime
import json

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_fetchers.okx_fetcher import OKXFetcher


class CryptoAnalysisState(TypedDict):
    """
    分析状态
    """
    symbol: str                          # 交易对，如BTC-USDT
    timeframe: str                       # 时间周期，如1H, 4H, 1D
    market_data: dict                    # 市场数据
    technical_analysis: str              # 技术分析结果
    sentiment_analysis: str              # 市场情绪分析
    final_recommendation: str            # 最终建议
    confidence: float                    # 置信度 0-1
    messages: Annotated[list, "消息历史"]  # 对话历史


class CryptoAnalystAgent:
    """
    加密货币分析Agent
    """

    def __init__(self, model_name: str = "gpt-4o-mini"):
        """
        初始化Agent

        Args:
            model_name: 使用的模型（可以是gpt-4o-mini, deepseek-chat等）
        """
        self.fetcher = OKXFetcher()

        # 初始化LLM
        # 如果使用DeepSeek，需要设置base_url
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=0.3,
            api_key=os.getenv("OPENAI_API_KEY")  # 或DEEPSEEK_API_KEY
        )

        # 构建工作流
        self.app = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        """
        构建LangGraph工作流

        流程:
        1. 获取市场数据
        2. 技术分析
        3. 情绪分析（可选）
        4. 综合决策
        """
        workflow = StateGraph(CryptoAnalysisState)

        # 添加节点
        workflow.add_node("fetch_data", self._fetch_market_data)
        workflow.add_node("technical_analysis", self._technical_analysis)
        workflow.add_node("make_decision", self._make_final_decision)

        # 添加边
        workflow.add_edge(START, "fetch_data")
        workflow.add_edge("fetch_data", "technical_analysis")
        workflow.add_edge("technical_analysis", "make_decision")
        workflow.add_edge("make_decision", END)

        return workflow.compile()

    def _fetch_market_data(self, state: CryptoAnalysisState) -> dict:
        """
        节点1: 获取市场数据

        Args:
            state: 当前状态

        Returns:
            更新后的状态
        """
        symbol = state["symbol"]
        timeframe = state["timeframe"]

        # 获取实时行情
        ticker = self.fetcher.get_ticker(symbol)

        # 获取K线数据
        df = self.fetcher.get_candles(symbol, timeframe, limit=100)

        # 计算技术指标
        if not df.empty:
            df_with_indicators = self.fetcher.calculate_indicators(df)
            latest = df_with_indicators.iloc[-1]

            market_data = {
                "current_price": ticker.get('last', 0),
                "high_24h": ticker.get('high_24h', 0),
                "low_24h": ticker.get('low_24h', 0),
                "volume_24h": ticker.get('vol_24h', 0),
                "rsi": round(latest['rsi'], 2) if 'rsi' in latest else None,
                "macd": round(latest['macd'], 2) if 'macd' in latest else None,
                "macd_signal": round(latest['macd_signal'], 2) if 'macd_signal' in latest else None,
                "bb_upper": round(latest['bb_upper'], 2) if 'bb_upper' in latest else None,
                "bb_lower": round(latest['bb_lower'], 2) if 'bb_lower' in latest else None,
                "price_change_24h": ((ticker.get('last', 0) - ticker.get('low_24h', 0)) /
                                     ticker.get('low_24h', 1)) * 100 if ticker.get('low_24h', 0) > 0 else 0
            }
        else:
            market_data = {"error": "无法获取K线数据"}

        return {
            **state,
            "market_data": market_data,
            "messages": state.get("messages", []) + [
                AIMessage(content=f"已获取{symbol}的市场数据")
            ]
        }

    def _technical_analysis(self, state: CryptoAnalysisState) -> dict:
        """
        节点2: 技术分析

        Args:
            state: 当前状态

        Returns:
            更新后的状态
        """
        market_data = state["market_data"]

        if "error" in market_data:
            return {
                **state,
                "technical_analysis": "数据获取失败，无法进行技术分析"
            }

        # 构建分析提示词
        prompt = f"""
作为专业的加密货币技术分析师，请分析以下数据：

交易对: {state["symbol"]}
时间周期: {state["timeframe"]}

当前市场数据:
- 当前价格: ${market_data['current_price']:,.2f}
- 24h最高: ${market_data['high_24h']:,.2f}
- 24h最低: ${market_data['low_24h']:,.2f}
- 24h涨跌幅: {market_data['price_change_24h']:.2f}%

技术指标:
- RSI(14): {market_data.get('rsi', 'N/A')}
- MACD: {market_data.get('macd', 'N/A')}
- MACD信号线: {market_data.get('macd_signal', 'N/A')}
- 布林带上轨: ${market_data.get('bb_upper', 0):,.2f}
- 布林带下轨: ${market_data.get('bb_lower', 0):,.2f}

请提供:
1. 趋势判断（上涨/下跌/震荡）
2. 支撑位和阻力位
3. RSI超买超卖分析
4. MACD背离信号
5. 短期交易建议

分析要简洁专业，300字以内。
"""

        # 调用LLM
        messages = [
            SystemMessage(content="你是专业的加密货币技术分析师，擅长使用技术指标分析市场。"),
            HumanMessage(content=prompt)
        ]

        try:
            response = self.llm.invoke(messages)
            technical_analysis = response.content
        except Exception as e:
            technical_analysis = f"技术分析失败: {str(e)}"

        return {
            **state,
            "technical_analysis": technical_analysis,
            "messages": state.get("messages", []) + [
                AIMessage(content="技术分析完成")
            ]
        }

    def _make_final_decision(self, state: CryptoAnalysisState) -> dict:
        """
        节点3: 综合决策

        Args:
            state: 当前状态

        Returns:
            更新后的状态
        """
        market_data = state["market_data"]
        technical_analysis = state["technical_analysis"]

        # 构建决策提示词
        prompt = f"""
基于以下分析，给出最终交易建议：

技术分析:
{technical_analysis}

当前价格: ${market_data['current_price']:,.2f}
RSI: {market_data.get('rsi', 'N/A')}

请给出:
1. 明确的操作建议: BUY(买入) / SELL(卖出) / HOLD(观望)
2. 置信度: 0-100的整数
3. 理由: 一句话说明（50字以内）

返回JSON格式:
{{
    "action": "BUY/SELL/HOLD",
    "confidence": 75,
    "reason": "技术指标显示超卖，且MACD即将金叉"
}}
"""

        messages = [
            SystemMessage(content="你是理性的量化交易决策者，基于数据给出明确建议。"),
            HumanMessage(content=prompt)
        ]

        try:
            response = self.llm.invoke(messages)
            # 尝试解析JSON
            decision_text = response.content

            # 简单解析（实际应该用json.loads，但LLM可能返回markdown格式）
            if "BUY" in decision_text.upper():
                action = "BUY"
            elif "SELL" in decision_text.upper():
                action = "SELL"
            else:
                action = "HOLD"

            # 提取置信度（简化处理）
            try:
                confidence_str = decision_text.split('"confidence":')[1].split(',')[0].strip()
                confidence = float(confidence_str) / 100
            except:
                confidence = 0.5

            final_recommendation = decision_text

        except Exception as e:
            action = "HOLD"
            confidence = 0.0
            final_recommendation = f"决策失败: {str(e)}"

        return {
            **state,
            "final_recommendation": final_recommendation,
            "confidence": confidence,
            "messages": state.get("messages", []) + [
                AIMessage(content=f"最终建议: {action} (置信度: {confidence:.0%})")
            ]
        }

    def analyze(self, symbol: str, timeframe: str = "1H") -> dict:
        """
        执行完整分析流程

        Args:
            symbol: 交易对，如BTC-USDT
            timeframe: 时间周期，如1H, 4H, 1D

        Returns:
            分析结果字典
        """
        # 初始化状态
        initial_state = {
            "symbol": symbol,
            "timeframe": timeframe,
            "market_data": {},
            "technical_analysis": "",
            "sentiment_analysis": "",
            "final_recommendation": "",
            "confidence": 0.0,
            "messages": [
                HumanMessage(content=f"分析{symbol} {timeframe}")
            ]
        }

        # 运行工作流
        result = self.app.invoke(initial_state)

        # 返回结果
        return {
            "symbol": result["symbol"],
            "timeframe": result["timeframe"],
            "current_price": result["market_data"].get("current_price"),
            "technical_analysis": result["technical_analysis"],
            "final_recommendation": result["final_recommendation"],
            "confidence": result["confidence"],
            "timestamp": datetime.now().isoformat()
        }


# 示例用法
if __name__ == "__main__":
    # 初始化Agent
    agent = CryptoAnalystAgent()

    # 分析BTC
    print("=== 开始分析BTC ===")
    result = agent.analyze("BTC-USDT", "1H")

    print(f"\n交易对: {result['symbol']}")
    print(f"当前价格: ${result['current_price']:,.2f}")
    print(f"\n技术分析:\n{result['technical_analysis']}")
    print(f"\n最终建议:\n{result['final_recommendation']}")
    print(f"\n置信度: {result['confidence']:.0%}")
