import os
from dotenv import load_dotenv
from datetime import date,timedelta
import datetime
import finnhub
from alpha_vantage.fundamentaldata import FundamentalData
from alpha_vantage.timeseries import TimeSeries
from fredapi import Fred

class DataProvider():
    def __init__(self):# 必须要有的都放在_init_()里面，涉及重复使用的self.xxx
        """初始化所有数据源"""
        load_dotenv()
        # 初始化FRED
        self.fred_client=Fred(api_key=os.getenv("FRED_API_KEY"))
        # 初始化Finnhub
        self.finnhub_client=finnhub.Client(api_key=os.getenv("FINNHUB_API_KEY"))
        # 初始化Alpha Vantage
        self.av_api_key=os.getenv("ALPHAVANTAGE_API_KEY")
        print("金融数据源初始化完成")
    
    def fetch_macro_economy_data(self):
        """
        获取美国宏观经济数据：
        返回包含以下数据的字典
        - 汇率(美元兑人民币、日元、欧元)
        - 利率(联邦基金目标利率)
        - 通胀(CPI、核心CPI、核心PCE)
        - GDP(名义GDP、实际GDP、GDP平减指数)
        """
        macro_data={}
        try:
        # 美元兑人民币(DEXCHUS)
         usd_cny=self.fred_client.get_series('DEXCHUS',observation_start='2024-01-01')
        # 调用fred_client中的get_series()方法，请求FRED数据库中序列为DEXCHUS(对应美元兑人民币汇率)的数据，
        # 且仅获取2024-01-01之后的观测值，返回的usd_cny是一个带日期索引的时间序列对象(通常是pandas series)
         macro_data['美元兑人民币']={# 在macro_data字典中创建一个'美元兑人民币'的子字典，用于存储该汇率的具体信息
            '最新值':round(usd_cny.iloc[-1],4),# iloc[-1]获取usd_cny序列的最后一个值(即最新的汇率数据)， round(xxx,4)将该值保留4位小数，作为'最新值'的内容存入子字典
            '更新日期':usd_cny.index[-1].strftime('%Y-%m-%d')# # index[-1]获取usd_cny序列的最后一个索引标签(即最新汇率数据对应的日期)，round(xxx,4)将该值保留4位小数
            # .strftime('%Y-%m-%d')将日期格式转化为'年-月-日'的字符串形式，作为‘更新日期’存入子字典中
            }
        # 美元兑日元(DEXJPUS)
         usd_jp=self.fred_client.get_series('DEXJPUS',observation_start='2024-01-01')
         macro_data['美元兑日元']={
            '最新值':round(usd_jp.iloc[-1],4),
            '更新日期':usd_jp.index[-1].strftime('%Y-%m-%d')
         }
        
        # 欧元兑美元(DEXUSEU)--注意，想要获得美元兑欧元需要去倒数
         eur_usd=self.fred_client.get_series('DEXUSEU',observation_start='2024-01-01')
         macro_data['美元兑欧元']={
            '最新值':round(1/eur_usd.iloc[-1],4),
            '更新日期':eur_usd.index[-1].strftime('%Y-%m-%d')
         }
        except Exception as e:
            print(f"获取汇率数据失败：{e}")
            macro_data['汇率数据']="获取失败"
        
        try:# 获取利率数据
        # 联邦基金目标利率上限(DFEDTARU)
         fed_rate_upper=self.fred_client.get_series('DFEDTARU',observation_start='2024-01-01')
         # 联邦基金目标利率下线(DFEDTARL)
         fed_rate_lower=self.fred_client.get_series('DFEDTARL',observation_start='2024-01-01')

         macro_data['联邦基金目标利率']={
            '利率区间':f"{fed_rate_lower.iloc[-1]:.2f}%-{fed_rate_upper.iloc[-1]:.2f}%",
            '更新日期':fed_rate_upper.index[-1].strftime('%Y-%m-%d')
         }
        except Exception as e:
            print(f'利率数据获取失败：{e}')
            macro_data['联邦基金目标利率']='获取失败'

        try:# 就业数据
        # 非农就业人数(千人)(PAYEMS)
         payrolls=self.fred_client.get_series('PAYEMS',observation_start='2024-01-01')
         macro_data['非农就业人数']={
            '最新值':int(payrolls.iloc[-1]),
            '月度变化(千人)':int(payrolls.iloc[-1]-payrolls.iloc[-2]),
            '更新日期':payrolls.index[-1].strftime('%Y-%m-%d')
         }
         # 失业率(UNRATE)
         unemployment=self.fred_client.get_series('UNRATE',observation_start='2024-01-01')
         macro_data['失业率']={
            '最新值(%)':round(unemployment.iloc[-1]),
            '更新日期':unemployment.index[-1].strftime('%Y-%m-%d')
         }
         # 平均时薪(美元/小时)(CES0500000003)
         hourly_earnings=self.fred_client.get_series('CES0500000003',observation_start='2024-01-01')
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
         cpi=self.fred_client.get_series('CPIAUCNS',observation_start='2023-01-01')
         cpi_yoy=((cpi.iloc[-1]/cpi.iloc[-13])-1)*100

         # 核心CPI(不含食品和能源)(CPILFESL)
         core_cpi=self.fred_client.get_series('CPILFESL',observation_start='2023-01-01')
         core_cpi_yoy=((core_cpi.iloc[-1]/core_cpi.iloc[-13])-1)*100

         # 核心PCE价格指数(PCEPILFE)
         core_pce=self.fred_client.get_series('PCEPILFE',observation_start='2023-01-01')
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
         nominal_gdp=self.fred_client.get_series('GDP',observation_start='2023-01-01')

         # 实际GDP(2017年链式美元)(GDPC1)
         real_gdp=self.fred_client.get_series('GDPC1',observation_start='2023-01-01')

         # GDP平减指数(GDPDEF)
         gdp_deflator=self.fred_client.get_series('GDPDEF',observation_start='2023-01-01')

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
        print("===宏观数据获取完成===")
        return macro_data
    
    def get_company_profile(self,symbol):# 定义函数的时候，也需要带上self
        """
        获取公司信息
        参数：
            symbol为公司股票代码,如"NVDA"
        返回：
            包含公司信息的字典
        """
        try:
            return self._fetch_company_profile_from_finnhub(symbol)# self._func(symbol)表示内部函数，此时里面不需要再写self
        except Exception as e:
            print(f"Finnhub获取失败,原因:{e}")
            print("切换到Alpha Vantage数据源")
            return self._fetch_company_profile_from_alpha_vantage(symbol)
    
    def _fetch_company_profile_from_finnhub(self,symbol):
        """通过Finnhub数据源来获取公司名称、所属行业、IPO时间、市值、官网等信息"""
        profile=self.finnhub_client.company_profile2(symbol=symbol)
        return {
            '名称':profile.get('name'),
            '行业':profile.get('finnhubIndustry'),
            'ipo时间':profile.get('ipo'),
            '市值(百万美元)':profile.get('marketCapitalization'),
            '官网':profile.get('weburl')
        }
    def _fetch_company_profile_from_alpha_vantage(self,symbol):
        """通过Alpha Vantage数据源来获取公司名称、所属行业、IPO时间、市值、官网等信息"""
        fd=FundamentalData(key=self.av_api_key,output_format='dict')
        overview,_=fd.get_company_overview(symbol)
        return {
            '名称':overview.get('Name','N/A'),
            '行业':overview.get('Industry','N/A'),
            'ipo时间':overview.get('IPODate','N/A'),
            '市值(百万美元)':float(overview.get('MarketCapitalization',0)/1000000),
            '官网':'N/A',#Alpha Vantage免费版不提供官网
        }
    def get_real_time_quote(self,symbol):
        """
        获取公司实时股价数据
        参数：
            symbol为公司股票代码,比如"NVDA"
        返回：
            返回包含公司股价相关的字典
        """
        try:
            return self._fetch_stock_real_time_quote_from_finnhub(symbol)
        except Exception as e:
            print(f"获取公司实时股价数据失败,原因{e}")
            print("切换到Alpha Vantage数据源")
            return self._fetch_stock_real_time_quote_from_alpha_vantage(symbol)
    def _fetch_stock_real_time_quote_from_finnhub(self,symbol):
        """通过Finnhub获取股票最新成交价、当日最高价、当日最低价、当日开盘价、前一个交易日的收盘价、上述数据的更新时间(北京时间)等数据"""
        real_time_data=self.finnhub_client.quote(symbol=symbol)
        timestamp = real_time_data.get('t')
        local_time = datetime.datetime.fromtimestamp(timestamp)
        formatted_local_time = local_time.strftime("%Y-%m-%d %H:%M:%S")
        return{
            "最新成交价": real_time_data.get('c'),
            "当日最高价": real_time_data.get('h'),
            "当日最低价": real_time_data.get('l'),
            "当日开盘价": real_time_data.get('o'),
            "前一个交易日的收盘价": real_time_data.get('pc'),
            "上述数据的更新时间(北京时间)": formatted_local_time
        }
    def _fetch_stock_real_time_quote_from_alpha_vantage(self,symbol):
        """Alpha Vantage获取股票最新成交价、当日最高价、当日最低价、当日开盘价、前一个交易日的收盘价、上述数据的更新时间(北京时间)等数据"""
        ts = TimeSeries(key=self.av_api_key, output_format='dict')
        quote, _ = ts.get_quote_endpoint(symbol)
        return{
                "最新成交价": float(quote.get('05. price', 0)),
                "当日最高价": float(quote.get('03. high', 0)),
                "当日最低价": float(quote.get('04. low', 0)),
                "当日开盘价": float(quote.get('02. open', 0)),
                "前一个交易日的收盘价": float(quote.get('08. previous close', 0)),
                "上述数据的更新时间(北京时间)": quote.get('07. latest trading day', 'N/A')
        }
    def get_financials(self,symbol):
        """
        获取公司一些金融数据
        参数：
            symbol为公司股票代码,比如"NVDA"
        返回：
            返回股票52周最高/最低价，返回Beta系数、PE比率、毛利率等数据的字典
        """
        try:
            return self._fetch_stock_financials_from_finnhub(symbol)
        except Exception as e:
            print(f"获取公司一些金融数据失败,原因：{e}")
            print("切换到Alpha Vantage数据源")
            return self._fetch_stock_financials_from_alpha_vantage(symbol)
    
    def _fetch_stock_financials_from_finnhub(self,symbol):
        """通过Finnhub获取52周最高最低股价,获取Beta系数、PE比率、毛利率等数据"""
        financials=self.finnhub_client.company_basic_financials(symbol,'all')
        metric=financials.get('metric',{})
        series=financials.get("series")# 这里有个问题，Finnhub免费版提示相较于Alpha Vantage能够提供更多的数据，因此使用try_except块并不能两个金融数据源提供一样多的金融数据
        return{
            "52周最高":metric.get('52WeekHigh'),
            "52周最低": metric.get("52WeekLow"),
            "最近10个交易日平均交易量":metric.get("10DayAverageTradingVolume"),
            "52周内最低点发生日期":metric.get("52WeekLowDate"),
            "基于过去52周每日收盘价计算的价格回报率":metric.get("52WeekPriceReturnDaily"),
            "Beta系数": metric.get("beta"),
            "PE比率": metric.get("peBasicExclExtraTTM"),
            "毛利率": metric.get("grossMarginTTM"),
            "流动比率历史变化情况":series.get("annual",{}).get("currentRatio",[]),
            "每股对应销售额历史变化情况":series.get("annual",{}).get("salesPerShare",[]),
            "净利润率历史变化情况":series.get("annual",{}).get("netMargin",[])
        }
    
    def _fetch_stock_financials_from_alpha_vantage(self,symbol):
        """通过Alpha Vantage获取52周最高最低股价,获取Beta系数、PE比率、毛利率等数据"""
        fd=FundamentalData(key=self.av_api_key,output_format='dict')
        overview,_=fd.get_company_overview(symbol)
        return {
            "52周最高": float(overview.get('52WeekHigh', 0)),
            "52周最低": float(overview.get('52WeekLow', 0)),
            "Beta系数": float(overview.get('Beta', 0)),
            "PE比率": float(overview.get('PERatio', 0)),
            "毛利率": float(overview.get('GrossMarginTTM', 0))
        }
    

    def fetch_company_lastest_14D_news(self,symbol):
        """获取公司最近14天的新闻(我目前使用的是免费版API,因此最多支持获取最近30天的新闻)"""
        end=date.today()
        start=end-timedelta(days=14)# (免费版可获取最近30天的数据，每日限次数)
        company_news=self.finnhub_client.company_news(symbol,start.isoformat(),end.isoformat())
        return company_news
    
    def fetch_company_peers(self,symbol):
        """获取公司的竞争对手(会返回一个列表，列表元素为同行业竞争对手的股票代码,比如AVGO、AMD)"""
        company_peers=self.finnhub_client.company_peers(symbol)
        return company_peers
    
    def fetch_earnings_calendar(self,symbol):
        """获取指定时间段内股票财报内容(财报发布时间、市场预期营收和实际营收,市场预期EPS和实际EPS)数据"""      
        end=date.today()
        start=end-timedelta(days=30)
        earnings_calendar=self.finnhub_client.earnings_calendar(_from=start,to=end,symbol=symbol,international=False)
        report_list=earnings_calendar.get('earningsCalendar',[])#获取最外面字典里面的列表
        report=report_list[0]#上面代码获取的report_list是一个列表，不能直接.get()方法，因此需要进入到列表里面，里面才是字典
        return{
        "股票代码":report.get('symbol'),
        "报告区间":f"{report.get('year')}年第{report.get('quarter')}季",
        "财报发布时间":report.get('date'),
        "预计营收(单位；亿美元)":report.get('revenueEstimate')/100000000,
        "实际营收(单位；亿美元)":report.get('revenueActual')/100000000,
        "预期EPS":report.get('epsEstimate'),
        "实际EPS":report.get('epsActual'),
        }
    
    def fetch_stock_inside_transactions(self,symbol):
        """获取公司内部人士增/减持股票数据"""
        end=date.today()
        start=end-timedelta(days=30)
        stock_inside_transactions=self.finnhub_client.stock_insider_transactions(symbol,start,end)# 还是获取最近30天的数据
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
    
    def fetch_reported_financials(self,symbol):
        """获取公司已经报告的财务数据,时间区间为年度"""
        financials_reported=self.finnhub_client.financials_reported(symbol=symbol,freq='annual')
        financial_reported_details={
        "股票代码":financials_reported.get("symbol"),
        "对应的CIK编码为":financials_reported.get("cik"),
        "具体的财务数据如下":financials_reported.get("data")
        }
        return financial_reported_details
    
    def fetch_SEC_fillings(self,symbol):
        """获取上市公司在SEC备案文件，时间跨度为最近30天"""
        end=date.today()
        start=end-timedelta(days=30)
        stock_filings=self.finnhub_client.filings(symbol=symbol,_from=start,to=end)
        return stock_filings

    

    
# 调用
if __name__=="__main__":
    # 创建对象
    financial_data_source=DataProvider()
    # 获取数据
    us_macro_data=financial_data_source.fetch_macro_economy_data()
    nv_company_profie=financial_data_source.get_company_profile("NVDA")
    nv_lastest_price=financial_data_source.get_real_time_quote("NVDA")
    nv_historical_financials=financial_data_source.get_financials("NVDA")
    nv_lastest_14D_news=financial_data_source.fetch_company_lastest_14D_news("NVDA")
    nv_company_peers=financial_data_source.fetch_company_peers("nvda")
    nv_financials_lastest_reported=financial_data_source.fetch_earnings_calendar("nvda")
    nv_insider_transactions=financial_data_source.fetch_stock_inside_transactions("NVDA")
    nv_reported_financials=financial_data_source.fetch_reported_financials("NVDA")
    nv_SEC_fillings=financial_data_source.fetch_SEC_fillings("NVDA")

    # print(f"公司信息如下:{nv_company_profie}")
    # print(f"公司最新的股价数据如下:{nv_lastest_price}")
    # print(f"公司一些历史金融数据如下:{nv_historical_financials}")
    # print(f"公司最近14天的新闻如下:{nv_lastest_14D_news}")
    # print(f"公司的竞争对手为{nv_company_peers}")
    # print(f"公司最近一个月披露的财报数据为:{nv_financials_lastest_reported}")
    # print(f"公司内部最近30天内部增/减持股票情况为:{nv_insider_transactions}")
    # print(f"美国宏观经济数据如下:{us_macro_data}")



