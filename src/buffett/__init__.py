"""
优化后的巴菲特股息筛选系统
采用分层架构，提高代码的可维护性和可扩展性
"""

__version__ = "2.1.0"
__author__ = "Buffett Strategy Team"

# 导入主要组件
from .models import StockInfo, ScreeningCriteria, ScreeningResult
from .core import InvestmentScorer, config
from .data import StockDataProvider, StockRepository
from .strategies import DividendScreeningStrategy, TargetStockAnalysisStrategy
from .utils import StockReporter, load_symbols_from_file

__all__ = [
    # 数据模型
    'StockInfo',
    'ScreeningCriteria',
    'ScreeningResult',

    # 核心功能
    'InvestmentScorer',
    'config',

    # 数据层
    'StockDataProvider',
    'StockRepository',

    # 策略层
    'DividendScreeningStrategy',
    'TargetStockAnalysisStrategy',

    # 工具层
    'StockReporter',
    'load_symbols_from_file'
]