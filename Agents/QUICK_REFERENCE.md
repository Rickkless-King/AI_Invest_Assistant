# Langchain Tool & Agent 快速参考卡

## 🔧 Tool 定义模板

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
- [ ] 有类型注解（`param: Type`, `-> Type`）
- [ ] 有 docstring（三引号注释）
- [ ] 参数与实际函数匹配

## 🤖 Agent 创建模板（新 API）

```python
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage

# 1. 定义工具
tools = [tool1, tool2, tool3]

# 2. 定义系统提示词
system_message = "你是...你有以下工具：..."

# 3. 创建 Agent
agent = create_react_agent(
    model=llm,
    tools=tools,
    state_modifier=system_message
)

# 4. 调用
result = agent.invoke({
    "messages": [HumanMessage(content="用户问题")]
})

# 5. 获取答案
answer = result["messages"][-1].content
```

## ⚠️ 常见错误对照表

| 错误代码 | 原因 | 解决方案 |
|---------|------|---------|
| `ValueError: Function must have a docstring` | Tool 缺少 docstring | 添加三引号注释 |
| `ImportError: cannot import name 'AgentExecutor'` | 使用了旧 API | 改用 `create_react_agent` |
| 参数不匹配错误 | Tool 定义的参数与实际函数不一致 | 检查参数是否真的需要 |

## 📋 你的项目专用

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

# Tool 3: 宏观数据（不需要参数！）
@tool
def fetch_macro_economic_data() -> dict:
    """获取美国宏观经济数据"""
    return get_macro_economic_data()  # ← 注意：这个函数不接受参数
```

### 系统提示词模板

```python
system_message = """你是一名顶级对冲基金经理。

分析步骤：
1. 先调用 fetch_macro_economic_data() 了解宏观环境
2. 再调用 fetch_company_profile(symbol) 和 fetch_real_time_data(symbol) 获取个股信息
3. 综合分析后给出投资建议

工具说明：
- fetch_company_profile(symbol): 获取公司信息
- fetch_real_time_data(symbol): 获取股票价格
- fetch_macro_economic_data(): 获取宏观数据（无需参数）
"""
```

## 🔄 旧 API vs 新 API

### ❌ 旧 API（不要用）

```python
from langchain.agents import AgentExecutor, create_tool_calling_agent

prompt = ChatPromptTemplate.from_messages([...])
agent = create_tool_calling_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools)
result = executor.invoke({"input": "...", "chat_history": []})
```

### ✅ 新 API（推荐）

```python
from langgraph.prebuilt import create_react_agent

agent = create_react_agent(llm, tools, state_modifier="系统提示词")
result = agent.invoke({"messages": [HumanMessage(content="...")]})
```

## 🎯 关键区别总结

| 对比项 | 旧 API | 新 API |
|-------|-------|--------|
| 导入 | `langchain.agents` | `langgraph.prebuilt` |
| 创建函数 | `create_tool_calling_agent` + `AgentExecutor` | `create_react_agent` |
| Prompt | `ChatPromptTemplate` | 普通字符串 |
| 调用格式 | `{"input": "...", "chat_history": []}` | `{"messages": [HumanMessage(...)]}` |
| 返回格式 | `result["output"]` | `result["messages"][-1].content` |

## 💡 重要提醒

### 关于 fetch_macro_economic_data

```python
# ❌ 错误 - 宏观数据不需要股票代码
@tool
def fetch_macro_economic_data(symbol: str) -> dict:
    return get_macro_economic_data()

# ✅ 正确 - GDP、利率等是全局数据
@tool
def fetch_macro_economic_data() -> dict:
    """获取美国宏观经济数据"""
    return get_macro_economic_data()
```

**为什么？**
- 宏观数据（GDP、利率、失业率）是全国性的
- 与具体股票无关
- 所有股票分析共享同一份宏观数据

### 关于 print vs return

```python
def my_function():
    print("这是调试信息")    # 输出到控制台
    return {"key": "value"}  # 这才是返回值（Tool 使用这个）
```

你的 `with_fallback` 函数是正确的：
- `print()` 只是调试信息
- `return {}` 才是 Tool 获取的数据

## 🚀 快速开始

```bash
# 1. 安装依赖
pip install langchain langchain-core langchain-openai langgraph python-dotenv

# 2. 配置环境变量（创建 .env 文件）
echo "DASHSCOPE_API_KEY=your_key" > Agents/.env
echo "FINNHUB_API_KEY=your_key" >> Agents/.env
echo "FRED_API_KEY=your_key" >> Agents/.env

# 3. 运行
cd Agents
python tools_and_agents.py
```

## 📚 文档索引

- **完整教程**: `LANGCHAIN_TOOL_AGENT_COMPLETE_TUTORIAL.md`
- **问题修复总结**: `FIXES_SUMMARY.md`
- **详细教程**: `AGENT_TUTORIAL.md`
- **测试代码**: `test_agent_basic.py`
- **完整实现**: `tools_and_agents.py`

## ⚡ 故障排查

### 问题 1: ValueError: Function must have a docstring

**检查：**
1. 是否有 docstring？
2. 参数类型注解是否完整？
3. 参数是否与实际函数匹配？

### 问题 2: ImportError: cannot import name 'AgentExecutor'

**解决：**
```python
# 删除这行
from langchain.agents import AgentExecutor

# 改为
from langgraph.prebuilt import create_react_agent
```

### 问题 3: 缺少 API key

**解决：**
```bash
# 创建 .env 文件
cd Agents
cat > .env << 'EOF'
DASHSCOPE_API_KEY=your_key_here
FINNHUB_API_KEY=your_key_here
FRED_API_KEY=your_key_here
EOF
```

## 🎓 面试快问快答

**Q: Tool 是什么？**
A: 标准化的函数，让 LLM 知道何时、如何调用。

**Q: Agent 是什么？**
A: LLM + Tools + ReAct 循环，自动决策调用哪些工具。

**Q: ReAct 是什么？**
A: Reasoning（推理）+ Acting（行动）的循环。

**Q: 为什么用 Agent？**
A: 可以根据情况自动调整策略，不需要硬编码流程。

**Q: Agent 有什么局限？**
A: 成本高、可能不稳定、延迟高。适合复杂任务，简单任务用 Chain。
