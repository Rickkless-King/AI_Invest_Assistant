from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.prebuilt import create_react_agent
import os
from dotenv import load_dotenv
from fundamental_analyst import *


load_dotenv()
finnhub_api_key = os.getenv("FINNHUB_API_KEY")
finnhub_client = finnhub.Client(api_key=finnhub_api_key)
av_api_key = os.getenv("ALPHAVANTAGE_API_KEY")
fred_api_key = os.getenv("FRED_API_KEY")
fred_client = Fred(api_key=fred_api_key)

llm = ChatOpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    temperature=0.1,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    model="qwen-plus"
)


# task1：理解Tool是什么
def old_way():
    # 目前我是手动调用函数并格式化
    price = get_real_time_data("NVDA")
    profile = get_company_profile("NVDA")

    prompt = f"公司信息为{profile},价格{price},请为我分析"
    # 然后把Prompt传给LLM


# tool方式
# Langchain中Tool是被标准化的函数/API，要求：1.必须用@tool装饰器标记，Langchain会自动生成工具描述。2.输入参数要求写明类型注解(symbol:str)
# 3.输出需要是结构化结果(如字符串、字典),方便Agent后续整理回答
@tool
def get_company_info(symbol: str) -> str:
    """获取公司基本信息"""
    return f"{symbol}是一家半导体公司，市值4.8T"


# 进阶用法：可给工具加自定义描述来让Agent更容易理解
@tool("获取股票当前价格,输入参数为股票代码(如'NVDA'/'AAPL'),返回格式为字符串")
def get_stock_price(symbol: str) -> str:
    """获取股票当前价格"""
    return f"{symbol}当前价格为199.5美元"


@tool
def get_pe_ratio(price: float, eps: float) -> str:
    """计算PE比率"""
    pe = price / eps
    return f"PE比率为{pe:.2f}"


# 接下来演示tool，创建你的第一个agent
def basic_agent_example():
    """
    Agent示例 - 使用 LangGraph 创建

    Agent：搭载LLM作为大脑，能自主决策、调用Tool完成复杂任务。
    核心作用：替代人类手动判断需要调用什么函数、按什么顺序调用函数的过程
    """

    # 1.定义工具列表：告诉Agent有哪些工具可用，Agent只能从这个列表中选择工具(不会调用列表外的tool)
    tools = [get_stock_price, get_pe_ratio, get_company_info]

    # 2.定义系统提示词
    system_message = """你是投资助手。

你可以使用以下工具来帮助用户：
- get_stock_price: 获取股票当前价格
- get_pe_ratio: 计算PE比率
- get_company_info: 获取公司基本信息

请根据用户的问题，选择合适的工具来回答。"""

    # 3.使用 LangGraph 创建 ReAct agent
    # create_react_agent 自动处理工具调用循环
    agent_executor = create_react_agent(
        model=llm,
        tools=tools,
        state_modifier=system_message  # 系统提示词
    )

    # 4.测试
    user_input = "NVDA的价格是多少？如果EPS是3.5，PE比率是多少？"
    print(f"\n用户问题: {user_input}\n")

    # invoke 返回一个包含消息列表的字典
    result = agent_executor.invoke({
        "messages": [HumanMessage(content=user_input)]
    })

    # 提取最终回答（最后一条 AI 消息）
    final_message = result["messages"][-1]
    print("\n" + "="*50)
    print("最终回答：", final_message.content)
    print("="*50)


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
@tool
def fetch_company_profile(symbol: str) -> dict:
    """
    获取股票对应公司信息

    输入参数:
        symbol: 股票代码(如'NVDA'/'AAPL')

    返回格式:
        包含公司基本信息的字典，包括名称、行业、市值等
    """
    return get_company_profile_with_fallback(symbol)


@tool
def fetch_real_time_data(symbol: str) -> dict:
    """
    获取股票实时数据

    输入参数:
        symbol: 股票代码(如'NVDA'/'AAPL')

    返回格式:
        包含股票价格数据的字典，包括最新成交价、最高价、最低价等
    """
    return get_real_time_data_with_fallback(symbol)


@tool
def fetch_macro_economic_data() -> dict:
    """
    获取美国宏观经济数据

    返回格式:
        包含宏观经济指标的字典，包括汇率、利率、就业数据、通胀数据、GDP数据等

    注意: 此函数不需要输入参数，返回最新的美国宏观经济数据
    """
    return get_macro_economic_data()


# 将之前的函数改造为tool之后，尝试做一个投资分析Agent
def invest_analyze_agent():
    """
    投资分析Agent - 使用 LangGraph 创建
    结合宏观经济与微观个股数据进行分析
    """

    # 定义工具列表
    tools = [fetch_company_profile, fetch_real_time_data, fetch_macro_economic_data]

    # 定义系统提示词
    system_message = """你的身份是一名顶级对冲基金经理，擅长通过结合美国宏观经济分析与微观个股数据来进行投资决策。

你有以下工具可以使用：
- fetch_company_profile(symbol): 获取公司基本信息（名称、行业、市值等）
- fetch_real_time_data(symbol): 获取股票实时价格数据
- fetch_macro_economic_data(): 获取美国宏观经济数据（无需参数）

分析步骤建议：
1. 先使用 fetch_macro_economic_data 获取宏观经济数据，了解当前经济环境
2. 再使用 fetch_company_profile 和 fetch_real_time_data 获取具体股票信息（需要提供股票代码如 'NVDA'）
3. 综合宏观和微观数据，给出投资建议

请一步步思考，使用合适的工具获取数据后再进行分析。"""

    # 使用 LangGraph 创建 ReAct agent
    agent_executor = create_react_agent(
        model=llm,
        tools=tools,
        state_modifier=system_message
    )

    # 用户问题
    user_question = "现在美国经济如何？如果按照目前英伟达的财务指标以及当前的价格进行投资，是否划算？"

    print("="*70)
    print("🤖 投资分析 Agent 开始工作...")
    print("="*70)
    print(f"\n📝 用户问题: {user_question}\n")
    print("="*70)
    print("\n⚙️  Agent 思考与工具调用过程:\n")

    # 调用 agent
    result = agent_executor.invoke({
        "messages": [HumanMessage(content=user_question)]
    })

    # 打印所有消息以显示思考过程
    for i, msg in enumerate(result["messages"]):
        if isinstance(msg, HumanMessage):
            print(f"\n👤 用户: {msg.content}")
        elif isinstance(msg, AIMessage):
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                # AI 调用工具
                for tool_call in msg.tool_calls:
                    print(f"\n🔧 Agent 调用工具: {tool_call['name']}")
                    print(f"   参数: {tool_call['args']}")
            elif msg.content:
                # AI 的最终回答或中间思考
                if i == len(result["messages"]) - 1:
                    # 最后一条消息是最终答案
                    print("\n" + "="*70)
                    print("📊 最终分析结果:")
                    print("="*70)
                    print(f"\n{msg.content}\n")
                    print("="*70)
                else:
                    print(f"\n💭 Agent 思考: {msg.content}")

    print("\n✅ 分析完成！\n")


if __name__ == "__main__":
    print("开始运行投资分析Agent...")
    print("="*50)
    invest_analyze_agent()
