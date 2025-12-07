import os
from dotenv import load_dotenv
from typing import List,Dict,Any# 类型注解，让代码更清晰比如List[BaseFetcher]表示这是一个装BaseFetcher子类的列表
from data_fetchers.base_fetcher import BaseFetcher
from data_fetchers.finnhub_fetcher import FinnhubFetcher #这里的data_fetchers文件夹和data_provider.py文件均处于Agents目录下，属于同级别目录，因此from data_fetchers.xxx
from data_fetchers.av_fetcher import AlphaVantageFetcher# 从data_fetcher包中导入抽象基类和两个数据源子类
# 而finnhub_fetcher.py和base_fetcher.py在同一个文件夹里面，因此在finnhub_fetcher.py中使用.base_fetcher

# 原来的fundamental_analyst.py是将所有get_xx函数挤在一个文件里，拆分代码是做模块化：base_fetcher.py抽象基类，finnhub_fetcher.py/av_fetcher.py这两个各自装一个数据源相关的代码
# __init__.py告诉pythondata_fetcher文件夹是一个模块/package
# data_provider.py 对外提供简单的交互接口，对内负责获取金融数据源的内容

class DataProvider:
    """
    对外隐藏数据源的复杂逻辑，只提供简单的查询接口(比如get_company_profile)
    用户不用关心背后是Finnhub还是Alpha Vantage
    """

    def __init__(self):
        load_dotenv()# 从.env文件读取你存在里面的两个API_KEY
        # 初始化所有数据源，先Finnhub再Alpha Vantage
        self.fetchers:List[BaseFetcher]=[# List[BaseFetcher]用到了多态：因为FinnhubFetcher和AlphaVantage都继承自BaseFetcher，
            # 我还是看不懂这个语法
            FinnhubFetcher(os.getenv("FINNHUB_API_KEY")),
            AlphaVantageFetcher(os.getenv("ALPHAVANTAGE_API_KEY"))
        ]
        print(f"已加载{len(self.fetchers)}个数据源")
    
    def get_company_profile(self,symbol:str)->Dict[str,Any]:
        """
        获取公司信息(自动容错)
        参数:
            symbol:股票代码
        返回：
            包含公司名称、行业等信息的字典
        """
        return self._fetch_with_fallback('fetch_company_profile',symbol)
    
    def get_real_time_quote(self,symbol:str)->Dict[str,Any]:
        """获取最新股价相关数据"""
        return self._fetch_with_fallback('fetch_real_time_quote',symbol)
    
    def get_historical_financials(self,symbol:str)->Dict[str,Any]:
        """获取历史股价相关数据"""
        return self._fetch_with_fallback('fetch_historical_financials',symbol)
    
    # 无论是get_real_time_quote/get_company_profile/get_historical_financials都是给用户用的“接口”，想查信息直接调用provider.get_company_profile("NVDA")，不需要明白具体怎么切换数据源
    
    def _fetch_with_fallback(self,method_name:str,symbol:str)->Dict[str,Any]:
        """
        核心方法：自动切换数据源
        参数：
            method_name:要调用的方法名
            symbol:股票代码
        """
        for fetcher in self.fetchers:# 按之前列表里的顺序遍历金融数据源
            try:
                #动态调用方法：根据method_name，从fetcher里拿到对应的方法
                method=getattr(fetcher,method_name)# 等价于fetcher.fetch_company_profile/fetch_real_time_quote/fetch_historical_financials
                result=method(symbol)

                # 添加数据源标识
                result['source']=fetcher.get_name()# result['source']用来向字典中添加新的键值对
                print(f"使用数据源:{fetcher.get_name()}")
                return result
            except Exception as e:
                print(f"使用{fetcher.get_name()}金融数据源失败，原因:{e}")
                continue # 循环继续，尝试下一个金融数据源

        # 所有数据源都失败
        raise RuntimeError(f"所有数据源获取{symbol}失败")
    
# 测试代码
if __name__=="__main__":
    provider=DataProvider()
    # 测试公司信息
    print("\n=== 测试公司信息 ===")
    profile = provider.get_company_profile("NVDA")
    print(f"公司: {profile['名称']}")
    print(f"行业: {profile['行业']}")
    print(f"数据源: {profile['金融数据来源']}")

    # 测试实时报价
    print("\n=== 测试实时报价 ===")
    quote = provider.get_real_time_quote("NVDA")
    print(f"价格: ${quote['最新成交价']}")
    print(f"数据源: {quote['source']}")
