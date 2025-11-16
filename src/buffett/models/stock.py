"""
股票相关数据模型
"""

from dataclasses import dataclass
from typing import List, Dict, Any
from datetime import datetime


@dataclass
class StockInfo:
    """股票信息数据类"""
    code: str
    name: str
    price: float
    dividend_yield: float
    pe_ratio: float
    pb_ratio: float
    change_pct: float
    volume: int
    market_cap: float
    eps: float
    book_value: float
    week_52_high: float
    week_52_low: float
    total_score: float = 0.0

    @classmethod
    def from_akshare_data(cls, symbol: str, stock_data: Dict[str, Any], detail_data: Dict[str, Any]) -> 'StockInfo':
        """从AKShare数据创建StockInfo实例"""

        def safe_float(value, default=0.0):
            """安全地将值转换为float"""
            try:
                if value is None or value == '' or value == '-':
                    return default
                return float(value)
            except (ValueError, TypeError):
                return default

        # 优先使用详细数据中的名称，否则使用基础数据
        name = detail_data.get('名称') or stock_data.get('名称', 'Unknown')

        # 优先使用详细数据中的价格，否则使用基础数据
        price = safe_float(detail_data.get('现价')) or safe_float(stock_data.get('最新价'))

        return cls(
            code=symbol,
            name=name,
            price=price,
            dividend_yield=safe_float(detail_data.get('股息率(TTM)')),
            pe_ratio=safe_float(detail_data.get('市盈率(动)')),
            pb_ratio=safe_float(detail_data.get('市净率')),
            change_pct=safe_float(stock_data.get('涨跌幅')),
            volume=int(safe_float(stock_data.get('成交量', 0))),
            market_cap=safe_float(detail_data.get('流通值')),
            eps=safe_float(detail_data.get('每股收益')),
            book_value=safe_float(detail_data.get('每股净资产')),
            week_52_high=safe_float(detail_data.get('52周最高')),
            week_52_low=safe_float(detail_data.get('52周最低'))
        )


@dataclass
class ScreeningCriteria:
    """筛选条件"""
    min_dividend_yield: float = 4.0
    min_price: float = 2.0
    max_price: float = 100.0
    min_volume: int = 1000000
    exclude_st: bool = True


@dataclass
class ScreeningResult:
    """筛选结果"""
    timestamp: datetime
    criteria: ScreeningCriteria
    total_stocks_analyzed: int
    passed_stocks: List[StockInfo]
    errors: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'criteria': {
                'min_dividend_yield': self.criteria.min_dividend_yield,
                'min_price': self.criteria.min_price,
                'max_price': self.criteria.max_price,
                'min_volume': self.criteria.min_volume,
                'exclude_st': self.criteria.exclude_st
            },
            'total_stocks_analyzed': self.total_stocks_analyzed,
            'passed_stocks_count': len(self.passed_stocks),
            'passed_stocks': [
                {
                    'code': stock.code,
                    'name': stock.name,
                    'price': stock.price,
                    'dividend_yield': stock.dividend_yield,
                    'pe_ratio': stock.pe_ratio,
                    'pb_ratio': stock.pb_ratio,
                    'total_score': stock.total_score,
                    'change_pct': stock.change_pct,
                    'week_52_high': stock.week_52_high,
                    'week_52_low': stock.week_52_low,
                    'eps': stock.eps,
                    'book_value': stock.book_value,
                    'market_cap': stock.market_cap
                }
                for stock in self.passed_stocks
            ],
            'errors': self.errors
        }