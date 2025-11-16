"""
Provider interface definitions.

This module defines abstract base classes for data providers and external
service integrations, supporting the Strategy pattern for different providers.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import pandas as pd
from datetime import date

from ..models.stock import StockInfo, DividendData


class IDataProvider(ABC):
    """Interface for external data providers (AKShare, Tushare, etc.)."""

    @abstractmethod
    async def get_stock_list(self) -> pd.DataFrame:
        """Get list of all available stocks."""
        pass

    @abstractmethod
    async def get_stock_basic_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get basic information for a stock."""
        pass

    @abstractmethod
    async def get_dividend_data(self, symbol: str) -> pd.DataFrame:
        """Get dividend data for a stock."""
        pass

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
    async def get_financial_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get financial data for a stock."""
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Get the name of the data provider."""
        pass

    @abstractmethod
    async def test_connection(self) -> bool:
        """Test if the provider is accessible."""
        pass


class ICacheProvider(ABC):
    """Interface for cache providers (Redis, Memory, File, etc.)."""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        pass

    @abstractmethod
    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: int = None
    ) -> bool:
        """Set value in cache with optional TTL."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        pass

    @abstractmethod
    async def clear(self) -> bool:
        """Clear all cache entries."""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        pass

    @abstractmethod
    async def get_ttl(self, key: str) -> Optional[int]:
        """Get remaining TTL for a key."""
        pass

    @abstractmethod
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment a numeric value in cache."""
        pass

    @abstractmethod
    async def get_keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching a pattern."""
        pass


class IConfigProvider(ABC):
    """Interface for configuration providers."""

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        pass

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        pass

    @abstractmethod
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration values."""
        pass

    @abstractmethod
    def reload(self) -> None:
        """Reload configuration from source."""
        pass

    @abstractmethod
    def watch(self, key: str, callback: callable) -> None:
        """Watch for changes to a configuration key."""
        pass


class ILoggerProvider(ABC):
    """Interface for logging providers."""

    @abstractmethod
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        pass

    @abstractmethod
    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        pass

    @abstractmethod
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        pass

    @abstractmethod
    def error(self, message: str, **kwargs) -> None:
        """Log error message."""
        pass

    @abstractmethod
    def critical(self, message: str, **kwargs) -> None:
        """Log critical message."""
        pass

    @abstractmethod
    def set_level(self, level: str) -> None:
        """Set logging level."""
        pass

    @abstractmethod
    def add_handler(self, handler) -> None:
        """Add a log handler."""
        pass


class INotificationProvider(ABC):
    """Interface for notification providers (Email, WeChat, etc.)."""

    @abstractmethod
    async def send_notification(
        self,
        message: str,
        title: str = None,
        recipients: List[str] = None
    ) -> bool:
        """Send notification message."""
        pass

    @abstractmethod
    async def send_alert(
        self,
        alert_type: str,
        message: str,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """Send alert notification."""
        pass

    @abstractmethod
    async def test_connection(self) -> bool:
        """Test notification provider connection."""
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Get the name of the notification provider."""
        pass