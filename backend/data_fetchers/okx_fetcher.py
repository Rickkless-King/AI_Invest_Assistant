"""
OKX交易所数据获取器
支持: 行情数据、K线数据、账户信息、交易下单
文档: https://www.okx.com/docs-v5/zh/
API v5 官方文档: https://www.okx.com/docs-v5/en/
"""

import requests
import hmac
import base64
import hashlib
from datetime import datetime
from typing import Dict, List, Optional
import time
import pandas as pd
import json
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class OKXFetcher:
    """
    OKX API数据获取类

    免费API限制:
    - 公共接口: 20次/2秒
    - 私有接口: 需要API Key
    """

    def __init__(self, api_key: str = "", secret_key: str = "", passphrase: str = "", demo: bool = True):
        # 我理解这里传入参数约定了参数类型，比如api_key为str类型，secret_key为str类型，但是这个demo：bool=True的意思是demo参数类型为bool，默认值是True，如果调用时不传入demo参数，会自动使用True
        """
        初始化OKX Fetcher

        Args:
            api_key: API密钥（可选，公共接口不需要）
            secret_key: 密钥（可选）
            passphrase: API密码（可选）
            demo: 是否使用模拟盘（True=模拟盘，False=实盘）
        """
        # 优先使用传入参数，否则从环境变量读取
        self.api_key = api_key or os.getenv("OKX_API_KEY", "")
        self.secret_key = secret_key or os.getenv("OKX_SECRET_KEY", "")
        self.passphrase = passphrase or os.getenv("OKX_PASSPHRASE", "")

        # 交易模式：1=模拟盘，0=实盘
        demo_env = os.getenv("OKX_DEMO_TRADING", "1")
        self.demo = demo if api_key else (demo_env == "1")# 这是一个三元条件表达式：if api_key: self.demo=demo else: self.demo=(demo_env==1) 即如果有API密钥，优先用户的传入，没有的话就使用模拟盘
        self.simulated = "1" if self.demo else "0"# 也是一个三元条件表达式： if self.demo为True，self.simulated="1" else:self.simulated="0"# 将布尔值转换为字符串"1"/"0"

        # OKX API基础URL
        self.base_url = "https://www.okx.com"

        # 请求头
        self.headers = {
            "Content-Type": "application/json"
        }# 是HTTP请求中的元数据，用于告诉服务器关于请求的额外信息，Content-Type:application/json 告诉服务器”我发送的数据是JSON格式"

        if self.demo:# 与上面呼应，如果self.demo为True，则self.simulated="1"，开启模拟盘模式
            print("⚠️  模拟盘模式 - 不会使用真实资金")

    def _generate_signature(self, timestamp: str, method: str, request_path: str, body: str = "") -> str:
        """
        生成签名（私有接口需要）

        Args:
            timestamp: ISO格式时间戳
            method: GET/POST
            request_path: 请求路径
            body: 请求体

        Returns:
            签名字符串
        """
        message = timestamp + method + request_path + body
        mac = hmac.new(
            bytes(self.secret_key, encoding='utf-8'),
            bytes(message, encoding='utf-8'),
            digestmod=hashlib.sha256
        )
        return base64.b64encode(mac.digest()).decode()

    def get_ticker(self, symbol: str = "BTC-USDT") -> Dict:
        """
        获取加密货币“币值对”的实时行情报价

        Args:
            symbol: 交易对，如 BTC-USDT, ETH-USDT

        Returns:
            {
                'symbol': 'BTC-USDT',
                'last': 42000.5,        # 最新成交价
                'bid': 41999.0,         # 买一价
                'ask': 42001.0,         # 卖一价
                'high_24h': 43000.0,    # 24h最高
                'low_24h': 41000.0,     # 24h最低
                'vol_24h': 1234.56,     # 24h成交量
                'timestamp': '2025-12-23T10:00:00Z'
            }
        """
        try:
            endpoint = f"/api/v5/market/ticker?instId={symbol}"
            url = self.base_url + endpoint
            # 假设endpoint=f"/api/v5/market/ticker?instId=BTC-USDT"
            # url="https://www.okx.com/api/v5/market/ticker?instId=BTC-USDT"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            # requests.get()是python的HTTP客户端，用来向服务器发送请求，获取数据
            # .raise_for_status()检查HTTP状态码，即检查HTTP请求是否成功
            # 如果状态码是200，response.raise_for_status()什么都不做，继续执行
            # 如果状态码是404/500/403(失败)，response.raise_for_status()抛出异常，跳到except块，不加这一行，即使请求失败，程序也会继续运行，导致后续代码出错

            data = response.json()
            # 从response对象中取出text部分，并将JSON字符串解析成python字典
            if data['code'] != '0':
                return {
                    'error': f"OKX API错误: {data['msg']}"
                }

            ticker_data = data['data'][0]
            # 上面通过data=response.json()已经将JSON字符串解析为字典，这里是获取data键对应的第一个值，并将其赋给变量ticker_data
            return {
                'symbol': symbol,
                'last': float(ticker_data['last']),
                'bid': float(ticker_data['bidPx']),
                'ask': float(ticker_data['askPx']),
                'high_24h': float(ticker_data['high24h']),
                'low_24h': float(ticker_data['low24h']),
                'vol_24h': float(ticker_data['vol24h']),
                'timestamp': datetime.now().isoformat()
            }
        # python允许一个try块配置多个except块，按从上到下的顺序匹配异常
        except requests.exceptions.RequestException as e:
            # RequestException是request库的基础异常，子类异常必须放在比如Exception这种父类异常的前面，用来捕获网络请求相关的所有异常
            # python从上到下依次检查except块，同时except块匹配成功了就停止
            return {
                'error': f"网络请求失败: {str(e)}"
            }
        except Exception as e:
            # Exception是普通异常的基类，几乎能捕获所有异常
            return {
                'error': f"未知错误: {str(e)}"# str(e)来获取异常的文字描述
            }

    def get_candles(
        self,
        symbol: str = "BTC-USDT",
        timeframe: str = "1H",
        limit: int = 300
    ) -> pd.DataFrame:
        """
        获取K线数据

        Args:
            symbol: 交易对
            timeframe: 时间周期
                - 1m, 3m, 5m, 15m, 30m (分钟)
                - 1H, 2H, 4H (小时)
                - 1D (日线)
                - 1W (周线)
            limit: 获取数量（最多300）

        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
        """
        try:
            # OKX的时间周期格式转换
            bar_map = {
                '1m': '1m', '3m': '3m', '5m': '5m', '15m': '15m', '30m': '30m',
                '1H': '1H', '2H': '2H', '4H': '4H',
                '1D': '1D', 
                '1W': '1W'
            }

            bar = bar_map.get(timeframe, '1H')
            limit = min(limit, 300)  # OKX限制最多300条

            endpoint = f"/api/v5/market/candles?instId={symbol}&bar={bar}&limit={limit}"
            url = self.base_url + endpoint

            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()

            data = response.json()

            if data['code'] != '0':
                print(f"OKX API错误: {data['msg']}")
                return pd.DataFrame()

            # 解析K线数据
            candles = data['data']

            df = pd.DataFrame(candles, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'volCcy', 'volCcyQuote', 'confirm'
            ])

            # 数据类型转换（OKX返回的是毫秒时间戳字符串）
            df['timestamp'] = pd.to_datetime(df['timestamp'].astype(float) / 1000, unit='s')
            df['open'] = df['open'].astype(float)
            df['high'] = df['high'].astype(float)
            df['low'] = df['low'].astype(float)
            df['close'] = df['close'].astype(float)
            df['volume'] = df['volume'].astype(float)

            # 只保留需要的列
            df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]

            # 按时间升序排列
            df = df.sort_values('timestamp').reset_index(drop=True)

            return df

        except Exception as e:
            print(f"获取K线数据失败: {str(e)}")
            return pd.DataFrame()

    def get_account_balance(self) -> Dict:
        """
        获取账户余额（需要API Key）

        Returns:
            {
                'total_equity': 10000.0,
                'balances': {
                    'USDT': 5000.0,
                    'BTC': 0.1
                }
            }
        """
        if not self.api_key:
            return {
                'error': '需要API Key才能获取账户信息'
            }

        try:
            endpoint = '/api/v5/account/balance'
            result = self._request_with_auth('GET', endpoint)

            if 'error' in result:
                return result

            # 解析余额数据
            balance_data = result['data'][0]
            details = balance_data['details']

            balances = {}
            for detail in details:
                currency = detail['ccy']
                available = float(detail['availBal'])
                if available > 0:
                    balances[currency] = available

            return {
                'total_equity': float(balance_data['totalEq']),
                'balances': balances,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'error': f"获取账户余额失败: {str(e)}"
            }

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算技术指标

        Args:
            df: K线数据DataFrame

        Returns:
            添加了技术指标的DataFrame
        """
        if df.empty:
            return df

        # RSI (14周期)
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))

        # MACD (12, 26, 9)
        exp1 = df['close'].ewm(span=12, adjust=False).mean()
        exp2 = df['close'].ewm(span=26, adjust=False).mean()
        df['macd'] = exp1 - exp2
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']

        # 布林带 (20, 2)
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['bb_std'] = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['sma_20'] + (df['bb_std'] * 2)
        df['bb_lower'] = df['sma_20'] - (df['bb_std'] * 2)

        # 成交量均线
        df['vol_ma_20'] = df['volume'].rolling(window=20).mean()

        return df

    # ==================== 交易相关功能 ====================

    def _request_with_auth(self, method: str, endpoint: str, params: Dict = None) -> Dict:
        """
        发送带认证的请求

        Args:
            method: HTTP方法 (GET/POST)
            endpoint: API端点
            params: 请求参数

        Returns:
            响应数据
        """
        if not self.api_key:
            return {'error': '需要配置 API Key 才能使用此功能'}

        try:
            # 生成时间戳 (ISO 8601格式)
            timestamp = datetime.utcnow().isoformat(timespec='milliseconds') + 'Z'
            # datetime不是从1970年开始计算的，从1970年开始的是Unix时间戳。datetime.utcnow()是获取当前的UTC时间，datetime.now()获取当前本地时间。
            # isoformat()将datetime对象转换成ISO 8601标准字符串，之所以转换成字符串是为了便于传输并使用国际标准格式。
            # timespec='milliseconds'即指定时间精度为毫秒(OKX要求毫秒级精度)。后面加个字符‘Z’这是UTC时区的标识

            # Unix时间戳，从1970年零时开始计算
            # timestamp=dt.timestamp()
            # print(timestamp)的结果是13453245324毫秒数
            
            # 准备请求体
            body = ""
            if params and method == 'POST':
                body = json.dumps(params)
                # json.dumps()将python字典转换成JSON字符串，简单可以理解为字典→‘字典’，注意，只能外单内双
                # 为什么需要转换，因为HTTP请求只能传输字符串，不能直接传输python对象
                # 服务器端会json.loads()将字符串转换回为字典

            # 生成签名
            signature = self._generate_signature(timestamp, method, endpoint, body)

            # 设置认证头
            auth_headers = self.headers.copy()
            auth_headers.update({
                'OK-ACCESS-KEY': self.api_key,
                'OK-ACCESS-SIGN': signature,
                'OK-ACCESS-TIMESTAMP': timestamp,
                'OK-ACCESS-PASSPHRASE': self.passphrase,
                'x-simulated-trading': self.simulated  # 模拟盘标识
            }) # 向字典中添加新的键值对(或更新已有的)，如果不使用.update()方法，就得dixt['key']='value'方式来逐个进行添加

            url = self.base_url + endpoint

            # 发送请求
            if method == 'GET':
                response = requests.get(url, headers=auth_headers, timeout=10)
                # requests.get()发送GET请求
                # GET用于获取数据，数据位置在URL参数中，数据大小受到URL长度限制，可用于查询价格、获取K线
            elif method == 'POST':
                response = requests.post(url, headers=auth_headers, data=body, timeout=10)
                # requests.post()发送POST请求
                # POST用于提交数据，数据放在body请求体中，数据大小不受限，可用于下单、转账、修改设置
                # data参数指定POST请求的请求体内容
            else:
                return {'error': f'不支持的HTTP方法: {method}'}

            response.raise_for_status()
            data = response.json()

            if data['code'] != '0':
                return {'error': f"OKX API错误: {data['msg']}"}

            return data

        except Exception as e:
            return {'error': f'请求失败: {str(e)}'}

    def place_order(self,symbol: str,side: str,order_type: str,size: float,price: Optional[float] = None
    # Optional[float]=float或None，即price可以是float或None 为什么不能直接写price:float=None。因为price只能是float类型，但给的默认值是None(不是float类型),类型声明和默认值矛盾。
    # 这样，当place_order1()时，没有价格为None,即其为市价单。place_order1(42000.0)，有价格float，我们知道其为限价单。
    # 另一个这样做的好处在于，IDE可能会提示你与做错误检查
    ) -> Dict:
        """
        下单

        Args:
            symbol: 交易对，如 BTC-USDT
            side: 订单方向 'buy' 或 'sell'
            order_type: 订单类型
                - 'market': 市价单
                - 'limit': 限价单
            size: 下单数量
            price: 价格（限价单必填）

        Returns:
            {
                'orderId': '123456789',
                'symbol': 'BTC-USDT',
                'side': 'buy',
                'type': 'limit',
                'price': 42000.0,
                'size': 0.01,
                'status': 'live'
            }
        """
        if not self.api_key:
            return {'error': '需要配置 API Key 才能下单'}

        try:
            # 构建订单参数
            order_params = {
                'instId': symbol,
                'tdMode': 'cash',  # 现货模式
                'side': side.lower(),
                'ordType': order_type.lower(),
                'sz': str(size)
            }

            # 限价单需要价格
            if order_type.lower() == 'limit':
                if price is None:
                    return {'error': '限价单必须指定价格'}# 如果是限价单但是没有价格，函数在这里直接return结束
                order_params['px'] = str(price)# 这里添加价格
            
            # 如果不是限价单，直接执行下面的程序
            endpoint = '/api/v5/trade/order'
            result = self._request_with_auth('POST', endpoint, order_params)

            if 'error' in result:
                return result

            # 解析响应
            if not result.get('data') or len(result['data']) == 0:
                # 如果只有len(result['data'])==0，则如果'data'不存在就会报错。
                # 想要简化直接 if not result.get('data')
                return {'error': f"OKX API返回数据为空: {result}"}

            order_data = result['data'][0]

            return {
                'orderId': order_data.get('ordId', ''),
                'symbol': symbol,
                'side': side,
                'type': order_type,
                'price': float(order_data.get('px', 0)) if order_data.get('px') else None,
                # 表达式格式 值1 if 条件 else 值2，这里的值1、值2分别为float(order_data.get('px', 0))、None。
                'size': float(size),  # 使用传入的size
                'status': order_data.get('sCode', ''),
                'message': order_data.get('sMsg', ''),
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            import traceback# 为了完整调用栈，按需导入，缺点是不太规范(最好在一开始)
            return {'error': f'下单失败: {str(e)}\n{traceback.format_exc()}'}
            # str(e)只有错误信息
            # traceback.format_exc()有完整的错误堆栈 ，能够告诉你错误类型、错误位置、错误代码

    def get_order(self, symbol: str, order_id: str) -> Dict:
        """
        查询订单状态

        Args:
            symbol: 交易对
            order_id: 订单ID

        Returns:
            订单详情
        """
        try:
            endpoint = f'/api/v5/trade/order?instId={symbol}&ordId={order_id}'
            result = self._request_with_auth('GET', endpoint)

            if 'error' in result:
                return result
            # 即如果result包含‘error’,则直接返回给调用者———result是self._request_with_auth()方法获取的结果，我们在_request_with_auth()里判断if data['code']!='0'返回的data中包含'error'键
            order_data = result['data'][0]

            return {
                'orderId': order_data['ordId'],
                'symbol': order_data['instId'],
                'side': order_data['side'],
                'type': order_data['ordType'],
                'price': float(order_data.get('px', 0)) if order_data.get('px') else None,
                'size': float(order_data['sz']),
                'filled': float(order_data['accFillSz']),
                'status': order_data['state'],
                'timestamp': order_data['cTime']
            }

        except Exception as e:
            return {'error': f'查询订单失败: {str(e)}'}

    def cancel_order(self, symbol: str, order_id: str) -> Dict:
        """
        取消订单

        Args:
            symbol: 交易对
            order_id: 订单ID

        Returns:
            取消结果
        """
        try:
            params = {
                'instId': symbol,
                'ordId': order_id
            }

            endpoint = '/api/v5/trade/cancel-order'
            result = self._request_with_auth('POST', endpoint, params)

            if 'error' in result:
                return result

            cancel_data = result['data'][0]

            return {
                'orderId': cancel_data['ordId'],
                'success': cancel_data['sCode'] == '0',
                'message': cancel_data['sMsg'],
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {'error': f'取消订单失败: {str(e)}'}

    def get_positions(self) -> List[Dict]:
        """
        查询当前持仓

        Returns:
            持仓列表
        """
        try:
            endpoint = '/api/v5/account/positions'
            result = self._request_with_auth('GET', endpoint)

            if 'error' in result:
                return []

            positions = []
            for pos in result['data']:
                if float(pos['pos']) != 0:  # 只返回有持仓的
                    positions.append({
                        'symbol': pos['instId'],
                        'side': pos['posSide'],
                        'size': float(pos['pos']),
                        'avgPrice': float(pos['avgPx']),
                        'unrealizedPnl': float(pos['upl']),
                        'margin': float(pos['margin'])
                    })

            return positions

        except Exception as e:
            print(f'查询持仓失败: {str(e)}')
            return []

    def get_order_history(self, symbol: str = "", limit: int = 100) -> List[Dict]:
        """
        查询历史订单

        Args:
            symbol: 交易对（可选，为空则查询所有）
            limit: 返回数量

        Returns:
            订单列表
        """
        try:
            endpoint = f'/api/v5/trade/orders-history-archive?instType=SPOT'
            if symbol:
                endpoint += f'&instId={symbol}'
            endpoint += f'&limit={limit}'

            result = self._request_with_auth('GET', endpoint)

            if 'error' in result:
                return []

            orders = []
            for order in result['data']:
                orders.append({
                    'orderId': order['ordId'],
                    'symbol': order['instId'],
                    'side': order['side'],
                    'type': order['ordType'],
                    'price': float(order.get('px', 0)) if order.get('px') else None,
                    'size': float(order['sz']),
                    'filled': float(order['accFillSz']),
                    'status': order['state'],
                    'timestamp': order['cTime']
                })

            return orders

        except Exception as e:
            print(f'查询历史订单失败: {str(e)}')
            return []

    def get_historical_candles_extended(
        self,
        symbol: str = "BTC-USDT",
        timeframe: str = "1H",
        days: int = 30
    ) -> pd.DataFrame:
        """
        获取扩展的历史K线数据（通过分页）

        Args:
            symbol: 交易对
            timeframe: 时间周期
            days: 需要多少天的数据

        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
        """
        try:
            from datetime import datetime, timedelta
            import time

            # 计算每个时间周期对应的小时数
            timeframe_hours = {
                '1m': 1/60, '3m': 3/60, '5m': 5/60, '15m': 15/60, '30m': 30/60,
                '1H': 1, '2H': 2, '4H': 4,
                '1D': 24,
                '1W': 168
            }

            hours_per_bar = timeframe_hours.get(timeframe, 1)
            total_bars_needed = int((days * 24) / hours_per_bar)

            print(f"\n📊 获取 {symbol} {timeframe} 的 {days} 天历史数据...")
            print(f"   预计需要 {total_bars_needed} 条K线")

            all_data = []
            bars_per_request = 300  # 每次请求300条

            # 计算需要多少次请求
            num_requests = (total_bars_needed + bars_per_request - 1) // bars_per_request

            bar_map = {
                '1m': '1m', '3m': '3m', '5m': '5m', '15m': '15m', '30m': '30m',
                '1H': '1H', '2H': '2H', '4H': '4H',
                '1D': '1D',
                '1W': '1W'
            }
            bar = bar_map.get(timeframe, '1H')

            # 第一次请求：获取最近300条
            print(f"   第1/{num_requests}次请求...")
            endpoint = f"/api/v5/market/candles?instId={symbol}&bar={bar}&limit=300"
            url = self.base_url + endpoint
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data['code'] != '0':
                print(f"❌ OKX API错误: {data['msg']}")
                return pd.DataFrame()

            candles = data['data']
            all_data.extend(candles)

            # 如果需要更多数据，使用history-candles端点分页获取
            if num_requests > 1 and len(candles) > 0:
                # 获取最早的时间戳作为after参数
                oldest_ts = candles[-1][0]  # 最早的K线时间戳

                for i in range(1, num_requests):
                    print(f"   第{i+1}/{num_requests}次请求...")

                    # 使用history-candles端点，每次最多100条
                    endpoint = f"/api/v5/market/history-candles?instId={symbol}&bar={bar}&after={oldest_ts}&limit=100"
                    url = self.base_url + endpoint

                    response = requests.get(url, headers=self.headers, timeout=10)
                    response.raise_for_status()
                    data = response.json()

                    if data['code'] != '0':
                        print(f"⚠️ 第{i+1}次请求失败: {data['msg']}")
                        break

                    new_candles = data['data']

                    if not new_candles:
                        print(f"   已获取所有可用数据")
                        break

                    all_data.extend(new_candles)
                    oldest_ts = new_candles[-1][0]

                    # 避免触发API限流
                    time.sleep(0.2)

                    # 如果已经获取足够数据，停止
                    if len(all_data) >= total_bars_needed:
                        break

            # 转换为DataFrame
            df = pd.DataFrame(all_data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'volCcy', 'volCcyQuote', 'confirm'
            ])

            # 数据类型转换
            df['timestamp'] = pd.to_datetime(df['timestamp'].astype(float) / 1000, unit='s')
            df['open'] = df['open'].astype(float)
            df['high'] = df['high'].astype(float)
            df['low'] = df['low'].astype(float)
            df['close'] = df['close'].astype(float)
            df['volume'] = df['volume'].astype(float)

            # 只保留需要的列
            df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]

            # 去重并按时间升序排列
            df = df.drop_duplicates(subset=['timestamp'])
            df = df.sort_values('timestamp').reset_index(drop=True)

            print(f"✅ 成功获取 {len(df)} 条K线数据")
            print(f"   时间范围: {df['timestamp'].iloc[0]} 至 {df['timestamp'].iloc[-1]}")
            print(f"   实际天数: {(df['timestamp'].iloc[-1] - df['timestamp'].iloc[0]).days} 天")

            return df

        except Exception as e:
            print(f"❌ 获取扩展历史数据失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()


# 示例用法
if __name__ == "__main__":
    print("=== OKX API 测试 ===\n")

    # 1. 公共数据测试（不需要 API Key）
    print("1️⃣ 测试公共数据接口...")
    fetcher = OKXFetcher()

    # 获取实时行情
    print("\n=== 获取BTC实时行情 ===")
    ticker = fetcher.get_ticker("BTC-USDT")
    if 'error' not in ticker:
        print(f"✅ BTC价格: ${ticker['last']:,.2f}")
        print(f"   24h最高: ${ticker['high_24h']:,.2f}")
        print(f"   24h最低: ${ticker['low_24h']:,.2f}")
        print(f"   24h成交量: {ticker['vol_24h']:,.2f} BTC")
    else:
        print(f"❌ {ticker['error']}")

    # 获取K线数据
    print("\n=== 获取BTC K线数据 ===")
    df = fetcher.get_candles("BTC-USDT", "1H", 10)
    if not df.empty:
        print(f"✅ 获取了 {len(df)} 条K线数据")
        print(df[['timestamp', 'close']].tail(3))
    else:
        print("❌ 获取K线数据失败")

    # 2. 私有数据测试（需要 API Key）
    print("\n2️⃣ 测试私有数据接口...")
    print("请在 .env 文件中配置你的 API Key 来测试以下功能：")
    print("  - 查询账户余额")
    print("  - 下单交易")
    print("  - 查询订单")
    print("  - 查询持仓")
    print("\n示例:")
    print("""
    # 创建 .env 文件并添加:
    OKX_API_KEY=your_api_key
    OKX_SECRET_KEY=your_secret_key
    OKX_PASSPHRASE=your_passphrase
    OKX_DEMO_TRADING=1  # 1=模拟盘, 0=实盘

    # 然后运行:
    from okx_fetcher import OKXFetcher

    fetcher = OKXFetcher()  # 会自动从.env读取配置

    # 查询余额
    balance = fetcher.get_account_balance()
    print(balance)

    # 下单（模拟盘）
    order = fetcher.place_order('BTC-USDT', 'buy', 'limit', 0.001, 40000)
    print(order)
    """)

    def get_historical_candles_extended(
        self,
        symbol: str = "BTC-USDT",
        timeframe: str = "1H",
        days: int = 30
    ) -> pd.DataFrame:
        """
        获取扩展的历史K线数据（通过分页）
        
        Args:
            symbol: 交易对
            timeframe: 时间周期
            days: 需要多少天的数据
            
        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
        """
        try:
            from datetime import datetime, timedelta
            import time
            
            # 计算每个时间周期对应的小时数
            timeframe_hours = {
                '1m': 1/60, '3m': 3/60, '5m': 5/60, '15m': 15/60, '30m': 30/60,
                '1H': 1, '2H': 2, '4H': 4,
                '1D': 24,
                '1W': 168
            }
            
            hours_per_bar = timeframe_hours.get(timeframe, 1)
            total_bars_needed = int((days * 24) / hours_per_bar)
            
            print(f"\n📊 获取 {symbol} {timeframe} 的 {days} 天历史数据...")
            print(f"   预计需要 {total_bars_needed} 条K线")
            
            all_data = []
            bars_per_request = 300  # 每次请求300条
            
            # 计算需要多少次请求
            num_requests = (total_bars_needed + bars_per_request - 1) // bars_per_request
            
            bar_map = {
                '1m': '1m', '3m': '3m', '5m': '5m', '15m': '15m', '30m': '30m',
                '1H': '1H', '2H': '2H', '4H': '4H',
                '1D': '1D', 
                '1W': '1W'
            }
            bar = bar_map.get(timeframe, '1H')
            
            # 第一次请求：获取最近300条
            print(f"   第1/{num_requests}次请求...")
            endpoint = f"/api/v5/market/candles?instId={symbol}&bar={bar}&limit=300"
            url = self.base_url + endpoint
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data['code'] != '0':
                print(f"❌ OKX API错误: {data['msg']}")
                return pd.DataFrame()
            
            candles = data['data']
            all_data.extend(candles)
            
            # 如果需要更多数据，使用history-candles端点分页获取
            if num_requests > 1 and len(candles) > 0:
                # 获取最早的时间戳作为after参数
                oldest_ts = candles[-1][0]  # 最早的K线时间戳
                
                for i in range(1, num_requests):
                    print(f"   第{i+1}/{num_requests}次请求...")
                    
                    # 使用history-candles端点，每次最多100条
                    endpoint = f"/api/v5/market/history-candles?instId={symbol}&bar={bar}&after={oldest_ts}&limit=100"
                    url = self.base_url + endpoint
                    
                    response = requests.get(url, headers=self.headers, timeout=10)
                    response.raise_for_status()
                    data = response.json()
                    
                    if data['code'] != '0':
                        print(f"⚠️ 第{i+1}次请求失败: {data['msg']}")
                        break
                    
                    new_candles = data['data']
                    
                    if not new_candles:
                        print(f"   已获取所有可用数据")
                        break
                    
                    all_data.extend(new_candles)
                    oldest_ts = new_candles[-1][0]
                    
                    # 避免触发API限流
                    time.sleep(0.2)
                    
                    # 如果已经获取足够数据，停止
                    if len(all_data) >= total_bars_needed:
                        break
            
            # 转换为DataFrame
            df = pd.DataFrame(all_data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'volCcy', 'volCcyQuote', 'confirm'
            ])
            
            # 数据类型转换
            df['timestamp'] = pd.to_datetime(df['timestamp'].astype(float) / 1000, unit='s')
            df['open'] = df['open'].astype(float)
            df['high'] = df['high'].astype(float)
            df['low'] = df['low'].astype(float)
            df['close'] = df['close'].astype(float)
            df['volume'] = df['volume'].astype(float)
            
            # 只保留需要的列
            df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
            
            # 去重并按时间升序排列
            df = df.drop_duplicates(subset=['timestamp'])
            df = df.sort_values('timestamp').reset_index(drop=True)
            
            print(f"✅ 成功获取 {len(df)} 条K线数据")
            print(f"   时间范围: {df['timestamp'].iloc[0]} 至 {df['timestamp'].iloc[-1]}")
            print(f"   实际天数: {(df['timestamp'].iloc[-1] - df['timestamp'].iloc[0]).days} 天")
            
            return df
            
        except Exception as e:
            print(f"❌ 获取扩展历史数据失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()
