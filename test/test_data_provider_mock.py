import pytest
from unittest.mock import Mock,patch
from agents.data_provider import DataProvider

# Mock()创建模拟对象
# return_value 设置方法返回值
# side_effect 模拟异常
# assert_called_once()验证方法被调用

class TestDataProviderMocked:
    """使用Mock对象的测试"""
    # patch是python unittest.mock模块提供的装饰器或者说上下文管理器，用于在测试时临时替换真实对象
    # 语法1：作为装饰器使用 @patch('模块路径.要替换的对象') def test_函数名(self,mock_object):其中mock_object就是被替换后的假对象
    # 若@patch('模块.类A')  @patch('模块.类B') 则def test_xx(self,mock_B,mock_A)
    @patch('agents.data_fetchers.finnhub_fetcher.finnhub.Client')  
    # 即找到agents/data_fetchers/finnhub_fetcher.py文件中的finnhub_Client类，把其替换为mock_finnhub_client
    def test_finnhub_api_call(self,mock_finnhub_client):
        """测试：模拟FinnhubAPI响应"""
        # Arrange:设置Mock返回值
        mock_instance=mock_finnhub_client.return_value
        mock_instance.company_profile2.return_value={
            "name":"Test Company",
            "finnhubIndustry":"Technology",
            "marketCapitalization":10000
        }
        # Act
        from agents.data_fetchers.finnhub_fetcher import FinnhubFetcher
        fetcher=FinnhubFetcher("fake_key")
        result=fetcher.fetch_company_profile("TEST")

        # Assert：实际返回的是中文键名
        assert result["名称"]=="Test Company"  # 修复：改为中文键名
        assert result["行业"]=="Technology"    # 修复：改为中文键名
        mock_instance.company_profile2.assert_called_once_with(symbol="TEST")

    def test_fallback_mechanism(self):
        """测试：主数据源失败时自动切换"""
        # Arrange:创建一个会失败的Mock Fetcher
        mock_fetcher1=Mock()
        mock_fetcher1.get_name.return_value="MockSource1"
        mock_fetcher1.fetch_company_profile.side_effect=RuntimeError("API限流")

        # 创建一个成功的Mock Fetcher
        mock_fetcher2=Mock()
        mock_fetcher2.get_name.return_value="MockSource2"
        mock_fetcher2.fetch_company_profile.return_value={
            "name":"Backup Data",
            "industry":"Tech"
        }

        # 手动注入Mock对象
        provider=DataProvider()
        provider.fetchers=[mock_fetcher1,mock_fetcher2]

        # Act
        result=provider.get_company_profile('AAPL')

        # Assert
        assert result['name']=="Backup Data"  # Mock返回的数据用的是英文键名
        assert result["source"]=="MockSource2" 
        mock_fetcher1.fetch_company_profile.assert_called_once()
        mock_fetcher2.fetch_company_profile.assert_called_once()


        

