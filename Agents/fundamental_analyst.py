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

print(get_company_peers('NVDA'))


# 定义获取财报发布时间、实际业绩、市场预期数据以及对应季度和年份的函数  (免费版只能获取一个月的历史盈利数据及新更新)






