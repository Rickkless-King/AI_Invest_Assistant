# 接下来的内容涵盖
# 1. LangGraph基础:State、Graph、Node、Edge
# State：存储整个工作流的所有数据(比如股票代码、宏观数据、分析结果)，所有节点都能读/写,数据全程共享不丢失
# Node：本质是一个函数，负责完成一件具体任务(比如查宏观数据/分析估值)，读取笔记本(State)的数据，做完后把结果写回State
# Edge：定义任务的执行顺序(比如查完宏观数据→查公司信息)，告诉程序“当前节点做完后，下一步该找谁”。

# 2.条件分支与循环
# 3.多Agent对话系统(SuperVisor模式、Router模式、Network模式)
# 4.投资分析系统实战

from typing import TypedDict,Annotated,Literal
# 导入python类型提示工具，TypeDict用于定义State的结构，Annotated用于指定字段更新策略，Literal用于限定可选值
from langchain_core.messages import HumanMessage,AIMessage,SystemMessage,BaseMessage
# 导入Langchain的消息类型，用于处理人机交互消息
from langgraph.graph import StateGraph,END,START
# StateGraph是工作流图的“容器”，START/END是固定的开始/结束节点
from langgraph.graph.message import add_messages
# add_messages会自动把新消息“追加”到列表，而不是覆盖原有信息
from langgraph.prebuilt import ToolNode
# ToolNode是专门用于执行工具调用的节点
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
import operator
from fundamental_analyst import *

load_dotenv()

finnhub_api_key=os.getenv("FINNHUB_API_KEY")
finnhub_client=finnhub.Client(api_key=finnhub_api_key)
av_api_key = os.getenv("ALPHAVANTAGE_API_KEY")
fred_api_key=os.getenv("FRED_API_KEY")
fred_client=Fred(api_key=fred_api_key)

llm=ChatOpenAI(
    model="qwen-plus",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    temperature=0.1,
)

"""
State是LangGraph的核心概念，是整个Graph执行过程中的“共享内存”
推荐的State定义方式：
1.使用TypeDict定义结构
2.使用Annotated[type,reducer]定义更新策略
3.消息列表使用add_messages作为reducer
"""

class InvestmentState(TypedDict):# InvestmentState继承自TypeDict    
    """投资分析流程的状态 """
    symbol:str#用户输入的股票代码
    macro_data:dict #宏观经济数据
    company_data:dict #公司数据
    company_price:dict #公司价格数据
    analysis:str #分析结果
    recommendation:str #投资建议
    messages:Annotated[list,add_messages]
    # Annotated指定类型为list，add_messages会自动将新消息列表追加到列表，而不是覆盖，预留用于人机交互

# 创建第一个Graph
def simple_graph_example():
    # 最简单的LangGraph示例，理解Node和Edge

    # 1.定义简单State，只有input、output；两个字段
    class SimpleState(TypedDict):
        input: str
        output: str

    # 2.定义节点Node(节点函数)：每个节点负责一件事情，输入是State，输出是要更新的字段
    def step1(state:SimpleState):
        """节点1：处理输入 """
        print(f"步骤1:收到输入'{state['input']}'")
        return {"output":"处理中..."}
    
    def step2(state:SimpleState):
        """节点2：生成输出 """
        print(f"步骤2：基于'{state['input']}'生成结果")
        return {"output":f"已完成对{state['input']}的分析"}
    
    # 3.创建StateGraph实例，绑定SimpleState
    workflow = StateGraph(SimpleState)

    # 4.添加节点到图中，参数是“节点名称”和“节点函数”
    workflow.add_node("处理",step1)# 节点名“处理”，对应函数step1
    workflow.add_node("生成",step2)# 节点名“生成”，对应函数step2

    # 5.定义Edge(执行顺序)：START→处理→生成→END
    workflow.add_edge(START,"处理")
    workflow.add_edge("处理","生成")
    workflow.add_edge("生成",END)

    # 6.编译工作流，把定义的State、Node、Edge变成可执行的程序
    app=workflow.compile()

    # 7.执行工作流，传入初始state(只有input字段)，返回最终state
    result=app.invoke({"input":"NVDA"})
    print("最终结果是:",result)

# 实战 投资分析工作流(基础版)
def investment_workflow_basic():
    """完整的投资分析LangGraph,使用真实的金融数据工具 """
    
    @tool
    def fetch_macro_data()->dict:
        """
        获取美国宏观经济数据
        参数:
            因为获取的是美国宏观经济数据，无需传入参数
        返回：
            返回包括汇率、联邦基金目标利率、通胀数据和GDP数据的字典
        """
        return get_macro_economic_data()
    
    @tool
    def fetch_stock_profile(symbol:str)->dict:
        """
        获取股票代码对应上市公司的信息
        参数：
            symbol为上市公司的股票代码(比如"NVDA"、"AAPL")
        返回:
            返回包括名称、行业、ipo时间、市值(百万美元)、官网、描述等数据的字典
        """
        return get_company_profile(symbol)
    
    @tool
    def fetch_stock_price(symbol:str)->dict:
        """
        获取股票代码对应上市公司的价格
        参数：
            symbol为上市公司的股票代码(比如"NVDA"、"AAPL")
        返回：
            返回包括最新成交价、当日最高价、当日最低价、当日开盘价、前一个交易日的收盘价等数据的字典
        """
        return get_real_time_data_with_fallback(symbol)
    
    # 节点1：获取宏观数据
    def get_macro_data_node(state:InvestmentState):
        print("正在获取宏观数据...")
        macro=fetch_macro_data.invoke({})# 该工具无参数，传入空字典
        return {"macro_data":macro}# 数据节点的返回必须使用字典的键值对
    
    # 节点2：获取公司数据
    def get_company_profile_node(state:InvestmentState):
        print("正在获取供公司信息")
        company_profile=fetch_stock_profile.invoke(state["symbol"])
        return {"company_data":company_profile}
    
    # 节点3：获取公司价格
    def get_company_price_node(state:InvestmentState):
        print("正在获取公司股票价格")
        company_price=fetch_stock_price.invoke(state["symbol"])
        return {"company_price":company_price}
    
    # 节点4：分析估值
    def analyze_node(state:InvestmentState):
        prompt = f"""
 基于以下数据分析{state['symbol']}:

 宏观环境：
 - 联邦利率：{state['macro_data']['联邦基金目标利率']}
 - CPI:{state['macro_data']['通胀数据']}
 - GDP数据:{state['macro_data']['GDP数据']}

 公司数据：
 - 公司介绍：{state['company_data']}
 - 公司股票价格:{state['company_price']}

 请判断估值水平（高估/合理/低估）,限200字内
 """
        analysis=llm.invoke(prompt).content
        return{"analysis":analysis}
     
    # 节点5：生成建议
    def recommend_node(state:InvestmentState):
        print("正在生成建议")
        prompt=f"""
     基于分析：{state['analysis']}
     给出明确的投资建议(买入/持有/卖出/)
     """
        recommendation=llm.invoke(prompt).content
        return{"recommendation":recommendation}
    
    # 构建图
    workflow=StateGraph(InvestmentState)

    # 添加所有节点
    workflow.add_node("获取宏观数据",get_macro_data_node)
    workflow.add_node("获取公司信息",get_company_profile_node)
    workflow.add_node("获取公司价格",get_company_price_node)
    workflow.add_node("分析公司估值",analyze_node)
    workflow.add_node("投资建议",recommend_node)

    # 定义流程
    workflow.add_edge(START,"获取宏观数据")
    workflow.add_edge("获取宏观数据","获取公司信息")
    workflow.add_edge("获取公司信息","获取公司价格")
    workflow.add_edge("获取公司价格","分析公司估值")
    workflow.add_edge("分析公司估值","投资建议")
    workflow.add_edge("投资建议",END)

    # 编译并执行
    app=workflow.compile()

    result=app.invoke({"symbol":"NVDA"})

    print(f"股票：{result['symbol']}")
    print(f"\n分析：\n{result['analysis']}")
    print(f"\n建议：\n{result['recommendation']}")

# if __name__=="__main__":
#     investment_workflow_basic()


# 接下来：条件分支——根据不同情况走不同路径
def conditional_workflow():
    """学习条件路由 高PE和低PE走不同分析路径 """
    print("高PE深度分析 vs 低PE快速评估")
    
    class AnalysisState(TypedDict):
        symbol:str
        price:float
        pe_ratio:float
        output:str

    # Node：获取数据
    def fetch_data(state:AnalysisState):
        # 模拟获取数据
        print(f"获取{state['symbol']}数据")
        return{
            "price":state.get("price",186.5),
            "pe_ratio":state.get("pe_ratio",52.0)
        }
    
    # 决策函数：根据PE比率决定路线
    def should_deep_dive(state:AnalysisState)->Literal["深度分析","快速评估"]:
        """高PE需要深度分析，低PE快速评估"""
        if state["pe_ratio"]>50:
            print(f"PE={state['pe_ratio']}>50,进入深度分析路径")
            return "深度分析"
        else:
            print(f"PE={state['pe_ratio']}≤50,进入快速分析路径")
            return "快速评估"
    # 两条不同的分析路径
    def deep_analysis(state:AnalysisState):
        return{"output":f"{state['symbol']}PE已经高达{state['symbol']},需要警惕泡沫风险"}
    
    def quick_analysis(state:AnalysisState):
        return{"output":f"{state['symbol']}PE目前为{state['pe_ratio']},估值较为合理"}
    
    # 构建图
    workflow=StateGraph(AnalysisState)

    workflow.add_node("获取数据",fetch_data)
    workflow.add_node("深度分析",deep_analysis)
    workflow.add_node("快速评估",quick_analysis)

    workflow.add_edge(START,"获取数据")
    # 关键：条件分支
    workflow.add_conditional_edges(
        "获取数据",
        should_deep_dive,#决策函数
        {
            "深度分析":"深度分析",
            "快速分析":"快速评估"
        }
    )
    workflow.add_edge("深度分析",END)
    workflow.add_edge("快速分析",END)

    app=workflow.compile()

    # 测试高PE股票(NVDA)
    print("测试1:NVDA(高PE):")
    result1=app.invoke({"symbol":"NVDA","pe_ratio":57})
    print(result1)

    # 测试低PE股票(ASEC)
    print("测试2:ASEC(低PE)")
    result2=app.invoke({"symbol":"ASEC","pe_ratio":7}) 
    print(result2)

if __name__=="__main__":
    conditional_workflow()

