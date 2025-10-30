### 目前我还停留在通过data=f-string的方式将内容送进messages里面进行触发。
## 前两周的任务是理解Langchain的LCEL语法，替代之前的字符串拼接方式
# 这两天的任务是理解核心概念： prompt|llm|parser
# 完成后改造我之前的fundamental_analysis函数

from langchain_core.prompts import ChatPromptTemplate
# 导入ChatPromptTemplate类，用于构建聊天格式的提示词模板，支持system，user，assistant等角色的消息组织
from langchain_core.output_parsers import StrOutputParser
# 导入StrOutputParser类，是一个输出解析器，将LLM的原始输出解析为字符串格式
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
import os# 用于操作系统相关功能，这里是读取变量
from dotenv import load_dotenv
from typing import Any
from fundamental_analyst import get_macro_economic_data
from fundamental_analyst import get_company_profile_with_fallback
from fundamental_analyst import get_real_time_data_with_fallback
from fundamental_analyst import get_financials_with_fallback

load_dotenv()# 加载.env()文件中的环境变量

llm=ChatOpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    model="qwen-plus",
    temperature=0.1,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

# 任务一：最简单的链
def simple_chain_example():
    """
    学习最基本的prompt|llm|parser结构
    """
    prompt=ChatPromptTemplate.from_messages([# 初始化ChatPromptTemplate实例prompt，使用form_messages方法构建多角色聊天格式的提示词模板
        ("system","你是专业的投资分析师"),
        # 大多数大模型的API输入要求都是“角色-内容”的结构化列表。
        ("user","用一句话评价{symbol}的投资价值")
        # {symbol}是一个模板变量，他不需要在函数定义时手动传入参数，而是在链执行时才会被动态替换。
        # 这算是Langchain“声明式模板+运行时绑定”机制：模板负责定义需要哪些变量，而执行时的输入字典负责“提供变量的值”。
    ])

    # LCEL的核心，用|连接组件
    chain=prompt|llm|StrOutputParser()# 构建完整的链chain：流程为prompt格式化输入→llm执行推理→StrOutputParser解析为字符串。
    # 管道操作符|是Langchain的LCEL(Langchain expressive Language)机制，核心是“组件串联即数据流串联”。
    # 直接使用管道操作符|让prompt接收输入变量，再将提示词传递给llm，再将llm的输出传给StrOutputParser，解析为字符串，声明式语法可以让开发者少写glue code。
    for chunk in chain.stream({"symbol":"NVDA"}):
        # print(chunk.content,end="",flush=True) 经过StrOutputParser解析之后，流式输出的chunk已经是字符串类型，而非包含content属性的对象。
        # 直接content输出
        print(chunk,end="",flush="True")

# if __name__=="__main__":
#     simple_chain_example()

# 任务二：多步骤链:用于演示“分析→建议”的两步流程，核心是学习如何传递中间结果
def multi_step_chain():
    # 学习如何传递中间结果
    from langchain_core.runnables import RunnablePassthrough# 导入RunnablePassthrough:Langchain的“数据传递组件”，
    # 用于在链的不同步骤间传递原始输入或中间结果(类似管道作用，不修改数据，仅负责传递)

    # 步骤1：生成分析
    analysis_prompt=ChatPromptTemplate.from_messages([
        ("system","你是投资分析师"),
        ("user","分析{symbol},数据：{data}\n只输出分析结论")
    ])
    # 步骤2：生成建议
    recommendation_prompt=ChatPromptTemplate.from_messages([
        ("system","你是投资顾问"),
        ("user","基于{analysis}的分析，给出买入/持有/卖出的建议")
    ])
    # 关键：用字典传递中间结果
    chain=(# 开始定义多步骤链chain
        # 调用RunnablePassthrough将外部输入(如{“symbol”:“NVDA“,“data”："XXXX")原样传递到下一个步骤，作为整个链的初始数据。[Any]表示接受任意类型的输入。
        RunnablePassthrough[Any]()
        # 执行分析链并将结果存为“analysis”
        | {"analysis":analysis_prompt|llm|StrOutputParser(),# |连接到一个字典{}。analysis_prompt(格式化输入)→llm(生成分析)→StrOutputParser(解析为字符串)，将结果存入字典的值中。
          "symbol":lambda x:x["symbol"],#字典的第二个键symbol，通过
          "data":lambda x:x["data"]}
        # 执行建议链 
        | {"recommendation":recommendation_prompt | llm |StrOutputParser(),
          "analysis":lambda x:x["analysis"]# 传递分析结果
          }
        # 总的来说，这个Chain里面就是 RunnablePassthrough|{字典1}}|{字典2},RunnablePassthrough把Chain，invoke中的内容传入字典1的x内容中
        # lambda x:x["symbol"]的意思是获取x中key为“symbol”的value，并返回作为“symbol”的value。
        # 对于字典2来说，首先是recommendation_prompt传入llm中进行分析，然后以字符串的形式返回，返回后作为"recommendation"的value。
        # 其中，recommendation_prompt里的{analysis}是会获取字典1中“analysis”key对应的value值。
        # 为什么“recommendation”键已经分析出结论并将其作为自己的value了，为什么还需要再搞一个“analysis”key-value对呢？
        # ——如果只保留了结果，就少了分析的留档，因此在这里也把其加上。
    )
    result=chain.invoke({# invoke里面写输入信息，有点像stream(messages)
        "symbol": "NVDA",
        "data": "PE=50, Beta=2.0, 52周涨幅+120%"
    })
    print("分析", result["analysis"])
    print("建议", result["recommendation"])

# if __name__=="__main__":
#     multi_step_chain()

# 任务三：用上述学到最简单链和多步骤链，修改自己之前的fundamental_analyst.py文件。
def Langchain_macro_eoconmy_stock_analyze_with_fallback(symbol:str):
    macro_data=get_macro_economic_data()#获取宏观经济数据
    macro_data_detailed=f"""
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
 """
    # 使用下列函数之前需要先from XXXX import XXX，同时注意，因为lcel_basic与fundamental_analyst.py位于同一文件夹下，因此可以不需要XX.XXX
    profile = get_company_profile_with_fallback(symbol)
    quote = get_real_time_data_with_fallback(symbol)
    financials = get_financials_with_fallback(symbol)
    symbol_detailed=f"""
     根据我提供的{symbol}的基本面数据，为我进行分析；
     公司信息：
     - 名称：{profile['名称']}
     - 行业：{profile['行业']}
     - 市值：{profile['市值(百万美元)']}百万美元
    
     最新报价：
     - 当前价格：${quote['最新成交价']}
     - 52周区间:${financials['52周最低']} - ${financials['52周最高']}
    
     财务指标：
     - PE比率:{financials['PE比率']}
     - Beta:{financials['Beta系数']}
 """
    # 现在使用Langchain替代最简单的data通过f-string塞进messages最后.invoke(messages)的方法，
    # 考虑参数传入Langchain_macro_eoconmy_stock_analyze_with_fallback()里太复杂了，我还是直接在.invoke()中先硬编码相关信息，再考虑参数传入
    # 形式还是使用prompt|llm|StrOutputParser()
    # 同时需要考虑到两个prompt里面都要传入角色-要求的内容，因此先让大模型分析宏观经济，然后再把宏观经济作为一部分，再塞进微观个股分析里
    macro_eco_prompt=ChatPromptTemplate.from_messages([
        ("system","现在你的身份是现在的你的身份是一名兼顾宏观经济周期分析与微观个股研究的顶级对冲基金经理，接下来我传入当下的宏观经济情况，请首先为我分析当下美国宏观经济情况如何"),
        ("user","基于我提供的{macro_eco_data},根据收到的宏观经济数据，判断当下所处的宏观经济环境是偏向宽松或是偏向紧缩，并根据通胀数据与就业数据，判断接下来美联储是会缩表或是扩表，即采取宽松的货币政策或是紧缩的货币政策，未来是否为继续降息放水。")
    ])# 在这里传入字典macro_eco_data键对应的value值，

    micro_stock_prompt=ChatPromptTemplate.from_messages([
        ("system","现在你的身份是现在的你的身份是一名兼顾宏观经济周期分析与微观个股研究的顶级对冲基金经理，擅长利用获得美国宏观经济数据与微观个股数据做出完整投资逻辑及判断"),
        ("user","基于已经获取的{analysis}宏观内容，结合{symbol_detailed}返回的内容进行个股的基本面数据分析，判断当下要分析的公司目前的股价是被高估或是低估，是否应当买入，为什么？按照目前的宏观情况与微观情况，什么样的价格买入比较合适？逻辑清晰，表达有条理，从宏观经济到微观个股进行自上而下的梳理")
    ])# 将{字典1}中{analysis}键的值传入本prompt中
    
    chain=(
        RunnablePassthrough[Any]()# 传递原始输入
        |{"analysis":macro_eco_prompt|llm|StrOutputParser(),#获取宏观数据分析结果，并将分析结果作为analysis键的value值。
          "symbol_detailed":lambda x:x["symbol_detailed"],
          "macro_eco_data":lambda x:x["macro_eco_data"]
        }# 第一个链获取宏观分析结果，并将其作为analysis的value值。
        |{"comprehensive_analysis":micro_stock_prompt|llm|StrOutputParser()
          #将之前获取的宏观数据分析结果，连同个股基本面信息送进llm中,并将其结果返回作为"comprehensive_analysis"的value值
        }

    )
    result=chain.invoke({
        "symbol_detailed":symbol_detailed,#我这里传入的value是字符串，而字符串本身使用f-string调用在fundamental_analyst.py中的函数key-value结果。
        "macro_eco_data":macro_data_detailed# 同样value为字符串，通过f-string方式获取，f-string里面使用[字典键]方式获取对应的value值。
    })

    print("AI大模型的建议:",result["comprehensive_analysis"])# 打印result[comprehensive_analysis]键对应的value值，即叠加了宏观的个股分析结果

if __name__=="__main__":
    Langchain_macro_eoconmy_stock_analyze_with_fallback("NVDA")# 这里必须传入“NVDA"以使用获取个股相关数据的函数

    


