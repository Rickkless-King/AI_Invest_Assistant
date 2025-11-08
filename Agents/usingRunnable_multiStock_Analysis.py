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
    symbols=get_company_peers(symbol)# symbols因为不用送进chain里，所有没有做Runnable处理，返回一个字符串列表
    macro_data=get_macro_economic_data()
    @chain
    def fetch_all_stocks_data(x):# 这里还是传入了x={"symbol":"XX"}的形式
        # all_data=[]#搞了一个空列表用来存放，但好像不用装
        # 回顾一下，之前分析一个行业里面的多只股票，我们是怎么做的？
        # 之前是使用一个for循环，all_data.append({}),在for循环里面往空列表里面添加字典，字典的key-value对就是通过get函数获取。
        # 这种方式就是在all_data中放字典，每一个子字典都是某一只股票特有的信息，可以通过symbol来区分。
        # 然后弄一个for循环，里面comparison_text+=f"""键，对应的value值"""，循环出来之后再添加美国宏观经济数据
        # from usingRunnable_rewrite_get_function import fetch_and_format()这种方式好像不行
        # 我的思路：我理解的.batch([{"symbol":x for x in symbols}])方法是类似.invoke({"symbol":"XX"})，因此不用特别装进all_data中
        symbol=x["symbol"]
        try:
            profile=finnhub_client.company_profile2(symbol=symbol)
            real_time_data = finnhub_client.quote(symbol=symbol)
            timestamp = real_time_data.get('t')
            local_time = datetime.datetime.fromtimestamp(timestamp)
            formatted_local_time = local_time.strftime("%Y-%m-%d %H:%M:%S")
            # all_data.append({
            # '金融数据来源':'Finnhub',
            # '名称':profile.get('name'),
            # '行业':profile.get('finnhubIndustry'),
            # 'ipo时间':profile.get('ipo'),
            # '市值':float(profile.get('marketCapitalization',0)),
            # '官网':profile.get('weburl'),
            # '描述':profile.get('description'),
            # "最新成交价": real_time_data.get('c'),
            # "当日最高价": real_time_data.get('h'),
            # "当日最低价": real_time_data.get('l'),
            # "当日开盘价": real_time_data.get('o'),
            # "前一个交易日的收盘价": real_time_data.get('pc'),
            # "上述数据的更新时间": formatted_local_time
            # })
            # return all_data
            return{
           '金融数据来源':'Finnhub',
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
            print(f"Finnhub获取公司资料失败,原因:{e}")
            print("尝试使用Alpha Vantage获取公司资料")
            av_companyfile=FundamentalData(key=av_api_key,output_format='dict')
            overview,_=av_companyfile.get_company_overview(symbol)
            ts = TimeSeries(key=av_api_key, output_format='dict')
            quote, _ = ts.get_quote_endpoint(symbol)
            # all_data.append({
            # '金融数据来源':'Alpha Vantage',
            # '名称':overview.get('Name','N/A'),
            # '行业':overview.get('Industry','N/A'),
            # 'ipo时间':overview.get('IPODate','N/A'),
            # '市值':float(overview.get('MarketCapitalization',0)),
            # '官网':'N/A',#Alpha Vantage不提供官网
            # '描述':overview.get('Description','N/A'),
            # "最新成交价": float(quote.get('05. price', 0)),
            # "当日最高价": float(quote.get('03. high', 0)),
            # "当日最低价": float(quote.get('04. low', 0)),
            # "当日开盘价": float(quote.get('02. open', 0)),
            # "前一个交易日的收盘价": float(quote.get('08. previous close', 0)),
            # "上述数据的更新时间": quote.get('07. latest trading day', 'N/A')
            # })
            # return all_data
            return{
            '金融数据来源':'Alpha Vantage',
            '名称':overview.get('Name','N/A'),
            '行业':overview.get('Industry','N/A'),
            'ipo时间':overview.get('IPODate','N/A'),
            '市值':float(overview.get('MarketCapitalization',0)),
            '官网':'N/A',#Alpha Vantage不提供官网
            '描述':overview.get('Description','N/A'),
            "最新成交价": float(quote.get('05. price', 0)),
            "当日最高价": float(quote.get('03. high', 0)),
            "当日最低价": float(quote.get('04. low', 0)),
            "当日开盘价": float(quote.get('02. open', 0)),
            "前一个交易日的收盘价": float(quote.get('08. previous close', 0)),
            "上述数据的更新时间": quote.get('07. latest trading day', 'N/A')   
            }

    # 使用RunnableParalle并行获取所有数据
    parallel_fetcher=RunnableParallel(
        # macro=fetch_macro_data,# 这里不需要传入参数，因为RunnableParallel会自动把输入数据给到Runnable
        # 传入chain里，macro=XXX会被循环调用很多次，不能这样写
        macro=lambda x:macro_data,# 直接返回已获取的数据，如同symbols一样，不需要重复调用FRED的API
        profile=fetch_all_stocks_data,# RunnableParallel会返回一个字典，其key为macro,其value为fetch_macro_data函数返回的内容
        symbol=lambda x:x["symbol"]# 这里x即{"symbol":"NVDA"}
    )
    @chain
    def merge_all_data(x):# 这里还是要传入参数x
        macro=x["macro"]# 因为上面的RunnableParallel传出的是一个字典
        profile=x["profile"]
        symbol=x["symbol"]
        return{# 这里直接返回一个字典
            "symbol":symbol,
            "名称":profile.get("名称"),
            # '行业':profile.get('Industry','N/A'),#从这里开始就出错了，上面我fetch_company_profile_with_fallback
            # 以及fetch_real_time_data_with_fallback返回的都是中文键的字典，但是我这里写的都是英文，所以出错了
            "行业":profile.get('行业','N/A'),
            'ipo时间':profile.get('IPO时间','N/A'),
            '市值':profile.get('市值',0),
            '官网':profile.get('官网','N/A'),
            '描述':profile.get('描述','N/A'),
            "最新成交价": profile.get('最新成交价', 0),
            "当日最高价": profile.get('当日最高价', 0),
            "当日最低价": profile.get('当日最低价', 0),
            "当日开盘价": profile.get('当日开盘价', 0),
            "前一个交易日的收盘价": profile.get('前一个交易日的收盘价', 0),
            "上述数据的更新时间": profile.get('上述数据的更新时间', 'N/A'),
            "美元兑人民币":macro.get("美元兑人民币"),
            "美元兑日元":macro.get("美元兑日元"),
            "美元兑欧元":macro.get("美元兑欧元"),
            "联邦基金目标利率":macro.get("联邦基金目标利率"),
            "非农就业人数":str(macro.get("非农就业人数")),
            "失业率":str(macro.get("失业率")),
            "平均时薪":str(macro.get("平均时薪")),
            "通胀数据":str(macro.get("通胀数据")),
            "GDP数据":str(macro.get("GDP数据"))
        } 
    prompt=ChatPromptTemplate.from_template(""" 
     现在你的身份是一名顶级对冲基金的基金经理，你非常擅长根据美国宏观经济数据以及具体个股数据来进行投资。
    目前美国宏观经济数据如下：
        目前美元兑人民币为{美元兑人民币},美元兑日元为{美元兑日元},美元兑欧元为{美元兑欧元},联邦基金目标利率为{联邦基金目标利率},
    目前非农就业人数为{非农就业人数},失业率为{失业率},平均时薪为{平均时薪},通胀数据为{通胀数据},GDP数据为{GDP数据}。
    目前具体个股数据如下：
        {名称}属于{行业},IPO时间为{ipo时间},市值为{市值}美元，其官网为{官网},最新成交价为{最新成交价},
    当日开盘最高价为{当日最高价},当日开盘最低价为{当日最低价},当日开盘价为{当日开盘价},前一个交易日的收盘价为{前一个交易日的收盘价}，
    以上数据更新时间是{上述数据的更新时间}。
                                            
    要求:1.根据收到的宏观经济数据，判断当下所处的宏观经济环境是偏向宽松或是偏向紧缩，并根据通胀数据与就业数据，
     判断接下来美联储是会缩表或是扩表，即采取宽松的货币政策或是紧缩的货币政策，未来是否为继续降息放水。
    2.结合上面关于宏观经济数据的分析结果,判断当下要分析的公司目前的股价是被高估或是低估，是否应当买入。
    3.逻辑清晰，表达有条理，数据需要基于事实，未来判断要基于历史数据。从宏观经济到微观个股进行自上而下的梳理。
 """)
    full_chain=parallel_fetcher|merge_all_data|prompt|llm|StrOutputParser()
    # results=full_chain.batch([{"symbol":x for x in symbols}]) 这里最严重的问题是batch里面的内容写错了
    results=full_chain.batch([{"symbol":x} for x in symbols])# 这样写才是列表推导式
    print("\n" + "="*80)

    print("批量分析结果：")

    print("="*80 + "\n")

    for company, result in zip(symbols, results): 

        print(f"\n{'='*80}")

        print(f"[{company}分析报告：")

        print(f"{'='*80}")

        print(result)# 

        print(f"\n{'='*80}\n")
    # 这样输出会报错，因为FRED代表的宏观数据被重复调用了很多次，报错：通胀/GDP/XXX数据获取失败:Too Many Requests. Exceeded Rate Limit

    # 因此，思路是首先在Runnable体外就获取宏观经济数据，如同获取symbols一样，然后在parallel中传入一个lambda x: 不带x的函数，即传入一个常量
    # 这样就不会因为变成Runnable的一部分而进入列表推导式里的循环中

    # 但是上述本质上是输出了每份结合宏观数据的多份股票分析报告，但是我需要的是一份报告：里面有宏观数据分析+同一行业所有公司的个股分析，最终得到我应该投资哪一只股票

    
# if __name__=="__main__":
#     analyse_stock_with_allPeers("NVDA")

# 重写：一份而不是多份报告，里面有宏观数据分析+同一行业所有公司的个股分析，最终得到我应该投资哪一只股票

def comprehensive_analyze_allStocks(symbol):
    # 分析宏观经济形势+同行业其他所有公司，生成一份综合对比分析报告
    # LCEL的优势是|传递数据，非常简洁，因此，微观个股相关的内容一定会传进去，但是宏观经济只需要传一次
    # symbols=get_company_peers(symbol) #我这里还是差点意思，只知道拿一个变量装，但是忘记了可以自己手动做一个字典，
    # 再通过引用字典的键来获取公司列表。
    # macro_data=get_macro_economic_data() #还是需要inputs作为输入，并且return返回
    # 步骤1：使用@chain装饰器获取同行业公司列表
    @chain
    def get_peer_companies(inputs):
        target_symbol=inputs["symbol"]
        peers=get_company_peers(target_symbol)
        print(f"获取到{len(peers)}家同行业公司:包括{peers}")
        return{
            "symbol":target_symbol,# 这里加一个return，手动做一个字典返回是我没想到的
            "peers":peers
        }
    # 步骤2：使用RunnableParallel并行获取宏观数据
    @chain
    def fetch_macro_data(inputs):
        macro=get_macro_economic_data()
        return{
            **inputs,"macro":macro# **inputs会把字典展开
        }
    # 步骤3：使用@chain装饰器+batch并行获取所有股票数据
    @chain
    def fetch_single_stock_with_fallback(inputs):
        symbol=inputs["symbol"]
        try:
            profile = finnhub_client.company_profile2(symbol=symbol)
            real_time_data = finnhub_client.quote(symbol=symbol)
            timestamp = real_time_data.get('t')
            local_time = datetime.datetime.fromtimestamp(timestamp)
            formatted_local_time = local_time.strftime("%Y-%m-%d %H:%M:%S")
            return{
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
            print(f" {symbol} Finnhub失败,原因{e}尝试Alpha Vantage...")
            try:
                av_companyfile = FundamentalData(key=av_api_key, output_format='dict')
                overview, _ = av_companyfile.get_company_overview(symbol)
                ts = TimeSeries(key=av_api_key, output_format='dict')
                quote, _ = ts.get_quote_endpoint(symbol)
                return{
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
            except Exception as e1:
                print(f"{symbol}数据获取失败：原因是{e1}")
                return None
    @chain
    def batch_all_stock(inputs):
        #使用batch并行获取所有股票数据
        peers=inputs["peers"]
        print(f"正在获取{len(peers)}家公司的财务数据")
        # 关键：使用batch()并行处理所有股票
        stock_inputs=[{"symbol":s} for s in peers]# 使用列表推导式，快速构建元素为子字典的列表
        all_results=fetch_single_stock_with_fallback.batch(stock_inputs)# 所以.batch相当于是获得了一堆元素为{"symbol":xx}的列表
        
        # 再使用列表推导式过滤失败的结果
        all_stock_data=[x for x in all_results if x is not None]
        print(f'成功获取了{len(all_stock_data)}家公司的数据')

        return{
            **inputs,"stocks":all_stock_data
        }
    # 步骤4：使用@chain装饰器格式化数据
    @chain
    def format_stock_report(inputs):
        #格式化股票对比数据为Prompt所需格式
        stocks=inputs["stocks"]
        macro=inputs["macro"]
        # 构建股票对比信息
        stocks_comparison=""
        for idx, stock in enumerate(stocks, 1):
            change_pct = ((stock['最新成交价'] - stock['前一个交易日的收盘价']) /stock['前一个交易日的收盘价'] * 100)
            stocks_comparison += f"""
             【公司{idx}】{stock['symbol']} - {stock['名称']}

              - 市值：{stock['市值']:.2f}百万美元

             - 最新成交价：${stock['最新成交价']}

             - 涨跌幅：{change_pct:.2f}%

             - 当日最高价：${stock['当日最高价']}

             - 当日最低价：${stock['当日最低价']}

             - IPO时间：{stock['ipo时间']}

             - 数据更新时间：{stock['上述数据的更新时间']}
             """
        return{
            "美元兑人民币": macro.get("美元兑人民币"),

            "美元兑日元": macro.get("美元兑日元"),

            "美元兑欧元": macro.get("美元兑欧元"),

            "联邦基金目标利率": macro.get("联邦基金目标利率"),

            "非农就业人数": macro.get("非农就业人数"),

            "失业率": macro.get("失业率"),

            "平均时薪": macro.get("平均时薪"),

            "通胀数据": macro.get("通胀数据"),

            "GDP数据": macro.get("GDP数据"),

            "公司对比数据": stocks_comparison,

            "行业名称": stocks[0]['行业'] if stocks else 'N/A',

            "公司数量": len(stocks)
            }

    # 步骤5：使用ChatPromptTemplate构建格式化Prompt
    prompt=ChatPromptTemplate.from_template("""
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

 ### 第一部分：宏观经济环境分析

 1. 判断当前美国宏观经济环境是偏向宽松还是紧缩

 2. 根据通胀数据、就业数据和利率水平，预判美联储未来货币政策走向（扩表/缩表、降息/加息）

 3. 分析当前宏观环境对{行业名称}行业的影响

 ### 第二部分：同行业公司横向对比分析

 1. 对比以上{公司数量}家公司的市值规模、股价表现

 2. 分析各公司的相对估值水平（基于市值和股价波动）

 3. 指出哪些公司表现强势、哪些相对疲软

 ### 第三部分：投资建议

 1. 结合宏观环境和公司对比，明确推荐1-2只最值得投资的股票

 2. 说明推荐理由（基于宏观趋势、行业地位、估值水平等）

 3. 给出具体的操作建议（买入/观望/等待回调）

 注意：

 - 逻辑清晰，表达有条理

 - 数据判断基于事实，未来预测基于历史规律

 - 自上而下的分析框架：宏观→行业→个股
 """)
    # 步骤6：使用管道操作符|构建完整的LCEL链
    full_chain=get_peer_companies|fetch_macro_data|batch_all_stock|format_stock_report|prompt|llm|StrOutputParser()
    for chunk in full_chain.stream({"symbol":symbol}):
        print(chunk,end="",flush=True)

    # 步骤7：执行LCEL链
if __name__=="__main__":
    comprehensive_analyze_allStocks("NVDA")


