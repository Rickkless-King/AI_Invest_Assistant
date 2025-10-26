## 现在我需要首先做一个基本面分析师，如果我想使用Langchain、LangGraph的话，
# 首先我需要把LLM比如说阿里百炼配置到.env环境中。
# 那么这个时候我首先需要打开Langchain，看其如何调用阿里百炼平台，或者打开阿里云百炼，看其如何在Langchain下工作
# 我们找到阿里云百炼中关于Langchain的描述：https://bailian.console.aliyun.com/?tab=api#/api/?type=model&url=2587654 
# 调用前提条件为：1.已获得API KEY。2.已将API KEY配置到环境变量中。
# 目前LLM在实际应用中逐渐分类为聊天模型、文本嵌入模型和重排序模型。我们本次可能聊天模型和文本嵌入模型这两个用的比较多。
# 这里页面的OpenAI和DashScope是两种不同的模型调用接口规范：阿里云百炼W为了降低开发者门槛，提供了OpenAI一致的接口。适配性比较高。
# DashScope是阿里云为自家大模型设计的接口规范，是阿里云百炼模型的“原生接口”。
# 下面我们以OpenAI规范为例，开始在Langchain中使用阿里云百炼模型。
# pip install langchain_openai 这行代码要写在【终端】里面。
# pip install python-dotenv也是要写在【终端】里面。
# 这个时候我们就是可以直接在终端pip freeze > requirements.txt 添加相关依赖了。
# 添加完LLM，我们下一步尝试添加金融数据源，我们首先添加Finnhub，这里分享一下Finnhub的python调用方法：https://github.com/Finnhub-Stock-API/finnhub-python
# 按照上面那个Github网页提示，在终端pip安装，然后使用pip freeze > requirements.txt 更新
# 接着在.env中输入你申请的Finnhub API KEY，然后回到本文件os.getenv()调用。
# 考虑到金融数据源有次数与频率的双重限制，这里我们再免费区搞一个Alpha Vintage的API KEY，然后如法炮制到我的项目中来
# 我们从股票基本面对股票进行基本面分析离不开对当下美国宏观经济情况的分析，因此我们尝试使用FRED (Federal Reserve Economic Data) API，
# 同时美国劳工统计局 (BLS - Bureau of Labor Statistics) API提供最原始的CPI和非农就业数据、美国经济分析局 (BEA - Bureau of Economic Analysis) API提供最原始的GDP数据


# Langchain相关库
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage,FunctionMessage
# 系统、环境变量、时间等库
import os
from dotenv import load_dotenv
import datetime
from datetime import date,timedelta
# Finnhub官方Python库
import finnhub  
from finnhub.exceptions import FinnhubAPIException, FinnhubRequestException  # 捕获Finnhub异常
# 新增Alpha Vantage相关导入
from alpha_vantage.timeseries import TimeSeries
from alpha_vantage.techindicators import TechIndicators
from alpha_vantage.fundamentaldata import FundamentalData
# 新增FRED美国宏观经济数据
from fredapi import Fred
# 新增EODHD相关导入
from eodhd import APIClient
import pandas as pd
# 新增Twelvedata相关导入
from twelvedata import TDClient



# 加载.env并打印密钥（测试用，后续可删除）

load_dotenv()
api_key = os.getenv("DASHSCOPE_API_KEY")
finnhub_api_key=os.getenv("FINNHUB_API_KEY")
av_api_key = os.getenv("ALPHAVANTAGE_API_KEY")
fred_api_key=os.getenv("FRED_API_KEY")
fred_client=Fred(api_key=fred_api_key)
# 从环境变量中获取EODHD的API KEY
eodhd_api_key=os.getenv("EODHD_API_KEY")
eodhd_client=APIClient(eodhd_api_key)
# 从环境变量中获取TWELVEDATA的API KEY
twelve_client=TDClient(apikey="TWELVE_DATA_API_KEY")


# 初始化模型
ChatLLM = ChatOpenAI(
    api_key=api_key,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    model="qwen-plus",
    streaming=True,
    temperature=0.1,
    timeout=15000,
    max_retries=3,
)

# 后续的messages定义和invoke/stream调用保持不变
# messages = [
#     {"role": "system", "content": "Now you are a very professional investment expert"},
#     {"role": "user", "content": "hello,How can I earn more money from stock market and crypto market?"}
# ]
# for chunck in ChatLLM.stream(messages):# 在上面的ChatOpenAI中将streaming=True，使用流式输出
#     print(chunck.content,end="",flush=True)

# 先用ctrl+"/"隐藏上面的LLM问答代码，先完成Finnhub/Alpha Vantage这类数据源的调用。再尝试将返回回来的金融数据塞进大模型中。

# 在上面我们已经通过finnhub_api_key获取了Finnhub的API KEY，下面需要初始化客户端


finnhub_client=finnhub.Client(api_key=finnhub_api_key)

# 定义一个通过股票代码获取公司概况的函数
def get_company_profile(symbol):
    profile=finnhub_client.company_profile2(symbol=symbol)#官网上免费版使用.company_profile2(symbol='NADA')方式获取公司概况
    return{
        "名称":profile.get('name'),#约定使用.get()方法获取，Finnhub会返回key_value这种键值对。
        "行业":profile.get('finnhubIndustry'),
        "ipo时间":profile.get('ipo'),
        "市值(百万美元)":profile.get('marketCapitalization'),
        "官网":profile.get('weburl'),
        "描述":profile.get('description')
    }

# print(get_company_profile('NVDA'))

# 定义一个获取实时股票数据报价的函数   （我用的是Finnhub免费版，最新成交价也是15-30分钟之前的演示数据)
def get_real_time_data(symbol):#免费版只能提供延时15-30分钟后的查询
    real_time_data=finnhub_client.quote(symbol=symbol)
    timestamp=real_time_data.get('t')
    # 转换为本地时间
    local_time=datetime.datetime.fromtimestamp(timestamp)
    # 格式化输出
    formatted_local_time=local_time.strftime("%Y-%m-%d %H:%M:%S")
    return{
        "最新成交价(免费版是延时15min的数据)":real_time_data.get('c'),
        "当日最高价":real_time_data.get('h'),
        "当日最低价":real_time_data.get('l'),
        "当日开盘价":real_time_data.get('o'),
        "前一个交易日的收盘价":real_time_data.get('pc'),
        # "上述数据的更新时间":real_time_data.get('t')#注意，这里Finnhub返回的是Unix时间戳，可通过datetime模板转换为具体的日期时间
        "上述数据的更新时间":formatted_local_time
    }

# print(get_real_time_data('NVDA'))

# 定义获取有关公司新闻的函数 (免费版可获取最近30天的数据，每日限次数)
def get_company_news(symbol,str_time,end_time):
    company_news=finnhub_client.company_news(symbol,_from=str_time,to=end_time)
    return company_news

# print(get_company_news('NVDA','2025-10-01','2025-10-16'))


# 定义获取同行业其他公司列表的函数
def get_company_peers(symbol):
    company_peers=finnhub_client.company_peers(symbol)
    return company_peers

# print(get_company_peers('NVDA'))


# 定义获取指定股票盈利日历(财报发布时间、实际业绩、市场预期数据以及对应季度和年份)的函数  (免费版只能获取最近一个月发布财报的公司的数据——两个限定：最新一个月+发布财报的公司)
def get_earnings_calendar(str_time,end_time,symbol):
    earnings_calendar=finnhub_client.earnings_calendar(_from=str_time,to=end_time,symbol=symbol,international=False)
    report_list=earnings_calendar.get('earningsCalendar',[])#获取最外面字典里面的列表
    report=report_list[0]#上面代码获取的report_list是一个列表，不能直接.get()方法，因此需要进入到列表里面，里面才是字典
    

    # return{ # 如果你是免费版且没有遵循 最新一个月+发布财报的公司 两个要求，就会返回一个空列表[]
    #     "股票代码":earnings_calendar.get('symbol'),
    #     "报告区间":f"{earnings_calendar.get('year')}年第{earnings_calendar.get('quarter')}季",
    #     "财报发布时间":earnings_calendar.get('date'),
    #     "预计营收":earnings_calendar.get('revenueEstimate'),
    #     "实际营收":earnings_calendar.get('revenueActual'),
    #     "预期EPS":earnings_calendar.get('epsEstimate'),
    #     "实际EPS":earnings_calendar.get('epsActual'),
    #     "发布时间":earnings_calendar.get('hour')
    # } 现在上面的代码打印都返回None，AI大模型告诉我Finnhub盈利日历返回的是包含列表的字典，结构为{“earnings_calendar”：[{},{},....{}]},value里面的value才是单条财务报表数据
    # 我上面的代码直接对最外面的字典做get操作，但实际都在列表里面的子字典中，因此全部返回None。

    return{
        "股票代码":report.get('symbol'),
        "报告区间":f"{report.get('year')}年第{report.get('quarter')}季",
        "财报发布时间":report.get('date'),
        "预计营收(单位；亿美元)":report.get('revenueEstimate')/100000000,
        "实际营收(单位；亿美元)":report.get('revenueActual')/100000000,
        "预期EPS":report.get('epsEstimate'),
        "实际EPS":report.get('epsActual'),
        "发布时间":report.get('hour') 
    }
# print(get_earnings_calendar("2025-09-19","2025-10-19","BAC"))#笔者实际写作时间为2025年10月19日，因此打印最新刚发布财报的美国银行。



# 定义获取区间段发布财报数据的函数(免费版查询最近一个月)
# 刚才我制指定了symbol为BOA.us，在官方给出的范例中，symbol可以=""，然后返回某个时间区间内全部发布财报资料的股票
def get_specific_time_period_earings_calendar(str_time,end_time):
    specific_time_period_earings_calendar=finnhub_client.earnings_calendar(_from=str_time,to=end_time,symbol="",international=False)
    # 上述代码不指定特定时间区间内的股票，因此返回的大字典里面为 "earningsCalendar"：[{字典1}，{字典2},...]
    report_list=specific_time_period_earings_calendar.get("earningsCalendar",[])# get方法默认返回None，report_list为None后续做遍历的话会报错TypeError
    all_reports=[]
    for i in range(len(report_list)):
        report=report_list[i]
        formatted_report={
        "股票代码":report.get('symbol'),
        "报告区间":f"{report.get('year')}年第{report.get('quarter')}季",
        "财报发布时间":report.get('date'),
        "预计营收(单位；美元)":report.get('revenueEstimate'),#有些股票不知道为什么，预计营收/实际应收Finnhub返回都是None，因此不能像上面那样直接除
        "实际营收(单位；美元)":report.get('revenueActual'),
        "预期EPS":report.get('epsEstimate'),
        "实际EPS":report.get('epsActual'),
        "发布时间":report.get('hour') 
        }
        all_reports.append(formatted_report)
    return all_reports #返回所有财报的解析结果

# print(get_specific_time_period_earings_calendar("2025-10-01","2025-10-18"))


# 定义获取公司基本财务信息(比如PE、PS、52周最高/低价、流动比率、净利率、美股营收额)的函数
# 优化一下我写的内容：比如一些.get()方法应当返回一个默认空字典{}，同时针对series/annual这种多层嵌套字典，尝试.get().get()方法
def get_company_basic_financials(symbol_1,symbol_2):
    company_basic_financials=finnhub_client.company_basic_financials(symbol_1,symbol_2)
    company_basic_financials_metricType=company_basic_financials.get("metricType")
    company_basic_financials_symbol=company_basic_financials.get("symbol")
    company_basic_financials_metric=company_basic_financials.get("metric",{})#通过.get()方法获取“metric”字典的value值

    company_basic_financials_serires=company_basic_financials.get("series")# 通过.get()方法获取一系列基础财务数据,返回的是“annual”字典的value值

    company_annual_currentRatio=company_basic_financials_serires.get("annual",{}).get("currentRatio",[])
    company_annual_salesPerShare=company_basic_financials_serires.get("annual",{}).get("salesPerShare",[])
    company_annual_netMargin=company_basic_financials_serires.get("annual",{}).get("netMargin",[])
    return{
        "公司名":company_basic_financials_symbol,
        "本次输出数据范围":company_basic_financials_metricType,
        "最近10个交易日平均交易量":company_basic_financials_metric.get("10DayAverageTradingVolume"),
        "52周最高":company_basic_financials_metric.get("52WeekHigh"),
        "52周最低":company_basic_financials_metric.get("52WeekLow"),
        "52周内最低点发生日期":company_basic_financials_metric.get("52WeekLowDate"),
        "基于过去52周每日收盘价计算的价格回报率":company_basic_financials_metric.get("52WeekPriceReturnDaily"),
        "Beta系数":company_basic_financials_metric.get("beta"),
        "流动比率历史变化情况":company_annual_currentRatio,
        "每股对应销售额历史变化情况":company_annual_salesPerShare,
        "净利润率历史变化情况":company_annual_netMargin
    }

# print(get_company_basic_financials('NVDA','all'))

# 定义获取公司内部人士增/减持股票的函数(每次调用最多不能超过100笔交易)
def get_stock_inside_transactions(symbol,str_time,end_time):
    stock_inside_transactions=finnhub_client.stock_insider_transactions(symbol,str_time,end_time)
    all_inside_transactions_data=[]
    for i in range(len(stock_inside_transactions.get("data"))):
        inside_transactions_data={
            "减持的股票为":stock_inside_transactions.get("symbol"),
            "减持者姓名":stock_inside_transactions.get("data")[i].get("name"),
            "交易后持有的股份":stock_inside_transactions.get("data")[i].get("share"),
            "相较于上次披露，股份变化(正数表示增持，负数表示减持)":stock_inside_transactions.get("data")[i].get("change"),
            "提交日期":stock_inside_transactions.get("data")[i].get("filingDate"),
            "交易日期":stock_inside_transactions.get("data")[i].get("transactionDate"),
            "交易代码":stock_inside_transactions.get("data")[i].get("transactionCode"),
            "平均交易价格":stock_inside_transactions.get("data")[i].get("transactionPrice"),
        }
        all_inside_transactions_data.append(inside_transactions_data)
    return all_inside_transactions_data

# print(get_stock_inside_transactions("NVDA",'2025-09-19','2025-10-19'))

# 定义获取公司内部人士情绪的函数(其中MSPR为Finnhub独创的指标，范围从-100极度看空到100极度看多)
# 但Finnhub自己也说了，预示未来30-90天的价格变化，没说长期。
def get_stock_insider_sentiment(symbol,str_time,end_time):
    stock_insider_sentiment=finnhub_client.stock_insider_sentiment(symbol,str_time,end_time)
    all_insider_sentiment=[]
    for i in range(len(stock_insider_sentiment.get("data"))):
        insider_sentiment={
            "股票代码":stock_insider_sentiment.get("data")[i].get("symbol"),
            "时间":f'{stock_insider_sentiment.get("data")[i].get("year")}年{stock_insider_sentiment.get("data")[i].get("month")}月',#使用f-string嵌套的时候，需要注意“ ‘的问题
            "所有内部人员交易合计的净买入/卖出":stock_insider_sentiment.get("data")[i].get("change"),
            "月度股票购买比例":stock_insider_sentiment.get("data")[i].get("mspr"),
        }
        all_insider_sentiment.append(insider_sentiment)
    return all_insider_sentiment

# print(get_stock_insider_sentiment('NVDA','2024-01-01','2024-12-31'))#有些月份有，有些月份没有，以2024年-12月为例，NVDA只有1-8月的相关数据

# 获取已报告的财务数据
def get_financials_reported(symbol,freq_time):
    financials_reported=finnhub_client.financials_reported(symbol=symbol,freq=freq_time)
    financial_reported_details={
        "股票代码":financials_reported.get("symbol"),
        "对应的CIK编码为":financials_reported.get("cik"),
        "具体的财务数据如下":financials_reported.get("data")
    }
    return financial_reported_details
# print(get_financials_reported('NVDA','annual'))


# 获取上市公司在SEC备案文件(一次最多不超过250份)
def get_stock_filings(symbol,str_time,end_time):
    stock_filings=finnhub_client.filings(symbol=symbol,_from=str_time,to=end_time)
    return stock_filings
# print(get_stock_filings('NVDA','2025-09-01','2025-10-01'))



# 现阶段应该更注重功能性＞严谨性，先让数据流动起来(数据→LLM→输出)

## 把Finnhub数据传给LLM，就是把数据塞进"user"的"content"里
def fundamental_analysis(symbol:str,str_time,end_time)->str:# symbol里面的str是用于提醒symbol中应该输入str，->str指定函数的返回值类型
    company_profile=get_company_profile(symbol)
    company_basic_financials=get_company_basic_financials(symbol,'all')
    company_real_time_data=get_real_time_data(symbol)
    company_news=get_company_news(symbol,str_time,end_time)
    company_peers=get_company_peers(symbol)
    comany_financials_reported=get_financials_reported(symbol,freq_time='annual')
    company_stock_filings=get_stock_filings(symbol,str_time,end_time)

    data=f"""
   请根据我提供的{symbol}的基本面数据，为我进行分析；
   公司基本信息：
  1.公司名称：{company_profile["名称"]}
  2.所属行业：{company_profile["行业"]}
  3.目前市值：{company_profile["市值(百万美元)"]}
  4.官网：{company_profile["官网"]}
  5.最近成交价：{company_real_time_data["最新成交价(免费版是延时15min的数据)"]}
  6.前一个交易日的收盘价：{company_real_time_data["前一个交易日的收盘价"]}
  7.52周最高价格：{company_basic_financials["52周最高"]}
  8.52周最低价格：{company_basic_financials["52周最低"]}
  9.基于过去52周每日收盘价就算的价格回报率：{company_basic_financials["基于过去52周每日收盘价计算的价格回报率"]}
  10.行业竞争对手：{company_peers}
  11.最近30天公司情况:{company_news}
  12.已公布的财务数据：{comany_financials_reported}
  13.最近公司在SEC的备案文件:{company_stock_filings}

   
   请从以下角度分析：
   1. 估值水平
   2.根据财务数据报表
   3.其他基本面分析可能会涉及的角度

   要求：
   1.分析客观，基于数据
   2.结论明确
   3.最终分析完后提供清晰的投资建议(被高估/被低估)，并给出理由

   """
    
    # # 调用大语言模型
    # messages=[
    #     {"role":"system","content":"现在的你是一名专业的金融投资基本面分析师，尤其擅长根据提供的企业资料与财务数据表现，并且结合当前企业股价表现判断企业股票价格当前被高估或是低估"},
    #     {"role":"user","content":data}
    # ]
    # # 回答建议使用流式输出
    # for chunck in ChatLLM.stream(messages):
    #     print(chunck.content,end="",flush=True)
# if __name__=="__main__":# 这个需要移到函数定义外面确保被调用
#         fundamental_analysis(symbol='NVDA',str_time='2025-09-01',end_time='2025-10-21')


# 通过FRED获取美国宏观经济数据
def get_macro_economic_data():
    """
    获取美国宏观经济数据：
    返回包含以下数据的字典
    - 汇率(美元兑人民币、日元、欧元)
    - 利率(联邦基金目标利率)
    - 通胀(CPI、核心CPI、核心PCE)
    - GDP(名义GDP、实际GDP、GDP平减指数)
    """
    macro_data={}#用一个空字典来存储宏观经济数据
    
    # 汇率数据
    try:
        # 美元兑人民币(DEXCHUS)
        usd_cny=fred_client.get_series('DEXCHUS',observation_start='2024-01-01')
        # 调用fred_client中的get_series()方法，请求FRED数据库中序列为DEXCHUS(对应美元兑人民币汇率)的数据，
        # 且仅获取2024-01-01之后的观测值，返回的usd_cny是一个带日期索引的时间序列对象(通常是pandas series)
        macro_data['美元兑人民币']={# 在macro_data字典中创建一个'美元兑人民币'的子字典，用于存储该汇率的具体信息
            '最新值':round(usd_cny.iloc[-1],4),# iloc[-1]获取usd_cny序列的最后一个值(即最新的汇率数据)， round(xxx,4)将该值保留4位小数，作为'最新值'的内容存入子字典
            '更新日期':usd_cny.index[-1].strftime('%Y-%m-%d')# # index[-1]获取usd_cny序列的最后一个索引标签(即最新汇率数据对应的日期)，round(xxx,4)将该值保留4位小数
            # .strftime('%Y-%m-%d')将日期格式转化为'年-月-日'的字符串形式，作为‘更新日期’存入子字典中
            }
        # 美元兑日元(DEXJPUS)
        usd_jp=fred_client.get_series('DEXJPUS',observation_start='2024-01-01')
        macro_data['美元兑日元']={
            '最新值':round(usd_jp.iloc[-1],4),
            '更新日期':usd_jp.index[-1].strftime('%Y-%m-%d')
        }
        
        # 欧元兑美元(DEXUSEU)--注意，想要获得美元兑欧元需要去倒数
        eur_usd=fred_client.get_series('DEXUSEU',observation_start='2024-01-01')
        macro_data['美元兑欧元']={
            '最新值':round(1/eur_usd.iloc[-1],4),
            '更新日期':eur_usd.index[-1].strftime('%Y-%m-%d')
        }
    except Exception as e:
        print(f"获取汇率数据失败：{e}")
        macro_data['汇率数据']="获取失败"

    try:# 获取利率数据
        # 联邦基金目标利率上限(DFEDTARU)
        fed_rate_upper=fred_client.get_series('DFEDTARU',observation_start='2024-01-01')
        # 联邦基金目标利率下线(DFEDTARL)
        fed_rate_lower=fred_client.get_series('DFEDTARL',observation_start='2024-01-01')

        macro_data['联邦基金目标利率']={
            '利率区间':f"{fed_rate_lower.iloc[-1]:.2f}%-{fed_rate_upper.iloc[-1]:.2f}%",
            '更新日期':fed_rate_upper.index[-1].strftime('%Y-%m-%d')
        }
    except Exception as e:
        print(f'利率数据获取失败：{e}')
        macro_data['联邦基金目标利率']='获取失败'

    try:# 就业数据
        # 非农就业人数(千人)(PAYEMS)
        payrolls=fred_client.get_series('PAYEMS',observation_start='2024-01-01')
        macro_data['非农就业人数']={
            '最新值':int(payrolls.iloc[-1]),
            '月度变化(千人)':int(payrolls.iloc[-1]-payrolls.iloc[-2]),
            '更新日期':payrolls.index[-1].strftime('%Y-%m-%d')
        }
        # 失业率(UNRATE)
        unemployment=fred_client.get_series('UNRATE',observation_start='2024-01-01')
        macro_data['失业率']={
            '最新值(%)':round(unemployment.iloc[-1]),
            '更新日期':unemployment.index[-1].strftime('%Y-%m-%d')
        }
        # 平均时薪(美元/小时)(CES0500000003)
        hourly_earnings=fred_client.get_series('CES0500000003',observation_start='2024-01-01')
        macro_data['平均时薪']={
            '最新值(美元/小时)':round(hourly_earnings.iloc[-1],2),
            '同比增长':round(((hourly_earnings.iloc[-1]/hourly_earnings.iloc[-13])-1)*100,2),
            '更新日期':hourly_earnings.index[-1].strftime('%Y-%m-%d')
        }
    except Exception as e:
        print(f"就业数据获取失败：{e}")
        macro_data['就业数据']='获取失败'
    
    try: # 通胀数据
        # 未季调CPI(CPIAUCNS)
        cpi=fred_client.get_series('CPIAUCNS',observation_start='2023-01-01')
        cpi_yoy=((cpi.iloc[-1]/cpi.iloc[-13])-1)*100

        # 核心CPI(不含食品和能源)(CPILFESL)
        core_cpi=fred_client.get_series('CPILFESL',observation_start='2023-01-01')
        core_cpi_yoy=((core_cpi.iloc[-1]/core_cpi.iloc[-13])-1)*100

        # 核心PCE价格指数(PCEPILFE)
        core_pce=fred_client.get_series('PCEPILFE',observation_start='2023-01-01')
        core_pce_yoy=((core_pce.iloc[-1]/core_pce.iloc[-13])-1)*100

        macro_data['通胀数据']={
            'CPI同比(%)':round(cpi_yoy,2),
            '核心CPI同比(%)':round(core_cpi_yoy,2),
            '核心PCE同比(%)':round(core_pce_yoy,2),
            '更新日期':cpi.index[-1].strftime('%Y-%m-%d')
        }
    except Exception as e:
        print(f'通胀数据获取失败:{e}')
        macro_data['通胀数据']="获取失败"

    try:
        # 名义GDP(十亿美元)(GDP)
        nominal_gdp=fred_client.get_series('GDP',observation_start='2023-01-01')

        # 实际GDP(2017年链式美元)(GDPC1)
        real_gdp=fred_client.get_series('GDPC1',observation_start='2023-01-01')

        # GDP平减指数(GDPDEF)
        gdp_deflator=fred_client.get_series('GDPDEF',observation_start='2023-01-01')

        # 计算同比增长率
        nominal_gdp_growth=((nominal_gdp.iloc[-1]/nominal_gdp.iloc[-5])-1)*100
        real_gdp_growth=((real_gdp.iloc[-1]/real_gdp.iloc[-4])-1)*100
        
        macro_data['GDP数据']={
            '名义GDP(十亿美元)':round(nominal_gdp.iloc[-1],1),
            '名义GDP同比增长(%)':round(nominal_gdp_growth,2),
            '实际GDP(十亿美元)':round(real_gdp.iloc[-1],1),
            '实际GDP同比增长(%)':round(real_gdp_growth,2),
            'GDP平减指数':round(gdp_deflator.iloc[-1],2),
            '更新日期':nominal_gdp.index[-1].strftime('%Y-%m-%d')
        }
    except Exception as e:
        print(f"GDP数据获取失败:{e}")
        macro_data['GDP数据']='获取失败'


    print("===宏观数据获取完成")
    return macro_data

# 测试函数
def test_macro_data():
    macro_data=get_macro_economic_data()#调用上面创建获取宏观经济数据的函数，将结果存储在变量macro_data中
    print("="*30)
    print("美国宏观经济数据汇总")

    for category,data in macro_data.items():# 遍历macro_data字典中的所有键值对，category是键，data是对应的值
        print(f"\n[{category}]")# 使用f-string格式化字符串，打印一个换行符，再加上用[]包围的类别名称
        if isinstance(data,dict):# isinstance()函数用于检查对象的类型，即检查data是否为字典类型
            for key,value in data.items():# 如果data是字典类型的话，遍历data这个字典的键值对
                print(f"{key}:{value}")# 打印字典中每个键值对，格式为key：value
        else:
            print(f"{data}")# 如果data不是字典类型，直接打印data的内容

# if __name__=="__main__":
#     test_macro_data()

# 完成FRED中宏观经济数据的导入后，我们尝试将FRED的宏观数据以及我们通过Finnhub获取的微观股票数据全部注入给大模型，
# 思路上还是data=f'''{string} '''方式，将data送进messages的content键对应的value值中。
def fundamental_macroeconomic_stock_fundamental_analyze(symbol:str,str_time:str,end_time:str)-> str:
    # 首先获取FRED中获取的宏观经济数据，因为是字典，子字典的形式，我们先字典[键]的方式获取到里面的子字典
    macro_data=get_macro_economic_data()
    # 接着获取Finnhub中获取的微观股票相关数据,这块还是跟之前差不多，因为之前定义的get_XXX函数都有返回值，直接把返回值继续赋给变量即可
    company_profile=get_company_profile(symbol)
    company_basic_financials=get_company_basic_financials(symbol,'all')
    company_real_time_data=get_real_time_data(symbol)
    company_news=get_company_news(symbol,str_time,end_time)
    company_peers=get_company_peers(symbol)
    comany_financials_reported=get_financials_reported(symbol,freq_time='annual')
    company_stock_filings=get_stock_filings(symbol,str_time,end_time)

    # 还是通过data=f-string的方式，将通过字典[键]的方式将value传入到data当中，最终函数返回data
    data=f'''
 现在的你的身份是一名兼顾宏观经济周期分析与微观个股研究的顶级对冲基金经理，接下来我传入当下的宏观经济情况与要分析的个股情况，
 请结合当下的宏观经济数据以及我提供给你的微观个股资料，进行由宏观经济周期到微观个股的完整分析。
 以下为宏观经济数据：
 1.汇率情况：
 美元兑人民币:{macro_data['美元兑人民币']},
 美元兑日元：{macro_data['美元兑日元']},
 美元兑欧元：{macro_data['美元兑欧元']}。
 2.联邦基金利率情况：
 美国联邦基金目标利率情况：{macro_data['联邦基金目标利率']}
 3.就业数据情况：
 美国非农就业人数：{ macro_data['非农就业人数']},
 美国失业率情况：{ macro_data['失业率']},
 美国平均时薪：{macro_data['平均时薪']}。
 4.通胀数据：
 美国通胀数据：{macro_data['通胀数据']}。
 5.宏观经济数据
 美国宏观经济数据：{macro_data['GDP数据']}。

 其次为微观股票数据
 请根据我提供的{symbol}的基本面数据，为我进行分析；
   公司基本信息：
  1.公司名称：{company_profile["名称"]}
  2.所属行业：{company_profile["行业"]}
  3.目前市值：{company_profile["市值(百万美元)"]}
  4.官网：{company_profile["官网"]}
  5.最近成交价：{company_real_time_data["最新成交价(免费版是延时15min的数据)"]}
  6.前一个交易日的收盘价：{company_real_time_data["前一个交易日的收盘价"]}
  7.52周最高价格：{company_basic_financials["52周最高"]}
  8.52周最低价格：{company_basic_financials["52周最低"]}
  9.基于过去52周每日收盘价就算的价格回报率:{company_basic_financials["基于过去52周每日收盘价计算的价格回报率"]}
  10.行业竞争对手：{company_peers}
  11.最近30天公司情况:{company_news}
  12.已公布的财务数据：{comany_financials_reported}
  13.最近公司在SEC的备案文件:{company_stock_filings}

  要求：
  1. 根据收到的宏观经济数据，判断当下所处的宏观经济环境是偏向宽松或是偏向紧缩，并根据通胀数据与就业数据，
  判断接下来美联储是会缩表或是扩表，即采取宽松的货币政策或是紧缩的货币政策，未来是否为继续降息防水。
  2. 结合上面关于宏观经济数据的分析结果，通过比较当前最近成交价与52周最高、最低价格的比较以及最新公司发生的新闻状况、公司的财务情况等，
  判断当下要分析的公司目前的股价是被高估或是低估，是否应当买入，为什么？按照目前的宏观情况与微观情况，什么样的价格买入比较合适？
  3.逻辑清晰，表达有条理，从宏观经济到微观个股进行自上而下的梳理。
 '''
    messages=[
    {"role":"system","content":"你的身份是一名兼顾宏观经济周期分析与微观个股研究的顶级对冲基金经理,非常擅长结合宏观经济形势与微观个股现状进行分析"},
    {"role":"user","content":data}]
    for chunk in ChatLLM.stream(messages):
        print(chunk.content,end="",flush=True)

# if __name__=="__main__":
#     fundamental_macroeconomic_stock_fundamental_analyze('NVDA','2025-09-25','2025-10-24')

# 现在尝试从Alpha Vantage等其他金融数据源中获取金融数据，并尝试如果Finnhub超时未能获取金融数据，使用Alpha Vantage及其他金融数据源获取数据
# 我们首先尝试使用Alpha Vantage,再尝试Twelve Data，最后再尝试使用EODHD









 

    



    




        


 



















