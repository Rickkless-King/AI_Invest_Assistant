# Langchain 1.0 Tool 和 Agent 最新教程（2025更新版）

## 🚨 重要更新说明

### API 变化时间线

**2024年底 - 2025年初：Langchain/LangGraph 达到 1.0 里程碑**

- ❌ `langgraph.prebuilt.create_react_agent` → **已弃用**
- ❌ `langchain.agents.AgentExecutor` → **已移除**
- ✅ `langchain.agents.create_agent` → **新的官方推荐 API**

### 依赖版本要求

```bash
# 必需的版本
langchain >= 1.0.0
langchain-core >= 1.0.0
langchain-openai >= 1.0.0
langgraph >= 1.0.0
```

**重要提示：**
- 升级 `langgraph` 会自动将 `langchain-core` 升级到 1.0+
- 需要同时升级 `langchain` 和 `langchain-openai` 以匹配 `langchain-core 1.0+`
- 导入路径从 `langchain.schema` 改为 `langchain_core.messages`

## 📋 第一章：正确的依赖安装

### 步骤 1：清理旧版本

```bash
# 查看当前版本
pip list | grep langchain
pip list | grep langgraph

# 如果发现版本冲突，卸载重装
pip uninstall langchain langchain-core langchain-openai langgraph -y
```

### 步骤 2：安装正确的版本

```bash
# 方法 1：升级到最新版本（推荐）
pip install --upgrade langchain langchain-core langchain-openai langgraph

# 方法 2：指定版本
pip install langchain>=1.0.0 langchain-core>=1.0.0 langchain-openai>=1.0.0 langgraph>=1.0.0

# 更新 requirements.txt
pip freeze > requirements.txt
```

### 步骤 3：验证安装

```bash
# 验证版本
python -c "import langchain; print(f'langchain: {langchain.__version__}')"
python -c "import langgraph; print(f'langgraph: {langgraph.__version__}')"

# 测试导入
python -c "from langchain.agents import create_agent; print('✅ Import successful!')"
```

## 📋 第二章：API 迁移指南

### 核心变化对比

| 项目 | 旧 API（已弃用） | 新 API（推荐） |
|------|----------------|---------------|
| **导入路径** | `from langgraph.prebuilt import create_react_agent` | `from langchain.agents import create_agent` |
| **函数名** | `create_react_agent()` | `create_agent()` |
| **系统提示词参数** | `state_modifier="..."` | `system_prompt="..."` |
| **消息格式** | `HumanMessage(content="...")` | `{"role": "user", "content": "..."}` |
| **消息导入** | `from langchain.schema import HumanMessage` | `from langchain_core.messages import HumanMessage` |

### 完整的迁移示例

#### ❌ 旧代码（不能用了）

```python
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage
from langchain.schema import HumanMessage  # 错误：此路径已不存在

# 创建 Agent
agent = create_react_agent(  # 已弃用
    model=llm,
    tools=tools,
    state_modifier="你是投资助手"  # 旧参数名
)

# 调用
result = agent.invoke({
    "messages": [HumanMessage(content="问题")]  # 需要导入 HumanMessage
})
```

#### ✅ 新代码（推荐）

```python
from langchain.agents import create_agent  # 新导入路径

# 创建 Agent
agent = create_agent(  # 新函数名
    model=llm,
    tools=tools,
    system_prompt="你是投资助手"  # 新参数名
)

# 调用 - 使用简单的字典格式
result = agent.invoke({
    "messages": [{"role": "user", "content": "问题"}]  # 不需要特殊导入
})
```

## 📋 第三章：Tool 定义（保持不变）

Tool 的定义方式在 1.0 中**没有变化**，继续按原来的方式定义即可。

### 标准 Tool 定义

```python
from langchain_core.tools import tool

@tool
def tool_name(param: str) -> dict:
    """
    工具的功能描述（必需）

    参数:
        param: 参数说明

    返回:
        返回值说明
    """
    return actual_function(param)
```

### 你的项目专用 Tools

```python
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
    return get_macro_economic_data()  # ✅ 注意：没有参数！
```

**关键检查清单：**
- [x] 有 `@tool` 装饰器
- [x] 有完整的 docstring（三引号注释）
- [x] 有类型注解（`param: Type`, `-> Type`）
- [x] 参数与实际函数匹配
- [x] `fetch_macro_economic_data` 没有参数

## 📋 第四章：Agent 创建（新 API）

### 基本用法

```python
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

# 1. 初始化 LLM
llm = ChatOpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    temperature=0.1,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    model="qwen-plus"
)

# 2. 定义工具列表
tools = [fetch_company_profile, fetch_real_time_data, fetch_macro_economic_data]

# 3. 定义系统提示词（普通字符串）
system_prompt = """你是一名顶级对冲基金经理。

你有以下工具：
- fetch_company_profile(symbol): 获取公司信息
- fetch_real_time_data(symbol): 获取股票价格
- fetch_macro_economic_data(): 获取宏观经济数据（无需参数）

分析步骤：
1. 先调用 fetch_macro_economic_data 了解宏观环境
2. 再调用 fetch_company_profile 和 fetch_real_time_data 获取个股信息
3. 综合分析后给出投资建议"""

# 4. 创建 Agent - 就这么简单！
agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt=system_prompt
)
```

### 调用 Agent

```python
# 方式 1：使用字典格式（推荐）
result = agent.invoke({
    "messages": [{"role": "user", "content": "NVDA是否值得投资？"}]
})

# 方式 2：也可以使用多轮对话
result = agent.invoke({
    "messages": [
        {"role": "user", "content": "美国经济如何？"},
        {"role": "assistant", "content": "根据最新数据..."},
        {"role": "user", "content": "那NVDA值得买吗？"}
    ]
})

# 获取最终回答
final_answer = result["messages"][-1]
if isinstance(final_answer, dict):
    print(final_answer["content"])
else:
    print(final_answer.content)
```

### 流式输出

```python
# 实时显示 Agent 的思考过程
for event in agent.stream(
    {"messages": [{"role": "user", "content": "分析NVDA"}]},
    stream_mode="values"
):
    if "messages" in event:
        last_msg = event["messages"][-1]
        if isinstance(last_msg, dict):
            print(last_msg.get("content", ""))
        else:
            print(last_msg.content)
```

## 📋 第五章：完整示例代码

### 投资分析 Agent（完整版）

```python
"""
投资分析 Agent - 使用 LangChain 1.0 API
"""

from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent  # ✅ 新 API
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
    """获取公司基本信息"""
    return get_company_profile_with_fallback(symbol)

@tool
def fetch_real_time_data(symbol: str) -> dict:
    """获取股票实时价格数据"""
    return get_real_time_data_with_fallback(symbol)

@tool
def fetch_macro_economic_data() -> dict:
    """获取美国宏观经济数据（无需参数）"""
    return get_macro_economic_data()

# ========== Agent 创建 ==========

def create_investment_agent():
    """创建投资分析 Agent"""

    tools = [fetch_company_profile, fetch_real_time_data, fetch_macro_economic_data]

    system_prompt = """你是一名顶级对冲基金经理。

分析步骤：
1. 先调用 fetch_macro_economic_data() 了解宏观环境
2. 再调用 fetch_company_profile(symbol) 和 fetch_real_time_data(symbol) 获取个股信息
3. 综合宏观和微观数据，给出投资建议

你有以下工具：
- fetch_company_profile(symbol): 获取公司信息
- fetch_real_time_data(symbol): 获取股票价格
- fetch_macro_economic_data(): 获取宏观数据（无需参数）"""

    return create_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt
    )

# ========== 主函数 ==========

def main():
    """主函数"""

    agent = create_investment_agent()

    # 测试问题
    question = "现在美国经济如何？英伟达（NVDA）是否值得投资？"

    print("="*70)
    print(f"📝 问题: {question}")
    print("="*70)

    # 调用 Agent
    result = agent.invoke({
        "messages": [{"role": "user", "content": question}]
    })

    # 显示思考过程
    print("\n⚙️  Agent 思考过程:")
    for msg in result["messages"]:
        if isinstance(msg, dict):
            role = msg.get("role", "")
            if role == "assistant" and "tool_calls" in msg:
                for tool_call in msg.get("tool_calls", []):
                    print(f"  🔧 调用: {tool_call.get('name')}({tool_call.get('args', {})})")

    # 显示最终答案
    final_answer = result["messages"][-1]
    if isinstance(final_answer, dict):
        content = final_answer.get("content", "")
    else:
        content = final_answer.content

    print("\n📊 分析结果:")
    print("="*70)
    print(content)
    print("="*70)

if __name__ == "__main__":
    main()
```

## 📋 第六章：常见问题和解决方案

### Q1: ImportError: cannot import name 'create_react_agent'

**问题：**
```python
from langgraph.prebuilt import create_react_agent
ImportError: cannot import name 'create_react_agent'
```

**原因：** `create_react_agent` 已被弃用

**解决方案：**
```python
# ✅ 改用新 API
from langchain.agents import create_agent
```

### Q2: ModuleNotFoundError: No module named 'langchain.schema'

**问题：**
```python
from langchain.schema import HumanMessage
ModuleNotFoundError: No module named 'langchain.schema'
```

**原因：** 导入路径在 1.0 中改变了

**解决方案：**
```python
# ✅ 使用新路径
from langchain_core.messages import HumanMessage
```

### Q3: 依赖冲突错误

**问题：**
```
ERROR: pip's dependency resolver does not currently take into account all the packages...
langchain 0.3.27 requires langchain-core<1.0.0, but you have langchain-core 1.0.4
```

**原因：** 版本不兼容

**解决方案：**
```bash
# 升级所有相关包到 1.0+
pip install --upgrade langchain langchain-core langchain-openai langgraph
```

### Q4: fetch_macro_economic_data 参数问题

**问题：** 要不要给 `fetch_macro_economic_data` 加 `symbol` 参数？

**答案：不要！**

```python
# ❌ 错误 - 宏观数据不需要股票代码
@tool
def fetch_macro_economic_data(symbol: str) -> dict:
    return get_macro_economic_data()  # 函数不接受参数

# ✅ 正确 - GDP、利率等是全局数据
@tool
def fetch_macro_economic_data() -> dict:
    """获取美国宏观经济数据（无需参数）"""
    return get_macro_economic_data()
```

### Q5: 消息格式问题

**问题：** 使用 `HumanMessage` 还是字典？

**答案：两种都可以，但推荐字典格式**

```python
# ✅ 推荐：使用字典（更简单，不需要导入）
result = agent.invoke({
    "messages": [{"role": "user", "content": "问题"}]
})

# ✅ 也可以：使用消息对象
from langchain_core.messages import HumanMessage
result = agent.invoke({
    "messages": [HumanMessage(content="问题")]
})
```

## 📋 第七章：新旧 API 完整对照表

### 创建 Agent

| 步骤 | 旧 API | 新 API |
|------|-------|--------|
| 导入 | `from langgraph.prebuilt import create_react_agent` | `from langchain.agents import create_agent` |
| 创建 | `create_react_agent(model, tools, state_modifier)` | `create_agent(model, tools, system_prompt)` |
| 参数名 | `state_modifier="..."` | `system_prompt="..."` |

### 调用 Agent

| 方面 | 旧 API | 新 API |
|------|-------|--------|
| 消息格式 | `HumanMessage(content="...")` | `{"role": "user", "content": "..."}` |
| 调用方法 | `agent.invoke({"messages": [...]})` | `agent.invoke({"messages": [...]})` ✅ 相同 |
| 结果获取 | `result["messages"][-1]` | `result["messages"][-1]` ✅ 相同 |

### 导入路径

| 模块 | 旧路径 | 新路径 |
|------|-------|--------|
| HumanMessage | `langchain.schema` | `langchain_core.messages` |
| Agent 创建 | `langgraph.prebuilt` | `langchain.agents` |
| Tool 装饰器 | `langchain_core.tools` | `langchain_core.tools` ✅ 不变 |

## 📋 第八章：快速开始

### 1. 更新依赖

```bash
# 升级到 1.0
pip install --upgrade langchain langchain-core langchain-openai langgraph

# 验证版本
python -c "import langchain; print(langchain.__version__)"  # 应该 >= 1.0.0
```

### 2. 修改导入

```python
# 旧导入 ❌
from langgraph.prebuilt import create_react_agent
from langchain.schema import HumanMessage

# 新导入 ✅
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage  # 如果需要
```

### 3. 修改 Agent 创建

```python
# 旧代码 ❌
agent = create_react_agent(
    model=llm,
    tools=tools,
    state_modifier="系统提示词"
)

# 新代码 ✅
agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt="系统提示词"  # 注意参数名变化
)
```

### 4. 修改调用方式

```python
# 旧代码 ❌
from langchain_core.messages import HumanMessage
result = agent.invoke({
    "messages": [HumanMessage(content="问题")]
})

# 新代码 ✅（推荐）
result = agent.invoke({
    "messages": [{"role": "user", "content": "问题"}]
})
```

### 5. 运行测试

```bash
cd Agents
python tools_and_agents.py
```

## 🎯 总结

### 关键变化

1. **函数名变化**：`create_react_agent` → `create_agent`
2. **导入路径变化**：`langgraph.prebuilt` → `langchain.agents`
3. **参数名变化**：`state_modifier` → `system_prompt`
4. **导入路径变化**：`langchain.schema` → `langchain_core.messages`
5. **版本要求**：所有 langchain 相关包都需要升级到 1.0+

### 不变的部分

1. ✅ Tool 定义方式不变（仍使用 `@tool` 装饰器）
2. ✅ Agent 调用方式基本不变（仍使用 `invoke` 方法）
3. ✅ 结果获取方式不变（仍从 `result["messages"]` 获取）

### 推荐做法

1. **优先升级所有依赖到 1.0+**
2. **使用 `langchain.agents.create_agent`**
3. **使用简单的字典格式传递消息**
4. **阅读官方迁移指南**：https://docs.langchain.com/oss/python/migrate/langchain-v1

### 你需要修改的文件

1. **tools_and_agents.py** ✅ 已更新
2. **test_agent_basic.py** ✅ 已更新
3. **fundamental_analyst.py** ✅ 导入路径已修复

所有代码已更新到 LangChain 1.0 标准！🎉
