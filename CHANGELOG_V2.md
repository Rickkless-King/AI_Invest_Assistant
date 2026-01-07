# 系统更新日志 v2.0

## 🎉 版本 2.0.0 - 重大更新 (2026-01-07)

### ✨ 新功能

#### 1. 策略选择模式
- **🤖 LLM自动选择（推荐）**: Agent智能分析交易对和时间周期，自动选择最适合的策略
- **👤 手动指定策略**: 用户可以自己选择策略（RSI/MACD/BollingerBands）并手动调整所有参数

#### 2. 手动参数调整
用户可以精确控制策略参数：

**RSI策略**:
- RSI周期 (5-30，默认14)
- 超卖阈值 (10-40，默认30)
- 超买阈值 (60-90，默认70)

**MACD策略**:
- 快线周期 (5-20，默认12)
- 慢线周期 (15-40，默认26)
- 信号线周期 (5-15，默认9)

**布林带策略**:
- 布林带周期 (10-30，默认20)
- 标准差倍数 (1.0-3.0，默认2.0)

#### 3. 回测结果持久化
- ✅ 自动保存每次回测结果到SQLite数据库
- ✅ 记录策略类型、参数、性能指标
- ✅ 标记是LLM选择还是用户指定
- ✅ 可追溯历史优化过程

#### 4. 历史回测记录查询
- 📊 查看所有历史回测记录
- 🔍 按交易对、策略类型筛选
- 📈 显示完整性能指标
- 🏆 自动推荐最佳策略（按夏普比率或收益率）

#### 5. 多轮对话系统
- 💬 与Agent进行连续对话
- 📝 保存对话历史
- 🤖 Agent记住上下文
- 💡 可询问策略选择原因、参数调整建议等

### 📊 新增Tab界面

系统现在分为3个标签页：

1. **🚀 运行回测**: 配置并运行策略优化
2. **📊 历史记录**: 查看过往回测结果和最佳策略推荐
3. **💬 对话**: 与Agent进行多轮对话交流

### 🗄️ 数据库Schema更新

新增 `backtest_results` 表：

```sql
CREATE TABLE backtest_results (
    id INTEGER PRIMARY KEY,
    symbol TEXT,
    timeframe TEXT,
    strategy_name TEXT,
    params TEXT,  -- JSON格式
    total_return_pct REAL,
    sharpe_ratio REAL,
    max_drawdown_pct REAL,
    win_rate REAL,
    total_trades INTEGER,
    winning_trades INTEGER,
    losing_trades INTEGER,
    avg_return_pct REAL,
    data_points INTEGER,
    backtest_start_time DATETIME,
    backtest_end_time DATETIME,
    created_at DATETIME,
    user_specified BOOLEAN,  -- 0=LLM选择, 1=用户指定
    notes TEXT
)
```

### 🔧 API更新

#### HistoricalDataManager 新增方法

```python
# 保存回测结果
manager.save_backtest_result(
    symbol="BTC-USDT",
    timeframe="1H",
    strategy_name="RSI",
    params={'rsi_period': 14, ...},
    metrics={...},
    df=data_frame,
    user_specified=True,  # 标记是否用户指定
    notes="用户手动调参"
)

# 查询历史记录
history_df = manager.get_backtest_history(
    symbol="BTC-USDT",  # 可选筛选
    strategy_name="RSI",  # 可选筛选
    limit=20
)

# 获取最佳策略
best = manager.get_best_strategy(
    symbol="BTC-USDT",
    timeframe="1H",
    metric='sharpe_ratio'  # 或 'total_return_pct'
)
```

#### StrategyAgent 新增参数

```python
# 运行Agent with用户指定策略
agent.run(
    symbol="BTC-USDT",
    timeframe="1H",
    user_strategy="MACD",  # 可选
    user_params={'fast_period': 10, 'slow_period': 20, 'signal_period': 5}  # 可选
)
```

### 🐛 Bug修复

1. **修复无限循环问题**: Agent迭代计数器未递增导致的25次递归限制错误
   - 在 `_optimize_params_node` 中添加 `iteration` 递增
   - 增加 `recursion_limit` 配置为30

2. **修复session_state键名不一致**: 将 `strategy_result` 统一改为 `current_result`

### 📈 性能改进

- 数据库自动保存减少重复计算
- 历史记录快速查询（带索引）
- 最佳策略推荐算法优化

### 💡 使用示例

#### 场景1: LLM自动选择策略
```
1. 选择"🤖 LLM自动选择（推荐）"
2. 点击"🚀 启动Agent优化"
3. Agent自动选择最佳策略并优化参数
4. 在"💬 对话"标签询问："为什么选择这个策略？"
```

#### 场景2: 手动调参测试
```
1. 选择"👤 手动指定策略"
2. 选择MACD策略
3. 设置 fast_period=10, slow_period=20, signal_period=5
4. 运行回测
5. 查看"📊 历史记录"对比不同参数效果
```

#### 场景3: 查询最佳历史策略
```
1. 进入"📊 历史记录"标签
2. 筛选交易对和策略类型
3. 查看"🏆 最佳策略推荐"
4. 复制最佳参数到"运行回测"页面
```

### 🔄 升级指南

#### 1. 数据库自动升级
首次运行时，系统会自动创建 `backtest_results` 表，无需手动操作。

#### 2. 旧版session_state兼容
如果遇到 `strategy_result` 相关错误，请：
```python
# 清除旧的session state
streamlit run frontend/streamlit_app.py
# 点击左上角 ⋮ → Clear cache
```

#### 3. API密钥配置
确保 `.env` 文件包含：
```
DEEPSEEK_API_KEY=your_key_here
DASHSCOPE_API_KEY=your_key_here  # 可选
```

### 📝 已知问题

1. **多轮对话限制**: 当前仅保留最近3轮对话作为上下文，避免token超限
2. **历史记录数量**: 建议定期清理数据库，保持查询性能

### 🚀 下一步规划

- [ ] 添加策略对比功能（同时运行多个策略）
- [ ] 导出回测报告（PDF/Excel）
- [ ] 实时交易信号推送
- [ ] 策略组合优化（Portfolio）

---

## 💬 用户反馈

### Q1: 策略选择是LLM决定还是随机的？
**A**: LLM智能决定。Agent会根据交易对特征和时间周期，分析市场特性后选择最适合的策略。

### Q2: 能否保存回测结果？
**A**: 是的！v2.0自动保存所有回测结果到数据库，可在"📊 历史记录"标签查看。

### Q3: Streamlit支持多轮对话吗？
**A**: v2.0已完整支持！在"💬 对话"标签可以进行连续对话，Agent会记住上下文。

### Q4: 如何手动调整参数？
**A**: 在"运行回测"页面选择"👤 手动指定策略"，即可精确设置所有参数。

---

## 📞 技术支持

如有问题，请查看：
- [SYSTEM_OVERVIEW.md](SYSTEM_OVERVIEW.md) - 系统完整概览
- [HISTORICAL_DATA_GUIDE.md](HISTORICAL_DATA_GUIDE.md) - 数据管理详解
- [STRATEGY_AGENT_GUIDE.md](STRATEGY_AGENT_GUIDE.md) - Agent使用指南
