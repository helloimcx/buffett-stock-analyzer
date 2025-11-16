"""
核心层
包含配置、评分算法等核心功能
"""

from .config import AppConfig, DataConfig, ScoringConfig, config
from .scoring import InvestmentScorer

__all__ = [
    'AppConfig',
    'DataConfig',
    'ScoringConfig',
    'config',
    'InvestmentScorer'
]