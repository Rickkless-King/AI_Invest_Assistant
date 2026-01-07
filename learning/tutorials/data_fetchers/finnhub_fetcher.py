import finnhub
from .base_fetcher import BaseFetcher
from typing import Dict,Any
import datetime

class FinnhubFetcher(BaseFetcher):
    """Finnhub数据获取器"""
    def __init__(self, api_key:str):
        super().__init__(api_key)
        self.client=finnhub.Client(api_key=self.api_key)

    def get_name(self)->str:
        return "Finnhub"
    
    def fetch_company_profile(self, symbol:str)->Dict[str,Any]:
        """从Finnhub金融数据源获取公司信息"""
        try:
            profile=self.client.company_profile2(symbol=symbol)
            return{
            '金融数据来源':'Finnhub',
            '名称':profile.get('name'),
            '行业':profile.get('finnhubIndustry'),
            'ipo时间':profile.get('ipo'),
            '市值(百万美元)':profile.get('marketCapitalization'),
            '官网':profile.get('weburl'),
            '描述':profile.get('description'),
             }
        except Exception as e:
            raise RuntimeError(f"Finnhub API error: {e}")
    
    def fetch_real_time_quote(self, symbol:str)->Dict[str,Any]:
        """从Finnhub金融数据源获取实时股价信息"""
        try:
            real_time_data=self.client.quote(symbol=symbol)
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
            raise RuntimeError(f"Finnhub API error: {e}")
    
    def fetch_historical_financials(self, symbol:str)->Dict[str,Any]:
        financials=self.client.company_basic_financials(symbol,"all")
        metric=financials.get('metric',{})
        return{
            '金融数据来源':'Finnhub',
            "52周最高":metric.get('52WeekHigh'),
            "52周最低": metric.get("52WeekLow"),
            "Beta系数": metric.get("beta"),
            "PE比率": metric.get("peBasicExclExtraTTM"),
            "毛利率": metric.get("grossMarginTTM")
        }
    
    def is_available(self):
        """健康检查"""
        try:
            self.client.quote("AAPL")
            return True
        except:
            return False
        
        