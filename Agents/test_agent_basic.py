"""
简化的 Agent 测试 - 不需要真实 API keys
用于测试 Agent 的基本功能和工具调用机制
"""

from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent
import os


# 模拟的 LLM（如果没有真实 API key）
# 如果有真实的 API key，可以取消注释下面的代码
# from dotenv import load_dotenv
# load_dotenv()
# llm = ChatOpenAI(
#     api_key=os.getenv("DASHSCOPE_API_KEY"),
#     temperature=0.1,
#     base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
#     model="qwen-plus"
# )

# 使用环境变量或默认值
try:
    llm = ChatOpenAI(
        api_key=os.getenv("OPENAI_API_KEY", "sk-test"),  # 使用真实的 API key
        temperature=0.1,
        model="gpt-3.5-turbo"
    )
except:
    print("警告：未配置 LLM，请设置 OPENAI_API_KEY 或其他 LLM 配置")
    exit(1)


# ========== 模拟工具定义 ==========

@tool
def get_company_info(symbol: str) -> str:
    """
    获取公司基本信息

    参数:
        symbol: 股票代码（如 'NVDA', 'AAPL'）

    返回:
        包含公司基本信息的字符串
    """
    # 模拟数据
    mock_data = {
        "NVDA": "英伟达（NVIDIA）是一家半导体公司，市值约4.8万亿美元，主要业务为GPU和AI芯片",
        "AAPL": "苹果公司（Apple）是一家科技巨头，市值约3.5万亿美元，主要业务为iPhone、Mac等产品",
        "TSLA": "特斯拉（Tesla）是一家电动车公司，市值约800亿美元，主要业务为电动汽车和能源存储"
    }
    return mock_data.get(symbol.upper(), f"{symbol}的公司信息暂时无法获取")


@tool
def get_stock_price(symbol: str) -> str:
    """
    获取股票当前价格

    参数:
        symbol: 股票代码（如 'NVDA', 'AAPL'）

    返回:
        包含股票价格的字符串
    """
    # 模拟数据
    mock_prices = {
        "NVDA": "当前价格: $135.50, 52周最高: $152.89, 52周最低: $39.23",
        "AAPL": "当前价格: $195.71, 52周最高: $198.23, 52周最低: $164.08",
        "TSLA": "当前价格: $242.84, 52周最高: $299.29, 52周最低: $138.80"
    }
    return mock_prices.get(symbol.upper(), f"{symbol}的价格信息暂时无法获取")


@tool
def get_pe_ratio(price: float, eps: float) -> str:
    """
    计算 PE 比率

    参数:
        price: 股票价格
        eps: 每股收益

    返回:
        PE 比率的字符串表示
    """
    if eps == 0:
        return "无法计算PE比率（EPS为0）"
    pe = price / eps
    return f"PE比率为 {pe:.2f}"


@tool
def get_macro_economic_data() -> str:
    """
    获取美国宏观经济数据

    注意: 此函数不需要输入参数

    返回:
        包含宏观经济指标的字符串
    """
    return """
    美国宏观经济数据（模拟）：
    - 联邦基金利率: 4.50%-4.75%
    - CPI同比: 3.2%
    - 失业率: 3.7%
    - GDP增长率: 2.8%
    - 非农就业人数变化: +150K
    """


# ========== Agent 示例 ==========

def test_basic_agent():
    """测试基本的 Agent 功能"""

    print("="*70)
    print("🧪 测试 1: 基本工具调用")
    print("="*70)

    # 定义工具列表
    tools = [get_stock_price, get_pe_ratio, get_company_info]

    # 系统提示词
    system_message = """你是一个投资助手。

你可以使用以下工具：
- get_stock_price(symbol): 获取股票价格
- get_pe_ratio(price, eps): 计算PE比率
- get_company_info(symbol): 获取公司基本信息

请根据用户的问题，选择合适的工具来回答。"""

    # 创建 Agent
    agent = create_react_agent(
        model=llm,
        tools=tools,
        state_modifier=system_message
    )

    # 测试问题
    question = "NVDA的价格是多少？如果EPS是3.5，PE比率是多少？"
    print(f"\n📝 用户问题: {question}\n")

    try:
        # 调用 Agent
        result = agent.invoke({
            "messages": [HumanMessage(content=question)]
        })

        # 提取最终回答
        final_message = result["messages"][-1]
        print("\n" + "="*70)
        print("✅ Agent 回答:")
        print("="*70)
        print(final_message.content)
        print("="*70 + "\n")
    except Exception as e:
        print(f"\n❌ 错误: {e}\n")


def test_investment_agent():
    """测试投资分析 Agent"""

    print("="*70)
    print("🧪 测试 2: 投资分析 Agent")
    print("="*70)

    # 定义工具列表
    tools = [get_company_info, get_stock_price, get_macro_economic_data]

    # 系统提示词
    system_message = """你是一名顶级对冲基金经理，擅长通过结合宏观经济分析与微观个股数据来进行投资决策。

你有以下工具可以使用：
- get_company_info(symbol): 获取公司基本信息
- get_stock_price(symbol): 获取股票价格数据
- get_macro_economic_data(): 获取美国宏观经济数据（无需参数）

分析步骤建议：
1. 先使用 get_macro_economic_data 获取宏观经济数据
2. 再使用 get_company_info 和 get_stock_price 获取具体股票信息
3. 综合分析后给出投资建议

请一步步思考，使用合适的工具获取数据后再进行分析。"""

    # 创建 Agent
    agent = create_react_agent(
        model=llm,
        tools=tools,
        state_modifier=system_message
    )

    # 测试问题
    question = "现在美国经济如何？英伟达（NVDA）是否值得投资？"
    print(f"\n📝 用户问题: {question}\n")

    try:
        # 调用 Agent
        result = agent.invoke({
            "messages": [HumanMessage(content=question)]
        })

        # 提取并显示思考过程
        print("\n⚙️  Agent 思考与工具调用过程:\n")
        for i, msg in enumerate(result["messages"]):
            if isinstance(msg, HumanMessage):
                print(f"👤 用户: {msg.content}")
            elif hasattr(msg, 'tool_calls') and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    print(f"\n🔧 Agent 调用工具: {tool_call['name']}")
                    print(f"   参数: {tool_call['args']}")

        # 最终回答
        final_message = result["messages"][-1]
        print("\n" + "="*70)
        print("📊 最终分析结果:")
        print("="*70)
        print(final_message.content)
        print("="*70 + "\n")
    except Exception as e:
        print(f"\n❌ 错误: {e}\n")


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                   Langchain Agent 基础测试                        ║
║                                                                  ║
║  这是一个简化的测试版本，使用模拟数据而不是真实 API            ║
║  用于验证 Agent 的工具调用机制是否正常工作                      ║
╚══════════════════════════════════════════════════════════════════╝
    """)

    # 运行测试
    test_basic_agent()
    print("\n" + "="*70 + "\n")
    test_investment_agent()

    print("""
✅ 测试完成！

如果上述测试成功运行，说明：
1. ✅ Tool 定义正确
2. ✅ Agent 可以正确调用工具
3. ✅ LangGraph API 使用正确

下一步：
1. 配置真实的 API keys（创建 .env 文件）
2. 运行完整版本的 tools_and_agents.py
3. 查看 AGENT_TUTORIAL.md 了解更多详情
    """)
