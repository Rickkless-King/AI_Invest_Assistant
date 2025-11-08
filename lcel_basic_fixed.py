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

# ## 下面是模仿我之前的get_XXX函数格式
# def get_company_profile(symbol:str)->dict:
#     """
#     模拟从Finnhub获取数据
#     """
#     return{
#         "name":"NVDA",
#         "industry":"Semiconductor",
#         "marketCap":400000000
#     }

# def get_real_time_data(symbol:str)->dict:
#     """
#     模拟获取实时数据
#     """
#     return{
#         "price":177.78,
#         "pe":52.13
#     }

## task1:用RunnableLambda包装函数
def basic_lambda_example():
    # 直接用RunnableLambda将普通函数包装成组件
    fetch_profile = RunnableLambda[Any, dict](lambda x: get_company_profile(x["symbol"]))
    # # RunnableLambda[输入类型，输出类型]，指定传给RunnableLambda的输入数据(即 lambda的参数x)的类型，
    # 输出类型指定RunnableLambda最终输出数据的类型。
    # 总的来说表示输入给RunnableLambda的data可以使任意类型，而输出类型必须是字典。
    # 从.invoke({"symbol":"NVDA"})这里面提取"symbol"键对应的value，即"NVDA"→→get_company_profille("NVDA")
    @chain  # 用@chain装饰器把普通函数fetch_and_format变成Langchain的Runnable，这样就能用管道符|把它和其他组件串起来。
    def fetch_and_format(input_dict):
        # 获取数据
        symbol = input_dict["symbol"]
        profile = get_company_profile(symbol)
        quote = get_real_time_data(symbol)

        # 格式化成prompt需要的格式
        return {
            "symbol": symbol,
            "data": f"{profile['名称']} - 市值：${profile['市值(百万美元)']}百万美元"
        }
    # 构建链
    prompt = ChatPromptTemplate.from_template("分析{symbol}:{data}")  # 用ChatPromptTemplate定义一个模板字符串(可绑定到链的输入变量)
    chain_example = fetch_and_format | prompt | llm | StrOutputParser()

    result = chain_example.invoke({"symbol": "NVDA"})  # 1.把输入的{"symbol":"NVDA"}转换成{"symbol":"NVDA","data":"XXXXX"}
    # 2.把上述字典喂给Prompt模板
    # 3.用StrOUtputParser确保产出产出是一段纯文本
    print(result)


# task2：并行获取多个数据源
def parallel_data_fetching():
    # 使用RunnableParallel进行并行分析

    # 这里必须要使用@chain将两个函数转换为Runnable才可以被RunnableParallel调用
    @chain
    def fetch_profile(x):
        return get_company_profile(x["symbol"])

    @chain
    def fetch_quote(x):
        return get_real_time_data(x["symbol"])

    # 并行执行
    parallel_fetcher = RunnableParallel[Any](  # 泛型参数Any表示"输入数据类型可以是任意类型"
        # 通过RunnableParallel的输出必然是字典
        profile=fetch_profile,  # 这里不需要传入参数x，因为RunnableParallel会自动把输入数据分法给子Runnable
        quote=fetch_quote,  # 即RunnableParallel会自动把XXX_chain。invoke({字典})中的字典作为x传入，即x={"symbol":"NVDA"}
        symbol=lambda x: x["symbol"]
        # 上面这3个都是变量名作为key，fetch_profile/fetch_quote/等作为value的组成 即通过RunnableParallel之后，
        # 输出为一个{"profile":get_comapny_profile('NVDA')的结果，"quote":get_real_time_data('NVDA')的结果}类似这样的字典
        #
    )
    # 总的来说，Langchain的Runnable生态具有"自动数据传递"特性，不用关心数据怎么分给每个组件，只需定义"要执行哪些任务"。
    # 格式化数据
    @chain
    def format_data(x):
        return {
            "symbol": x["symbol"],
            "analysis_input": f"""公司：{x['profile']['名称']},行业:{x['profile']['行业']},最新成交价:{x["quote"]["最新成交价(免费版是延时15min的数据)"]}"""
        }

    # 构建完整链
    prompt = ChatPromptTemplate.from_template(
        "分析{symbol}的投资价值：{analysis_input}"  # prompt里面的文字基本上看上面return返回的key，作为prompt里面{XXX}的内容
    )
    full_chain = (parallel_fetcher | format_data | prompt | llm | StrOutputParser())

    result = full_chain.invoke({"symbol": "NVDA"})
    print(result)


# 任务3:容错处理
def error_handling_chain():
    # 学习在链中处理异常
    @chain  # 使用@chain装饰器，将下面的函数变为Runnable。
    def fetch_with_fallback(x):  # 这里的输入x为{"symbol":"NVDA"}
        symbol = x["symbol"]  # 获取symbol对应的value "NVDA"
        try:
            # 尝试主数据源(Finnhub)
            data = get_company_profile(symbol)  # 使用get_company_profile()获取返回字典
            data["source"] = "Finnhub"  # 继续往里面添加key_value对
            return data
        except Exception as e:
            print(f"主数据源失败:{e}")  # 如果报错，这里输出报错原因
            # 切换备用数据源
            return {
                "名称": f"{symbol}Corp",
                "行业": "Unknown",
                "市值(百万美元)": 0,
                "source": "Fallback"
            }

    # 构建链
    prompt = ChatPromptTemplate.from_template("分析{名称}(数据源{source})")

    chain_example = fetch_with_fallback | prompt | llm | StrOutputParser()

    result = chain_example.invoke({"symbol": "NVDA"})
    print(result)


# ==================== 正确的实现方式 ====================
def rewrite_get_functions():
    """
    正确的方式：使用RunnableParallel并行获取所有数据，然后合并后传给prompt
    """

    # 1. 包装宏观数据获取函数（不需要symbol参数）
    @chain
    def fetch_macro(x):
        """获取宏观数据，忽略输入参数"""
        return get_macro_economic_data()

    # 2. 包装公司资料获取函数（带容错）
    @chain
    def fetch_profile(x):
        symbol = x["symbol"]
        try:
            profile = finnhub_client.company_profile2(symbol=symbol)
            return {
                'source': 'Finnhub',
                '名称': profile.get('name'),
                '行业': profile.get('finnhubIndustry'),
                'ipo时间': profile.get('ipo'),
                '市值': profile.get('marketCapitalization'),
                '官网': profile.get('weburl'),
                '描述': profile.get('description'),
            }
        except Exception as e:
            print(f"⚠️  Finnhub获取公司资料失败: {e}")
            print("🔄 切换为Alpha Vantage...")

            av_company_profile = FundamentalData(key=av_api_key, output_format='dict')
            overview, _ = av_company_profile.get_company_overview(symbol)
            return {
                'source': 'Alpha Vantage',
                '名称': overview.get('Name', 'N/A'),
                '行业': overview.get('Industry', 'N/A'),
                'ipo时间': overview.get('IPODate', 'N/A'),
                '市值': float(overview.get('MarketCapitalization', 0) / 1000000),
                '官网': 'N/A',
                '描述': overview.get('Description', 'N/A'),
            }

    # 3. 包装实时数据获取函数（带容错）
    @chain
    def fetch_quote(x):
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
                "前一日收盘价": real_time_data.get('pc'),
                "更新时间": formatted_local_time
            }
        except Exception as e:
            print(f"⚠️  Finnhub获取实时数据失败: {e}")
            print("🔄 切换为Alpha Vantage...")

            ts = TimeSeries(key=av_api_key, output_format='dict')
            quote, _ = ts.get_quote_endpoint(symbol)
            return {
                'source': 'Alpha Vantage',
                "最新成交价": float(quote.get('05. price', 0)),
                "当日最高价": float(quote.get('03. high', 0)),
                "当日最低价": float(quote.get('04. low', 0)),
                "当日开盘价": float(quote.get('02. open', 0)),
                "前一日收盘价": float(quote.get('08. previous close', 0)),
                "更新时间": quote.get('07. latest trading day', 'N/A')
            }

    # 4. 使用RunnableParallel并行获取所有数据
    parallel_fetcher = RunnableParallel(
        macro=fetch_macro,      # 宏观数据
        profile=fetch_profile,  # 公司资料
        quote=fetch_quote,      # 实时报价
        symbol=lambda x: x["symbol"]  # 保留symbol以便后续使用
    )

    # 5. 合并数据并格式化
    @chain
    def merge_and_format(x):
        """将并行获取的数据合并成一个字典，供prompt使用"""
        macro = x["macro"]
        profile = x["profile"]
        quote = x["quote"]
        symbol = x["symbol"]

        # 返回一个扁平化的字典，包含所有需要的字段
        return {
            "symbol": symbol,
            "名称": profile.get("名称", "N/A"),
            "行业": profile.get("行业", "N/A"),
            "描述": profile.get("描述", "N/A"),
            "ipo时间": profile.get("ipo时间", "N/A"),
            "市值": profile.get("市值", "N/A"),
            "更新时间": quote.get("更新时间", "N/A"),
            "最新成交价": quote.get("最新成交价", "N/A"),
            "当日最高价": quote.get("当日最高价", "N/A"),
            "当日最低价": quote.get("当日最低价", "N/A"),
            "当日开盘价": quote.get("当日开盘价", "N/A"),
            "前一日收盘价": quote.get("前一日收盘价", "N/A"),
            # 宏观数据
            "美元兑人民币": str(macro.get("美元兑人民币", "N/A")),
            "美元兑日元": str(macro.get("美元兑日元", "N/A")),
            "美元兑欧元": str(macro.get("美元兑欧元", "N/A")),
            "联邦基金目标利率": str(macro.get("联邦基金目标利率", "N/A")),
            "非农就业人数": str(macro.get("非农就业人数", "N/A")),
            "失业率": str(macro.get("失业率", "N/A")),
            "通胀数据": str(macro.get("通胀数据", "N/A")),
            "GDP数据": str(macro.get("GDP数据", "N/A")),
        }

    # 6. 构建prompt模板（注意：使用 {名称} 而不是 {"名称"}）
    prompt = ChatPromptTemplate.from_template("""
请结合我提供的宏观经济数据以及微观个股数据，分析 {名称} 公司。

【公司基本信息】
- 股票代码: {symbol}
- 行业: {行业}
- 描述: {描述}
- IPO时间: {ipo时间}
- 市值: {市值} 百万美元

【最新交易数据】（更新时间: {更新时间}）
- 最新成交价: ${最新成交价}
- 当日最高价: ${当日最高价}
- 当日最低价: ${当日最低价}
- 当日开盘价: ${当日开盘价}
- 前一日收盘价: ${前一日收盘价}

【宏观经济环境】
- 汇率: 美元兑人民币 {美元兑人民币}, 美元兑日元 {美元兑日元}, 美元兑欧元 {美元兑欧元}
- 利率: {联邦基金目标利率}
- 就业: {非农就业人数}, {失业率}
- 通胀: {通胀数据}
- GDP: {GDP数据}

请从以下角度进行分析：
1. 当前宏观经济环境判断（宽松/紧缩）
2. 结合宏观环境，该股票估值水平如何
3. 投资建议（买入/持有/卖出）及理由
""")

    # 7. 构建完整的链
    full_chain = (
        parallel_fetcher       # 并行获取数据
        | merge_and_format    # 合并格式化
        | prompt              # 生成prompt
        | llm                 # 调用LLM
        | StrOutputParser()   # 解析输出
    )

    # 8. 执行（使用流式输出）
    print("=" * 50)
    print("开始分析...")
    print("=" * 50)
    print("\n【分析结果】")
    # 使用 .stream() 方法实现流式输出
    for chunk in full_chain.stream({"symbol": "NVDA"}):
        print(chunk, end="", flush=True)  # end="" 避免换行，flush=True 立即输出
    print("\n" + "=" * 50)


# ==================== 测试所有示例 ====================
if __name__ == "__main__":  # ✅ 修正：添加缺失的两个下划线
    print("\n" + "=" * 50)
    print("正确的实现：包装fundamental_analyst.py中的get_xxx函数")
    print("=" * 50)
    rewrite_get_functions()
