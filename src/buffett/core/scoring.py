"""
评分系统
实现股票投资价值评分算法
"""

from ..models import StockInfo
from .config import config


class InvestmentScorer:
    """投资评分器"""

    def __init__(self):
        self.config = config.scoring

    def calculate_dividend_score(self, stock: StockInfo) -> float:
        """计算股息率评分"""
        dividend_yield = stock.dividend_yield

        if dividend_yield >= self.config.high_dividend_threshold:
            return 50.0 * self.config.dividend_weight  # 提高基础分数
        elif dividend_yield >= self.config.medium_dividend_threshold:
            return 40.0 * self.config.dividend_weight  # 提高基础分数
        elif dividend_yield >= self.config.low_dividend_threshold:
            return 25.0 * self.config.dividend_weight  # 新增评分档位
        else:
            return 10.0 * self.config.dividend_weight  # 即使很低也给基础分

    def calculate_valuation_score(self, stock: StockInfo) -> float:
        """计算估值评分"""
        pe_ratio = stock.pe_ratio
        pb_ratio = stock.pb_ratio

        pe_score = 0.0
        pb_score = 0.0

        # P/E评分（调整为25分制）
        if 0 < pe_ratio < self.config.low_pe_threshold:
            pe_score = 25.0
        elif self.config.low_pe_threshold <= pe_ratio < self.config.medium_pe_threshold:
            pe_score = 15.0
        elif pe_ratio >= self.config.medium_pe_threshold:
            pe_score = 5.0  # 即使P/E很高也给基础分

        # P/B评分（调整为25分制）
        if 0 < pb_ratio < self.config.low_pb_threshold:
            pb_score = 25.0
        elif self.config.low_pb_threshold <= pb_ratio < self.config.medium_pb_threshold:
            pb_score = 15.0
        elif pb_ratio >= self.config.medium_pb_threshold:
            pb_score = 5.0  # 即使P/B很高也给基础分

        return (pe_score + pb_score) * self.config.valuation_weight

    def calculate_technical_score(self, stock: StockInfo) -> float:
        """计算技术位置评分"""
        high_52w = stock.week_52_high
        low_52w = stock.week_52_low
        current_price = stock.price

        if high_52w > 0 and low_52w > 0:
            position = (current_price - low_52w) / (high_52w - low_52w)

            if position < self.config.oversold_threshold:
                return 50.0 * self.config.technical_weight  # 接近52周低点
            elif position < self.config.neutral_threshold:
                return 30.0 * self.config.technical_weight  # 中位位置
            else:
                return 15.0 * self.config.technical_weight  # 接近52周高点
        else:
            return 20.0 * self.config.technical_weight  # 没有数据也给基础分

    def calculate_fundamental_score(self, stock: StockInfo) -> float:
        """计算基本面评分"""
        score = 0.0

        # EPS评分
        if stock.eps > 0:
            score += 5.0

        # 安全边际评分（账面价值）
        if stock.book_value > stock.price * 0.5:
            score += 5.0

        return score * self.config.fundamental_weight

    def calculate_total_score(self, stock: StockInfo) -> float:
        """计算综合评分"""
        dividend_score = self.calculate_dividend_score(stock)
        valuation_score = self.calculate_valuation_score(stock)
        technical_score = self.calculate_technical_score(stock)
        fundamental_score = self.calculate_fundamental_score(stock)

        total_score = dividend_score + valuation_score + technical_score + fundamental_score
        return min(total_score, 100.0)  # 最高100分

    def rank_stocks(self, stocks: list[StockInfo]) -> list[StockInfo]:
        """对股票进行评分和排序"""
        for stock in stocks:
            stock.total_score = self.calculate_total_score(stock)

        # 按评分降序排序
        return sorted(stocks, key=lambda x: x.total_score, reverse=True)