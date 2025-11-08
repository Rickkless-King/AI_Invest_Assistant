"""
测试batch语法的简单验证脚本
"""

# 模拟symbols列表
symbols = ["AAPL", "MSFT", "GOOGL", "NVDA", "AMD"]

# 错误的方式（会导致只有一个字典）
wrong_way = [{"symbol": x for x in symbols}]
print("❌ 错误方式的结果：")
print(f"  类型：{type(wrong_way)}")
print(f"  长度：{len(wrong_way)}")
print(f"  内容：{wrong_way}")
print()

# 正确的方式（会生成字典列表）
correct_way = [{"symbol": x} for x in symbols]
print("✅ 正确方式的结果：")
print(f"  类型：{type(correct_way)}")
print(f"  长度：{len(correct_way)}")
print(f"  内容：{correct_way}")
print()

# 验证zip用法
results = ["result1", "result2", "result3", "result4", "result5"]
print("✅ zip使用示例：")
for company, result in zip(symbols, results):
    print(f"  {company}: {result}")
