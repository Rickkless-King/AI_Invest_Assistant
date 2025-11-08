from langchain_core.runnables import RunnableLambda,RunnableParallel,RunnablePassthrough,chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
from fundamental_analyst import *

load_dotenv()
finnhub_api_key=os.getenv("FINNHUB_API_KEY")
finnhub_client=finnhub.Client(api_key=finnhub_api_key)
av_api_key = os.getenv("ALPHAVANTAGE_API_KEY")
fred_api_key=os.getenv("FRED_API_KEY")
fred_client=Fred(api_key=fred_api_key)

llm=ChatOpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    temperature=0.1,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    model="qwen-plus"
)

# 之前我们已经使用了基础的流式输出： for chunk in xx.stream({"symbol":"NVDA"}): print(chunk,end="",flush=True)
# task1：接下来首先尝试批量分析
def batch_analysis():
    # 同时分析多只股票
    prompt=ChatPromptTemplate.from_template("用一句话评价{symbol}")
    chain=prompt|llm|StrOutputParser()
    symbols=["AAPL","EMC","HPQ","DELL","WDC","HPE","NTAP","CPQ","SNDK"]

    # 方式1：循环调用(慢)
    print("方式1:串行调用")
    for x in symbols:
        result=chain.invoke({"symbol":x})#这里把x作为key对应的value，逐个调用，必须等上一个完成再继续下一个
        # 总耗时=每个请求耗时之和
        print(f"{x}:{result}")

    # 方式2：批处理(快)
    print("\n方式2:并行调用")
    results=chain.batch([{"symbol":s} for s in symbols])
    # .batch()是Langchain中用于并行处理多个输入的方法，接收一个输入列表，通过列表推导式，生成输入字典列表
    for symbol,result in zip(symbols,results): # zip(symbols,results)将股票代码和结果配对
        print(f"{symbol}:{result}")
        # 需要API支持并发(通常支持)，注意API的并发限制，避免过多请求
     # 总耗时≈最慢的那个请求的耗时
# if __name__=="__main__":
#     batch_analysis()

# task2：实现batch批量输出之后，接着尝试异步流式输出
# 在异步环境中进行流式输出，既能实时显示，又能同时处理其他任务，适合web应用及其他并发场景
async def async_streaming():# async def定义异步函数，函数内可使用await和 async for
    # 学习异步调用(重要)
    import asyncio# 用于运行异步代码
    prompt=ChatPromptTemplate.from_template("分析{symbol}")
    chain=prompt|llm|StrOutputParser()

    print("异步流式输出")
    async for chunk in chain.astream({"symbol":"NVDA"}):# astream()是异步流式方法，返回异步迭代器。
        print(chunk,end="",flush=True)

# if __name__=="__main__":
#     async_streaming()

"""
完成这周学习后，你应该能回答：

Q1: invoke()、stream()、batch()有什么区别？
A: - invoke(): 一次性返回完整结果
   - stream(): 逐块返回，适合长文本实时显示
   - batch(): 并行处理多个输入，适合批量任务

Q2: 什么时候用RunnableLambda？
A: 需要在链中插入自定义Python函数时，如数据获取、预处理。
   用@chain装饰器包装后可以和其他Runnable组件串联。

Q3: 如何实现容错？
A: 在@chain函数内用try-except，主数据源失败时返回备用数据源结果。

Q4: 你的项目中哪里用了LCEL？
A: "我用LCEL构建了多步分析链：
   数据获取(RunnableLambda) | 格式化 | LLM分析 | 输出解析
   支持流式输出，提升用户体验。"

实战作业：
1. 将fundamental_analyst.py完全改造成LCEL风格
2. 实现流式输出，测试用户体验
3. 添加批量分析功能：输入多只股票，并行分析
"""

# 在之前的usingRunnable_rewrite_get_function.py文件中，我们通过RunnableParallel的方式将构建{"变量名":get_XX函数返回结果作为value}
# 的方式，将get_xxx函数的结果送进Runnable中，再通过merge_all_data重新构建字典，prompt中采用from_template("""XX{行业}"""),
# 将之前的字典的value送进prompt中，进而通过LLM获取答案。
# 但上述我们只是获取了{"symbol":"NVDA"}即"NVDA"的相关分析，我们还需要完成对同属半导体行业其他公司的相关分析
# 因此，我们需要：对半导体行业其他公司进行分析，然后使用batch并发快速输出

def analyse_stock_with_allPeers(symbol):
    """
    使用LCEL风格分析目标股票及其同行业公司，生成综合对比分析报告

    LCEL核心概念应用：
    1. @chain装饰器：将普通函数转换为Runnable
    2. RunnableParallel：并行获取宏观数据
    3. RunnableLambda：包装数据获取和格式化逻辑
    4. ChatPromptTemplate：结构化prompt
    5. 管道操作符|：串联多个Runnable组件
    6. batch()：并行处理多个输入

    Args:
        symbol: 目标股票代码，如"NVDA"

    输出：
        一份包含宏观分析+同行业股票对比+投资推荐的综合报告
    """

    # ====== 步骤1：使用@chain装饰器获取同行业公司列表 ======
    @chain
    def get_peer_companies(inputs):
        """Runnable: 获取同行业公司列表"""
        target_symbol = inputs["symbol"]
        peers = get_company_peers(target_symbol)
        print(f"获取到{len(peers)}家同行业公司：{peers}")
        return {
            "symbol": target_symbol,
            "peers": peers
        }

    # ====== 步骤2：使用RunnableParallel并行获取宏观数据 ======
    @chain
    def fetch_macro_data(inputs):
        """Runnable: 获取宏观经济数据"""
        print("\n【步骤1/3】正在获取美国宏观经济数据...")
        macro = get_macro_economic_data()
        print("✅ 宏观数据获取完成\n")
        return {**inputs, "macro": macro}

    # ====== 步骤3：使用@chain装饰器+batch并行获取所有股票数据 ======
    @chain
    def fetch_single_stock_data(inputs):
        """Runnable: 获取单只股票的数据（支持fallback容错）"""
        symbol = inputs["symbol"]
        try:
            # 主数据源：Finnhub
            profile = finnhub_client.company_profile2(symbol=symbol)
            real_time_data = finnhub_client.quote(symbol=symbol)
            timestamp = real_time_data.get('t')
            local_time = datetime.datetime.fromtimestamp(timestamp)
            formatted_local_time = local_time.strftime("%Y-%m-%d %H:%M:%S")

            print(f"  ✓ {symbol} 数据获取成功")
            return {
                'symbol': symbol,
                '名称': profile.get('name'),
                '行业': profile.get('finnhubIndustry'),
                'ipo时间': profile.get('ipo'),
                '市值': float(profile.get('marketCapitalization', 0)),
                '官网': profile.get('weburl'),
                '描述': profile.get('description'),
                "最新成交价": real_time_data.get('c'),
                "当日最高价": real_time_data.get('h'),
                "当日最低价": real_time_data.get('l'),
                "当日开盘价": real_time_data.get('o'),
                "前一个交易日的收盘价": real_time_data.get('pc'),
                "上述数据的更新时间": formatted_local_time
            }
        except Exception as e:
            # Fallback数据源：Alpha Vantage
            print(f"  ⚠ {symbol} Finnhub失败，尝试Alpha Vantage...")
            try:
                av_companyfile = FundamentalData(key=av_api_key, output_format='dict')
                overview, _ = av_companyfile.get_company_overview(symbol)
                ts = TimeSeries(key=av_api_key, output_format='dict')
                quote, _ = ts.get_quote_endpoint(symbol)

                print(f"  ✓ {symbol} 数据获取成功（备用源）")
                return {
                    'symbol': symbol,
                    '名称': overview.get('Name', 'N/A'),
                    '行业': overview.get('Industry', 'N/A'),
                    'ipo时间': overview.get('IPODate', 'N/A'),
                    '市值': float(overview.get('MarketCapitalization', 0)),
                    '官网': 'N/A',
                    '描述': overview.get('Description', 'N/A'),
                    "最新成交价": float(quote.get('05. price', 0)),
                    "当日最高价": float(quote.get('03. high', 0)),
                    "当日最低价": float(quote.get('04. low', 0)),
                    "当日开盘价": float(quote.get('02. open', 0)),
                    "前一个交易日的收盘价": float(quote.get('08. previous close', 0)),
                    "上述数据的更新时间": quote.get('07. latest trading day', 'N/A')
                }
            except Exception as e2:
                print(f"  ✗ {symbol} 数据获取失败：{e2}")
                return None

    @chain
    def batch_fetch_all_stocks(inputs):
        """Runnable: 使用batch并行获取所有股票数据"""
        peers = inputs["peers"]
        print(f"【步骤2/3】正在批量获取{len(peers)}家公司的财务数据...")

        # 关键：使用batch()并行处理所有股票
        stock_inputs = [{"symbol": s} for s in peers]
        all_results = fetch_single_stock_data.batch(stock_inputs)

        # 过滤掉失败的结果
        all_stocks_data = [r for r in all_results if r is not None]
        print(f"✅ 成功获取{len(all_stocks_data)}/{len(peers)}家公司数据\n")

        return {**inputs, "stocks": all_stocks_data}

    # ====== 步骤4：使用@chain装饰器格式化数据 ======
    @chain
    def format_comparison_report(inputs):
        """Runnable: 格式化公司对比数据为Prompt所需格式"""
        stocks = inputs["stocks"]
        macro = inputs["macro"]

        # 构建公司对比信息文本
        companies_comparison = ""
        for idx, stock in enumerate(stocks, 1):
            change_pct = ((stock['最新成交价'] - stock['前一个交易日的收盘价']) /
                         stock['前一个交易日的收盘价'] * 100)
            companies_comparison += f"""
【公司{idx}】{stock['symbol']} - {stock['名称']}
  - 市值：{stock['市值']:.2f}百万美元
  - 最新成交价：${stock['最新成交价']}
  - 涨跌幅：{change_pct:.2f}%
  - 当日最高价：${stock['当日最高价']}
  - 当日最低价：${stock['当日最低价']}
  - IPO时间：{stock['ipo时间']}
  - 数据更新时间：{stock['上述数据的更新时间']}
"""

        # 返回格式化后的数据字典（供ChatPromptTemplate使用）
        return {
            "美元兑人民币": macro.get("美元兑人民币"),
            "美元兑日元": macro.get("美元兑日元"),
            "美元兑欧元": macro.get("美元兑欧元"),
            "联邦基金目标利率": macro.get("联邦基金目标利率"),
            "非农就业人数": macro.get("非农就业人数"),
            "失业率": macro.get("失业率"),
            "平均时薪": macro.get("平均时薪"),
            "通胀数据": macro.get("通胀数据"),
            "GDP数据": macro.get("GDP数据"),
            "公司对比数据": companies_comparison,
            "行业名称": stocks[0]['行业'] if stocks else 'N/A',
            "公司数量": len(stocks)
        }

    # ====== 步骤5：使用ChatPromptTemplate构建结构化Prompt ======
    analysis_prompt = ChatPromptTemplate.from_template("""
现在你的身份是一名顶级对冲基金的基金经理，你非常擅长根据美国宏观经济数据以及同行业多家公司的对比分析来进行投资决策。

## 一、美国宏观经济数据
- 美元兑人民币：{美元兑人民币}
- 美元兑日元：{美元兑日元}
- 美元兑欧元：{美元兑欧元}
- 联邦基金目标利率：{联邦基金目标利率}
- 非农就业人数：{非农就业人数}
- 失业率：{失业率}
- 平均时薪：{平均时薪}
- 通胀数据：{通胀数据}
- GDP数据：{GDP数据}

## 二、同行业公司数据对比
{公司对比数据}

## 分析要求
请按照以下结构输出一份综合投资分析报告：

### 第一部分：宏观经济环境分析（300字左右）
1. 判断当前美国宏观经济环境是偏向宽松还是紧缩
2. 根据通胀数据、就业数据和利率水平，预判美联储未来货币政策走向（扩表/缩表、降息/加息）
3. 分析当前宏观环境对{行业名称}行业的影响

### 第二部分：同行业公司横向对比分析（500字左右）
1. 对比以上{公司数量}家公司的市值规模、股价表现
2. 分析各公司的相对估值水平（基于市值和股价波动）
3. 指出哪些公司表现强势、哪些相对疲软

### 第三部分：投资建议（200字左右）
1. 结合宏观环境和公司对比，明确推荐1-2只最值得投资的股票
2. 说明推荐理由（基于宏观趋势、行业地位、估值水平等）
3. 给出具体的操作建议（买入/观望/等待回调）

注意：
- 逻辑清晰，表达有条理
- 数据判断基于事实，未来预测基于历史规律
- 自上而下的分析框架：宏观→行业→个股
""")

    # ====== 步骤6：使用管道操作符|构建完整的LCEL链 ======
    print("【步骤3/3】构建LCEL分析链并生成综合对比分析报告...\n")

    # 完整的LCEL链：数据获取 → 格式化 → Prompt → LLM → 解析输出
    full_analysis_chain = (
        get_peer_companies          # 1. 获取同行业公司
        | fetch_macro_data           # 2. 获取宏观数据
        | batch_fetch_all_stocks     # 3. batch并行获取所有股票数据
        | format_comparison_report   # 4. 格式化为prompt需要的格式
        | analysis_prompt            # 5. 填充prompt模板
        | llm                        # 6. LLM生成分析
        | StrOutputParser()          # 7. 解析输出为字符串
    )

    # ====== 步骤7：执行LCEL链（支持invoke和stream两种方式） ======
    print("="*100)
    print("【综合投资分析报告】")
    print("="*100 + "\n")

    # 方式1：invoke一次性返回完整结果
    result = full_analysis_chain.invoke({"symbol": symbol})
    print(result)

    # 方式2（可选）：stream流式输出，实时显示生成过程
    # print("使用流式输出：\n")
    # for chunk in full_analysis_chain.stream({"symbol": symbol}):
    #     print(chunk, end="", flush=True)

    print("\n" + "="*100)
    print("\n💡 LCEL技术要点总结：")
    print("  1. ✅ 使用@chain装饰器将函数转换为Runnable")
    print("  2. ✅ 使用batch()并行处理多个股票数据获取")
    print("  3. ✅ 使用ChatPromptTemplate实现结构化prompt")
    print("  4. ✅ 使用管道操作符|串联7个Runnable组件")
    print("  5. ✅ 支持invoke()和stream()两种执行方式")
    print("  6. ✅ 数据获取自动fallback容错机制")
    print("="*100)

if __name__=="__main__":
    analyse_stock_with_allPeers("NVDA")
