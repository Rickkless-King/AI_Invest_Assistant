# LangGraph多Agent教程 - 快速开始指南

## 🚀 5分钟快速体验

### 第一步：检查依赖

确保你已经安装了必要的包：

```bash
pip install langgraph langchain langchain-openai
```

如果缺少，运行：
```bash
pip install -r requirements.txt
```

---

### 第二步：运行完整教程

```bash
cd /home/user/AI_Invest_Assistant
python Agents/langgraph_advanced_tutorial.py
```

**你会看到5个示例依次运行：**

1. ✅ **示例1：最简单的Graph**
   - 理解Node和Edge的基本概念
   - 看到数据如何在节点间流动

2. ✅ **示例2：投资分析工作流**
   - 完整的投资分析流程
   - 看到LLM如何生成分析和建议

3. ✅ **示例3：条件分支**
   - 高PE走深度分析
   - 低PE走快速评估
   - 理解如何根据数据做决策

4. ✅ **示例4：循环与Memory**
   - Agent自动调用工具
   - 看到ReAct循环的过程

5. ✅ **示例5：多Agent对话（重点！）**
   - Supervisor协调3个专家
   - 看到多Agent如何协作

---

### 第三步：理解输出

每个示例都会输出详细的执行过程，例如：

```
==================================================
示例5：多Agent对话 - Supervisor监督者模式
==================================================

==================================================
[问题 1] 现在美国的经济形势如何？
==================================================

🎯 Supervisor决策：将问题转给 macro_expert
  → 宏观经济专家工作中...

💬 回答：根据最新数据，美国经济形势总体温和：
联邦利率4.0%-4.25%，处于限制性水平；
CPI为3.01%，通胀有所缓解；
失业率4.0%，就业市场稳健。
```

---

## 📖 代码结构说明

### 核心文件

```
AI_Invest_Assistant/
├── Agents/
│   ├── langgraph_advanced_tutorial.py  # ⭐ 新教程（主文件）
│   ├── TUTORIAL_CHANGELOG.md           # 📝 更新说明
│   ├── QUICK_START.md                  # 🚀 本文件
│   ├── tools_and_agents.py             # 你现有的代码
│   └── fundamental_analyst.py          # 你现有的代码
```

### 教程包含的示例

| 示例 | 文件中的函数 | 学习重点 |
|------|-------------|---------|
| 1 | `simple_graph_example()` | 基础：State、Node、Edge |
| 2 | `investment_workflow_basic()` | 实战：投资分析流程 |
| 3 | `conditional_workflow()` | 进阶：条件分支 |
| 4 | `loop_with_memory()` | 进阶：循环与工具调用 |
| 5 | `multi_agent_supervisor()` | ⭐ 核心：多Agent对话 |

---

## 🎯 学习路径

### 阶段1：理解基础（Day 1-2）

**目标：理解State、Graph、Node、Edge的概念**

1. 阅读 `simple_graph_example()`
2. 修改代码，添加一个新节点
3. 运行并观察输出

**练习：**
```python
# 添加第三个节点
def step3(state: SimpleState):
    return {"output": f"最终处理：{state['output']}"}

workflow.add_node("最终处理", step3)
workflow.add_edge("生成", "最终处理")
workflow.add_edge("最终处理", END)
```

---

### 阶段2：实现投资分析流程（Day 3-4）

**目标：将你的金融数据工具整合到Graph中**

1. 阅读 `investment_workflow_basic()`
2. 用你的真实工具替换示例工具：
   - `fetch_macro()` → 你的 `fetch_macro_economy()`
   - `fetch_company()` → 你的 `fetch_stock_profile()`

**练习：**
```python
# 在investment_workflow_basic()中修改
@tool
def fetch_company(symbol: str) -> dict:
    """获取公司数据"""
    # 调用你的真实函数
    from tools_and_agents import fetch_stock_profile
    return fetch_stock_profile.invoke(symbol)
```

---

### 阶段3：掌握条件分支（Day 5-6）

**目标：根据不同情况走不同分析路径**

1. 阅读 `conditional_workflow()`
2. 理解 `should_deep_dive()` 决策函数
3. 修改决策条件

**练习：添加更多分支**
```python
def should_analyze(state) -> Literal["深度", "中等", "快速"]:
    pe = state["pe_ratio"]
    if pe > 60:
        return "深度"
    elif pe > 30:
        return "中等"
    else:
        return "快速"

workflow.add_conditional_edges(
    "获取数据",
    should_analyze,
    {
        "深度": "deep_node",
        "中等": "medium_node",
        "快速": "quick_node"
    }
)
```

---

### 阶段4：理解Agent循环（Day 7-8）

**目标：让Agent自动决定调用哪些工具**

1. 阅读 `loop_with_memory()`
2. 观察Agent如何多次调用工具
3. 理解 `should_continue()` 的终止逻辑

**关键概念：**
- **tool_calls**：LLM决定调用哪个工具
- **ToolNode**：自动执行工具调用
- **循环边**：tools → agent → tools → ...

---

### 阶段5：实现多Agent系统（Day 9-14）⭐

**目标：构建你的多专家投资分析系统**

#### 步骤1：理解Supervisor模式

阅读 `multi_agent_supervisor()`，理解：
- Supervisor如何决策
- 专家Agent如何定义
- 如何路由到不同专家

#### 步骤2：创建你的专家团队

在 `tools_and_agents.py` 中添加：

```python
def create_macro_expert():
    """宏观经济分析专家"""
    return create_agent(
        model=llm,
        tools=[fetch_macro_economy],  # 使用你已有的工具
        system_prompt="""你是宏观经济分析专家。
        分析美国的利率、通胀、就业、GDP等指标。
        给出当前宏观经济环境的评分（1-10分）。"""
    )

def create_fundamental_expert():
    """基本面分析专家"""
    return create_agent(
        model=llm,
        tools=[fetch_stock_profile, fetch_stock_price],
        system_prompt="""你是基本面分析专家。
        分析公司的行业地位、财务状况、增长潜力。
        给出基本面评分（1-10分）。"""
    )

def create_valuation_expert():
    """估值分析专家"""
    return create_agent(
        model=llm,
        tools=[],  # 可以添加估值计算工具
        system_prompt="""你是估值分析专家。
        判断股票是高估还是低估。
        给出估值评分（1-10分，10分表示严重低估）。"""
    )
```

#### 步骤3：构建Supervisor

```python
def create_investment_supervisor():
    """投资分析Supervisor"""

    class SupervisorState(TypedDict):
        messages: Annotated[list, add_messages]
        symbol: str
        next_agent: str

    # 创建专家
    macro_expert = create_macro_expert()
    fundamental_expert = create_fundamental_expert()
    valuation_expert = create_valuation_expert()

    # Supervisor节点
    def supervisor_node(state):
        last_message = state["messages"][-1].content

        prompt = f"""
        用户问题：{last_message}
        股票代码：{state['symbol']}

        应该调用哪个专家？
        - macro_expert: 宏观经济问题
        - fundamental_expert: 公司基本面问题
        - valuation_expert: 估值问题
        - FINISH: 已经回答完毕

        只回复一个专家名称或FINISH。
        """

        response = llm.invoke(prompt)
        return {"next_agent": response.content.strip()}

    # 构建Graph
    workflow = StateGraph(SupervisorState)

    # ... 添加节点和边（参考教程）

    return workflow.compile()
```

#### 步骤4：测试系统

```python
if __name__ == "__main__":
    supervisor = create_investment_supervisor()

    questions = [
        "现在美国经济形势如何？",
        "NVDA是一家什么样的公司？",
        "NVDA现在估值贵不贵？"
    ]

    for q in questions:
        print(f"\nQ: {q}")
        result = supervisor.invoke({
            "messages": [HumanMessage(content=q)],
            "symbol": "NVDA"
        })
        print(f"A: {result['messages'][-1].content}")
```

---

## 🐛 常见问题

### Q1: 运行时报错 "No module named 'langgraph'"
**A:** 安装LangGraph
```bash
pip install langgraph
```

### Q2: 提示 "add_messages is not defined"
**A:** 添加导入
```python
from langgraph.graph.message import add_messages
```

### Q3: LLM调用失败
**A:** 检查.env中的API KEY
```bash
# 确保.env中有
DASHSCOPE_API_KEY=your_key_here
```

### Q4: Supervisor总是返回错误的专家
**A:** 优化Supervisor的prompt
```python
# 给出更明确的示例
prompt = """
示例1：
问题："现在利率多高？" → macro_expert
问题："NVDA做什么的？" → fundamental_expert
问题："NVDA是否高估？" → valuation_expert

现在判断：{last_message}
"""
```

### Q5: Agent陷入死循环
**A:** 添加迭代限制
```python
class State(TypedDict):
    messages: Annotated[list, add_messages]
    iteration: int

def should_continue(state):
    if state["iteration"] > 5:  # 最多5次
        return "end"
    return "continue"
```

---

## 📊 性能优化建议

### 1. 并行执行多个Agent

如果多个Agent不相互依赖，可以并行执行：

```python
from langgraph.graph import StateGraph

workflow = StateGraph(State)

# 添加多个可以并行的节点
workflow.add_node("macro", macro_node)
workflow.add_node("fundamental", fundamental_node)

# 从同一个节点分出去
workflow.add_edge(START, "macro")
workflow.add_edge(START, "fundamental")

# 汇总结果
workflow.add_node("summary", summary_node)
workflow.add_edge("macro", "summary")
workflow.add_edge("fundamental", "summary")
```

### 2. 缓存工具调用结果

避免重复调用相同的工具：

```python
from functools import lru_cache

@lru_cache(maxsize=128)
@tool
def fetch_company_cached(symbol: str) -> dict:
    """带缓存的公司数据获取"""
    return fetch_stock_profile(symbol)
```

### 3. 使用流式输出

实时显示进度：

```python
for chunk in app.stream(
    {"messages": [HumanMessage(content="分析NVDA")]},
    stream_mode="values"
):
    print(chunk)
```

---

## 🎓 进阶学习

完成基础教程后，继续学习：

### 1. Checkpointing（状态持久化）
```python
from langgraph.checkpoint.sqlite import SqliteSaver

memory = SqliteSaver.from_conn_string(":memory:")
app = workflow.compile(checkpointer=memory)

# 可以暂停和恢复
config = {"configurable": {"thread_id": "thread-1"}}
result = app.invoke(state, config)
```

### 2. Human-in-the-loop（人工干预）
```python
from langgraph.checkpoint.sqlite import SqliteSaver

def human_approval_node(state):
    # 等待人工确认
    print("是否继续？(y/n)")
    response = input()
    if response.lower() == "y":
        return {"approved": True}
    return {"approved": False}
```

### 3. LangSmith追踪
```python
import os
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = "your_key"

# 自动上传追踪数据到LangSmith
```

---

## 🎉 完成后的检查清单

- [ ] 成功运行了所有5个示例
- [ ] 理解了State、Graph、Node、Edge的概念
- [ ] 知道如何添加条件分支
- [ ] 理解了Agent的ReAct循环
- [ ] 掌握了Supervisor模式
- [ ] 用自己的工具替换了示例工具
- [ ] 创建了至少3个专家Agent
- [ ] 实现了简单的多Agent系统
- [ ] 测试了不同类型的问题
- [ ] 更新了README文档

---

## 📚 下一步

1. **继续完善多Agent系统**
   - 添加更多专家（技术分析、风险评估等）
   - 优化Supervisor的决策逻辑
   - 添加结果汇总Agent

2. **集成到Web界面**
   - 修改 `web/streamlit.py`
   - 添加多Agent选项
   - 显示各专家的分析过程

3. **学习高级特性**
   - Checkpointing保存对话状态
   - 并行执行提高性能
   - LangSmith追踪调试

---

**祝学习顺利！有问题随时查看TUTORIAL_CHANGELOG.md 🚀**
