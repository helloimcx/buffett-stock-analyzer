"""
Repository interface definitions.

This module defines abstract base classes for data repositories following the
Repository pattern to encapsulate data access logic.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import pandas as pd
from datetime import datetime, date

from ..models.stock import Stock, StockInfo, DividendData, PriceData


class IStockRepository(ABC):
    """Repository interface for stock basic information."""

    @abstractmethod
    async def get_all_stocks(self) -> List[Stock]:
        """Get all stocks from the repository."""
        pass

    @abstractmethod
    async def get_stock_by_symbol(self, symbol: str) -> Optional[Stock]:
        """Get a specific stock by symbol."""
        pass

    @abstractmethod
    async def get_stock_info(self, symbol: str) -> Optional[StockInfo]:
        """Get detailed stock information by symbol."""
        pass

    @abstractmethod
    async def get_stocks_by_market(self, market: str) -> List[Stock]:
        """Get all stocks from a specific market."""
        pass

    @abstractmethod
    async def get_stocks_by_industry(self, industry: str) -> List[Stock]:
        """Get all stocks from a specific industry."""
        pass

    @abstractmethod
    async def save_stock(self, stock: Stock) -> None:
        """Save a stock to the repository."""
        pass

    @abstractmethod
    async def save_stocks(self, stocks: List[Stock]) -> None:
        """Save multiple stocks to the repository."""
        pass

    async def load_from_dataframe(self, df: pd.DataFrame) -> None:
        """Load stocks from a pandas DataFrame."""
        pass


class IStockInfoRepository(ABC):
    """Repository interface for detailed stock information."""

    @abstractmethod
    async def get_stock_info(self, symbol: str) -> Optional[StockInfo]:
        """Get detailed stock information by symbol."""
        pass

    @abstractmethod
    async def save_stock_info(self, stock_info: StockInfo) -> None:
        """Save detailed stock information."""
        pass

    @abstractmethod
    async def get_stocks_by_industry(self, industry: str) -> List[StockInfo]:
        """Get all stocks from a specific industry."""
        pass

    @abstractmethod
    async def get_top_stocks_by_market_cap(self, limit: int = 10) -> List[StockInfo]:
        """Get top stocks by market capitalization."""
        pass


class IDividendRepository(ABC):
    """Repository interface for dividend data."""

    @abstractmethod
    async def get_dividend_history(
        self,
        symbol: str,
        start_year: int = None,
        end_year: int = None
    ) -> List[DividendData]:
        """Get dividend history for a stock."""
        pass

    @abstractmethod
    async def save_dividend_data(self, dividend_data: DividendData) -> None:
        """Save dividend data."""
        pass

    @abstractmethod
    async def get_stocks_with_consistent_dividends(
        self,
        min_years: int = 3,
        min_yield: float = 0.0
    ) -> List[str]:
        """Get stocks with consistent dividend payments."""
        pass

    @abstractmethod
    async def get_latest_dividend_yield(self, symbol: str) -> Optional[float]:
        """Get the latest dividend yield for a stock."""
        pass


class IPriceRepository(ABC):
    """Repository interface for price data."""

    @abstractmethod
    async def get_price_data(
        self,
        symbol: str,
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """Get price data for a stock within date range."""
        pass

    @abstractmethod
    async def get_historical_prices(
        self,
        symbol: str,
        years: int = 5
    ) -> pd.DataFrame:
        """Get historical price data for a stock for specified number of years."""
        pass

    @abstractmethod
    async def get_latest_price(self, symbol: str) -> Optional[float]:
        """Get the latest price for a stock."""
        pass

    @abstractmethod
    async def save_price_data(self, symbol: str, price_data: pd.DataFrame) -> None:
        """Save price data for a stock."""
        pass

    @abstractmethod
    async def calculate_moving_averages(
        self,
        symbol: str,
        periods: List[int]
    ) -> Dict[int, float]:
        """Calculate moving averages for a stock."""
        pass


class ICacheRepository(ABC):
    """Repository interface for caching."""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get cached value by key."""
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl_seconds: int = None) -> None:
        """Set a cached value with optional TTL."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete a cached value."""
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all cached values."""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if a key exists in cache."""
        pass

    @abstractmethod
    async def get_ttl(self, key: str) -> Optional[int]:
        """Get remaining TTL for a key."""
        pass