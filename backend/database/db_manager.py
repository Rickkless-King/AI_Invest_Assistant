"""
SQLite数据库管理器
用途: 存储历史K线数据、交易记录、分析结果
"""

import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
import pandas as pd
from pathlib import Path
import threading


class DatabaseManager:
    """
    数据库管理类
    """

    def __init__(self, db_path: str = "crypto_trading.db"):
        """
        初始化数据库连接

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self._lock = threading.Lock()  # 添加线程锁
        self._connect()
        self._create_tables()

    def _connect(self):
        """建立数据库连接"""
        try:
            # check_same_thread=False 允许多线程使用同一连接（配合锁使用）
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.cursor = self.conn.cursor()
            print(f"✅ 数据库连接成功: {self.db_path}")
        except Exception as e:
            print(f"❌ 数据库连接失败: {str(e)}")

    def _create_tables(self):
        """创建所有必要的表"""
        with self._lock:  # 使用线程锁保护写操作
            # 1. K线数据表
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS klines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                open REAL NOT NULL,
                high REAL NOT NULL,
                low REAL NOT NULL,
                close REAL NOT NULL,
                volume REAL NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(symbol, timeframe, timestamp)
            )
            """)

            # 2. 交易记录表
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,              -- BUY/SELL
                price REAL NOT NULL,
                quantity REAL NOT NULL,
                amount REAL NOT NULL,             -- price * quantity
                fee REAL DEFAULT 0,
                strategy TEXT,                    -- 策略名称
                timestamp DATETIME NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # 3. 分析结果表
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                analysis_type TEXT NOT NULL,      -- technical/fundamental/sentiment
                result TEXT NOT NULL,             -- JSON格式的分析结果
                recommendation TEXT,              -- BUY/SELL/HOLD
                confidence REAL,                  -- 0-1之间
                timestamp DATETIME NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # 4. 策略回测表
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS backtest_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_name TEXT NOT NULL,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                start_date DATETIME NOT NULL,
                end_date DATETIME NOT NULL,
                initial_capital REAL NOT NULL,
                final_capital REAL NOT NULL,
                total_return REAL NOT NULL,       -- 总收益率
                sharpe_ratio REAL,
                max_drawdown REAL,
                win_rate REAL,
                total_trades INTEGER,
                config TEXT,                      -- JSON格式的策略配置
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # 5. 系统日志表
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level TEXT NOT NULL,              -- INFO/WARNING/ERROR
                module TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """)

            self.conn.commit()
            print("✅ 数据表创建成功")

    def save_klines(self, df: pd.DataFrame, symbol: str, timeframe: str):
        """
        保存K线数据

        Args:
            df: K线DataFrame
            symbol: 交易对
            timeframe: 时间周期
        """
        with self._lock:  # 使用线程锁保护写操作
            try:
                for _, row in df.iterrows():
                    # 将 pandas Timestamp 转换为字符串
                    timestamp_str = row['timestamp']
                    if isinstance(timestamp_str, pd.Timestamp):
                        timestamp_str = timestamp_str.strftime('%Y-%m-%d %H:%M:%S')

                    self.cursor.execute("""
                        INSERT OR IGNORE INTO klines
                        (symbol, timeframe, timestamp, open, high, low, close, volume)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        symbol,
                        timeframe,
                        timestamp_str,
                        float(row['open']),
                        float(row['high']),
                        float(row['low']),
                        float(row['close']),
                        float(row['volume'])
                    ))

                self.conn.commit()
                print(f"✅ 保存了 {len(df)} 条K线数据: {symbol} {timeframe}")

            except Exception as e:
                print(f"❌ 保存K线数据失败: {str(e)}")
                self.conn.rollback()

    def get_klines(
        self,
        symbol: str,
        timeframe: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 1000
    ) -> pd.DataFrame:
        """
        查询K线数据

        Args:
            symbol: 交易对
            timeframe: 时间周期
            start_date: 开始时间（可选）
            end_date: 结束时间（可选）
            limit: 最大返回数量

        Returns:
            K线DataFrame
        """
        try:
            query = """
                SELECT timestamp, open, high, low, close, volume
                FROM klines
                WHERE symbol = ? AND timeframe = ?
            """
            params = [symbol, timeframe]

            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date)

            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date)

            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            df = pd.read_sql_query(query, self.conn, params=params)
            df['timestamp'] = pd.to_datetime(df['timestamp'])

            return df.sort_values('timestamp').reset_index(drop=True)

        except Exception as e:
            print(f"❌ 查询K线数据失败: {str(e)}")
            return pd.DataFrame()

    def save_trade(self, trade_data: Dict):
        """
        保存交易记录

        Args:
            trade_data: {
                'symbol': 'BTC-USDT',
                'side': 'BUY',
                'price': 42000.0,
                'quantity': 0.01,
                'fee': 0.42,
                'strategy': 'LLM_Trend',
                'timestamp': '2025-12-23T10:00:00'
            }
        """
        with self._lock:  # 使用线程锁保护写操作
            try:
                self.cursor.execute("""
                    INSERT INTO trades
                    (symbol, side, price, quantity, amount, fee, strategy, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    trade_data['symbol'],
                    trade_data['side'],
                    trade_data['price'],
                    trade_data['quantity'],
                    trade_data['price'] * trade_data['quantity'],
                    trade_data.get('fee', 0),
                    trade_data.get('strategy', 'manual'),
                    trade_data['timestamp']
                ))

                self.conn.commit()
                print(f"✅ 交易记录已保存: {trade_data['side']} {trade_data['quantity']} {trade_data['symbol']}")

            except Exception as e:
                print(f"❌ 保存交易记录失败: {str(e)}")
                self.conn.rollback()

    def get_trades(
        self,
        symbol: Optional[str] = None,
        start_date: Optional[str] = None,
        limit: int = 100
    ) -> pd.DataFrame:
        """
        查询交易记录

        Args:
            symbol: 交易对（可选）
            start_date: 开始时间（可选）
            limit: 最大返回数量

        Returns:
            交易记录DataFrame
        """
        try:
            query = "SELECT * FROM trades WHERE 1=1"
            params = []

            if symbol:
                query += " AND symbol = ?"
                params.append(symbol)

            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date)

            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            df = pd.read_sql_query(query, self.conn, params=params)
            return df

        except Exception as e:
            print(f"❌ 查询交易记录失败: {str(e)}")
            return pd.DataFrame()

    def save_analysis(self, analysis_data: Dict):
        """
        保存分析结果

        Args:
            analysis_data: {
                'symbol': 'BTC-USDT',
                'timeframe': '1H',
                'analysis_type': 'technical',
                'result': '{"rsi": 45, "trend": "bullish"}',
                'recommendation': 'BUY',
                'confidence': 0.75,
                'timestamp': '2025-12-23T10:00:00'
            }
        """
        with self._lock:  # 使用线程锁保护写操作
            try:
                self.cursor.execute("""
                    INSERT INTO analysis
                    (symbol, timeframe, analysis_type, result, recommendation, confidence, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    analysis_data['symbol'],
                    analysis_data['timeframe'],
                    analysis_data['analysis_type'],
                    analysis_data['result'],
                    analysis_data.get('recommendation'),
                    analysis_data.get('confidence'),
                    analysis_data['timestamp']
                ))

                self.conn.commit()
                print(f"✅ 分析结果已保存: {analysis_data['symbol']} {analysis_data['analysis_type']}")

            except Exception as e:
                print(f"❌ 保存分析结果失败: {str(e)}")
                self.conn.rollback()

    def log(self, level: str, module: str, message: str):
        """
        记录系统日志

        Args:
            level: INFO/WARNING/ERROR
            module: 模块名称
            message: 日志内容
        """
        with self._lock:  # 使用线程锁保护写操作
            try:
                self.cursor.execute("""
                    INSERT INTO system_logs (level, module, message)
                    VALUES (?, ?, ?)
                """, (level, module, message))

                self.conn.commit()

            except Exception as e:
                print(f"❌ 记录日志失败: {str(e)}")

    def get_statistics(self) -> Dict:
        """
        获取数据库统计信息

        Returns:
            {
                'total_klines': 1000,
                'total_trades': 50,
                'total_analysis': 200
            }
        """
        try:
            stats = {}

            self.cursor.execute("SELECT COUNT(*) FROM klines")
            stats['total_klines'] = self.cursor.fetchone()[0]

            self.cursor.execute("SELECT COUNT(*) FROM trades")
            stats['total_trades'] = self.cursor.fetchone()[0]

            self.cursor.execute("SELECT COUNT(*) FROM analysis")
            stats['total_analysis'] = self.cursor.fetchone()[0]

            return stats

        except Exception as e:
            print(f"❌ 获取统计信息失败: {str(e)}")
            return {}

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            print("✅ 数据库连接已关闭")


# 示例用法
if __name__ == "__main__":
    # 初始化数据库
    db = DatabaseManager("test_crypto.db")

    # 查看统计
    print("\n=== 数据库统计 ===")
    stats = db.get_statistics()
    print(stats)

    # 测试保存交易
    trade = {
        'symbol': 'BTC-USDT',
        'side': 'BUY',
        'price': 42000.0,
        'quantity': 0.01,
        'fee': 0.42,
        'strategy': 'test',
        'timestamp': datetime.now().isoformat()
    }
    db.save_trade(trade)

    # 查询交易
    print("\n=== 交易记录 ===")
    trades_df = db.get_trades(limit=10)
    print(trades_df)

    # 关闭连接
    db.close()
