# Langchain Agent 使用教程

## 问题分析与解决方案

### 原始问题

您遇到的错误：
```
ValueError: Function must have a docstring if description not provided.
```

### 根本原因

1. **`fetch_macro_economic_data` 函数参数错误**
   - 原代码：`def fetch_macro_economic_data(symbol:str)->dict:`
   - 问题：宏观经济数据不需要 `symbol` 参数
   - 底层函数 `get_macro_economic_data()` 不接受任何参数

2. **prompt 语法错误**
   - 原代码：`("human",{input})`
   - 正确：`("human","{input}")`

3. **API 版本不兼容**
   - 您的代码使用了旧版 langchain API (`AgentExecutor`, `create_tool_calling_agent`)
   - 项目使用 langchain 1.0+ 和 langgraph，这些 API 已经改变

## 修复内容

### 1. 修复 Tool 定义

**错误的写法：**
```python
@tool("获取美国宏观经济数据,输入参数为股票代码...")
def fetch_macro_economic_data(symbol:str)->dict:  # ❌ 不应该有 symbol 参数
    return get_macro_economic_data()
```

**正确的写法：**
```python
@tool
def fetch_macro_economic_data() -> dict:
    """
    获取美国宏观经济数据

    返回格式:
        包含宏观经济指标的字典，包括汇率、利率、就业数据、通胀数据、GDP数据等

    注意: 此函数不需要输入参数，返回最新的美国宏观经济数据
    """
    return get_macro_economic_data()
```

### 2. 使用新的 LangGraph API

**旧的 API（已弃用）：**
```python
from langchain.agents import AgentExecutor, create_tool_calling_agent

agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools)
```

**新的 API（推荐）：**
```python
from langgraph.prebuilt import create_react_agent

agent_executor = create_react_agent(
    model=llm,
    tools=tools,
    state_modifier=system_message  # 直接传入系统提示词
)
```

### 3. 正确的调用方式

**新的 API 使用：**
```python
result = agent_executor.invoke({
    "messages": [HumanMessage(content=user_question)]
})
```

### 4. 修复 fundamental_analyst.py 导入

**错误的导入：**
```python
from langchain.schema import HumanMessage, FunctionMessage
```

**正确的导入：**
```python
from langchain_core.messages import HumanMessage, FunctionMessage
```

## 使用方法

### 前置条件

1. **安装依赖（如果还没安装）：**
```bash
cd /home/user/AI_Invest_Assistant
pip install -r requirements.txt

# 如果遇到版本冲突，升级 langchain-core
pip install --upgrade langchain-core
```

2. **配置环境变量（创建 .env 文件）：**
```bash
# 在项目根目录创建 .env 文件
touch /home/user/AI_Invest_Assistant/Agents/.env
```

在 `.env` 文件中添加以下内容：
```
# 阿里云 DashScope API Key
DASHSCOPE_API_KEY=your_dashscope_api_key_here

# Finnhub API Key
FINNHUB_API_KEY=your_finnhub_api_key_here

# Alpha Vantage API Key
ALPHAVANTAGE_API_KEY=your_alphavantage_api_key_here

# FRED (Federal Reserve Economic Data) API Key
FRED_API_KEY=your_fred_api_key_here

# EODHD API Key
EODHD_API_KEY=your_eodhd_api_key_here

# Twelve Data API Key (修正 KEY 名称)
TWELVE_DATA_API_KEY=your_twelve_data_api_key_here
```

**重要提示**：fundamental_analyst.py 第58行有一个问题：
```python
# 错误：
twelve_client=TDClient(apikey="TWELVE_DATA_API_KEY")  # ❌ 这里是字符串而不是变量

# 应该改为：
twelve_client=TDClient(apikey=os.getenv("TWELVE_DATA_API_KEY"))  # ✅
```

### 运行 Agent

```bash
cd /home/user/AI_Invest_Assistant/Agents
python tools_and_agents.py
```

## Agent 工作原理

### ReAct Pattern

Agent 使用 ReAct（Reasoning + Acting）模式：

1. **Reasoning（推理）**：分析当前任务，决定下一步
2. **Action（行动）**：调用某个 Tool 获取数据
3. **Observation（观察）**：获取 Tool 返回结果
4. **重复 1-3 直到完成任务**

### 示例执行流程

```
用户问题: 现在美国经济如何？英伟达是否值得投资？

Agent 思考: 我需要先获取宏观经济数据
↓
调用工具: fetch_macro_economic_data()
↓
获得结果: {美元汇率、利率、就业数据...}
↓
Agent 思考: 现在我需要获取英伟达的数据
↓
调用工具: fetch_company_profile("NVDA")
调用工具: fetch_real_time_data("NVDA")
↓
获得结果: {公司信息、股价数据...}
↓
Agent 思考: 现在我有了所有数据，可以给出分析了
↓
最终回答: 综合分析宏观经济环境和英伟达财务状况...
```

## 关于 print vs return 的问题

您提到的关于 `with_fallback` 函数中 print 的问题：

**当前实现（已经是正确的）：**
```python
def get_company_profile_with_fallback(symbol:str) -> dict:
    try:
        # Finnhub 获取数据
        profile = finnhub_client.company_profile2(symbol=symbol)
        return {  # ✅ 返回字典
            '金融数据源来源':'Finnhub',
            '名称':profile.get('name'),
            # ...
        }
    except Exception as e:
        print(f"Finnhub调用失败：{e}")  # 这个 print 用于调试，保留也可以
        print("切换为Alpha Vantage...")

    try:
        # Alpha Vantage 获取数据
        fd = FundamentalData(key=av_api_key, output_format='dict')
        overview, _ = fd.get_company_overview(symbol)
        return {  # ✅ 返回字典
            '金融数据来源':'Alpha Vantage',
            # ...
        }
    except Exception as e2:
        return {'error': f"Both APIs failed:{e},{e2}"}  # ✅ 即使失败也返回字典
```

**这个实现是正确的**：
- 成功时返回数据字典
- 失败时返回包含错误信息的字典
- print 语句只是用于调试输出，不影响返回值
- 如果想要完全静默，可以移除 print 或改用 logging

## 完整代码示例

查看 `/home/user/AI_Invest_Assistant/Agents/tools_and_agents.py` 获取完整的、已修复的代码。

## 面试问题准备

### Q1: Tool和普通函数有什么区别？
**A:** Tool是带类型标注和文档字符串的函数，LLM可以：
1. 自动识别工具功能（通过docstring）
2. 决定何时调用哪个工具
3. 正确传递参数

我用@tool装饰器包装数据获取函数，让Agent自动组合调用。

### Q2: Agent的工作原理是什么？
**A:** Agent的核心是ReAct循环：
1. Reasoning（推理）：分析当前任务，决定下一步
2. Action（行动）：调用某个Tool
3. Observation（观察）：获取Tool返回结果
4. 重复1-3直到完成任务

我的项目中，Agent会自动决定先查宏观数据还是先查个股数据。

### Q3: 你项目中为什么用Agent？
**A:** 因为投资分析是多步骤任务：
1. 需要获取多个数据源
2. 数据之间有依赖关系（先宏观后微观）
3. 不同股票需要不同分析流程

用Agent可以让AI自动规划最优路径，而不是硬编码流程。

### Q4: Agent有什么局限性？
**A:** 主要有三个：
1. 成本高：每次推理都要调用LLM
2. 不稳定：可能陷入死循环或调用错误工具
3. 延迟高：多步推理需要时间

我的解决方案：
- 设置 max_iterations 参数防止死循环（LangGraph自动处理）
- 用清晰的系统提示词引导Agent
- 对高频任务用固定Chain代替Agent

## 下一步

1. ✅ 修复了 Tool 定义和 API 兼容性问题
2. ✅ 更新为使用 LangGraph 的新 API
3. ⏰ 配置环境变量（创建 .env 文件）
4. ⏰ 运行测试并验证 Agent 工作正常
5. ⏰ 更新 README 文档，添加"Agent 架构设计"章节

## 故障排除

### 问题：`ValueError: Function must have a docstring`
- **原因**：Tool 函数缺少 docstring 且没有显式提供 description
- **解决**：为每个 @tool 装饰的函数添加 docstring（三引号注释）

### 问题：`ImportError: cannot import name 'AgentExecutor'`
- **原因**：使用了已弃用的旧 API
- **解决**：改用 `langgraph.prebuilt.create_react_agent`

### 问题：`ValueError: You need to set a valid API key`
- **原因**：缺少 .env 文件或 API key 未配置
- **解决**：创建 .env 文件并添加所有必需的 API keys
