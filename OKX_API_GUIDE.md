# OKX API 集成使用指南

## 📋 概述

本项目已集成 OKX API v5，支持实时行情查询、账户管理和交易下单功能。

## 🔑 API 密钥配置

### 方法1：通过 Streamlit 界面配置（推荐）

1. 启动应用：`streamlit run frontend/streamlit_app.py`
2. 进入 "🔑 API配置与交易" 页面
3. 点击 "📝 配置 API 密钥"
4. 输入你的 API 凭证并保存

### 方法2：通过 .env 文件配置

1. 在 `AI_Invest_Assistant/` 目录下创建 `.env` 文件
2. 添加以下配置：

```bash
# OKX API 配置
OKX_API_KEY=your_api_key_here
OKX_SECRET_KEY=your_secret_key_here
OKX_PASSPHRASE=your_passphrase_here

# 交易模式（1=模拟盘，0=实盘）
OKX_DEMO_TRADING=1
```

## 🎯 如何获取 OKX API 密钥

1. 登录 [OKX 官网](https://www.okx.com/)
2. 进入 **账户** → **API 管理**
3. 点击 **创建 API**
4. 设置权限：
   - ✅ 读取
   - ✅ 交易
   - ❌ 提现（不建议开启）
5. 绑定 IP 地址（可选，但更安全）
6. 保存生成的：
   - API Key
   - Secret Key  
   - Passphrase（你自己设置的密码）

⚠️ **重要提示**：API 密钥只显示一次，请妥善保管！

## 🚀 功能列表

### 1. 公共接口（无需 API Key）

- ✅ 获取实时行情
- ✅ 获取 K 线数据
- ✅ 计算技术指标（RSI、MACD、布林带）

### 2. 私有接口（需要 API Key）

- ✅ 查询账户余额
- ✅ 下单（市价单、限价单）
- ✅ 查询订单状态
- ✅ 取消订单
- ✅ 查询持仓
- ✅ 查询订单历史

## 💡 使用示例

### Python 代码示例

```python
from backend.data_fetchers.okx_fetcher import OKXFetcher

# 1. 公共数据（不需要 API Key）
fetcher = OKXFetcher()
ticker = fetcher.get_ticker("BTC-USDT")
print(f"BTC 价格: ${ticker['last']:,.2f}")

# 2. 私有数据（需要 API Key）
api_fetcher = OKXFetcher(
    api_key="your_key",
    secret_key="your_secret",
    passphrase="your_passphrase",
    demo=True  # 模拟盘模式
)

# 查询余额
balance = api_fetcher.get_account_balance()
print(balance)

# 下单（限价单）
order = api_fetcher.place_order(
    symbol="BTC-USDT",
    side="buy",
    order_type="limit",
    size=0.001,
    price=40000
)
print(order)
```

### Streamlit 界面使用

1. **实时行情**：查看币价、K线、技术指标
2. **API配置与交易**：
   - 配置 API 密钥
   - 查看账户余额
   - 实时下单交易
   - 查看订单历史
3. **历史数据**：保存和查询 K 线数据
4. **交易记录**：管理交易记录

## ⚠️ 安全提示

1. **永远不要**将 API 密钥提交到 Git 仓库
2. `.env` 文件已在 `.gitignore` 中，不会被提交
3. **建议先使用模拟盘**测试（`OKX_DEMO_TRADING=1`）
4. 实盘交易时设置 **IP 白名单**
5. 不要给 API 密钥 **提现权限**
6. 定期更换 API 密钥

## 🔧 故障排除

### 1. "需要配置 API Key"

- 检查 `.env` 文件是否存在
- 检查环境变量是否正确加载
- 尝试通过 Streamlit 界面重新配置

### 2. "签名验证失败"

- 确认 API Key、Secret Key、Passphrase 正确
- 检查系统时间是否准确
- 确认 API 权限包含 "交易"

### 3. "模拟盘账户余额为 0"
- 模拟盘的账户与欧易的账户是互通的，如果已经有了欧易账户，可以直接登录。
- 模拟盘API交易需要再模拟盘上创建APIKEY：登录欧易账户→交易→模拟交易→个人中心→创建模拟盘API KEY→开始模拟交易 


## 📚 参考文档

- [OKX API 官方文档](https://www.okx.com/docs-v5/en/)
- [OKX API v5 指南](https://www.okx.com/en-us/learn/complete-guide-to-okex-api-v5-upgrade)
- [Wundertrading OKX API 教程](https://wundertrading.com/journal/en/learn/article/okx-api)

## 🎓 下一步

1. 测试模拟盘交易
2. 验证 API 功能正常
3. 开发自动交易策略
4. 集成 AI 分析功能

---

**祝你交易顺利！** 🚀

如有问题，请参考官方文档或提交 Issue。
