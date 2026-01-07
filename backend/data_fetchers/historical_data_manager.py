"""
历史数据管理器
负责自动下载、存储和管理OKX历史K线数据
"""

import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import time
import os
from typing import Optional, Tuple
from .okx_fetcher import OKXFetcher


class HistoricalDataManager:
    def __init__(self, db_path: str = "data/historical_klines.db"):
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
        
        self.db_path = db_path
        self.okx_fetcher = OKXFetcher()
        self._init_database()
    
    def _init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
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
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_symbol_timeframe_timestamp 
            ON klines(symbol, timeframe, timestamp)
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS data_coverage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                earliest_timestamp DATETIME,
                latest_timestamp DATETIME,
                total_bars INTEGER DEFAULT 0,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(symbol, timeframe)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS backtest_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                strategy_name TEXT NOT NULL,
                params TEXT NOT NULL,
                total_return_pct REAL,
                sharpe_ratio REAL,
                max_drawdown_pct REAL,
                win_rate REAL,
                total_trades INTEGER,
                winning_trades INTEGER,
                losing_trades INTEGER,
                avg_return_pct REAL,
                data_points INTEGER,
                backtest_start_time DATETIME,
                backtest_end_time DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                user_specified BOOLEAN DEFAULT 0,
                notes TEXT
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_backtest_symbol_strategy
            ON backtest_results(symbol, strategy_name, created_at DESC)
        """)

        conn.commit()
        conn.close()

        print(f"历史数据数据库初始化: {self.db_path}")
    
    def get_data_coverage(self, symbol: str, timeframe: str) -> Optional[dict]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT earliest_timestamp, latest_timestamp, total_bars, last_updated
            FROM data_coverage
            WHERE symbol = ? AND timeframe = ?
        """, (symbol, timeframe))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'earliest_timestamp': pd.to_datetime(result[0]),
                'latest_timestamp': pd.to_datetime(result[1]),
                'total_bars': result[2],
                'last_updated': pd.to_datetime(result[3])
            }
        return None
    
    def save_klines(self, df: pd.DataFrame, symbol: str, timeframe: str) -> int:
        if df.empty:
            return 0
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        inserted = 0
        for _, row in df.iterrows():
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO klines 
                    (symbol, timeframe, timestamp, open, high, low, close, volume)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    symbol,
                    timeframe,
                    row['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                    row['open'],
                    row['high'],
                    row['low'],
                    row['close'],
                    row['volume']
                ))
                if cursor.rowcount > 0:
                    inserted += 1
            except Exception as e:
                continue
        
        cursor.execute("""
            INSERT OR REPLACE INTO data_coverage 
            (symbol, timeframe, earliest_timestamp, latest_timestamp, total_bars, last_updated)
            SELECT ?, ?, MIN(timestamp), MAX(timestamp), COUNT(*), CURRENT_TIMESTAMP
            FROM klines WHERE symbol = ? AND timeframe = ?
        """, (symbol, timeframe, symbol, timeframe))
        
        conn.commit()
        conn.close()
        
        return inserted
    
    def load_klines(self, symbol: str, timeframe: str, start_time: Optional[datetime] = None,
                    end_time: Optional[datetime] = None, limit: Optional[int] = None) -> pd.DataFrame:
        conn = sqlite3.connect(self.db_path)
        
        query = "SELECT timestamp, open, high, low, close, volume FROM klines WHERE symbol = ? AND timeframe = ?"
        params = [symbol, timeframe]
        
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time.strftime('%Y-%m-%d %H:%M:%S'))
        
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time.strftime('%Y-%m-%d %H:%M:%S'))
        
        query += " ORDER BY timestamp ASC"
        
        if limit:
            query += f" LIMIT {limit}"
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        return df
    
    def download_historical_data(self, symbol: str, timeframe: str, days: int = 90, force_refresh: bool = False) -> dict:
        print(f"\n下载历史数据: {symbol} {timeframe} ({days}天)")

        coverage = self.get_data_coverage(symbol, timeframe)

        if coverage and not force_refresh:
            existing_days = (coverage['latest_timestamp'] - coverage['earliest_timestamp']).days

            if existing_days >= days:
                print(f"已有{existing_days}天数据，跳过下载")
                return {'status': 'skip', 'existing_bars': coverage['total_bars']}

            # 如果已有部分数据，只下载缺失的天数
            missing_days = days - existing_days
            if missing_days > 0:
                print(f"已有{existing_days}天数据，只需补充{missing_days}天")
                # 计算需要下载的起始时间（向前推missing_days天）
                start_time = coverage['earliest_timestamp'] - pd.Timedelta(days=missing_days)
                end_time = coverage['earliest_timestamp']

                # 只下载缺失的时间段
                df = self.okx_fetcher.get_historical_candles_extended(
                    symbol=symbol,
                    timeframe=timeframe,
                    days=missing_days
                )

                if not df.empty:
                    # 只保留早于已有数据的部分
                    df = df[df['timestamp'] < coverage['earliest_timestamp']]
                    inserted = self.save_klines(df, symbol, timeframe)
                    print(f"补充完成: 获取{len(df)}条, 新增{inserted}条")
                    return {'status': 'success', 'total_bars': len(df), 'inserted_bars': inserted}
                else:
                    print("未能获取补充数据")
                    return {'status': 'partial', 'existing_bars': coverage['total_bars']}

        # 没有数据或需要强制刷新，下载完整数据
        df = self.okx_fetcher.get_historical_candles_extended(symbol=symbol, timeframe=timeframe, days=days)

        if df.empty:
            return {'status': 'error', 'message': '未获取到数据'}

        inserted = self.save_klines(df, symbol, timeframe)

        print(f"下载完成: 获取{len(df)}条, 新增{inserted}条")

        return {'status': 'success', 'total_bars': len(df), 'inserted_bars': inserted,
                'start_time': df['timestamp'].iloc[0], 'end_time': df['timestamp'].iloc[-1]}
    
    def check_and_fill_gaps(self, symbol: str, timeframe: str, target_days: int = 90) -> dict:
        print(f"\n检查数据完整性: {symbol} {timeframe}")
        
        coverage = self.get_data_coverage(symbol, timeframe)
        
        if not coverage:
            print("没有历史数据，开始首次下载...")
            return self.download_historical_data(symbol, timeframe, target_days)
        
        now = datetime.now()
        hours_since_update = (now - coverage['latest_timestamp']).total_seconds() / 3600
        
        print(f"最新数据: {coverage['latest_timestamp']} (距今{hours_since_update:.1f}小时)")
        
        if hours_since_update > 2:
            print("更新最新数据...")
            df_latest = self.okx_fetcher.get_candles(symbol, timeframe, limit=300)
            
            if not df_latest.empty:
                inserted = self.save_klines(df_latest, symbol, timeframe)
                print(f"更新了{inserted}条新数据")
        
        existing_days = (coverage['latest_timestamp'] - coverage['earliest_timestamp']).days
        
        if existing_days < target_days:
            print(f"当前{existing_days}天，目标{target_days}天，补充历史数据...")
            return self.download_historical_data(symbol, timeframe, target_days)
        
        print("数据完整")
        return {'status': 'complete', 'existing_bars': coverage['total_bars']}
    
    def get_latest_data_for_backtest(self, symbol: str, timeframe: str, days: int = 90, auto_update: bool = True) -> pd.DataFrame:
        if auto_update:
            self.check_and_fill_gaps(symbol, timeframe, days)

        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)

        df = self.load_klines(symbol=symbol, timeframe=timeframe, start_time=start_time, end_time=end_time)

        if not df.empty:
            actual_days = (df['timestamp'].iloc[-1] - df['timestamp'].iloc[0]).days
            print(f"\n加载回测数据: {len(df)}条 ({actual_days}天)")
            print(f"时间: {df['timestamp'].iloc[0]} ~ {df['timestamp'].iloc[-1]}")

        return df

    def save_backtest_result(self, symbol: str, timeframe: str, strategy_name: str,
                            params: dict, metrics: dict, df: pd.DataFrame,
                            user_specified: bool = False, notes: str = "") -> int:
        """保存回测结果到数据库"""
        import json

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO backtest_results (
                symbol, timeframe, strategy_name, params,
                total_return_pct, sharpe_ratio, max_drawdown_pct, win_rate,
                total_trades, winning_trades, losing_trades, avg_return_pct,
                data_points, backtest_start_time, backtest_end_time,
                user_specified, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            symbol, timeframe, strategy_name, json.dumps(params, ensure_ascii=False),
            metrics.get('total_return_pct', 0),
            metrics.get('sharpe_ratio', 0),
            metrics.get('max_drawdown_pct', 0),
            metrics.get('win_rate', 0),
            metrics.get('total_trades', 0),
            metrics.get('winning_trades', 0),
            metrics.get('losing_trades', 0),
            metrics.get('avg_return_pct', 0),
            len(df),
            df['timestamp'].iloc[0].strftime('%Y-%m-%d %H:%M:%S') if not df.empty else None,
            df['timestamp'].iloc[-1].strftime('%Y-%m-%d %H:%M:%S') if not df.empty else None,
            1 if user_specified else 0,
            notes
        ))

        result_id = cursor.lastrowid
        conn.commit()
        conn.close()

        print(f"回测结果已保存 (ID: {result_id})")
        return result_id

    def get_backtest_history(self, symbol: str = None, strategy_name: str = None,
                            limit: int = 20) -> pd.DataFrame:
        """获取历史回测结果"""
        import json

        conn = sqlite3.connect(self.db_path)

        query = "SELECT * FROM backtest_results WHERE 1=1"
        params = []

        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)

        if strategy_name:
            query += " AND strategy_name = ?"
            params.append(strategy_name)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        df = pd.read_sql_query(query, conn, params=params)
        conn.close()

        if not df.empty:
            df['created_at'] = pd.to_datetime(df['created_at'])
            df['params'] = df['params'].apply(lambda x: json.loads(x) if x else {})

        return df

    def get_best_strategy(self, symbol: str, timeframe: str, metric: str = 'sharpe_ratio') -> Optional[dict]:
        """获取指定交易对的最佳策略"""
        import json

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(f"""
            SELECT * FROM backtest_results
            WHERE symbol = ? AND timeframe = ?
            ORDER BY {metric} DESC
            LIMIT 1
        """, (symbol, timeframe))

        result = cursor.fetchone()
        conn.close()

        if result:
            columns = ['id', 'symbol', 'timeframe', 'strategy_name', 'params',
                      'total_return_pct', 'sharpe_ratio', 'max_drawdown_pct', 'win_rate',
                      'total_trades', 'winning_trades', 'losing_trades', 'avg_return_pct',
                      'data_points', 'backtest_start_time', 'backtest_end_time',
                      'created_at', 'user_specified', 'notes']
            result_dict = dict(zip(columns, result))
            result_dict['params'] = json.loads(result_dict['params'])
            return result_dict

        return None
