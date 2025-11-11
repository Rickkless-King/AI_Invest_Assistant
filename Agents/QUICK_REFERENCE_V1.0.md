# Langchain 1.0 Tool & Agent 快速参考卡（2025更新版）

## 🚨 重要：API 已变更

**LangChain 1.0（2025）的关键变化：**
- ❌ `langgraph.prebuilt.create_react_agent` → 已弃用
- ✅ `langchain.agents.create_agent` → 新的官方 API

## 🔧 Tool 定义模板（不变）

```python
from langchain_core.tools import tool

@tool
def tool_name(param: ParamType) -> ReturnType:
    """
    [必需] 工具的功能描述

    参数:
        param: 参数说明

    返回:
        返回值说明
    """
    return actual_function(param)
```

**检查清单：**
- [ ] 有 `@tool` 装饰器
- [ ] 有 docstring（三引号注释）
- [ ] 有类型注解（`param: Type`, `-> Type`）
- [ ] 参数与实际函数匹配

## 🤖 Agent 创建模板（✅ 新 API）

```python
from langchain.agents import create_agent  # ✅ 新导入路径

# 1. 定义工具
tools = [tool1, tool2, tool3]

# 2. 定义系统提示词（普通字符串）
system_prompt = "你是...你有以下工具：..."

# 3. 创建 Agent
agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt=system_prompt  # ✅ 新参数名
)

# 4. 调用 - 使用字典格式（推荐）
result = agent.invoke({
    "messages": [{"role": "user", "content": "用户问题"}]
})

# 5. 获取答案
final_answer = result["messages"][-1]
if isinstance(final_answer, dict):
    print(final_answer["content"])
else:
    print(final_answer.content)
```

## ⚠️ API 变化对照表

| 项目 | 旧 API（❌ 已弃用） | 新 API（✅ 推荐） |
|------|-------------------|-----------------|
| **导入** | `from langgraph.prebuilt import create_react_agent` | `from langchain.agents import create_agent` |
| **函数名** | `create_react_agent()` | `create_agent()` |
| **参数名** | `state_modifier="..."` | `system_prompt="..."` |
| **消息导入** | `from langchain.schema import HumanMessage` | `from langchain_core.messages import HumanMessage` |
| **消息格式** | `HumanMessage(content="...")` | `{"role": "user", "content": "..."}` ✅ 推荐 |

## 📋 你的项目专用模板

### 三个核心 Tool

```python
# Tool 1: 公司信息（需要 symbol）
@tool
def fetch_company_profile(symbol: str) -> dict:
    """获取公司基本信息"""
    return get_company_profile_with_fallback(symbol)

# Tool 2: 股票价格（需要 symbol）
@tool
def fetch_real_time_data(symbol: str) -> dict:
    """获取股票实时价格"""
    return get_real_time_data_with_fallback(symbol)

# Tool 3: 宏观数据（✅ 不需要参数！）
@tool
def fetch_macro_economic_data() -> dict:
    """获取美国宏观经济数据"""
    return get_macro_economic_data()  # ✅ 无参数
```

### 投资分析 Agent 模板

```python
from langchain.agents import create_agent  # ✅ 新 API

tools = [fetch_company_profile, fetch_real_time_data, fetch_macro_economic_data]

system_prompt = """你是一名顶级对冲基金经理。

分析步骤：
1. 先调用 fetch_macro_economic_data() 了解宏观环境
2. 再调用 fetch_company_profile(symbol) 和 fetch_real_time_data(symbol) 获取个股信息
3. 综合分析后给出投资建议

你有以下工具：
- fetch_company_profile(symbol): 获取公司信息
- fetch_real_time_data(symbol): 获取股票价格
- fetch_macro_economic_data(): 获取宏观数据（无需参数）"""

agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt=system_prompt
)

result = agent.invoke({
    "messages": [{"role": "user", "content": "问题"}]
})
```

## 🔄 完整的迁移步骤

### 步骤 1：升级依赖

```bash
pip install --upgrade langchain langchain-core langchain-openai langgraph
pip freeze > requirements.txt
```

### 步骤 2：修改导入

```python
# ❌ 删除
from langgraph.prebuilt import create_react_agent
from langchain.schema import HumanMessage

# ✅ 改为
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage  # 如果需要
```

### 步骤 3：修改创建代码

```python
# ❌ 旧代码
agent = create_react_agent(
    model=llm,
    tools=tools,
    state_modifier="系统提示词"
)

# ✅ 新代码
agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt="系统提示词"  # 参数名改变
)
```

### 步骤 4：修改调用代码（可选）

```python
# ❌ 旧方式（仍可用，但需要导入）
from langchain_core.messages import HumanMessage
result = agent.invoke({
    "messages": [HumanMessage(content="问题")]
})

# ✅ 新方式（推荐，更简单）
result = agent.invoke({
    "messages": [{"role": "user", "content": "问题"}]
})
```

## 💡 常见错误速查

### 错误 1: ImportError: cannot import name 'create_react_agent'

```python
# ❌ 问题代码
from langgraph.prebuilt import create_react_agent

# ✅ 解决方案
from langchain.agents import create_agent
```

### 错误 2: ModuleNotFoundError: No module named 'langchain.schema'

```python
# ❌ 问题代码
from langchain.schema import HumanMessage

# ✅ 解决方案
from langchain_core.messages import HumanMessage
```

### 错误 3: 依赖冲突

```bash
# ❌ 错误信息
langchain 0.3.27 requires langchain-core<1.0.0, but you have langchain-core 1.0.4

# ✅ 解决方案
pip install --upgrade langchain langchain-core langchain-openai
```

### 错误 4: ValueError: Function must have a docstring

```python
# ❌ 问题代码
@tool
def my_tool(param):  # 缺少类型注解和 docstring
    return something

# ✅ 解决方案
@tool
def my_tool(param: str) -> dict:
    """工具描述"""
    return something
```

## 🚀 快速测试

```python
"""最小可运行示例"""
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
import os

# LLM
llm = ChatOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-3.5-turbo"
)

# Tool
@tool
def get_weather(city: str) -> str:
    """获取天气"""
    return f"{city} 今天晴天"

# Agent
agent = create_agent(
    model=llm,
    tools=[get_weather],
    system_prompt="你是天气助手"
)

# 调用
result = agent.invoke({
    "messages": [{"role": "user", "content": "北京天气如何？"}]
})

print(result["messages"][-1])
```

## 📚 文档索引

- **最新迁移指南**: `LANGCHAIN_1.0_MIGRATION_GUIDE.md` ← 🌟 详细教程
- **完整示例**: `tools_and_agents.py` ← ✅ 可运行代码
- **测试代码**: `test_agent_basic.py` ← 🧪 快速验证
- **旧版教程**: `LANGCHAIN_TOOL_AGENT_COMPLETE_TUTORIAL.md` ← ⚠️ 已过时

## 🎯 版本要求

```
langchain >= 1.0.0
langchain-core >= 1.0.0
langchain-openai >= 1.0.0
langgraph >= 1.0.0
```

验证命令：
```bash
python -c "import langchain; print(f'✅ langchain {langchain.__version__}')"
```

## 💼 面试快问快答（更新版）

**Q: Langchain 1.0 的主要变化是什么？**
A: Agent 创建 API 从 `langgraph.prebuilt.create_react_agent` 迁移到 `langchain.agents.create_agent`，参数名从 `state_modifier` 改为 `system_prompt`，消息导入路径从 `langchain.schema` 改为 `langchain_core.messages`。

**Q: 为什么要用 `create_agent` 而不是 `create_react_agent`？**
A: `create_react_agent` 已被弃用。`create_agent` 是 LangChain 1.0 的官方推荐 API，提供更好的稳定性和长期支持。

**Q: Tool 定义有变化吗？**
A: Tool 定义方式没有变化，仍然使用 `@tool` 装饰器，仍然需要 docstring 和类型注解。

**Q: 旧代码会报什么错？**
A: 主要是 `ImportError: cannot import name 'create_react_agent'` 或 `ModuleNotFoundError: No module named 'langchain.schema'`。

**Q: 升级后需要改什么？**
A: 三个地方：1) 导入路径，2) 函数名和参数名，3) 消息格式（可选但推荐改为字典格式）。

---

**最后更新：** 2025年，基于 LangChain 1.0 正式版
**状态：** ✅ 当前最新、生产可用
