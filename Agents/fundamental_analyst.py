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



from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage,FunctionMessage
import finnhub  # Finnhub官方Python库
import os
from dotenv import load_dotenv
from finnhub.exceptions import FinnhubAPIException, FinnhubRequestException  # 捕获Finnhub异常
# 新增Alpha Vantage相关导入
from alpha_vantage.timeseries import TimeSeries
from alpha_vantage.techindicators import TechIndicators
from alpha_vantage.fundamentaldata import FundamentalData



# 加载.env并打印密钥（测试用，后续可删除）
# 手动指定.env路径（比如.env和脚本都在agents文件夹里）
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
    temperature=0.3
)

# 后续的messages定义和invoke调用保持不变
messages = [
    {"role": "system", "content": "Now you are a very professional investment expert"},
    {"role": "user", "content": "hello,what's the date today?"}
]
for chunck in ChatLLM.stream(messages):# 在上面的ChatOpenAI中将streaming=True，使用流式输出
    print(chunck.content,end="",flush=True)


