from abc import ABC, abstractmethod
from typing import Dict,Any

class BaseFetcher(ABC):
    """
    数据获取器抽象基类，所有数据源必必须继承此类并实现指定方法
    """
    def __init__(self,api_key:str):
        """
        初始化数据源
        参数:api_key API密钥
        """
        self.api_key=api_key
        self._validate_api_key()

    def _validate_api_key(self):
        """验证API密钥"""
        if not self.api_key or len(self.api_key)==0:
            raise ValueError(f"{self.get_name()}API key is required")
    
    @abstractmethod
    def get_name(self)->str:
        """
        返回数据源名称，比如"Finnhub","Alpha Vantage"
        """
        pass

    @abstractmethod
    def fetch_company_profile(self,symbol:str)->Dict[str,Any]:
        """
        获取公司资料
        参数：
            symbol为公司股票代码,示例"NVDA"/"AAPL"
        返回：
            返回名称、行业、市值、网址等数据信息的字典
        """
        pass

    @abstractmethod
    def fetch_real_time_quote(self,symbol:str)->Dict[str,Any]:
        """
        获取实时股票报价
        参数：
            symbol为公司股票代码,示例"NVDA"/"AAPL"
        返回：
            返回最新成交价、当日最高价、当日最低价、当日开盘价、前一个交易日的收盘价等数据信息的字典
        """
        pass

    @abstractmethod
    def fetch_historical_financials(self,symbol:str)->Dict[str,Any]:
        """
        获取公司历史金融数据
        参数：
            symbol为公司股票代码,示例"NVDA"/"AAPL"
        返回：
            返回52周最高/价、Beta系数、最新数据更新时间等数据信息的字典
        """
        pass
    
    def is_available(self)->bool:
        """
        检查数据源是否可用
        子类可重写方法实现健康检查
        """
        return True

        
