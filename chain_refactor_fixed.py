# 之前已经学习了prompt|llm|Parser的方式将prompt传进llm中，并通过Parser进行返回
# 学习了chain.invoke({})里装字典的方式将要分析的内容送进去，或者是直接在函数定义的时候将具体要大模型分析的内容送进去
# 学习了ChatPromptTemplate类能够传递符合OpenAI等大模型公司要求带有角色的promopt进入LLM。RunnablePassthrough作为管道
# 任务：用@chain包装fundamental_analyst.py中所有get_xxx函数

from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.runnables import RunnableParallel
from langchain_core.prompts import ChatPromptTemplate  # 用于把变量送进Prompt
from langchain_core.output_parsers import StrOutputParser  # |||后为字符串
from langchain_core.runnables import chain  # 导入@chain装饰器
from langchain_openai import ChatOpenAI
from typing import Any  # 类型提示
import os
from dotenv import load_dotenv
import sys
sys.path.append('/home/user/AI_Invest_Assistant/Agents')
from fundamental_analyst import *  # import * 一键导入fundamental_analyst.py文件中所有不以_开头的公开对象(包括函数、类、变量)

load_dotenv()
finnhub_api_key = os.getenv("FINNHUB_API_KEY")
finnhub_client = finnhub.Client(api_key=finnhub_api_key)
av_api_key = os.getenv("ALPHAVANTAGE_API_KEY")
fred_api_key = os.getenv("FRED_API_KEY")
fred_client = Fred(api_key=fred_api_key)

llm = ChatOpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    temperature=0.1,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    model="qwen-plus"
)


def rewrite_get_xx_function():
    """
    正确实现：使用@chain包装get_xxx函数，并确保键名匹配
    """

    @chain
    def fetch_macro_data(x):
        """获取宏观数据"""
        return get_macro_economic_data()

    @chain
    def fetch_company_profile_with_fallback(x):
        """获取公司资料（带容错）"""
        symbol = x["symbol"]
        try:
            profile = finnhub_client.company_profile2(symbol=symbol)
            return {
                '金融数据源来源': 'Finnhub',
                '名称': profile.get('name'),
                '行业': profile.get('finnhubIndustry'),
                'ipo时间': profile.get('ipo'),
                '市值(百万美元)': profile.get('marketCapitalization'),
                '官网': profile.get('weburl'),
                '描述': profile.get('description'),
            }
        except Exception as e:
            print(f"⚠️  Finnhub获取公司资料失败: {e}")
            print("🔄 切换为Alpha Vantage...")
            av_companyfile = FundamentalData(key=av_api_key, output_format='dict')
            overview, _ = av_companyfile.get_company_overview(symbol)
            return {
                '金融数据源来源': 'Alpha Vantage',
                '名称': overview.get('Name', 'N/A'),
                '行业': overview.get('Industry', 'N/A'),
                'ipo时间': overview.get('IPODate', 'N/A'),
                '市值(百万美元)': float(overview.get('MarketCapitalization', 0) / 1000000),
                '官网': 'N/A',  # Alpha Vantage不提供官网
                '描述': overview.get('Description', 'N/A'),
            }

    @chain
    def fetch_real_time_data_with_fallback(x):
        """获取实时报价（带容错）"""
        symbol = x["symbol"]
        try:
            real_time_data = finnhub_client.quote(symbol=symbol)
            timestamp = real_time_data.get('t')
            local_time = datetime.datetime.fromtimestamp(timestamp)
            formatted_local_time = local_time.strftime("%Y-%m-%d %H:%M:%S")
            return {
                'source': 'Finnhub',
                "最新成交价": real_time_data.get('c'),
                "当日最高价": real_time_data.get('h'),
                "当日最低价": real_time_data.get('l'),
                "当日开盘价": real_time_data.get('o'),
                "前一个交易日的收盘价": real_time_data.get('pc'),
                "上述数据的更新时间": formatted_local_time
            }
        except Exception as e:
            print(f"⚠️  Finnhub获取股票数据失败: {e}")
            print("🔄 切换为Alpha Vantage...")
            ts = TimeSeries(key=av_api_key, output_format='dict')
            quote, _ = ts.get_quote_endpoint(symbol)

            return {
                'source': 'Alpha Vantage',
                "最新成交价": float(quote.get('05. price', 0)),
                "当日最高价": float(quote.get('03. high', 0)),
                "当日最低价": float(quote.get('04. low', 0)),
                "当日开盘价": float(quote.get('02. open', 0)),
                "前一个交易日的收盘价": float(quote.get('08. previous close', 0)),
                "上述数据的更新时间": quote.get('07. latest trading day', 'N/A')
            }

    # 使用RunnableParallel并行获取所有数据
    parallel_fetcher = RunnableParallel(
        macro=fetch_macro_data,  # 宏观数据
        profile=fetch_company_profile_with_fallback,  # 公司资料
        quote=fetch_real_time_data_with_fallback,  # 实时报价
        symbol=lambda x: x["symbol"]  # 保留symbol
    )

    @chain
    def merge_all_data(x):
        """
        合并并行获取的数据
        ⚠️ 关键：确保键名与前面函数返回的键名一致！
        """
        macro = x["macro"]
        profile = x["profile"]
        quote = x["quote"]
        symbol = x["symbol"]

        return {
            # 基本信息
            "symbol": symbol,
            "名称": profile.get("名称", "N/A"),  # ✅ 使用中文键
            "行业": profile.get("行业", "N/A"),  # ✅ 使用中文键（不是'Industry'）
            "ipo时间": profile.get("ipo时间", "N/A"),  # ✅ 使用中文键（不是'IPODate'）
            "市值": profile.get("市值(百万美元)", "N/A"),  # ✅ 注意有括号！
            "官网": profile.get("官网", "N/A"),  # ✅ 使用中文键（不是'weburl'）
            "描述": profile.get("描述", "N/A"),  # ✅ 使用中文键（不是'Description'）

            # 实时报价数据
            "最新成交价": quote.get("最新成交价", "N/A"),  # ✅ 使用中文键（不是'05. price'）
            "当日最高价": quote.get("当日最高价", "N/A"),  # ✅ 使用中文键
            "当日最低价": quote.get("当日最低价", "N/A"),  # ✅ 使用中文键
            "当日开盘价": quote.get("当日开盘价", "N/A"),  # ✅ 使用中文键
            "前一个交易日的收盘价": quote.get("前一个交易日的收盘价", "N/A"),  # ✅ 使用中文键
            "上述数据的更新时间": quote.get("上述数据的更新时间", "N/A"),  # ✅ 使用中文键

            # 宏观数据（转为字符串以便在prompt中使用）
            "美元兑人民币": str(macro.get("美元兑人民币", "N/A")),
            "美元兑日元": str(macro.get("美元兑日元", "N/A")),
            "美元兑欧元": str(macro.get("美元兑欧元", "N/A")),
            "联邦基金目标利率": str(macro.get("联邦基金目标利率", "N/A")),
            "非农就业人数": str(macro.get("非农就业人数", "N/A")),
            "失业率": str(macro.get("失业率", "N/A")),
            "平均时薪": str(macro.get("平均时薪", "N/A")),
            "通胀数据": str(macro.get("通胀数据", "N/A")),
            "GDP数据": str(macro.get("GDP数据", "N/A"))
        }

    # 构建prompt模板
    prompt = ChatPromptTemplate.from_template("""
现在你的身份是一名顶级对冲基金的基金经理，你非常擅长根据美国宏观经济数据以及具体个股数据来进行投资。

【宏观经济环境】
- 汇率: 美元兑人民币 {美元兑人民币}, 美元兑日元 {美元兑日元}, 美元兑欧元 {美元兑欧元}
- 利率: {联邦基金目标利率}
- 就业: {非农就业人数}, {失业率}, {平均时薪}
- 通胀: {通胀数据}
- GDP: {GDP数据}

【个股基本信息】
- 股票代码: {symbol}
- 公司名称: {名称}
- 所属行业: {行业}
- IPO时间: {ipo时间}
- 市值: {市值} 百万美元
- 官网: {官网}
- 公司描述: {描述}

【最新交易数据】（更新时间: {上述数据的更新时间}）
- 最新成交价: ${最新成交价}
- 当日最高价: ${当日最高价}
- 当日最低价: ${当日最低价}
- 当日开盘价: ${当日开盘价}
- 前一交易日收盘价: ${前一个交易日的收盘价}

【分析要求】
1. 根据宏观经济数据，判断当前处于宽松还是紧缩环境，预测美联储未来货币政策方向
2. 结合宏观环境，分析该股票估值水平（被高估/低估）
3. 给出明确的投资建议（买入/持有/卖出）及理由
4. 分析逻辑清晰，从宏观到微观自上而下梳理
""")

    # 构建完整链
    full_chain = parallel_fetcher | merge_all_data | prompt | llm | StrOutputParser()

    # 执行（流式输出）
    print("=" * 50)
    print("开始分析 NVIDIA (NVDA)...")
    print("=" * 50)
    print("\n【分析结果】\n")

    for chunk in full_chain.stream({"symbol": "NVDA"}):
        print(chunk, end="", flush=True)  # 流式输出

    print("\n" + "=" * 50)


if __name__ == "__main__":
    rewrite_get_xx_function()
