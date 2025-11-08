# 之前已经学习了prompt|llm|Parser的方式将prompt传进llm中，并通过Parser进行返回
# 学习了chain.invoke({})里装字典的方式将要分析的内容送进去，或者是直接在函数定义的时候将具体要大模型分析的内容送进去
# 学习了ChatPromptTemplate类能够传递符合OpenAI等大模型公司要求带有角色的promopt进入LLM。RunnablePassthrough作为管道
# 任务：用@chain包装fundamental_analyst.py中所有get_xxx函数

from langchain_core.runnables import RunnableLambda,RunnablePassthrough
from langchain_core.runnables import RunnableParallel
from langchain_core.prompts import ChatPromptTemplate# 用于把变量送进Prompt
from langchain_core.output_parsers import StrOutputParser# |||后为字符串
from langchain_core.runnables import chain# 导入@chain装饰器
from langchain_openai import ChatOpenAI
from typing import Any # 类型提示
import os
from dotenv import load_dotenv
from fundamental_analyst import *# import * 一键导入fundamental_analyst.py文件中所有不以_开头的公开对象(包括函数、类、变量)

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
    fetch_profile=RunnableLambda[Any,dict](lambda x:get_company_profile(x["symbol"]))
    # # RunnableLambda[输入类型，输出类型]，指定传给RunnableLambda的输入数据(即 lambda的参数x)的类型，
    # 输出类型指定RunnableLambda最终输出数据的类型。
    # 总的来说表示输入给RunnableLambda的data可以使任意类型，而输出类型必须是字典。
    # 从.invoke({"symbol":"NVDA"})这里面提取"symbol"键对应的value，即"NVDA"→→get_company_profille("NVDA")
    @chain# 用@chain装饰器把普通函数fetch_and_format变成Langchain的Runnable，这样就能用管道符|把它和其他组件串起来。
    def fetch_and_format(input_dict):
        # 获取数据
        symbol=input_dict["symbol"]
        profile=get_company_profile(symbol)
        quote=get_real_time_data(symbol)

        # 格式化成prompt需要的格式
        return{
            "symbol":symbol,
            "data":f"{profile['name']} -PE:{quote['pe']},市值：${profile['marketCap']}百万美元"
        }
    # 构建链
    prompt=ChatPromptTemplate.from_template("分析{symbol}:{data}")# 用ChatPromptTemplate定义一个模板字符串(可绑定到链的输入变量)
    chain=fetch_and_format|prompt|StrOutputParser()

    result=chain.invoke({"symbol":"NVDA"})# 1.把输入的{"symbol":"NVDA"}转换成{"symbol":"NVDA","data":"XXXXX"}
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
    parallel_fetcher=RunnableParallel[Any](# 泛型参数Any表示“输入数据类型可以是任意类型”
        # 通过RunnableParallel的输出必然是字典
        profile=fetch_profile,# 这里不需要传入参数x，因为RunnableParallel会自动把输入数据分发给子Runnable
        quote=fetch_quote,# 即RunnableParallel会自动把XXX_chain。invoke({字典})中的字典作为x传入，即x={"symbol":"NVDA"}
        symbol=lambda x:x["symbol"] 
        # 上面这3个都是变量名作为key，fetch_profile/fetch_quote/等作为value的组成 即通过RunnableParallel之后，
        # 输出为一个{"profile":get_comapny_profile('NVDA')的结果，"quote":get_real_time_data('NVDA')的结果}类似这样的字典
        # 
    )
    # 总的来说，Langchain的Runnable生态具有“自动数据传递”特性，不用关心数据怎么分给每个组件，只需定义“要执行哪些任务”。
    # 格式化数据
    @chain
    def format_data(x):
        return{
            "symbol":x["symbol"],
            "analysis_input":f"""公司：{x['profile']['name']},行业:{x['profile']['industry']},当前价格:{x["quote"]["price"]},
            PE比率:{x['quote']['pe']}"""# 这也解释为什么需要x['profile']['name']的方式获取对应的数据，本身profile为key，里面装着一个字典value，然后需要再[key]来获取值
        }
    # 构建完整链
    prompt=ChatPromptTemplate.from_template(
        "分析{symbol}的投资价值：{analysis_input}"# prompt里面的文字基本上看上面return返回的key，作为prompt里面{XXX}的内容
    )
    full_chain=(parallel_fetcher|format_data|prompt|llm|StrOutputParser())

    result=full_chain.invoke({"symbol":"NVDA"})
    print(result)



# 任务3:容错处理
def error_handling_chain():
    # 学习在链中处理异常
    @chain# 使用@chain装饰器，将下面的函数变为Runnable。
    def fetch_with_fallback(x):# 这里的输入x为{"symbol":"NVDA"}
        symbol=x["symbol"]# 获取symbol对应的value "NVDA"
        try:
            # 尝试主数据源(Finnhub)
            data=get_company_profile(symbol)# 使用get_company_profile()获取返回字典
            data["source"]="Finnhub"# 继续往里面添加key_value对
            return data
        except Exception as e:
            print(f"主数据源失败:{e}")# 如果报错，这里输出报错原因
            # 切换备用数据源
            return {
                "name":f"{symbol}Corp",
                "industry":"Unkown",
                "marketCap":0,
                "Source":"Fallback"
            }
        
    # 构建链
    prompt=ChatPromptTemplate.from_template("分析{name}(数据源{source})")

    chain=fetch_with_fallback|prompt|llm|StrOutputParser()

    result=chain.invoke({"symbol":"NVDA"})
    print(result)


# 任务：将我在fundamental_analyst.py文件中的函数进行Langchain的Runnable改写。
"""
1. 将你fundamental_analyst.py中的所有get_xxx函数包装成@chain
2. 用RunnableParallel同时获取profile、quote、financials
3. 测试容错：故意让Finnhub失败，看是否切换到Alpha Vantage
4. 在README中记录你的实现思路

面试问题准备：
Q: "RunnableLambda和普通函数有什么区别？"
A: "RunnableLambda实现了Runnable接口，可以用|连接，支持流式输出、批处理、异步调用。
   我在项目中用它包装数据获取函数，这样可以和LLM串联成完整的分析链。"

Q: "如何实现数据源容错？"
A: "我用@chain装饰器包装函数，在内部用try-except捕获异常。
   主数据源失败时自动切换到备用源，保证系统稳定性。"
"""

def rewrite_get_functions():
    fetch_macro_economic_data=RunnableLambda(lambda x:get_macro_economic_data())
    # 我首先应该传入FRED的内容，因为没有替代品，写不了try_except块,所以用最简单的RunnableLambda生成Runnable。
    # 然后考虑到Alpha Vantage作为Finnhub的替代源，所以用@chain装饰器+try_except块来保障
    # 
    @chain# 装饰器下面接函数定义，函数定义里面装try_except块
    def fetch_company_profile_with_fallback(x):# 这里还是传入字典
        symbol=x["symbol"]# 思路还是获取x字典里面symbol对应的value值，然后以获取Finnhub金融数据源的函数的方式将symbol作为形参传入
        try:
            finnhub_company_profile=finnhub_client.company_profile2(symbol=symbol)
            return{
            '金融数据来源':'Finnhub',
            '名称':finnhub_company_profile.get('name'),
            '行业':finnhub_company_profile.get('finnhubIndustry'),
            'ipo时间':finnhub_company_profile.get('ipo'),
            '市值(百万美元)':finnhub_company_profile.get('marketCapitalization'),
            '官网':finnhub_company_profile.get('weburl'),
            '描述':finnhub_company_profile.get('description'),
            }
        except Exception as e:
            print(f"通过Finnhub获取公司资料失败,原因:{e}")
            print("接下来切换为Alpha Vantage获取公司资料")

            av_company_profile=FundamentalData(key=av_api_key,output='dict')
            overview,_=av_company_profile.get_company_overview(symbol)
            return{
            '金融数据来源':'Alpha Vantage',
            '名称':overview.get('Name','N/A'),
            '行业':overview.get('Industry','N/A'),
            'ipo时间':overview.get('IPODate','N/A'),
            '市值(百万美元)':float(overview.get('MarketCapitalization',0)/1000000),
            '官网':'N/A',#Alpha Vantage不提供官网
            '描述':overview.get('Description','N/A'),
        }
    # 除了尝试改写获取公司资料外，继续尝试获取股票数据，然后尝试RunnableParallel
    @chain
    def fetch_real_time_data_with_fallback(x):
        symbol=x["symbol"]#还是从字典的symbol键获取对应的value值，这里是'NVDA'
        try:
            real_time_data = finnhub_client.quote(symbol=symbol)
            timestamp = real_time_data.get('t')
            local_time = datetime.datetime.fromtimestamp(timestamp)
            formatted_local_time = local_time.strftime("%Y-%m-%d %H:%M:%S")
            return{
            'source': 'Finnhub',
            "最新成交价": real_time_data.get('c'),
            "当日最高价": real_time_data.get('h'),
            "当日最低价": real_time_data.get('l'),
            "当日开盘价": real_time_data.get('o'),
            "前一个交易日的收盘价": real_time_data.get('pc'),
            "上述数据的更新时间": formatted_local_time
            }
        except Exception as e:
            print(f"通过Finnhub获取实时股票数据失败,原因:{e}")
            print("接下来使用接下来切换为Alpha Vantage获取实时股票数据")
            
            ts=TimeSeries(key=av_api_key,output_format='dict')
            quote,_=ts.get_quote_endpoint(symbol)
            return{
                'source': 'Alpha Vantage',
                "最新成交价": float(quote.get('05. price', 0)),
                "当日最高价": float(quote.get('03. high', 0)),
                "当日最低价": float(quote.get('04. low', 0)),
                "当日开盘价": float(quote.get('02. open', 0)),
                "前一个交易日的收盘价": float(quote.get('08. previous close', 0)),
                "上述数据的更新时间": quote.get('07. latest trading day', 'N/A')
            }
    # 现在已经完成了宏观数据、公司资料、股票价格三个Runnable的改写，接下来写prompt，写完prompt，然后用full_chain串联起来
    prompt=ChatPromptTemplate.from_template("""请结合我提供的宏观经济数据以及我提供的微观个股数据，为我分析{"名称"}公司，属于{"行业"},{"描述"},IPO时间为{"ipo时间"},市值为{"市值(百万美元)"},
                                            目前最新交易日是{"上述数据的更新时间"},
                                            最新交易日其价格为{最新成交价}，当日其最高价为{"当日最高价"},当日其最低价为{"当日最低价"},
                                            当日开盘价为{"当日开盘价"},前一个交易日的收盘价为{"前一个交易日的收盘价"}""")
    # full_chain=fetch_macro_economic_data|fetch_company_profile_with_fallback|fetch_real_time_data_with_fallback|prompt|llm|StrOutputParser()
    # 上面这样写不行，fetch_macro_economic_data返回的是宏观数据字典，但是fetch_company_profile_with_fallback需要的是{"symbol":"NVDA"}
    # 所以还是需要使用RunnableParallel，通过XX=xx_function_xx的方式返回一个{XX:{xx_function_xx函数返回的内容}}的结果，
    # 然后使用yy=x["XX"]获取里面的字典，最后return“Chinese”:yy.get("")，然后把内容传入prompt，再传给LLM。
    # result=full_chain.invoke({"symbol":"NVDA"})# 不管上面重写多少get_xxx，这里还是传入{"symbol":"NVDA"}
    # print(result)

# if __name__=="__main":# 我__main__写错了，所以这里不会执行
#     rewrite_get_functions()


## 重写rewrite_get_xx_functions():
def rewrite_get_xx_function():
    @chain
    def fetch_macro_data(x):
        return get_macro_economic_data()
    
    @chain
    def fetch_company_profile_with_fallback(x):
        symbol=x["symbol"]
        try:
            profile=finnhub_client.company_profile2(symbol=symbol)
            return{
            '金融数据源来源':'Finnhub',
            '名称':profile.get('name'),
            '行业':profile.get('finnhubIndustry'),
            'ipo时间':profile.get('ipo'),
            '市值':float(profile.get('marketCapitalization',0)),
            '官网':profile.get('weburl'),
            '描述':profile.get('description'),
            }
        except Exception as e:
            print(f"Finnhub获取公司资料失败,原因:{e}")
            print("尝试使用Alpha Vantage获取公司资料")
            av_companyfile=FundamentalData(key=av_api_key,output_format='dict')
            overview,_=av_companyfile.get_company_overview(symbol)
            return{
            '金融数据来源':'Alpha Vantage',
            '名称':overview.get('Name','N/A'),
            '行业':overview.get('Industry','N/A'),
            'ipo时间':overview.get('IPODate','N/A'),
            '市值':float(overview.get('MarketCapitalization',0)),
            '官网':'N/A',#Alpha Vantage不提供官网
            '描述':overview.get('Description','N/A'),
            }


    @chain 
    def fetch_real_time_data_with_fallback(x):
        symbol=x["symbol"]
        try:
            real_time_data = finnhub_client.quote(symbol=symbol)
            timestamp = real_time_data.get('t')
            local_time = datetime.datetime.fromtimestamp(timestamp)
            formatted_local_time = local_time.strftime("%Y-%m-%d %H:%M:%S")
            return{
            'source': 'Finnhub',
            "最新成交价": real_time_data.get('c'),
            "当日最高价": real_time_data.get('h'),
            "当日最低价": real_time_data.get('l'),
            "当日开盘价": real_time_data.get('o'),
            "前一个交易日的收盘价": real_time_data.get('pc'),
            "上述数据的更新时间": formatted_local_time
            }
        except Exception as e:
            print(f"使用Finnhub获取股票数据失败,原因:{e}")
            print("尝试使用Alpha Vantage获取股票数据")
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

    # 使用RunnableParalle并行获取所有数据
    parallel_fetcher=RunnableParallel(
        macro=fetch_macro_data,# 这里不需要传入参数，因为RunnableParallel会自动把输入数据给到Runnable
        profile=fetch_company_profile_with_fallback,# RunnableParallel会返回一个字典，其key为macro,其value为fetch_macro_data函数返回的内容
        quote=fetch_real_time_data_with_fallback,
        symbol=lambda x:x["symbol"]# 这里x即{"symbol":"NVDA"}
    )
    
    @chain
    def merge_all_data(x):# 这里还是要传入参数x
        macro=x["macro"]# 因为上面的RunnableParallel传出的是一个字典
        profile=x["profile"]
        quote=x["quote"]
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
            "最新成交价": quote.get('最新成交价', 0),
            "当日最高价": quote.get('当日最高价', 0),
            "当日最低价": quote.get('当日最低价', 0),
            "当日开盘价": quote.get('当日开盘价', 0),
            "前一个交易日的收盘价": quote.get('前一个交易日的收盘价', 0),
            "上述数据的更新时间": quote.get('上述数据的更新时间', 'N/A'),
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
    for chunk in full_chain.stream({"symbol":"NVDA"}):
        print(chunk,end="",flush=True)# end=“”避免每次print后自动换行，flush=True强制立即输出，不缓冲


if __name__=="__main__":
    rewrite_get_xx_function()






    


    
