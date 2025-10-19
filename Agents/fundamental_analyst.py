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


# Langchain相关库
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage,FunctionMessage
# 系统、环境变量、时间等库
import os
from dotenv import load_dotenv
import datetime
# Finnhub官方Python库
import finnhub  
from finnhub.exceptions import FinnhubAPIException, FinnhubRequestException  # 捕获Finnhub异常
# 新增Alpha Vantage相关导入
from alpha_vantage.timeseries import TimeSeries
from alpha_vantage.techindicators import TechIndicators
from alpha_vantage.fundamentaldata import FundamentalData

# 加载.env并打印密钥（测试用，后续可删除）

load_dotenv()
api_key = os.getenv("DASHSCOPE_API_KEY")
finnhub_api_key=os.getenv("FINNHUB_API_KEY")
av_api_key = os.getenv("ALPHAVANTAGE_API_KEY")

# 初始化模型
ChatLLM = ChatOpenAI(
    api_key=api_key,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    model="qwen-plus",
    streaming=True,
    temperature=0.1,
    timeout=15,
    max_retries=1,
)

# # 后续的messages定义和invoke/stream调用保持不变
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

    




        


 



















