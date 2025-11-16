"""
数据提供者
封装AKShare数据访问逻辑
"""

import time
import pandas as pd
import akshare as ak
from typing import List, Dict, Any, Optional

from ..models import StockInfo, ScreeningCriteria
from ..core.config import config


class StockDataProvider:
    """股票数据提供者"""

    def __init__(self):
        self.config = config.data

    def _safe_float(self, value: Any, default: float = 0.0) -> float:
        """安全地将值转换为float"""
        try:
            if value is None or value == '' or value == '-':
                return default
            return float(value)
        except (ValueError, TypeError):
            return default

    def _normalize_symbol(self, symbol: str) -> str:
        """标准化股票代码格式"""
        symbol = symbol.upper().strip()

        # 跳过北交所股票
        if symbol.startswith('BJ'):
            return None  # 北交所股票在雪球网上没有数据

        if symbol.startswith('6'):
            return f"SH{symbol}"
        elif symbol.startswith('0') or symbol.startswith('3'):
            return f"SZ{symbol}"
        elif symbol.startswith('SH') or symbol.startswith('SZ'):
            return symbol
        else:
            return f"SH{symbol}"

    def get_all_stocks(self) -> pd.DataFrame:
        """获取所有A股实时数据"""
        try:
            print("📊 正在获取A股市场数据...")
            df = ak.stock_zh_a_spot()
            print(f"✅ 成功获取 {len(df)} 只股票数据")
            return df
        except Exception as e:
            print(f"❌ 获取股票数据失败: {e}")
            return pd.DataFrame()

    def get_stock_detail(self, symbol: str) -> pd.DataFrame:
        """获取单只股票详细信息"""
        ak_symbol = self._normalize_symbol(symbol)

        # 跳过北交所股票
        if ak_symbol is None:
            return pd.DataFrame()

        try:
            time.sleep(self.config.request_delay)  # 请求延迟
            return ak.stock_individual_spot_xq(symbol=ak_symbol)
        except Exception as e:
            print(f"⚠️  获取 {symbol} 详细信息失败: {e}")
            return pd.DataFrame()

    def extract_stock_info(self, symbol: str, stock_data: Dict[str, Any]) -> Optional[StockInfo]:
        """从原始数据提取股票信息"""
        try:
            # 跳过北交所股票
            if symbol.upper().startswith('BJ'):
                return None

            detail_df = self.get_stock_detail(symbol)
            if detail_df.empty:
                return None  # 静默跳过，不显示错误信息

            detail_data = dict(zip(detail_df['item'], detail_df['value']))

            # 使用基础数据作为名称备选
            stock_name = detail_data.get('名称') or stock_data.get('名称', 'Unknown')
            if not stock_name or stock_name == 'Unknown':
                print(f"⚠️  {symbol} 股票名称无效，跳过")
                return None

            # 价格验证 - 使用基础数据作为备选
            price = self._safe_float(detail_data.get('现价')) or self._safe_float(stock_data.get('最新价'))
            if price <= 0:
                print(f"⚠️  {stock_name} ({symbol}) 价格数据异常，跳过")
                return None

            stock_info = StockInfo.from_akshare_data(symbol, stock_data, detail_data)
            return stock_info

        except Exception as e:
            print(f"⚠️  提取 {symbol} 信息失败: {e}")
            return None

    def filter_potential_stocks(self, df: pd.DataFrame, criteria: ScreeningCriteria) -> pd.DataFrame:
        """筛选有潜力的股票"""
        filtered = df.copy()

        if criteria.exclude_st:
            filtered = filtered[~filtered['名称'].str.contains('ST', na=False)]

        filtered = filtered[
            (filtered['最新价'] >= criteria.min_price) &
            (filtered['最新价'] <= criteria.max_price) &
            (filtered['成交量'] >= criteria.min_volume)
        ]

        return filtered

    def analyze_stocks(self, symbols: List[str]) -> List[StockInfo]:
        """分析指定股票列表"""
        results = []
        print(f"🎯 分析 {len(symbols)} 只指定股票...")

        for symbol in symbols:
            # 直接分析单个股票，不需要预先获取所有数据
            stock_info = self.extract_stock_info(symbol, {'名称': 'Unknown', '最新价': 0})
            if stock_info:
                results.append(stock_info)
                print(f"   ✅ {stock_info.name} ({symbol}) - 数据获取成功")
            else:
                print(f"   ❌ {symbol} - 数据获取失败")

        return results