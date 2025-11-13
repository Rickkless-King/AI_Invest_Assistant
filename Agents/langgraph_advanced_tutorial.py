# ============================================================================
# Week 5-6: LangGraph核心教程（2025年最新版本）
# 基于LangGraph 1.0+ 和 LangChain 1.0+
# 作者：Claude
# 更新日期：2025年1月
# ============================================================================

"""
本教程涵盖：
1. LangGraph基础：State、Graph、Node、Edge
2. 条件分支与循环
3. 多Agent对话（Supervisor模式、Router模式、Network模式）
4. 投资分析系统实战

前置要求：
- 已完成Week 1-4的LCEL学习
- 已掌握@tool装饰器和create_agent的用法
- 已配置好finnhub、alpha_vantage等API
"""

from typing import TypedDict, Annotated, Literal
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages  # ⭐ 2025新版本推荐导入
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent  # ⭐ 2025新版本推荐使用
import os
from dotenv import load_dotenv
import operator

load_dotenv()

llm = ChatOpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    model="qwen-plus",
    temperature=0.1
)

# ============================================================================
# Day 15-16: 理解State（状态）- 2025最新版本
# ============================================================================

"""
State是LangGraph的核心概念，它是整个Graph执行过程中的"共享内存"

⭐ 2025年推荐的State定义方式：
1. 使用TypedDict定义结构
2. 使用Annotated[type, reducer]定义更新策略
3. 消息列表使用add_messages作为reducer
"""

# ❌ 旧版本写法（不推荐）
class OldInvestmentState(TypedDict):
    symbol: str
    macro_data: dict
    company_data: dict
    messages: Annotated[list, "消息历史"]  # ❌ 字符串注解已过时

# ✅ 2025推荐写法
class InvestmentState(TypedDict):
    """投资分析流程的状态"""
    symbol: str  # 用户输入的股票代码
    macro_data: dict  # 宏观经济数据
    company_data: dict  # 公司数据
    analysis: str  # 分析结果
    recommendation: str  # 投资建议
    messages: Annotated[list, add_messages]  # ⭐ 使用add_messages reducer
    # add_messages会自动将新消息追加到列表，而不是覆盖


# ============================================================================
# Day 17-18: 创建第一个Graph - 最简单的例子
# ============================================================================

def simple_graph_example():
    """最简单的LangGraph示例 - 理解Node和Edge"""

    print("="*50)
    print("示例1：最简单的Graph")
    print("="*50)

    # 1. 定义状态
    class SimpleState(TypedDict):
        input: str
        output: str

    # 2. 定义节点（每个节点是一个函数）
    def step1(state: SimpleState):
        """节点1：处理输入"""
        print(f"✓ 步骤1：收到输入 '{state['input']}'")
        return {"output": "处理中..."}

    def step2(state: SimpleState):
        """节点2：生成输出"""
        print(f"✓ 步骤2：基于 '{state['input']}' 生成结果")
        return {"output": f"已完成对 {state['input']} 的分析"}

    # 3. 构建图
    workflow = StateGraph(SimpleState)

    # 4. 添加节点
    workflow.add_node("处理", step1)
    workflow.add_node("生成", step2)

    # 5. 定义流程：START → 处理 → 生成 → END
    workflow.add_edge(START, "处理")  # ⭐ 2025推荐使用START常量
    workflow.add_edge("处理", "生成")
    workflow.add_edge("生成", END)

    # 6. 编译
    app = workflow.compile()

    # 7. 执行
    result = app.invoke({"input": "NVDA"})
    print("\n最终结果：", result)
    print("\n")


# ============================================================================
# Day 19-20: 实战 - 投资分析工作流（基础版）
# ============================================================================

def investment_workflow_basic():
    """完整的投资分析LangGraph - 使用真实的金融数据工具"""

    print("="*50)
    print("示例2：投资分析工作流（基础版）")
    print("="*50)

    # 定义简化的工具
    @tool
    def fetch_macro(symbol: str) -> dict:
        """获取宏观经济数据"""
        return {
            "fed_rate": "4.0%-4.25%",
            "cpi": 3.01,
            "unemployment": 4.0
        }

    @tool
    def fetch_company(symbol: str) -> dict:
        """获取公司数据"""
        # 这里可以接入你的get_company_profile_with_fallback函数
        return {
            "name": "NVIDIA",
            "price": 186.5,
            "pe": 52.0
        }

    # 节点1：获取宏观数据
    def get_macro_node(state: InvestmentState):
        print("🌍 正在获取宏观数据...")
        macro = fetch_macro.invoke(state["symbol"])
        return {"macro_data": macro}

    # 节点2：获取公司数据
    def get_company_node(state: InvestmentState):
        print("🏢 正在获取公司数据...")
        company = fetch_company.invoke(state["symbol"])
        return {"company_data": company}

    # 节点3：分析估值
    def analyze_node(state: InvestmentState):
        print("📊 正在分析...")

        prompt = f"""
基于以下数据分析{state['symbol']}：

宏观环境：
- 联邦利率：{state['macro_data']['fed_rate']}
- CPI：{state['macro_data']['cpi']}%

公司数据：
- 当前价格：${state['company_data']['price']}
- PE比率：{state['company_data']['pe']}

请判断估值水平（高估/合理/低估），限50字以内
"""

        analysis = llm.invoke(prompt).content
        return {"analysis": analysis}

    # 节点4：生成建议
    def recommend_node(state: InvestmentState):
        print("💡 正在生成建议...")

        prompt = f"""
基于分析：{state['analysis']}

给出明确的投资建议（买入/持有/卖出），限30字以内
"""

        recommendation = llm.invoke(prompt).content
        return {"recommendation": recommendation}

    # 构建图
    workflow = StateGraph(InvestmentState)

    # 添加所有节点
    workflow.add_node("获取宏观", get_macro_node)
    workflow.add_node("获取公司", get_company_node)
    workflow.add_node("分析", analyze_node)
    workflow.add_node("建议", recommend_node)

    # 定义流程
    workflow.add_edge(START, "获取宏观")
    workflow.add_edge("获取宏观", "获取公司")
    workflow.add_edge("获取公司", "分析")
    workflow.add_edge("分析", "建议")
    workflow.add_edge("建议", END)

    # 编译并执行
    app = workflow.compile()

    result = app.invoke({"symbol": "NVDA"})

    print("\n" + "="*50)
    print("📋 最终报告")
    print("="*50)
    print(f"股票：{result['symbol']}")
    print(f"\n分析：\n{result['analysis']}")
    print(f"\n建议：\n{result['recommendation']}")
    print("\n")


# ============================================================================
# Day 21-22: 条件分支 - 根据不同情况走不同路径
# ============================================================================

def conditional_workflow():
    """学习条件路由 - 高PE和低PE走不同分析路径"""

    print("="*50)
    print("示例3：条件分支 - 高PE深度分析 vs 低PE快速评估")
    print("="*50)

    class AnalysisState(TypedDict):
        symbol: str
        price: float
        pe_ratio: float
        output: str

    # 节点：获取数据
    def fetch_data(state: AnalysisState):
        # 模拟获取数据
        print(f"📥 获取{state['symbol']}数据...")
        return {
            "price": state.get("price", 186.5),
            "pe_ratio": state.get("pe_ratio", 52.0)
        }

    # ⭐ 决策函数：根据PE比率决定路线
    def should_deep_dive(state: AnalysisState) -> Literal["深度分析", "快速评估"]:
        """高PE需要深度分析，低PE快速评估"""
        if state["pe_ratio"] > 50:
            print(f"⚠️  PE={state['pe_ratio']} > 50，进入深度分析路径")
            return "深度分析"
        else:
            print(f"✓ PE={state['pe_ratio']} ≤ 50，进入快速评估路径")
            return "快速评估"

    # 两条不同的分析路径
    def deep_analysis(state: AnalysisState):
        print("🔬 执行深度分析...")
        return {"output": f"{state['symbol']} PE过高({state['pe_ratio']}x)，需警惕泡沫风险"}

    def quick_analysis(state: AnalysisState):
        print("⚡ 执行快速评估...")
        return {"output": f"{state['symbol']} PE合理({state['pe_ratio']}x)，估值健康"}

    # 构建图
    workflow = StateGraph(AnalysisState)

    workflow.add_node("获取数据", fetch_data)
    workflow.add_node("深度分析", deep_analysis)
    workflow.add_node("快速评估", quick_analysis)

    workflow.add_edge(START, "获取数据")

    # ⭐ 关键：条件分支
    workflow.add_conditional_edges(
        "获取数据",
        should_deep_dive,  # 决策函数
        {
            "深度分析": "深度分析",
            "快速评估": "快速评估"
        }
    )

    workflow.add_edge("深度分析", END)
    workflow.add_edge("快速评估", END)

    app = workflow.compile()

    # 测试高PE股票（NVDA）
    print("\n[测试1] NVDA（高PE）：")
    result1 = app.invoke({"symbol": "NVDA", "pe_ratio": 52.0})
    print(f"结果：{result1['output']}\n")

    # 测试低PE股票（INTC）
    print("[测试2] INTC（低PE）：")
    result2 = app.invoke({"symbol": "INTC", "pe_ratio": 15.0})
    print(f"结果：{result2['output']}\n")


# ============================================================================
# Day 23-24: 循环和Memory - Agent模式
# ============================================================================

def loop_with_memory():
    """学习循环节点 - Agent可以多次调用工具直到完成任务"""

    print("="*50)
    print("示例4：循环与Memory - Agent自动决定调用次数")
    print("="*50)

    class AgentState(TypedDict):
        messages: Annotated[list, add_messages]  # ⭐ 使用add_messages
        iteration: int

    # 定义工具
    @tool
    def search_data(query: str) -> str:
        """搜索财务数据"""
        print(f"  🔍 搜索：{query}")
        return f"找到关于{query}的数据：PE=52, EPS=$3.5"

    @tool
    def calculate(expression: str) -> str:
        """计算数值"""
        print(f"  🧮 计算：{expression}")
        # 简化计算：52 * 3.5 = 182
        return "182"

    tools = [search_data, calculate]
    tool_node = ToolNode(tools)

    # Agent节点：决定下一步行动
    def agent_node(state: AgentState):
        messages = state["messages"]
        iteration = state.get("iteration", 0)

        print(f"\n[迭代 {iteration + 1}] Agent思考中...")

        # LLM决定使用哪个工具
        response = llm.bind_tools(tools).invoke(messages)

        return {
            "messages": [response],
            "iteration": iteration + 1
        }

    # ⭐ 决策：继续还是结束
    def should_continue(state: AgentState) -> Literal["tools", "end"]:
        last_message = state["messages"][-1]

        # 如果LLM返回了工具调用，继续
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            print("  → 需要调用工具，继续循环")
            return "tools"
        # 否则结束
        print("  → 任务完成，结束循环")
        return "end"

    # 构建图
    workflow = StateGraph(AgentState)

    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tool_node)

    workflow.add_edge(START, "agent")

    # ⭐ 循环结构
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": END
        }
    )

    workflow.add_edge("tools", "agent")  # 工具执行后回到agent

    app = workflow.compile()

    # 测试
    print("\n[用户问题]")
    question = "NVDA的PE是多少？如果EPS是3.5，合理价格应该是多少？"
    print(f"Q: {question}")

    result = app.invoke({
        "messages": [HumanMessage(content=question)],
        "iteration": 0
    })

    print("\n" + "="*50)
    print("📝 对话历史：")
    print("="*50)
    for i, msg in enumerate(result["messages"]):
        if isinstance(msg, HumanMessage):
            print(f"\n👤 用户: {msg.content}")
        elif isinstance(msg, AIMessage):
            if msg.content:
                print(f"\n🤖 AI: {msg.content}")
    print("\n")


# ============================================================================
# Day 25-28: 多Agent对话 - Supervisor模式（重点！）
# ============================================================================

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


# ============================================================================
# Day 29-30: 完整投资分析系统架构设计
# ============================================================================

def complete_investment_system_architecture():
    """
    展示完整的投资分析系统架构

    这是你的最终目标架构：
    """

    architecture = """
╔═══════════════════════════════════════════════════════════════╗
║           AI投资助手系统 - 多Agent协作架构                     ║
╚═══════════════════════════════════════════════════════════════╝

1. 用户输入：股票代码（如"NVDA"）
   │
   ▼
2. Supervisor（投资分析主管）
   │   - 理解用户意图
   │   - 规划分析流程
   │   - 协调各专家Agent
   │
   ├──────────┬──────────┬──────────┬──────────┐
   ▼          ▼          ▼          ▼          ▼
3. 专家Agent团队：
   │
   ├─ 宏观经济分析师
   │    ├─ Tool: fetch_macro_data()
   │    └─ 分析利率、通胀、就业、GDP
   │
   ├─ 基本面分析师
   │    ├─ Tool: fetch_company_profile()
   │    ├─ Tool: fetch_financials()
   │    └─ 分析公司业务、财务状况
   │
   ├─ 技术分析师
   │    ├─ Tool: fetch_price_data()
   │    ├─ Tool: calculate_indicators()
   │    └─ 分析价格趋势、技术指标
   │
   ├─ 估值分析师
   │    ├─ Tool: calculate_valuation()
   │    └─ 判断高估/低估
   │
   └─ 风险管理师
        ├─ Tool: assess_risk()
        └─ 评估投资风险
   │
   ▼
4. 结果汇总Agent
   │   - 整合各专家意见
   │   - 生成综合报告
   │
   ▼
5. 输出：投资建议报告
   ├─ 宏观环境评分
   ├─ 公司基本面评分
   ├─ 技术面信号
   ├─ 估值水平
   ├─ 风险评估
   └─ 最终建议（买入/持有/卖出）

═══════════════════════════════════════════════════════════════

核心优势：
✓ 模块化：每个Agent专注自己的领域
✓ 可扩展：轻松添加新的专家Agent
✓ 容错性：某个Agent失败不影响整体
✓ 可追溯：记录每个Agent的分析过程
✓ 并行执行：多个Agent可以同时工作

下一步实现：
1. 完善各专家Agent的工具函数（使用你已有的get_xxx函数）
2. 实现结果汇总逻辑
3. 添加流式输出，实时显示分析进度
4. 集成到Streamlit界面
"""

    print(architecture)


# ============================================================================
# 运行所有示例
# ============================================================================

if __name__ == "__main__":
    print("\n" + "🎓"*30)
    print("  LangGraph核心教程 - 2025最新版")
    print("🎓"*30 + "\n")

    # Day 15-16
    simple_graph_example()

    # Day 19-20
    investment_workflow_basic()

    # Day 21-22
    conditional_workflow()

    # Day 23-24
    loop_with_memory()

    # Day 25-28: 多Agent对话（重点！）
    multi_agent_supervisor()

    # Day 29-30: 完整架构
    complete_investment_system_architecture()

    print("\n" + "="*70)
    print("✅ 教程完成！")
    print("="*70)
    print("""
下一步学习路径：

Week 7-8: 高级特性
├─ Checkpointing（保存和恢复状态）
├─ Human-in-the-loop（需要人工确认）
├─ 并行执行多个节点
└─ 流式输出优化

Week 9-10: 生产环境部署
├─ LangSmith追踪和调试
├─ 错误处理和重试机制
├─ 性能优化
└─ Docker容器化

实战项目：
1. 完善tools_and_agents.py，添加更多专家Agent
2. 实现多Agent并行分析不同股票
3. 添加历史对话记忆功能
4. 集成到Streamlit创建Web界面

面试必问：
Q: LangGraph和普通函数调用有什么区别？
A: LangGraph提供状态管理、可视化、可恢复性、条件分支等高级功能

Q: 什么时候用单Agent，什么时候用多Agent？
A: 简单任务用单Agent，复杂任务需要专业分工时用多Agent

Q: Supervisor模式的优缺点？
A: 优点是集中控制、易于理解；缺点是Supervisor可能成为瓶颈

Q: 如何避免Agent死循环？
A: 设置max_iterations限制，添加明确的终止条件

加油！你已经掌握了LangGraph的核心概念，现在可以构建企业级的AI Agent系统了！
""")


# ============================================================================
# 附录：2025年LangGraph核心API速查表
# ============================================================================

"""
⭐ 2025年LangGraph核心API速查表

1. 导入
   from langgraph.graph import StateGraph, START, END
   from langgraph.graph.message import add_messages
   from langchain.agents import create_agent  # 替代旧的create_react_agent

2. 定义状态
   class State(TypedDict):
       field: type
       messages: Annotated[list, add_messages]  # 消息列表必须这样定义

3. 创建图
   workflow = StateGraph(State)

4. 添加节点
   workflow.add_node("name", function)

5. 添加边
   workflow.add_edge(START, "node1")           # 起始边
   workflow.add_edge("node1", "node2")         # 普通边
   workflow.add_edge("node2", END)             # 结束边

6. 添加条件边
   workflow.add_conditional_edges(
       "source_node",
       decision_function,  # 返回 Literal["option1", "option2", ...]
       {
           "option1": "target_node1",
           "option2": "target_node2",
       }
   )

7. 编译和运行
   app = workflow.compile()
   result = app.invoke(initial_state)

8. 流式输出
   for chunk in app.stream(initial_state, stream_mode="values"):
       print(chunk)

9. 创建Agent（2025新API）
   from langchain.agents import create_agent

   agent = create_agent(
       model=llm,
       tools=[tool1, tool2],
       system_prompt="你的提示词"
   )

重要变化：
❌ 不再使用：from langgraph.prebuilt import create_react_agent
✅ 现在使用：from langchain.agents import create_agent

❌ 不再使用：messages: Annotated[list, "消息历史"]
✅ 现在使用：messages: Annotated[list, add_messages]

❌ 不再使用：workflow.set_entry_point("node")
✅ 现在使用：workflow.add_edge(START, "node")
"""
