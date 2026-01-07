"""
OKX 模拟盘 API 测试脚本
"""
from backend.data_fetchers.okx_fetcher import OKXFetcher
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

print("=" * 60)
print("OKX 模拟盘 API 完整测试")
print("=" * 60)

# 初始化 OKX Fetcher（会自动从.env读取配置）
fetcher = OKXFetcher()

print(f"\n📌 配置信息:")
print(f"   API Key: {fetcher.api_key[:10]}..." if fetcher.api_key else "   API Key: 未配置")
print(f"   模拟盘模式: {'是' if fetcher.demo else '否'}")
print(f"   x-simulated-trading: {fetcher.simulated}")

# 测试1: 获取账户余额
print("\n" + "=" * 60)
print("测试 1: 查询账户余额")
print("=" * 60)

balance = fetcher.get_account_balance()
if 'error' not in balance:
    print(f"✅ 总权益: ${balance.get('total_equity', 0):,.2f}")
    print(f"\n💰 各币种余额:")
    for currency, amount in balance.get('balances', {}).items():
        print(f"   {currency}: {amount:,.6f}")
else:
    print(f"❌ 错误: {balance['error']}")

# 测试2: 查询持仓
print("\n" + "=" * 60)
print("测试 2: 查询当前持仓")
print("=" * 60)

positions = fetcher.get_positions()
if positions:
    print(f"✅ 找到 {len(positions)} 个持仓:")
    for pos in positions:
        print(f"   {pos['symbol']}: {pos['size']} ({pos['side']})")
else:
    print("📭 当前无持仓")

# 测试3: 查询订单历史
print("\n" + "=" * 60)
print("测试 3: 查询历史订单")
print("=" * 60)

orders = fetcher.get_order_history(limit=5)
if orders:
    print(f"✅ 找到 {len(orders)} 个历史订单:")
    for order in orders[:3]:  # 只显示前3个
        print(f"   {order['symbol']} - {order['side']} - {order['status']}")
else:
    print("📭 暂无历史订单")

# 测试4: 下单测试（限价单 - 不会成交的价格）
print("\n" + "=" * 60)
print("测试 4: 下单测试（限价单）")
print("=" * 60)

# 获取当前BTC价格
ticker = fetcher.get_ticker("BTC-USDT")
current_price = ticker.get('last', 0)

if current_price > 0:
    # 设置一个远低于市场价的买入价（不会立即成交）
    test_price = current_price * 0.8  # 低于市价20%
    
    print(f"📊 当前BTC价格: ${current_price:,.2f}")
    print(f"🎯 测试下单价格: ${test_price:,.2f} (不会成交)")
    
    order_result = fetcher.place_order(
        symbol="BTC-USDT",
        side="buy",
        order_type="limit",
        size=0.001,  # 0.001 BTC
        price=test_price
    )
    
    if 'error' not in order_result:
        print(f"✅ 订单提交成功!")
        print(f"   订单ID: {order_result['orderId']}")
        print(f"   状态: {order_result['status']}")
        print(f"   消息: {order_result['message']}")
        
        # 查询订单状态
        print(f"\n🔍 查询订单状态...")
        order_status = fetcher.get_order("BTC-USDT", order_result['orderId'])
        if 'error' not in order_status:
            print(f"   状态: {order_status['status']}")
            print(f"   成交: {order_status['filled']} / {order_status['size']}")
        
        # 取消订单
        print(f"\n🚫 取消订单...")
        cancel_result = fetcher.cancel_order("BTC-USDT", order_result['orderId'])
        if 'error' not in cancel_result:
            print(f"   ✅ 取消成功: {cancel_result['message']}")
        else:
            print(f"   ❌ 取消失败: {cancel_result['error']}")
    else:
        print(f"❌ 下单失败: {order_result['error']}")
else:
    print("❌ 无法获取当前价格，跳过下单测试")

print("\n" + "=" * 60)
print("✅ 测试完成!")
print("=" * 60)
