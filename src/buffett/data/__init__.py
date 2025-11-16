"""
Data access layer for the Buffett dividend screening system.

This package provides data access components including repositories,
data fetchers, and caching mechanisms for external data sources.
"""

from .fetcher import DataFetcher
from .repositories import StockRepository
from .cache import CacheManager

__all__ = [
    "DataFetcher",
    "StockRepository",
    "CacheManager",
]