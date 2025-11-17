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
from langchain.agents import create_agent
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


# 尝试加入记忆与循环
"""Agent可以多次调用工具直到完成任务"""
def loop_with_memory():
    #循环与Memory-Agent自动决定调用次数
    class AgentState(TypedDict):
        messages:Annotated[list,add_messages]# 使用add_messages
        iteration:int
    
    @tool
    def search_data(query:str)->str:
        """搜索财务数据"""
        return f"找到关于{query}的数据:PE=52,EPS=$3.5"
    
    @tool
    def calculate(expression:str)->str:
        """计算数值"""
        return "182"
    
    tools=[search_data,calculate]
    tool_node=ToolNode(tools)

    # Agent节点：决定下一步行动
    def agent_node(state:AgentState):
        messages=state["messages"]
        iteration=state.get("iteration",0)
        print(f"迭代{iteration+1} Agent思考中")
        response=llm.bind_tools(tools).invoke(messages)

        return{
            "messages":[response],
            "iteration":iteration+1
        }
    
    # 决策：继续还是结束
    def should_continue(state:AgentState)->Literal["tools","end"]:
        last_messages=state["messages"][-1]

        # 如果LLM返回了工具调用，继续
        if hasattr(last_messages,"tool_calls") and last_messages.tool_calls:
            print("→需要调用工具，继续循环")
            return tools
        # 否则结束
        print("→任务完成，循环结束")
        return "end"

    # 构建图
    workflow=StateGraph(AgentState)
    workflow.add_node("agent",agent_node)
    workflow.add_node("tools",tool_node)
    workflow.add_conditional_edges(
        "agent",
        should_continue,{
            "tools":"tools",
            "end":END
        }
    )
    workflow.add_edge("tools","agent") #工具执行后回到Agent

    app=workflow.compile()

    # 测试
    question="NVDA的PE是多少？如果EPS是3，合理价格应该是多少？"
    result=app.invoke({
        "messages":[HumanMessage(content=question)],
        "iteration":0
    })

    for i,msg in enumerate(result["messages"]):
        if isinstance(msg,HumanMessage):
            print(f"\n👤 用户: {msg.content}")
        elif isinstance(msg, AIMessage):
            if msg.content:
                print(f"\n🤖 AI: {msg.content}")  


# 多agent对话
def multi_agent_supervisor():
    """
    多Agent对话 - Supervisor监督者模式

    架构：
    ┌─────────────────────────────────────────┐
    │         用户输入问题                    │
    └─────────────┬───────────────────────────┘
                  │
                  ▼
    ┌─────────────────────────────────────────┐
    │      Supervisor（监督者Agent）          │
    │  决定：该问题应该由哪个专家来回答？      │
    └─────────┬───────────────────────────────┘
              │
      ┌───────┴───────┐
      ▼               ▼
    ┌─────────┐   ┌─────────┐   ┌─────────┐
    │宏观分析 │   │公司分析 │   │估值分析 │
    │  专家   │   │  专家   │   │  专家   │
    └────┬────┘   └────┬────┘   └────┬────┘
         │             │             │
         └─────────────┴─────────────┘
                       │
                       ▼
               返回给Supervisor
                       │
                       ▼
                   输出结果

    这是2025年最推荐的多Agent架构！
    """

    print("="*50)
    print("示例5：多Agent对话 - Supervisor监督者模式")
    print("="*50)

    # 定义状态
    class SupervisorState(TypedDict):
        messages: Annotated[list, add_messages]
        next_agent: str  # 下一个要调用的agent

    # 创建三个专家Agent

    # 1. 宏观经济分析专家
    @tool
    def get_macro_data() -> dict:
        """获取宏观经济数据"""
        return {
            "fed_rate": "4.0%-4.25%",
            "cpi": 3.01,
            "unemployment": 4.0
        }

    macro_agent = create_agent(
        model=llm,
        tools=[get_macro_data],
        system_prompt="""你是宏观经济分析专家。
        专门分析美国的利率、通胀、就业等宏观经济指标。
        当被问到宏观经济问题时，使用get_macro_data工具获取数据并分析。
        回答要简洁专业，50字以内。"""
    )

    # 2. 公司基本面分析专家
    @tool
    def get_company_info(symbol: str) -> dict:
        """获取公司基本信息"""
        return {
            "name": "NVIDIA",
            "industry": "Semiconductors",
            "market_cap": "4.5T"
        }

    company_agent = create_agent(
        model=llm,
        tools=[get_company_info],
        system_prompt="""你是公司基本面分析专家。
        专门分析公司的行业地位、业务模式、竞争优势等。
        当被问到公司情况时，使用get_company_info工具获取数据并分析。
        回答要简洁专业，50字以内。"""
    )

    # 3. 估值分析专家
    @tool
    def get_valuation(symbol: str) -> dict:
        """获取估值数据"""
        return {
            "pe": 52.0,
            "price": 186.5,
            "target_price": 220.0
        }

    valuation_agent = create_agent(
        model=llm,
        tools=[get_valuation],
        system_prompt="""你是估值分析专家。
        专门分析股票的PE、PB等估值指标，判断高估还是低估。
        当被问到估值问题时，使用get_valuation工具获取数据并分析。
        回答要简洁专业，50字以内。"""
    )

    # Supervisor节点：决定调用哪个专家
    def supervisor_node(state: SupervisorState):
        messages = state["messages"]

        # 使用LLM决定路由
        supervisor_prompt = """你是投资分析团队的Supervisor（监督者）。

你手下有三位专家：
1. macro_expert - 宏观经济分析专家（分析利率、通胀、就业等）
2. company_expert - 公司基本面分析专家（分析公司业务、行业地位等）
3. valuation_expert - 估值分析专家（分析PE、价格、是否高估等）

根据用户的问题，决定应该把问题转给哪位专家。

规则：
- 如果问宏观经济、美联储、通胀 → 选择 macro_expert
- 如果问公司业务、行业、竞争力 → 选择 company_expert
- 如果问估值、价格、PE、是否值得买 → 选择 valuation_expert
- 如果需要综合分析，先选择最相关的一个

只回复专家名称，不要其他内容。从以下选项中选一个：
macro_expert, company_expert, valuation_expert, FINISH
"""

        response = llm.invoke([
            SystemMessage(content=supervisor_prompt),
            *messages
        ])

        next_agent = response.content.strip()
        print(f"\n🎯 Supervisor决策：将问题转给 {next_agent}")

        return {"next_agent": next_agent}

    # 各专家节点
    def macro_expert_node(state: SupervisorState):
        print("  → 宏观经济专家工作中...")
        result = macro_agent.invoke(state)
        return {"messages": result["messages"]}

    def company_expert_node(state: SupervisorState):
        print("  → 公司分析专家工作中...")
        result = company_agent.invoke(state)
        return {"messages": result["messages"]}

    def valuation_expert_node(state: SupervisorState):
        print("  → 估值分析专家工作中...")
        result = valuation_agent.invoke(state)
        return {"messages": result["messages"]}

    # 决策函数：根据supervisor的决定路由
    def route_to_expert(state: SupervisorState) -> Literal["macro", "company", "valuation", "end"]:
        next_agent = state["next_agent"]

        if "macro" in next_agent.lower():
            return "macro"
        elif "company" in next_agent.lower():
            return "company"
        elif "valuation" in next_agent.lower():
            return "valuation"
        else:
            return "end"

    # 构建图
    workflow = StateGraph(SupervisorState)

    # 添加节点
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("macro", macro_expert_node)
    workflow.add_node("company", company_expert_node)
    workflow.add_node("valuation", valuation_expert_node)

    # 定义流程
    workflow.add_edge(START, "supervisor")

    # Supervisor根据决策路由到不同专家
    workflow.add_conditional_edges(
        "supervisor",
        route_to_expert,
        {
            "macro": "macro",
            "company": "company",
            "valuation": "valuation",
            "end": END
        }
    )

    # 专家回答后回到supervisor（可以继续问下一个专家）
    workflow.add_edge("macro", END)
    workflow.add_edge("company", END)
    workflow.add_edge("valuation", END)

    app = workflow.compile()

    # 测试不同类型的问题
    test_questions = [
        "现在美国的经济形势如何？",
        "NVDA是一家什么样的公司？",
        "NVDA现在的估值贵不贵？"
    ]

    for i, question in enumerate(test_questions, 1):
        print(f"\n{'='*50}")
        print(f"[问题 {i}] {question}")
        print('='*50)

        result = app.invoke({
            "messages": [HumanMessage(content=question)]
        })

        # 提取最后的AI回答
        last_ai_message = None
        for msg in reversed(result["messages"]):
            if isinstance(msg, AIMessage) and msg.content:
                last_ai_message = msg
                break

        if last_ai_message:
            print(f"\n💬 回答：{last_ai_message.content}")
        print()
  
