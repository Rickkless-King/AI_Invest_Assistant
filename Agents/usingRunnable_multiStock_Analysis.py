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
    分析目标股票及其同行业公司，生成一份综合对比分析报告

    Args:
        symbol: 目标股票代码，如"NVDA"

    输出：
        一份包含宏观分析+同行业股票对比+投资推荐的综合报告
    """
    symbols=get_company_peers(symbol)# 获取同行业公司列表
    print(f"获取到{len(symbols)}家同行业公司：{symbols}")

    # 步骤1：获取宏观数据（只获取一次）
    print("\n【步骤1/3】正在获取美国宏观经济数据...")
    macro_data = get_macro_economic_data()
    print("✅ 宏观数据获取完成\n")

    # 步骤2：批量获取所有股票的数据
    print(f"【步骤2/3】正在批量获取{len(symbols)}家公司的财务数据...")

    def fetch_single_stock_data(symbol):
        """获取单只股票的数据"""
        try:
            profile=finnhub_client.company_profile2(symbol=symbol)
            real_time_data = finnhub_client.quote(symbol=symbol)
            timestamp = real_time_data.get('t')
            local_time = datetime.datetime.fromtimestamp(timestamp)
            formatted_local_time = local_time.strftime("%Y-%m-%d %H:%M:%S")

            print(f"  ✓ {symbol} 数据获取成功")
            return{
                'symbol': symbol,
                '名称':profile.get('name'),
                '行业':profile.get('finnhubIndustry'),
                'ipo时间':profile.get('ipo'),
                '市值':float(profile.get('marketCapitalization',0)),
                '官网':profile.get('weburl'),
                '描述':profile.get('description'),
                "最新成交价": real_time_data.get('c'),
                "当日最高价": real_time_data.get('h'),
                "当日最低价": real_time_data.get('l'),
                "当日开盘价": real_time_data.get('o'),
                "前一个交易日的收盘价": real_time_data.get('pc'),
                "上述数据的更新时间": formatted_local_time
            }
        except Exception as e:
            print(f"  ⚠ {symbol} Finnhub失败，尝试Alpha Vantage...")
            try:
                av_companyfile=FundamentalData(key=av_api_key,output_format='dict')
                overview,_=av_companyfile.get_company_overview(symbol)
                ts = TimeSeries(key=av_api_key, output_format='dict')
                quote, _ = ts.get_quote_endpoint(symbol)

                print(f"  ✓ {symbol} 数据获取成功（备用源）")
                return{
                    'symbol': symbol,
                    '名称':overview.get('Name','N/A'),
                    '行业':overview.get('Industry','N/A'),
                    'ipo时间':overview.get('IPODate','N/A'),
                    '市值':float(overview.get('MarketCapitalization',0)),
                    '官网':'N/A',
                    '描述':overview.get('Description','N/A'),
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

    # 批量获取所有股票数据
    all_stocks_data = []
    for sym in symbols:
        stock_data = fetch_single_stock_data(sym)
        if stock_data:
            all_stocks_data.append(stock_data)

    print(f"✅ 成功获取{len(all_stocks_data)}/{len(symbols)}家公司数据\n")

    # 步骤3：构建综合分析的prompt
    print("【步骤3/3】生成综合对比分析报告...")

    # 构建公司对比信息文本
    companies_comparison = ""
    for idx, stock in enumerate(all_stocks_data, 1):
        companies_comparison += f"""
【公司{idx}】{stock['symbol']} - {stock['名称']}
  - 市值：{stock['市值']:.2f}百万美元
  - 最新成交价：${stock['最新成交价']}
  - 涨跌幅：{((stock['最新成交价'] - stock['前一个交易日的收盘价']) / stock['前一个交易日的收盘价'] * 100):.2f}%
  - 当日最高价：${stock['当日最高价']}
  - 当日最低价：${stock['当日最低价']}
  - IPO时间：{stock['ipo时间']}
  - 数据更新时间：{stock['上述数据的更新时间']}
"""

    # 综合分析prompt
    comprehensive_prompt = f"""
现在你的身份是一名顶级对冲基金的基金经理，你非常擅长根据美国宏观经济数据以及同行业多家公司的对比分析来进行投资决策。

## 一、美国宏观经济数据
- 美元兑人民币：{macro_data.get("美元兑人民币")}
- 美元兑日元：{macro_data.get("美元兑日元")}
- 美元兑欧元：{macro_data.get("美元兑欧元")}
- 联邦基金目标利率：{macro_data.get("联邦基金目标利率")}
- 非农就业人数：{macro_data.get("非农就业人数")}
- 失业率：{macro_data.get("失业率")}
- 平均时薪：{macro_data.get("平均时薪")}
- 通胀数据：{macro_data.get("通胀数据")}
- GDP数据：{macro_data.get("GDP数据")}

## 二、同行业公司数据对比
{companies_comparison}

## 分析要求
请按照以下结构输出一份综合投资分析报告：

### 第一部分：宏观经济环境分析（300字左右）
1. 判断当前美国宏观经济环境是偏向宽松还是紧缩
2. 根据通胀数据、就业数据和利率水平，预判美联储未来货币政策走向（扩表/缩表、降息/加息）
3. 分析当前宏观环境对{all_stocks_data[0]['行业']}行业的影响

### 第二部分：同行业公司横向对比分析（500字左右）
1. 对比以上{len(all_stocks_data)}家公司的市值规模、股价表现
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
"""

    # 直接调用LLM生成综合报告
    response = llm.invoke(comprehensive_prompt)

    print("\n" + "="*100)
    print("【综合投资分析报告】")
    print("="*100 + "\n")
    print(response.content)
    print("\n" + "="*100)

if __name__=="__main__":
    analyse_stock_with_allPeers("NVDA")
