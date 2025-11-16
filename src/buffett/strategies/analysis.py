"""
目标股票分析策略
实现对指定股票的分析
"""

from typing import List
from datetime import datetime

from ..models import ScreeningCriteria, ScreeningResult
from ..core.scoring import InvestmentScorer
from ..data.repository import StockRepository


class TargetStockAnalysisStrategy:
    """目标股票分析策略"""

    def __init__(self):
        self.repository = StockRepository()
        self.scorer = InvestmentScorer()
        self.errors: List[str] = []

    def analyze_target_stocks(self, symbols: List[str]) -> ScreeningResult:
        """分析指定股票列表"""
        print(f"🎯 分析 {len(symbols)} 只指定股票...")

        # 分析股票
        stocks = self.repository.get_stocks_by_symbols(symbols)

        # 评分和排序
        ranked_stocks = self.scorer.rank_stocks(stocks)

        # 创建虚拟的筛选条件
        criteria = ScreeningCriteria(min_dividend_yield=0.0)  # 不限制股息率

        return ScreeningResult(
            timestamp=datetime.now(),
            criteria=criteria,
            total_stocks_analyzed=len(symbols),
            passed_stocks=ranked_stocks,
            errors=self.errors
        )