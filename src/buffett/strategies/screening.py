"""
股息筛选策略
实现高股息股票的筛选逻辑
"""

from typing import List
from datetime import datetime

from ..models import StockInfo, ScreeningCriteria, ScreeningResult
from ..core.scoring import InvestmentScorer
from ..data.repository import StockRepository


class DividendScreeningStrategy:
    """股息筛选策略"""

    def __init__(self):
        self.repository = StockRepository()
        self.scorer = InvestmentScorer()
        self.errors: List[str] = []

    def screen_dividend_stocks(self, min_dividend_yield: float = 4.0) -> ScreeningResult:
        """筛选高股息股票"""
        print(f"🔍 筛选股息率≥{min_dividend_yield}%的股票...")

        # 创建筛选条件
        criteria = ScreeningCriteria(min_dividend_yield=min_dividend_yield)

        # 获取符合条件的股票
        qualified_stocks = self.repository.get_potential_stocks(criteria)

        # 评分和排序
        ranked_stocks = self.scorer.rank_stocks(qualified_stocks)

        # 获取总分析数量
        all_stocks_df = self.repository.get_all_stocks_dataframe()
        total_analyzed = len(all_stocks_df) if not all_stocks_df.empty else 0

        return ScreeningResult(
            timestamp=datetime.now(),
            criteria=criteria,
            total_stocks_analyzed=total_analyzed,
            passed_stocks=ranked_stocks,
            errors=self.errors
        )