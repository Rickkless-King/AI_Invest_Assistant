# Langchain Tool 和 Agent 完整教程

## 🎯 教程目标

通过这个教程，你将学会：
1. ✅ 什么是 Tool，如何正确定义 Tool
2. ✅ 什么是 Agent，Agent 的工作原理
3. ✅ Langchain API 的演变（旧 API vs 新 API）
4. ✅ 如何将你的投资分析项目改造成 Agent
5. ✅ 常见错误和解决方案

## 📚 第一章：Tool 基础知识

### 1.1 什么是 Tool？

**传统方式（手动调用）：**
```python
# 你需要手动决定调用什么函数
price = get_real_time_data("NVDA")
profile = get_company_profile("NVDA")
macro_data = get_macro_economic_data()

# 手动组装 prompt
prompt = f"公司信息：{profile}，价格：{price}，宏观数据：{macro_data}，请分析"

# 手动调用 LLM
response = llm.invoke(prompt)
```

**使用 Tool 的方式（AI 自动决策）：**
```python
# 你只需要定义工具
tools = [get_real_time_data_tool, get_company_profile_tool, get_macro_data_tool]

# AI 自己决定调用什么、什么顺序、传什么参数
agent = create_agent(llm, tools)
response = agent.invoke("分析 NVDA 是否值得投资")

# AI 会自动：
# 1. 先调用 get_macro_data_tool() 了解宏观环境
# 2. 再调用 get_company_profile_tool("NVDA") 获取公司信息
# 3. 最后调用 get_real_time_data_tool("NVDA") 获取价格
# 4. 综合分析后给出回答
```

**核心区别：**
- 传统方式：你是"导演"，手动编排所有步骤
- Tool + Agent：你是"制片人"，AI 是导演，自己决定拍摄流程

### 1.2 如何定义 Tool？

#### ❌ 错误示例 1：缺少 docstring

```python
from langchain_core.tools import tool

@tool
def get_stock_price(symbol: str) -> str:
    # ❌ 没有 docstring，LLM 不知道这个工具是干什么的
    return f"{symbol} 的价格是 $100"

# 运行会报错：
# ValueError: Function must have a docstring if description not provided.
```

**为什么会报错？**
- LLM 需要知道每个工具的功能
- 没有 docstring，LLM 不知道什么时候该用这个工具

#### ✅ 正确示例 1：添加 docstring

```python
@tool
def get_stock_price(symbol: str) -> str:
    """
    获取股票的当前价格

    参数:
        symbol: 股票代码，如 'NVDA', 'AAPL'

    返回:
        包含股票价格信息的字符串
    """
    return f"{symbol} 的价格是 $100"
```

#### ✅ 正确示例 2：使用显式 description

```python
@tool("获取股票当前价格，输入参数为股票代码如 'NVDA'")
def get_stock_price(symbol: str) -> str:
    """可以不写 docstring，因为已经在装饰器中提供了描述"""
    return f"{symbol} 的价格是 $100"
```

#### ❌ 错误示例 2：参数与实际函数不匹配

```python
@tool
def get_macro_data(symbol: str) -> dict:
    """获取宏观经济数据"""
    # ❌ 定义了 symbol 参数，但实际调用的函数不需要参数
    return get_macro_economic_data()  # 这个函数不接受参数！
```

**问题：**
- Tool 定义说需要 `symbol` 参数
- 但实际的 `get_macro_economic_data()` 不需要参数
- 宏观数据（GDP、利率）与具体股票无关

#### ✅ 正确示例 2：参数匹配

```python
@tool
def get_macro_data() -> dict:
    """
    获取美国宏观经济数据

    注意：此函数不需要任何参数，返回当前的宏观经济指标

    返回:
        包含 GDP、利率、通胀等数据的字典
    """
    return get_macro_economic_data()  # ✅ 参数匹配
```

### 1.3 Tool 定义的完整规范

**必须满足的要求：**
```python
@tool
def tool_name(param1: Type1, param2: Type2) -> ReturnType:
    """
    [必需] 工具的描述 - 告诉 LLM 这个工具是干什么的

    参数:
        param1: [可选但推荐] 参数说明
        param2: [可选但推荐] 参数说明

    返回:
        [可选但推荐] 返回值说明

    示例:
        [可选] 使用示例
    """
    # 1. ✅ 必须有类型注解 (param1: Type1)
    # 2. ✅ 必须有返回类型 (-> ReturnType)
    # 3. ✅ 必须有 docstring 或在装饰器中提供 description
    # 4. ✅ 参数必须与实际调用的函数匹配

    return actual_function(param1, param2)
```

### 1.4 实战练习：改造你的函数为 Tool

**你的原始函数：**
```python
def get_company_profile_with_fallback(symbol: str) -> dict:
    try:
        profile = finnhub_client.company_profile2(symbol=symbol)
        return {
            '金融数据源来源': 'Finnhub',
            '名称': profile.get('name'),
            '行业': profile.get('finnhubIndustry'),
            # ...
        }
    except Exception as e:
        print(f"Finnhub调用失败：{e}")
        # 备用方案...
```

**改造成 Tool：**
```python
@tool
def fetch_company_profile(symbol: str) -> dict:
    """
    获取公司基本信息

    通过股票代码获取公司的名称、行业、市值等基本信息。
    会自动在多个数据源之间切换以确保成功获取数据。

    参数:
        symbol: 股票代码（大写），例如 'NVDA', 'AAPL', 'TSLA'

    返回:
        包含以下字段的字典：
        - 名称: 公司名称
        - 行业: 所属行业
        - 市值: 市值（百万美元）
        - ipo时间: IPO 日期
        - 官网: 公司官网

    示例:
        >>> fetch_company_profile("NVDA")
        {'名称': 'NVIDIA Corp', '行业': 'Semiconductors', ...}
    """
    # 注意：这里只是调用原函数，不需要重写逻辑
    return get_company_profile_with_fallback(symbol)
```

**关键点：**
1. ✅ 使用 `@tool` 装饰器
2. ✅ 保留原有的类型注解 `symbol: str` 和 `-> dict`
3. ✅ 添加详细的 docstring
4. ✅ 参数与原函数完全匹配
5. ✅ 只是包装原函数，不重写业务逻辑

## 📚 第二章：Agent 基础知识

### 2.1 什么是 Agent？

**Agent = LLM（大脑）+ Tools（手）+ ReAct 循环（思考方式）**

```
┌─────────────────────────────────────────┐
│           Agent 的工作流程               │
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
```

**ReAct = Reasoning（推理）+ Acting（行动）**

### 2.2 Langchain API 的演变

#### 🕰️ 旧版 API（你在教程中看到的）

```python
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate

# 1. 定义 prompt 模板
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是投资助手。工具：{tools}"),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}")
])

# 2. 创建 agent
agent = create_tool_calling_agent(llm, tools, prompt)

# 3. 创建执行器
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True
)

# 4. 调用
result = agent_executor.invoke({
    "input": "NVDA是否值得投资？",
    "chat_history": []
})
```

**问题：**
- ❌ `AgentExecutor` 在 langchain 1.0+ 中已被移除
- ❌ `create_tool_calling_agent` 也不再推荐使用
- ❌ 你会看到 `ImportError: cannot import name 'AgentExecutor'`

#### 🆕 新版 API（推荐使用 - LangGraph）

```python
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage

# 1. 定义系统提示词（普通字符串即可）
system_message = """你是投资助手。

你有以下工具：
- fetch_company_profile(symbol): 获取公司信息
- fetch_real_time_data(symbol): 获取股票价格
- fetch_macro_data(): 获取宏观经济数据
"""

# 2. 创建 agent（一步完成）
agent = create_react_agent(
    model=llm,
    tools=tools,
    state_modifier=system_message
)

# 3. 调用（使用消息格式）
result = agent.invoke({
    "messages": [HumanMessage(content="NVDA是否值得投资？")]
})

# 4. 获取结果
final_answer = result["messages"][-1].content
```

**优势：**
- ✅ 更简洁，只需要一个函数
- ✅ 自动处理 ReAct 循环
- ✅ 更好的错误处理
- ✅ 支持流式输出
- ✅ 与最新的 Langchain 版本兼容

### 2.3 为什么会报错？

**你的报错：**
```python
ValueError: Function must have a docstring if description not provided.
```

**真正的原因有 3 个：**

1. **主要原因：Tool 定义错误**
```python
# ❌ 你的代码
@tool("获取美国宏观经济数据,输入参数为股票代码...")
def fetch_macro_economic_data(symbol:str)->dict:  # ← 这里！
    return get_macro_economic_data()  # 不需要 symbol

# ✅ 正确的
@tool
def fetch_macro_economic_data() -> dict:  # ← 移除 symbol
    """获取美国宏观经济数据"""
    return get_macro_economic_data()
```

2. **次要原因：API 版本不兼容**
```python
# ❌ 旧 API - 会报错
from langchain.agents import AgentExecutor  # ImportError!

# ✅ 新 API
from langgraph.prebuilt import create_react_agent
```

3. **其他问题：导入路径过时**
```python
# ❌ 旧导入
from langchain.schema import HumanMessage

# ✅ 新导入
from langchain_core.messages import HumanMessage
```

## 📚 第三章：实战 - 改造你的投资分析项目

### 3.1 第一步：定义所有 Tool

```python
# tools_and_agents.py

from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent
import os
from dotenv import load_dotenv
from fundamental_analyst import *

# 加载环境变量
load_dotenv()

# 初始化 LLM
llm = ChatOpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    temperature=0.1,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    model="qwen-plus"
)

# ============= Tool 1: 获取公司信息 =============
@tool
def fetch_company_profile(symbol: str) -> dict:
    """
    获取公司基本信息

    参数:
        symbol: 股票代码（如 'NVDA', 'AAPL'）

    返回:
        包含公司名称、行业、市值、IPO时间等信息的字典
    """
    return get_company_profile_with_fallback(symbol)


# ============= Tool 2: 获取股票价格 =============
@tool
def fetch_real_time_data(symbol: str) -> dict:
    """
    获取股票实时价格数据

    参数:
        symbol: 股票代码（如 'NVDA', 'AAPL'）

    返回:
        包含最新成交价、最高价、最低价等数据的字典
    """
    return get_real_time_data_with_fallback(symbol)


# ============= Tool 3: 获取宏观经济数据 =============
@tool
def fetch_macro_economic_data() -> dict:
    """
    获取美国宏观经济数据

    注意：此函数不需要任何参数

    返回:
        包含汇率、利率、就业、通胀、GDP等数据的字典
    """
    return get_macro_economic_data()
```

**关键点检查清单：**
- [x] 所有函数都有 `@tool` 装饰器
- [x] 所有函数都有类型注解（`symbol: str`, `-> dict`）
- [x] 所有函数都有 docstring
- [x] `fetch_macro_economic_data` 没有参数（宏观数据不需要股票代码）
- [x] Tool 函数只是包装原函数，不重写逻辑

### 3.2 第二步：创建 Agent

```python
def invest_analyze_agent():
    """投资分析 Agent"""

    # 1. 定义工具列表
    tools = [
        fetch_company_profile,
        fetch_real_time_data,
        fetch_macro_economic_data
    ]

    # 2. 定义系统提示词
    system_message = """你是一名顶级对冲基金经理。

你的分析流程：
1. 先调用 fetch_macro_economic_data() 了解宏观经济环境
2. 再调用 fetch_company_profile(symbol) 和 fetch_real_time_data(symbol) 获取个股信息
3. 综合分析后给出投资建议

你有以下工具：
- fetch_company_profile(symbol): 获取公司基本信息
- fetch_real_time_data(symbol): 获取股票价格数据
- fetch_macro_economic_data(): 获取宏观经济数据（无需参数）

请一步步思考，先获取数据，再进行分析。"""

    # 3. 创建 Agent
    agent = create_react_agent(
        model=llm,
        tools=tools,
        state_modifier=system_message
    )

    # 4. 调用 Agent
    user_question = "现在美国经济如何？英伟达（NVDA）是否值得投资？"

    print("="*70)
    print("🤖 投资分析 Agent 开始工作...")
    print("="*70)
    print(f"\n用户问题: {user_question}\n")

    result = agent.invoke({
        "messages": [HumanMessage(content=user_question)]
    })

    # 5. 显示思考过程
    print("\n⚙️  Agent 思考过程:\n")
    for msg in result["messages"]:
        if isinstance(msg, HumanMessage):
            print(f"👤 用户: {msg.content}")
        elif hasattr(msg, 'tool_calls') and msg.tool_calls:
            for tool_call in msg.tool_calls:
                print(f"🔧 调用工具: {tool_call['name']}({tool_call['args']})")

    # 6. 显示最终结果
    final_answer = result["messages"][-1].content
    print("\n" + "="*70)
    print("📊 最终分析结果:")
    print("="*70)
    print(final_answer)
    print("="*70)


if __name__ == "__main__":
    invest_analyze_agent()
```

### 3.3 第三步：运行和测试

**运行前检查：**
```bash
# 1. 确保已安装依赖
pip install langchain langchain-core langchain-openai langgraph

# 2. 确保已配置环境变量（创建 .env 文件）
DASHSCOPE_API_KEY=your_key_here
FINNHUB_API_KEY=your_key_here
ALPHAVANTAGE_API_KEY=your_key_here
FRED_API_KEY=your_key_here
```

**运行：**
```bash
cd Agents
python tools_and_agents.py
```

**预期输出：**
```
======================================================================
🤖 投资分析 Agent 开始工作...
======================================================================

用户问题: 现在美国经济如何？英伟达（NVDA）是否值得投资？

⚙️  Agent 思考过程:

👤 用户: 现在美国经济如何？英伟达（NVDA）是否值得投资？
🔧 调用工具: fetch_macro_economic_data({})
🔧 调用工具: fetch_company_profile({'symbol': 'NVDA'})
🔧 调用工具: fetch_real_time_data({'symbol': 'NVDA'})

======================================================================
📊 最终分析结果:
======================================================================
根据获取的数据分析：

宏观经济环境：
- 联邦基金利率 4.5%-4.75%，处于高位
- GDP 增长 2.8%，经济稳健
- 失业率 3.7%，就业市场健康
...

英伟达分析：
- 当前价格 $135.50
- 市值 4.8 万亿美元
- 行业：半导体
...

投资建议：...
======================================================================
```

## 📚 第四章：常见问题和解决方案

### Q1: ValueError: Function must have a docstring

**原因：**
- Tool 函数缺少 docstring
- 或者参数定义与实际函数不匹配

**解决方案：**
```python
# ❌ 错误
@tool
def my_tool(param):  # 没有类型注解，没有 docstring
    return something

# ✅ 正确
@tool
def my_tool(param: str) -> dict:
    """工具描述"""
    return something
```

### Q2: ImportError: cannot import name 'AgentExecutor'

**原因：**
- 使用了旧版 API
- langchain 1.0+ 已移除 `AgentExecutor`

**解决方案：**
```python
# ❌ 旧 API
from langchain.agents import AgentExecutor

# ✅ 新 API
from langgraph.prebuilt import create_react_agent
```

### Q3: 宏观数据 Tool 应该有参数吗？

**答案：不应该！**

```python
# ❌ 错误 - 宏观数据不需要股票代码
@tool
def fetch_macro_data(symbol: str) -> dict:
    return get_macro_economic_data()  # 这个函数不接受参数

# ✅ 正确 - 宏观数据是全局的
@tool
def fetch_macro_data() -> dict:
    """获取美国宏观经济数据"""
    return get_macro_economic_data()
```

**原因：**
- GDP、利率、失业率等是全国性数据
- 与具体股票无关
- 所有股票共享同一份宏观数据

### Q4: print 和 return 的区别

```python
def my_function():
    print("这是调试信息")  # 输出到控制台，不是返回值
    return {"data": "value"}  # 这才是返回值
```

**你的代码是正确的：**
```python
def get_company_profile_with_fallback(symbol: str):
    try:
        profile = finnhub_client.company_profile2(symbol=symbol)
        return {...}  # ✅ 返回字典
    except Exception as e:
        print(f"失败：{e}")  # 只是调试信息，不影响返回值

    try:
        # 备用方案
        return {...}  # ✅ 返回字典
    except Exception as e2:
        return {'error': '...'}  # ✅ 即使失败也返回字典
```

### Q5: 旧代码和新代码对比

**旧代码（不能用了）：**
```python
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages([
    ("system", "...{tools}...{chat_history}..."),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}")
])

agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools)

result = agent_executor.invoke({
    "input": "问题",
    "chat_history": []
})
```

**新代码（推荐）：**
```python
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage

system_message = "你是投资助手..."

agent = create_react_agent(
    model=llm,
    tools=tools,
    state_modifier=system_message
)

result = agent.invoke({
    "messages": [HumanMessage(content="问题")]
})
```

## 📚 第五章：进阶技巧

### 5.1 添加记忆功能（保留对话历史）

```python
# 创建带记忆的 Agent
from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()

agent = create_react_agent(
    model=llm,
    tools=tools,
    state_modifier=system_message,
    checkpointer=memory  # 添加记忆
)

# 使用线程 ID 保持对话
config = {"configurable": {"thread_id": "user_123"}}

# 第一轮对话
result1 = agent.invoke({
    "messages": [HumanMessage(content="NVDA的价格是多少？")]
}, config)

# 第二轮对话（记得之前的内容）
result2 = agent.invoke({
    "messages": [HumanMessage(content="那它值得投资吗？")]  # Agent 知道"它"指的是 NVDA
}, config)
```

### 5.2 流式输出（实时显示 Agent 的思考）

```python
# 使用 stream 代替 invoke
for event in agent.stream(
    {"messages": [HumanMessage(content="分析 NVDA")]},
    stream_mode="values"
):
    # 实时打印每个步骤
    if "messages" in event:
        event["messages"][-1].pretty_print()
```

### 5.3 限制工具调用次数（防止死循环）

```python
# LangGraph 会自动处理，但你可以设置最大步数
from langgraph.prebuilt import create_react_agent

agent = create_react_agent(
    model=llm,
    tools=tools,
    state_modifier=system_message
)

# 设置最大递归深度
result = agent.invoke(
    {"messages": [HumanMessage(content="问题")]},
    {"recursion_limit": 10}  # 最多10步
)
```

## 📚 第六章：完整代码示例

### 完整的 tools_and_agents.py

```python
"""
Langchain Agent 完整示例
基于投资分析项目
"""

from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.prebuilt import create_react_agent
import os
from dotenv import load_dotenv
from fundamental_analyst import *

# ========== 配置 ==========
load_dotenv()

llm = ChatOpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    temperature=0.1,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    model="qwen-plus"
)


# ========== Tool 定义 ==========

@tool
def fetch_company_profile(symbol: str) -> dict:
    """
    获取公司基本信息

    参数:
        symbol: 股票代码（如 'NVDA', 'AAPL'）

    返回:
        包含公司名称、行业、市值等信息的字典
    """
    return get_company_profile_with_fallback(symbol)


@tool
def fetch_real_time_data(symbol: str) -> dict:
    """
    获取股票实时价格数据

    参数:
        symbol: 股票代码（如 'NVDA', 'AAPL'）

    返回:
        包含股票价格、最高价、最低价等数据的字典
    """
    return get_real_time_data_with_fallback(symbol)


@tool
def fetch_macro_economic_data() -> dict:
    """
    获取美国宏观经济数据

    注意：此函数不需要任何参数，返回最新的宏观经济指标

    返回:
        包含汇率、利率、就业、通胀、GDP等数据的字典
    """
    return get_macro_economic_data()


# ========== Agent 创建 ==========

def create_investment_agent():
    """创建投资分析 Agent"""

    tools = [fetch_company_profile, fetch_real_time_data, fetch_macro_economic_data]

    system_message = """你是一名顶级对冲基金经理，擅长宏观经济分析和个股研究。

你的分析步骤：
1. 先使用 fetch_macro_economic_data() 了解宏观经济环境
2. 再使用 fetch_company_profile(symbol) 和 fetch_real_time_data(symbol) 获取个股信息
3. 综合宏观和微观数据，给出投资建议

你有以下工具：
- fetch_company_profile(symbol): 获取公司基本信息（名称、行业、市值等）
- fetch_real_time_data(symbol): 获取股票价格数据
- fetch_macro_economic_data(): 获取宏观经济数据（无需参数）

请一步步思考，先获取必要数据，再进行综合分析。"""

    return create_react_agent(
        model=llm,
        tools=tools,
        state_modifier=system_message
    )


# ========== 主函数 ==========

def main():
    """主函数"""

    agent = create_investment_agent()

    # 测试问题
    questions = [
        "现在美国经济如何？",
        "英伟达（NVDA）是否值得投资？",
        "对比 NVDA 和 AAPL，哪个更值得买？"
    ]

    for question in questions:
        print("\n" + "="*70)
        print(f"📝 问题: {question}")
        print("="*70)

        result = agent.invoke({
            "messages": [HumanMessage(content=question)]
        })

        # 显示思考过程
        print("\n⚙️  Agent 思考过程:")
        for msg in result["messages"]:
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    print(f"  🔧 调用: {tool_call['name']}({tool_call.get('args', {})})")

        # 显示最终答案
        final_answer = result["messages"][-1].content
        print("\n📊 回答:")
        print(final_answer)
        print("="*70)


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║        Langchain Agent 投资分析系统                          ║
║        基于 LangGraph 的 ReAct Agent                         ║
╚══════════════════════════════════════════════════════════════╝
    """)
    main()
```

## 🎯 总结

### 你学到了什么？

1. **Tool 定义规范**
   - ✅ 必须有 `@tool` 装饰器
   - ✅ 必须有类型注解
   - ✅ 必须有 docstring 或显式 description
   - ✅ 参数必须与实际函数匹配

2. **Agent 创建（新 API）**
   - ✅ 使用 `create_react_agent` 而不是 `AgentExecutor`
   - ✅ 系统提示词是普通字符串，不需要复杂的 prompt 模板
   - ✅ 使用消息格式而不是字典格式

3. **常见错误**
   - ❌ `fetch_macro_data(symbol)` → ✅ `fetch_macro_data()`
   - ❌ `AgentExecutor` → ✅ `create_react_agent`
   - ❌ `langchain.schema` → ✅ `langchain_core.messages`

### 下一步

1. ✅ 运行完整代码，测试 Agent 是否正常工作
2. ✅ 尝试添加更多工具（如获取财务报表、新闻等）
3. ✅ 实验不同的系统提示词，优化 Agent 的表现
4. ✅ 添加记忆功能，让 Agent 记住对话历史
5. ✅ 尝试流式输出，实时看到 Agent 的思考过程

### 面试准备

**Q: Tool 和普通函数有什么区别？**
A: Tool 是标准化的函数，让 LLM 知道何时、如何调用。需要 docstring 描述功能，类型注解明确参数和返回值。

**Q: Agent 的工作原理是什么？**
A: Agent 使用 ReAct 模式：推理（决定做什么）→ 行动（调用工具）→ 观察（获取结果）→ 循环直到完成任务。

**Q: 为什么要用 Agent 而不是写固定流程？**
A: Agent 可以根据不同情况自动调整策略。比如某个数据源失败了，Agent 可以尝试其他方案；用户问不同问题，Agent 会调用不同的工具组合。

希望这个教程对你有帮助！🎉
