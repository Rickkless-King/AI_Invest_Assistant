# 日志系统使用指南

## 概述

系统已集成日志记录功能，所有重要操作和错误都会自动记录到日志文件中。

## 日志文件位置

日志文件存储在 `AI_Invest_Assistant/logs/` 目录下：

- **app_YYYY-MM-DD.log** - 所有级别的日志（DEBUG, INFO, WARNING, ERROR, CRITICAL)
- **error_YYYY-MM-DD.log** - 只记录错误和严重错误

## 日志功能特性

### 1. 自动日志轮换
- 单个日志文件最大 10MB
- 自动保留最近 5 个备份文件
- 按日期命名，便于查找

### 2. 多级别日志
- **DEBUG**: 详细的调试信息
- **INFO**: 一般信息（如策略选择、回测完成）
- **WARNING**: 警告信息
- **ERROR**: 错误信息
- **CRITICAL**: 严重错误

### 3. 统一格式
```
[2026-01-07 22:00:00] [模块名] [级别] 日志消息
```

## 在代码中使用日志

### 导入日志模块

```python
from backend.utils.logger import get_logger

# 在模块开头初始化
logger = get_logger(__name__)
```

### 记录日志

```python
# 信息日志
logger.info("策略优化开始")

# 警告日志
logger.warning("数据可能不完整")

# 错误日志（自动包含堆栈信息）
try:
    # 你的代码
    pass
except Exception as e:
    logger.error(f"操作失败: {str(e)}", exc_info=True)
```

## 已集成日志的模块

当前已经在以下模块中集成了日志：

1. **backend/agents/strategy_agent.py**
   - 策略选择过程
   - 回测执行
   - 优化迭代
   - 错误捕获

2. **backend/utils/logger.py**
   - 日志管理器核心模块

## 查看日志

### 查看今天的所有日志
```bash
# Windows
type AI_Invest_Assistant\logs\app_2026-01-07.log

# Linux/Mac
cat AI_Invest_Assistant/logs/app_2026-01-07.log
```

### 查看今天的错误日志
```bash
# Windows
type AI_Invest_Assistant\logs\error_2026-01-07.log

# Linux/Mac
cat AI_Invest_Assistant/logs/error_2026-01-07.log
```

### 实时监控日志
```bash
# Windows (PowerShell)
Get-Content AI_Invest_Assistant\logs\app_2026-01-07.log -Wait

# Linux/Mac
tail -f AI_Invest_Assistant/logs/app_2026-01-07.log
```

## 日志级别说明

### 何时使用各级别

- **DEBUG**: 开发调试时使用，生产环境可关闭
  ```python
  logger.debug(f"变量值: {value}")
  ```

- **INFO**: 记录正常的业务流程
  ```python
  logger.info("用户登录成功")
  logger.info("策略优化完成")
  ```

- **WARNING**: 可能导致问题的情况
  ```python
  logger.warning("API调用接近限额")
  logger.warning("数据延迟超过预期")
  ```

- **ERROR**: 功能执行失败
  ```python
  logger.error("无法连接数据库")
  logger.error(f"策略执行失败: {error}", exc_info=True)
  ```

- **CRITICAL**: 系统级严重错误
  ```python
  logger.critical("配置文件损坏，系统无法启动")
  ```

## 日志最佳实践

1. **使用有意义的消息**: 清楚说明发生了什么
   ```python
   # Good
   logger.info(f"回测完成 - 策略: RSI, 收益率: 5.2%, 耗时: 2.3秒")

   # Bad
   logger.info("完成")
   ```

2. **包含关键上下文**: 记录相关变量和参数
   ```python
   logger.error(f"API调用失败 - URL: {url}, 状态码: {status_code}")
   ```

3. **错误时记录堆栈**: 使用 `exc_info=True`
   ```python
   try:
       risky_operation()
   except Exception as e:
       logger.error(f"操作失败: {str(e)}", exc_info=True)
   ```

4. **避免敏感信息**: 不要记录密码、API密钥等
   ```python
   # Bad
   logger.info(f"使用API密钥: {api_key}")

   # Good
   logger.info(f"使用API密钥: ***{api_key[-4:]}")
   ```

## 测试日志系统

运行测试脚本：
```bash
cd AI_Invest_Assistant/backend/utils
python logger.py
```

检查 `logs` 目录确认日志文件已创建。

## 故障排查

### 问题：日志文件未创建
- 检查 `logs` 目录权限
- 确保磁盘空间充足

### 问题：日志信息不完整
- 检查日志级别设置
- 确认 `exc_info=True` 用于捕获异常详情

### 问题：日志文件过大
- 日志会自动轮换，单文件限制 10MB
- 旧文件会自动归档，保留最近 5 个

## 未来改进

计划在以下模块中添加更多日志：
- [ ] 数据获取模块 (OKX API调用)
- [ ] 回测引擎 (详细交易记录)
- [ ] 前端交互 (用户操作日志)
- [ ] 数据库操作 (查询和更新)
