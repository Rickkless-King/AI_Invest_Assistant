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
    recommendation:str #投资建议
    messages:Annotated[list,add_messages]
    # Annotated指定类型为list，add_messages会自动将新消息列表追加到列表，而不是覆盖，预留用于人机交互

# 简单尝试
def basic_investment_workflow():
    @tool
    def fetch_macro_data()->dict:
        """
        获取美国宏观经济数据
        参数：
            无需参数，因为获取的是美国宏观经济数据
        返回：
             返回一个包含汇率、利率、就业、通胀、GDP等数据的字典
        """
        return get_macro_economic_data()
    @tool
    def fetch_stock_profile(symbol:str)->dict:
        """
        获取股票对应上市公司的公司资料
        参数：
            symbol:上市公司的股票代码(比如“NVDA”/"BMNR")
        返回:
            返回一个包含公司名称、行业、ipo时间、市值、官网等信息的字典
        """
        return get_company_profile_with_fallback(symbol)
    @tool
    def fetch_stock_price(symbol:str)->dict:
        """
        获取股票最新的一些价格数据
        参数：
            symbol:上市公司的股票代码(比如“NVDA”/"BMNR")
        返回：
            返回一个包含最新成交价、当日最高价、当日最低价、当日开盘价、前一个交易日的收盘价等信息的字典
        """
        return get_real_time_data_with_fallback(symbol)
    
    # 节点1：获取美国宏观经济数据
    def get_macro_data_node(state:InvestmentState):
        macro=fetch_macro_data.invoke({})# 这里没有参数，传入空字典
        return{"macro_data":macro}
    

    #节点2：获取上市公司的公司介绍
    def get_stock_profile_node(state:InvestmentState):
        stock_profile=fetch_stock_profile.invoke(state["symbol"])
        return{"company_data":stock_profile}
    

    # 节点3：获取上市公司的价格数据
    def get_stock_price_node(state:InvestmentState):
        stock_price=fetch_stock_price.invoke(state["symbol"])
        return {"company_price":stock_price}
    

    # 节点4:根据提供的宏观美国经济数据和微观个股数据，给出投资建议
    def investment_analyis_node(state:InvestmentState):
        prompt=f"""
     现在你的身份是一名顶级对冲基金的基金经理，非常擅长根据宏观经济情况结合微观个股走势来做出投资判断，
     先给你提供如下数据，请基于以下数据对{state["symbol"]}进行分析
     宏观经济方面：
     外汇利率方面：美元兑人民币：{state['macro_data']["美元兑人民币"]}、
     美元兑日元：{state['macro_data']["美元兑日元"]}、美元兑欧元：{state['macro_data']["美元兑欧元"]}。
     联邦基金目标利率：{state['macro_data']["联邦基金目标利率"]}。
     非农就业人数：{state['macro_data']["非农就业人数"]}。
     失业率：{state['macro_data']["失业率"]}。
     通胀数据：{state['macro_data']["通胀数据"]}。
     GDP数据:{state['macro_data']["GDP数据"]}。

     微观个股方面：
     公司名称：{state['company_data']['名称']},
     公司所属行业：{state['company_data']['行业']},
     IPO时间:{state['company_data']['ipo时间']},
     市值(百万美元):{state['company_data']['市值(百万美元)']},
     官网:{state['company_data']['官网']},
     描述:{state['company_data']['描述']},
     最新成交价：{state['company_price']["最新成交价"]},
     当日最高价：{state['company_price']["当日最高价"]},
     当日最低价：{state['company_price']["当日最低价"]},
     当日开盘价：{state['company_price']["当日开盘价"]},
     前一个交易日的收盘价：{state['company_price']["前一个交易日的收盘价"]},
     上述数据的更新时间：{state['company_price']["上述数据的更新时间"]}。
     
     一些要求：
      1. 根据收到的宏观经济数据，判断当下所处的宏观经济环境是偏向宽松或是偏向紧缩，并根据通胀数据与就业数据，
      判断接下来美联储是会缩表或是扩表，即采取宽松的货币政策或是紧缩的货币政策，未来是否为继续降息放水。
      2.判断当下要分析的公司目前的股价是被高估或是低估，是否应当买入，为什么？按照目前的宏观情况与微观情况，什么样的价格买入比较合适？
      3.逻辑清晰，表达有条理，从宏观经济到微观个股进行自上而下的梳理。
     """
        recommendation=llm.invoke(prompt).content
        return{"recommendation":recommendation}
    
    # 开始构建图
    workflow=StateGraph(InvestmentState)

    # 添加所有节点
    workflow.add_node("宏观数据",get_macro_data_node)
    workflow.add_node("获取公司资料",get_stock_profile_node)
    workflow.add_node("获取公司股票价格信息",get_stock_price_node)
    workflow.add_node("对目标公司给出投资建议",investment_analyis_node)

    # 添加完节点后，指定边顺序
    workflow.add_edge(START,"宏观数据")
    workflow.add_edge("宏观数据","获取公司资料")
    workflow.add_edge("获取公司资料","获取公司股票价格信息")
    workflow.add_edge("获取公司股票价格信息","对目标公司给出投资建议")
    workflow.add_edge("对目标公司给出投资建议",END)

    # 编译并执行
    app=workflow.compile()
    result=app.invoke({"symbol":"NVDA"})

    # print(result) 这里返回的result是完整的state快照，之前定义的InvestmentState里有好几个字段，打印result本质是打印
    # “完整的字典对象”，会把所有字段都全部输出。而python字典打印是“紧凑无格式输出”，所以打印出来会显得非常挤。

    print("="*60)
    print(f"📊 {result['symbol']} 投资分析报告")
    print("="*60)

 # 1. 宏观经济（只展示核心指标，不冗余）
    print("\n🌍 核心宏观数据：")
    macro = result["macro_data"]
    print(f"  - 联邦基金利率：{macro['联邦基金目标利率']['利率区间']}")
    print(f"  - CPI同比：{macro['通胀数据']['CPI同比(%)']}%")
    print(f"  - 失业率：{macro['失业率']['最新值(%)']}%")
    print(f"  - 美元兑人民币：{macro['美元兑人民币']['最新值']}")

 # 2. 公司&股价（合并展示，提取关键信息）
    print("\n🏢 公司&股价核心信息：")
    company = result["company_data"]
    price = result["company_price"]
    print(f"  - 公司名称：{company['名称']} | 行业：{company['行业']} | 市值：{company['市值(百万美元)']/1000:.1f}十亿美元")
    print(f"  - 最新股价：${price['最新成交价']} | 当日波动：${price['当日最低价']:.2f}-${price['当日最高价']:.2f}")
    print(f"  - 数据更新时间：{price['上述数据的更新时间']}")

 # 3. 投资建议（直接展示，保留LLM原始格式）
    print("\n💡 投资分析与建议：")
    print("-"*40)
    print(result["recommendation"].strip())  # 去掉首尾空行，保持原有换行
    print("\n" + "="*60)

# if __name__=="__main__":
#     basic_investment_workflow()

# 尝试加入条件分支
def conditional_workflow():
    class AnalysisState(TypedDict):
        symbol:str
        peers:list
        output:str

    #     symbol:str
    #     price:float
    #     pe_ratio:float
    #     peer_pes:list[dict]
    #     out_put:str

 
    # 我们在写程序的时候需要牢记，如果需要agent灵活调用的时候，才需要使用节点tool。且使用了tool，就需要用到ToolNode
    # 如果只是固定使用，普通函数也可以
    @tool
    def fetch_company_peers(symbol:str)->dict:
        """
        获取上市公司同行业竞争对手
        参数：
           symbol:上市公司的股票代码(比如"NVDA"/"BMNR")
        返回：
            包含同行业其他上市公司股票代码的列表
        """
        return get_company_peers(symbol)
    
    @tool
    def fetch_company_financials(symbol:str)->dict:
        """
        获取上市公司财务数据情况
        参数：
            symbol:上市公司的股票代码(比如"NVDA"/"BMNR")
        返回：
            包括52周最高、52周最低、Beta系数、PE比率、毛利率等数据的字典
        """
        return get_financials_with_fallback(symbol)
    
    # 我们这里搞一个普通函数来获取各个竞争公司对手的市盈率情况
    def get_peer_company_ratio(symbol:str)->list[dict]:
        peers=get_company_peers(symbol)# 首先获取竞争对手list，然后使用for循环获取每一个竞争对手的pe_ratio，
        # 下面是之前我的写法
        # # 搞一个空字典，然后添加进去
        # empty_dict=[]
        # for i in len(range(peers)):
        #     peer_dict=get_financials_with_fallback(peers[i])
        #     empty_dict+={peers[i]:peer_dict["PE比率"]}
        #     return empty_dict
        # 现在我们已经使用一个普通函数通过列表的方式获取了每一个竞争对手的市盈率情况，但是市盈率及对应symbol目前是列表里面的字典
        # 我们应该怎么把这个列表里面的字典取出来并作为state的一部分呢？
        # 接下来是Codex为我修改的部分
        peer_ratios=[]
        for x in peers:
            financials=get_financials_with_fallback(x)# 我之前是使用i从0开始，然后使用列表[数字]方式获取，
            # 这样的缺点是我自己也没办法很好了解细化到每一个的输出情况
            peer_ratios.append({"symbol":x,"pe_ratio":financials.get("PE比率")})
        return peer_ratios
    
    # Node：获取同行市盈率列表
    def fetch_peer_data(state:AnalysisState)->dict:
        peer_ratios=get_peer_company_ratio(state["symbol"])
        return {"peers":peer_ratios}# 这里直接把整个同行业竞争对手以及其对应的市盈率送进去了
    
    # 决策函数：根据同行市盈率列表来决定走哪条路径
    def choose_peer_path(state:AnalysisState)->Literal["深度分析","快速评估"]:# Literal是python的类型提示(type hint)，表示函数只能返回这两个字符串之一
        high_peers=[p for p in state["peers"] if p.get("pe_ratio",0) and p["pe_ratio"]>50]# 这一行的意思是使用推导式遍历列表里面的字典元素，
        # 然后对列表使用.get(,0)方法判是否存在，不存在返回0，这是一种安全写法，然后用字典名[键]获取对应的value
        # 最后返回的是列表，这个列表里元素是字典，且字典里第二个key“pe_ratio”大于50。
        if high_peers:
            print(f"发现{len(high_peers)}家公司PE>50,进入深度分析路径")
            return "深度分析"
        else:
            print("同行公司PE普通较低,进入快速评估")
            return "快速评估"
        
    def deep_analysis(state: AnalysisState):
        high_peers = [f"{p['symbol']}(市盈率为:{p['pe_ratio']}倍)" for p in state["peers"] if p.get("pe_ratio")]
        return {
            "out_put": f"{state['symbol']}所属行业内出现高PE公司:{', '.join(high_peers)}，需要警惕估值泡沫"
        }

    def quick_analysis(state: AnalysisState):
        peers_desc = [f"{p['symbol']}(市盈率为:{p['pe_ratio']}倍)" for p in state["peers"] if p.get("pe_ratio")]
        return {
            "out_put": f"{state['symbol']} 所属行业同行PE水平正常:{', '.join(peers_desc)}，估值较为健康"
        }

    workflow=StateGraph(AnalysisState)
    workflow.add_node("获取同行PE",fetch_peer_data)
    workflow.add_node("深分",deep_analysis)
    workflow.add_node("快分",quick_analysis)
    workflow.add_edge(START,"获取同行PE")
    workflow.add_conditional_edges(# conditional edges条件路由
        "获取同行PE",#这里再写一遍是因为上面的.add_edge(START,"获取同行PE")
        choose_peer_path,#作为决策函数根据state的内容进行判断
        {
        "深度分析": "深分",# 这里左边的“深度分析”是choose_peer_path函数的返回值，右边的“深度分析”是add_node时定义的节点名称。
        "快速评估": "快分",
        },
        workflow.add_edge("深分",END),
        workflow.add_edge("快分",END)
    )
    app=workflow.compile()# 将你定义的节点和边编译成可执行的图结构，并返回一个可调用.invoke()的应用实例
    result=app.invoke({"symbol":"NVDA"})# 其实整个conditional_flow()函数都没用到大语言模型，是因为没用到大语言模型，所以没有用agent
    # 进而导致上面定义的两个tool也没有用到
    print(result)

# if __name__=="__main__":
#     conditional_workflow()

# 重新做一个conditional_workflow_with_agent():
def conditional_workflow_with_agent():
    # codex给到我的设计思路：1.先用工具节点获取同行业列表和各自PE
    # 2.决策函数只做路由判断，LLM负责生成最终文本
    # 3.add_conditional_edges控制分支，深度/快速两条路径都可访问到前置工具产出的同行PE数据
    class ConditionalState(TypedDict):# 这里需要从typeDict继承
        symbol:str
        peers:list
        decision:str# codex 新增一个decision
        output:str
    # 之所以重新做一个workflow是希望能够用到tool、agent
    # @tool
    # def fetch_peer_ratios(state:ConditionalState)->dict:
    #     peers=get_company_peers(state["symbol"])
    #     # 使用一个for循环，将上市公司及其对应的市盈率重新做一个字典，然后字典作为列表的元素，整个列表返回作为peers的value
    #     peer_ratios=[]
    #     for peer in peers:
    #         financials=get_financials_with_fallback(peer)
    #         peer_ratios.append({"symbol":peer,"pe_ratio":financials["PE比率"]})
    #     return {"peers":peer_ratios}#目前peers对应的value为一个list，list里面的元素为字典，字典key为股票代码，value为对应给的PE值
    
    
    # @tool
    # def analysis_pe_ratios(state:ConditionalState)->Literal["深分","快分"]:
    #     for peer in state["peers"]:
    #         if peer["pe_ratio"]>50:
    #             return "深分"
    #         else:
    #             return "快分"
    
    # codex的做法
    @tool
    def fetch_company_peers(symbol:str)->list:#工具函数用不用state:XxxState
        """
        获取同行业中上市的竞争对手公司的股票代码列表
        参数：
            symbol为上市公司股票代码(比如："NVDA"/"BMNR")
        返回：
            同行业上市公司的股票代码列表(比如：["NVDA","AMD","INTC"])
        """
        return get_company_peers(symbol)
    @tool
    def fetch_company_financials(symbol:str)->dict:# symbol:str用在工具函数@tool里，LLM调用工具时不必传整个state
        """
        获取上市公司财务数据
        参数：
            symbol为上市公司股票代码(比如："NVDA"/"BMNR")
        返回：
            对应上市公司的52周最高价、52周最低价、PE比率、毛利率等财务指标的字典
        """
        return get_financials_with_fallback(symbol)
    
    # 调用fetch_company_peers获取同行列表
    def peer_node(state:ConditionalState):# state:ConditionalState用在节点函数里，LangGraph会自动传入完整的statte，同时要求节点必须更新/读取state
        peer_list=fetch_company_peers.invoke(state["symbol"])# 目前来看，tool工具函数在LangGraph中基本用在节点函数中
        return {"peers":[{"symbol":p}for p in peer_list]}# 这个推导式的结果确实变成[{"symbol":"NVDA"},{"symbol":"AVGO"},{"symbol":"AMD"}]
    
    # 为每个同行补齐PE数据
    def peer_financials_node(state:ConditionalState):
        enriched=[]
        for peer in state["peers"]:
            fin=fetch_company_financials.invoke(peer["symbol"])#这里注意一下peer["symbol"]写法
            enriched.append({"symbol":peer["symbol"],"pe_ratio":fin.get("PE比率")})# fin是获取了公司金融数据的字典，.get()方法是列表的，。get( ,默认值)相较于字典名[key]更安全，因为当key不存在时，不会报错
        return {"peers":enriched}# node都要返回字典
    
    # 决策函数，根据同行PE选择路径
    def choose_path(state:ConditionalState)->Literal["深度分析","快速评估"]:
        high=[p for p in state["peers"]if p.get("pe_ratio") and p["pe_ratio"]>50]
        if high:
            return "深度分析"
        else:
            return "快速评估"
    
    # 在深度分析函数中使用大模型得出结论
    def deep_analysis(state:ConditionalState):
        prompt=f"""
     你是顶级对冲基金的分析师。目标公司：{state['symbol']}。
     同行PE情况:{state['peers']}。请为我进行PE相关的深度分析。
     字数不超过300字
     """
        answer=llm.invoke(prompt).content
        return{"output":answer,"decision":"深度分析"}
    def quick_analysis(state:ConditionalState):
        prompt=f"""
     你是顶级对冲基金的分析师。目标公司：{state['symbol']}。
     同行PE情况:{state['peers']}。
     请快速给出估值简评,100字内。
     """
        answer=llm.invoke(prompt).content# 通过f-string方式将prompt送进llm.invoke(prompt)中
        return{"output":answer,"decision":"快速评估"}
    
    workflow=StateGraph(ConditionalState)
    workflow.add_node("获取同行列表",peer_node)
    workflow.add_node("补充同行PE",peer_financials_node)
    workflow.add_node("深分",deep_analysis)
    workflow.add_node("快分",quick_analysis)
    #注意到这里添加节点add_node时没有添加决策函数choose_path
    workflow.add_edge(START,"获取同行列表")
    workflow.add_edge("获取同行列表","补充同行PE")
    workflow.add_conditional_edges(
        "补充同行PE",
        choose_path,{
            "深度分析": "深分",#左边的“深度分析”是choose_path的返回值,右边的“深分”是add_node节点时定义的节点名称
            "快速评估":"快分"#左边的“快速评估”是choose_path的返回值，右边的“快分”是add_node节点时定义的节点名称
            # 为什么需要{choose_path的返回值,add_node时定义的节点名称}，原因在于当choose_path返回“深度分析”时，路由到名为“深分”的节点
        }
    )
    workflow.add_edge("深分",END)
    workflow.add_edge("快分",END)
    # workflow.add_node("获取同行业其他上市公司的PE",fetch_peer_ratios)
    # workflow.add_node("分析PE比率",analysis_pe_ratios)
    app=workflow.compile()
    result=app.invoke({"symbol":"NVDA"})
    print(result)# 这里直接print(result)还是一样会出现打印出一坨的问题。

# if __name__=="__main__":
#     conditional_workflow_with_agent() 

# 现在我们已经学习了LangGraph中State、Edge、node相关概念，并且学习了如何使用add_conditional_edges()。
# 接下来我们继续学习在LangGraph中循环与记忆。
def loop_with_memory():
    """
    循环+记忆：让Agent在每轮根据对话历史决定是否继续调用工具
    add_messages把每一轮的AI/工具回复自动拼接到messages里。
    should_continue根据是否存在tool_calls来跳回tools节点
    """
    class AgentState(TypedDict):
        # messages：使用add_messages，保留所有往返消息，形成“短期记忆”。
        messages:Annotated[list,add_messages]
        iteration:int

    @tool
    def fetch_profile(symbol:str)->dict:
        """
        获取公司信息
        参数：
            symbol为上市公司股票代码(比如"NVDA"/"AMD")
        返回：
            返回包括公司名称、行业、ipo时间、市值(百万美元)、官网、描述等内容的字典
        """
        return get_company_profile(symbol)
    
    @tool
    def fetch_financials(symbol:str)->dict:
        """
        获取公司财务信息
        参数：
            symbol为上市公司股票代码(比如"NVDA"/"AMD")
        返回：
            返回包含上市公司52周最高价、52周最低价、Beta系数、PE比率、毛利率等财务信息的字典
        """
        return get_financials_with_fallback(symbol)
    
    @tool
    def fetch_latest_news(symbol:str)->list:
        """
        获取公司最新一周的新闻
        参数：
            symbol为上市公司股票代码(比如"NVDA"/"AMD")
        返回：
            目标公司最新一周发生的新闻
        """
        from datetime import date,timedelta
        end=date.today()
        start=end-timedelta(days=7)
        return get_company_news(symbol,start.isoformat(),end.isoformat())
    
    tools=[fetch_financials,fetch_latest_news,fetch_profile]# 在上一个conditional_workflow_with_agent()例子中，尽管我们使用了@tool来定义工具函数，但是却没有使用统一将其装进一个列表tools，再使用ToolNode()方法，而是在节点函数中，通过工具函数名.invoke(state)方式进行调用，
    # 而这里将其装进一个列表tools，再使用ToolNode()方法
    tool_node=ToolNode(tools)
    # 之所以出现不同的方式，因为一个是手动调用，另一个是LLM自主决定
    # 在conditional_workflow_with_agent例子中，在节点函数中，直接工具函数名.invoke(state)直接确定工具调用顺序
    # 在本loop_with_memory例子中，把工具都放在一个tools列表里，打包给了tool_node,然后在agent_node中llm.bind_tools(tools)，让LLM看到用户问题后，自己决定调用哪些工具
    # 当然我们add_node节点的时候还需要add_node("tools",tool_node)
    # 本质上ToolNode是一个自动执行器，它会读取LLM的tool_calls，自动执行这些工具，把结果包装成ToolMessage添加到对话历史中

    # 读取对话历史，决定是否再调用工具或给出最终回答
    def agent_node(state:AgentState):
        messages=state["messages"]
        iteration=state.get("iteration",0)
        print(f"迭代{iteration+1}-Agent思考中(结合记忆长度={len(messages)})")
        # 为什么这里iteration+1，是因为我们开始在下面app.invoke里面的"iteration":0(即初始值为0)

        # 绑定工具后让LLM决定：是继续要数据(产生tool_calls)还是直接回答
        response=llm.bind_tools(tools).invoke(
            [SystemMessage(content="你是金融分析师，按需调用工具补全信息，信息够了就直接回答并停止调用工具")]
            +messages
        )
        return{
            #add_messages会把新消息append到列表，形成“循环记忆”
            "messages":[response],
            "iteration":iteration+1,
        }
    # 有tool_calls就跳到tools，达到上限或无调用则结束
    def should_continue(state:AgentState)->Literal["tools","end"]:
        last_message=state["messages"][-1]
        # 如果LLM产生工具调用，则继续循环
        if getattr(last_message,"tool_calls",None):
            print("需要调用工具，进入ToolNode再回来")
            return "tools"
        # 为防止无限循环，加一个迭代上限
        if state.get("iteration",0)>=4:
            print("达到迭代上限，强制结束")
            return "end"
        # 否则直接结束，输出最终回答
        print("没有工具调用，结束循环")
        return "end"
    
    # 开始构建图：agent→(判定)→tools→agent，形成闭环
    workflow=StateGraph(AgentState)
    workflow.add_node("agent",agent_node)
    workflow.add_node("tools",tool_node)
    workflow.add_edge(START,"agent")
    workflow.add_conditional_edges(
        "agent",
        should_continue,{
            "tools":"tools",
            "end":END,
        },
    )
    workflow.add_edge("tools","agent")# 工具执行后回到Agent，形成循环
    app=workflow.compile()

    # 测试：让Agent自己决定需要调用哪些真实函数
    question="请用最近7天新闻和基础财务数据给我总结一下NVDA的基本面要点，如果数据不足请先补全"
    result=app.invoke({
        "messages":[HumanMessage(content=question)],
        "iteration":0,
    })

    print("\n========= 对话回放（体现 memory） =========")
    for i,msg in enumerate(result["messages"]):
        if isinstance(msg,HumanMessage):
            print(f"用户:{msg.content}")
        elif isinstance(msg,AIMessage):
            if msg.content:
                print(f"\n AI:{msg.content}")

if __name__=="__main__":
    loop_with_memory()
    


    
 

    
    
        



