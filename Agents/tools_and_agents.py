from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
# from langchain.agents import AgentExecutor,create_tool_calling_agent  
# 最近的Langchain已经放弃了AgentExecutor和create_tool_calling_agent
# 推荐使用LangGraph
from langgraph.prebuilt import create_react_agent
# 在LangGraph1.0+版本中，create_react_agent已经被弃用，官方推荐使用create_tool_calling_agent作为替代方案。
from langgraph.prebuilt import create_tool_calling_agent# 我import create_tool_calling_agent 但是提示未存取
from langchain_core.prompts import ChatPromptTemplate
import os
from dotenv import load_dotenv
from fundamental_analyst import *



load_dotenv()
finnhub_api_key=os.getenv("FINNHUB_API_KEY")
finnhub_client=finnhub.Client(api_key=finnhub_api_key)
av_api_key = os.getenv("ALPHAVANTAGE_API_KEY")
fred_api_key=os.getenv("FRED_API_KEY")
fred_client=Fred(api_key=fred_api_key)

llm=ChatOpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    temperature=0.1,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    model="qwen-plus"
)

# task1：理解Tool是什么
def old_way():
    # 目前我是手动调用函数并格式化
    price=get_real_time_data("NVDA")
    profile=get_company_profile("NVDA")

    prompt=f"公司信息为{profile},价格{price},请为我分析"
    # 然后把Prompt传给LLM

# tool方式
# Langchain中Tool是被标准化的函数/API，要求：1.必须用@tool装饰器标记，2.输入参数要求写明类型注解(symbol:str)3.要么写显式docstring，要么在@tool("写介绍")
# 3.输出需要是结构化结果(如字符串、字典),方便Agent后续整理回答，具体完整规范如下：
@tool
# def tool_name(para1:Type1,para2:Type2)->ReturnType:
#     """
#     [必需]工具的描述 - 告诉LLM这个工具是干什么的

#     参数：
#         para1:[可选但推荐]参数说明
#         para2:[可选但推荐]参数说明
#     返回：
#         [可选但推荐]返回值说明
#     示例：
#         [可选]使用示例
#     """
#     # 必须有类型注释
#     # 必须有返回类型
#     # 必须有docstring或在装饰器中提供description
#     return actual_function(para1,para2)

# 将之前的get_company_profile_with_fallback(symbol:str)->dict改为tool
@tool
def get_company_profile_with_fallback(symbol:str)->str:
    """
    获取上市公司基本信息
    通过股票代码获取公司的名称、行业、ipo时间、市值、官网、描述等基本信息
    会自动在Finnhub和Alpha Vantage两个数据源之间切换以确保成功获取数据

    参数：
       symbol:股票代码(大写),例如"NVDA"、"BMNR"、"MU"
    
    返回：
        包含以下字段的字典：
        -名称:公司名称
        -行业：公司所属行业
        -ipo时间:公司IPO日期
        -市值:市值(百万美元)
        -官网:公司官网
        -描述:公司的描述
    """
    # 注意，这里只是调用原函数，不需要重写逻辑
    return get_company_profile_with_fallback(symbol)

"""
┌─────────────────────────────────────────┐
│ Agent 的工作流程:REAct=Reasoning+Acting+Observation             
├─────────────────────────────────────────┤
│                                         │
│  用户问题: "NVDA 是否值得投资？"         │
│      ↓                                  │
│  [1] Reasoning（推理）                  │
│      "我需要先了解宏观经济环境"          │
│      ↓                                  │
│  [2] Action（行动）                     │
│      调用 fetch_macro_data()             │
│      ↓                                  │
│  [3] Observation（观察）                │
│      "GDP增长2.8%, 利率4.5%..."         │
│      ↓                                  │
│  [1] Reasoning（推理）                  │
│      "现在我需要获取 NVDA 的信息"        │
│      ↓                                  │
│  [2] Action（行动）                     │
│      调用 fetch_company_profile("NVDA")  │
│      调用 fetch_real_time_data("NVDA")   │
│      ↓                                  │
│  [3] Observation（观察）                │
│      "NVDA 市值4.8万亿, 价格$135..."     │
│      ↓                                  │
│  [1] Reasoning（推理）                  │
│      "我已经有足够信息了，可以分析"      │
│      ↓                                  │
│  [最终回答]                              │
│  "综合宏观经济和公司数据..."            │
└─────────────────────────────────────────┘
"""


# 下面这种使用AgentExecutor和create_tool_calling_agent已经被Langchain所抛弃。
# def basic_agent_example():
#     # Agent：搭载LLM作为大脑，能自主决策、调用Tool完成复杂任务。
#     # 核心作用：替代人类手动判断需要调用什么函数、按什么顺序调用函数的过程

#     # 1.定义工具列表：告诉Agent有哪些工具可用，Agent只能从这个列表中选择工具(不会调用列表外的tool)
#     tools=[get_stock_price,get_pe_ratio,get_company_info]

#     # 2.定义prompt：告诉Agent身份、工具用法、思考方式
#     # {tools}自动渲染工具列表的描述，让Agent知道每个工具的用途
#     # {input}用户的问题
#     # {agent_scratchpad}核心占位符——存储Agent的思考过程和工具调用记录
#     prompt=ChatPromptTemplate.from_messages([
#         ("system", """你是投资助手。你有以下工具：{tools} 使用工具的格式：工具名称: 参数 当前对话历史：{chat_history}"""),
#                 ("human", "{input}"),
#         ("placeholder", "{agent_scratchpad}")  
#         ])
    
#     # 3.创建agent
#     # create_tool_calling_agent是Langchain专门用于 工具调用型Agent 的创建函数
#     agent=create_tool_calling_agent(llm,tools,prompt)

#     # 4.创建执行器AgentExecutor：接收用户输入，传给Agent→执行Agent的工具调用指令(调用tools的函数)
#     # →把工具返回结果回传给Agent，让Agent判断是否需要继续调用工具
#     agent_executor=AgentExecutor(
#         agent=agent,
#         tools=tools,
#         verbose=True,#verbose=True，会在控制台打印Agent的完整思考过程，方便调试
#     )

    # # 测试
    # result=agent_executor.invoke({# invoke方法的输入是字典
    #     "input": "NVDA的价格是多少？如果EPS是3.5，PE比率是多少？",# input 用户的核心需求
    #     "chat_history": []# 对话历史
    # })
    
    # print("\n最终回答：", result["output"])


"""
必问问题：

Q1: Tool和普通函数有什么区别？
A: "Tool是带类型标注和文档字符串的函数，LLM可以：
   1. 自动识别工具功能（通过docstring）
   2. 决定何时调用哪个工具
   3. 正确传递参数
   我用@tool装饰器包装数据获取函数，让Agent自动组合调用。"

Q2: Agent的工作原理是什么？
A: "Agent的核心是ReAct循环：
   1. Reasoning（推理）：分析当前任务，决定下一步
   2. Action（行动）：调用某个Tool
   3. Observation（观察）：获取Tool返回结果
   4. 重复1-3直到完成任务
   我的项目中，Agent会自动决定先查宏观数据还是先查个股数据。"

Q3: 你项目中为什么用Agent？
A: "因为投资分析是多步骤任务：
   1. 需要获取多个数据源
   2. 数据之间有依赖关系（先宏观后微观）
   3. 不同股票需要不同分析流程
   用Agent可以让AI自动规划最优路径，而不是硬编码流程。"

Q4: Agent有什么局限性？
A: "主要有三个：
   1. 成本高：每次推理都要调用LLM
   2. 不稳定：可能陷入死循环或调用错误工具
   3. 延迟高：多步推理需要时间
   我的解决方案：
   - 设置max_iterations防止死循环
   - 用verbose=True监控过程
   - 对高频任务用固定Chain代替Agent"

实战作业：
1. 将fundamental_analyst.py中所有get_xxx函数改造成@tool
2. 创建一个完整的投资分析Agent
3. 测试Agent是否能自动决定调用顺序
4. 记录一次完整的Agent执行日志，分析思考过程
5. 更新README，添加"Agent架构设计"章节
"""

# 接下来将之前的函数改造为Tool
@tool("获取股票对应供公司信息,输入参数为股票代码(如'NVDA'/'AAPL'),返回格式为字典")
def fetch_company_profile(symbol:str)->dict:
    return get_company_profile_with_fallback(symbol)# 但是这里我有一个问题，因为我的get_company_profile_with_fallback(symbol)函数里面内置了try except块，
# 我的问题是：如果获取失败了，返回的是print打印出来的字符串，但是这里要求返回的是dict字典，所以不行，应该把print都删除，直接except里面return字典？
# A：with_fallback返回的是字典，只是有些中间过程的print语句
# 返回的字典内容如下：
#             '金融数据源来源':'Finnhub',
#             '名称':profile.get('name'),
#             '行业':profile.get('finnhubIndustry'),
#             'ipo时间':profile.get('ipo'),
#             '市值(百万美元)':profile.get('marketCapitalization'),
#             '官网':profile.get('weburl'),
#             '描述':profile.get('description'),


@tool("获取股票数据,输入参数为股票代码(如'NVDA'/'AAPL'),返回格式为字典")
def fetch_real_time_data(symbol:str)->dict:
    return get_real_time_data_with_fallback(symbol)
# 返回的字典内容如下：
            # 'source': 'Finnhub',
            # "最新成交价": real_time_data.get('c'),
            # "当日最高价": real_time_data.get('h'),
            # "当日最低价": real_time_data.get('l'),
            # "当日开盘价": real_time_data.get('o'),
            # "前一个交易日的收盘价": real_time_data.get('pc'),
            # "上述数据的更新时间": formatted_local_time

@tool("获取美国宏观经济数据,输入参数为股票代码(如'NVDA'/'AAPL'),返回格式为字典")
# def fetch_macro_economic_data(symbol:str)->dict:# 这里不需要输入参数
def fetch_macro_economic_data()->dict:
    return get_macro_economic_data()

# 将之前的函数改造为tool之后，尝试做一个投资分析Agent
def invest_analyze_agent():

    # 定义工具列表
    tools=[fetch_company_profile,fetch_real_time_data,fetch_macro_economic_data]
    # 定义prompt
    prompt=ChatPromptTemplate.from_messages([
        ("system","""
         你的身份是一名顶级对冲基金经理，擅长通过结合美国宏观经济分析与微观个股数据来进行投资决策。你有以下工具：{tools}
         使用工具的格式：
         工具名称：参数
         当前对话历史：{chat_history}
         分析步骤建议：
         1. 先使用 fetch_macro_economic_data 获取宏观经济数据，了解当前经济环境
         2. 再使用 fetch_company_profile 和 fetch_real_time_data 获取具体股票信息
         3. 综合宏观和微观数据，给出投资建议
         """),("human","{input}"),("placeholder","{agent_scratchpad}")
    ])
    # 创建Agent
    # agent=create_tool_calling_agent(llm,tools,prompt)

    # # 创建Agent执行器
    # agent_executor=AgentExecutor(
    #     agent=agent,
    #     tools=tools,
    #     verbose=True,# 输出思考过程
    #     max_iterations=10,#防止死循环
    #     handle_parsing_errors=True# 优雅处理解析错误
    # )
    # result=agent_executor.invoke({"input":"现在美国经济如何？如果按照目前英伟达的财务指标以及当前的价格进行投资，是否划算？",
    #                               "chat_history":[]
    #                               })
    # print("最终分析结果：",result["output"])

    #现在我已经在原代码的基础上删除了def fetch_macro_economic_data()->dict参数，
    # 并且修改了prompt中("human","{input}")语法，
    # 但是Claude给我提供的教程里的AgentExecutor()、create_tool_calling_agent这几个方法随着Langchain的版本更新不能继续使用了
    # 因此我让Claude Code重新提交了一版教程

# if __name__=="__main__":
#     invest_analyze_agent()


