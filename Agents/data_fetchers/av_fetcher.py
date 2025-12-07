from alpha_vantage.fundamentaldata import FundamentalData
from alpha_vantage.timeseries import TimeSeries
from .base_fetcher import BaseFetcher
from typing import Dict,Any

class AlphaVantageFetcher(BaseFetcher):
    def __init__(self, api_key):
        super().__init__(api_key)

    def get_name(self)->str:
        return "Alpha Vantage"
    
    def fetch_company_profile(self, symbol:str)->Dict[str,Any]:
        """从Alpha Vantage中获取公司信息"""
        try:
            fd=FundamentalData(key=self.api_key,output_format='dict')
            overview, _ = fd.get_company_overview(symbol)
            return{
            '金融数据来源':'Alpha Vantage',
            '名称':overview.get('Name','N/A'),
            '行业':overview.get('Industry','N/A'),
            'ipo时间':overview.get('IPODate','N/A'),
            '市值(百万美元)':float(overview.get('MarketCapitalization',0)/1000000),
            '官网':'N/A',#Alpha Vantage不提供官网
            '描述':overview.get('Description','N/A'),
            }
        except Exception as e:
            raise RuntimeError(f"Alpha Vantage API error: {e}")
        
    def fetch_real_time_quote(self, symbol:str)->Dict[str,Any]:
        """从Alpha Vantage中获取股价数据"""
        try:
            ts = TimeSeries(key=self.api_key, output_format='dict')
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
        except Exception as e:
            raise RuntimeError(f"Alpha Vantage API error: {e}")
        
    def fetch_historical_financials(self, symbol:str)->Dict[str,Any]:
        try:
            fd=FundamentalData(key=self.api_key,output_format='dict')
            overview,_=fd.get_company_overview(symbol)
            return {
                'source': 'Alpha Vantage',
                "52周最高": float(overview.get('52WeekHigh', 0)),
                "52周最低": float(overview.get('52WeekLow', 0)),
                "Beta系数": float(overview.get('Beta', 0)),
                "PE比率": float(overview.get('PERatio', 0)),
                "毛利率": float(overview.get('GrossMarginTTM', 0))
            }
        except Exception as e:
            raise RuntimeError(f"Alpha Vantage API error: {e}")

# 好像av_fetcher.py文件没有做is_available测试。。

        
            