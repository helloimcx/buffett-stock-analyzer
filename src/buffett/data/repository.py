"""
数据仓储层
提供更高级的数据操作接口
"""

from typing import List
import pandas as pd

from ..models import StockInfo, ScreeningCriteria
from .providers import StockDataProvider


class StockRepository:
    """股票数据仓储"""

    def __init__(self, provider: StockDataProvider = None):
        self.provider = provider or StockDataProvider()

    def get_potential_stocks(self, criteria: ScreeningCriteria) -> List[StockInfo]:
        """获取有潜力的股票"""
        stocks_df = self.provider.get_all_stocks()
        if stocks_df.empty:
            return []

        filtered_df = self.provider.filter_potential_stocks(stocks_df, criteria)
        print(f"🎯 从 {len(filtered_df)} 只有潜力的股票中筛选...")

        qualified_stocks = []
        for _, stock_data in filtered_df.iterrows():
            try:
                symbol = stock_data['代码']
                stock_info = self.provider.extract_stock_info(symbol, stock_data.to_dict())

                if stock_info and stock_info.dividend_yield >= criteria.min_dividend_yield:
                    qualified_stocks.append(stock_info)

                # 显示进度
                if len(qualified_stocks) % 10 == 0:
                    print(f"   已找到 {len(qualified_stocks)} 只符合条件的股票...")

            except Exception as e:
                print(f"   ⚠️ 处理 {stock_data.get('代码', 'unknown')} 时出错: {e}")
                continue

        return qualified_stocks

    def get_stocks_by_symbols(self, symbols: List[str]) -> List[StockInfo]:
        """根据股票代码列表获取股票信息"""
        return self.provider.analyze_stocks(symbols)

    def get_all_stocks_dataframe(self) -> pd.DataFrame:
        """获取所有股票的数据框"""
        return self.provider.get_all_stocks()