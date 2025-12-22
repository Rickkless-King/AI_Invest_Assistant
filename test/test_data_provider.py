# 为之前的DataProvider编写测试
# 步骤1：安装pytest
## pip install pytest pytest-cov
## cd AI_Invest_Assistant pip freeze>requirements.txt
import pytest
from agents.data_provider import DataProvider
from agents.data_fetchers.base_fetcher import BaseFetcher

## 面向对象的概念VS“奶茶店日常”
## 封装：奶茶店对外只说“点单→取餐”，顾客不用知道珍珠怎么制作。    对外暴露简单接口，隐藏复杂逻辑
## 抽象基类ABC：老板的“菜谱”规定所有饮品都需要有“调甜度”+“加配料”+“选冷热”这几个步骤    只定义必须遵守的方法，不写具体实现
## 继承：子类用父类规则，实现自己的细节
## 多态：同一个“制作”指令，不同饮品有不同执行逻辑。    同一个方法名，不同子类有不同实现

## 映射到金融股票场景(面向对象版)
## 封装：股票数据提供者stockProvider对外只暴露get_stock_data接口，内部怎么调用API、合并数据管不到。
## 抽象基类：BaseFetcher：所有股票数据获取器(比如调用Finnhub/AVAPI的.py文件里)必须实现fetch_xxx方法。
## 继承：FinnhubFetcher、YahooFetcher都继承自BaseFetcher
## 多态：stockDataProvider调用fetch_realtime_data时，不管用Finnhub还是AV的获取器，都能拿到股票数据(同一个方法，不同API有不同实现)







class TestDataProvider:
    """测试DataProvider类"""
    @pytest.fixture
    def provider(self):# 制作或者说构造fixture之前需要弄一个@pytest.fixture装饰器
        """每个测试方法都会获得新的DataProvider对象"""
        return DataProvider()  #class DataProvider的实例化
    
    def test_initialization(self,provider):
        """测试：初始化应该成功加载数据源"""
        assert len(provider.fetchers)>=2# provider.fetchers应该包括FinnhubFetcher和 AlphaVantageFetcher，
        assert all(isinstance(f,BaseFetcher) for f in provider.fetchers)
        # 上面这句话是首先判断两个f是否为BaseFetcher类型，all()确保两个fetcher均为BaseFetcher类型
    
    # 测试函数的构成一般为test_函数名_success()   test_函数名_invalid_symbol()
    def test_get_company_profile_success(self,provider):# 使用Fixture就是需要在每个test函数中继承
        """测试:是否能够成功获取公司信息"""
        result=provider.get_company_profile("AAPL")
        # 整个测试函数来看，def test_函数名_success(self,fixture名称):
        # result=fixture名称.函数名()
        # 然后assert判断围绕result来展开
        assert result is not None
        assert "名称" in result  # 数据源返回的是中文键名
        assert "行业" in result
        assert "source" in result
        assert result["名称"]!=" "
    
    def test_get_company_profile_invalid_symbol(self,provider):
        """测试：无效股票代码应该返回空数据"""
        # Finnhub API不会对无效股票代码抛出异常，而是返回None值
        result = provider.get_company_profile("INVALID_SYMBOL_12123131")
        assert result is not None  # 仍然返回字典
        assert result["名称"] is None  # 但关键字段为None
    
    def test_get_real_time_quote(self,provider):
        quote=provider.get_real_time_quote("NVDA")

        assert quote is not None
        assert "最新成交价" in quote  # 数据源返回的是中文键名
        assert "当日最高价" in quote
        assert "当日最低价" in quote
        assert quote["最新成交价"]>0

    # 接下来进行参数化测试
    # 想要进行参数化测试，还是需要先弄一个装饰器@pytest.mark.parametrize("xx,yy",[(1-1,1-2),(2-1,2-2),(3-1,3-2)])
    @pytest.mark.parametrize("symbol,expected_field",[("AAPL","名称"),("NVDA","行业"),("GOOGL","市值(百万美元)")])
    def test_multiple_symbols(self,provider,symbol,expected_field):
        """测试：多个股票代码"""
        result=provider.get_company_profile(symbol)
        assert expected_field in result



    
    


