"""
Interface definitions for the Buffett dividend screening system.

This package contains abstract interfaces that define contracts for various
components, supporting dependency injection and SOLID principles.
"""

from .repositories import (
    IStockRepository,
    IDividendRepository,
    IPriceRepository,
    ICacheRepository
)
from .services import (
    IDataFetchService,
    IScreeningService,
    IValuationService
)
from .providers import (
    IDataProvider,
    ICacheProvider
)

__all__ = [
    # Repository interfaces
    "IStockRepository",
    "IDividendRepository",
    "IPriceRepository",
    "ICacheRepository",

    # Service interfaces
    "IDataFetchService",
    "IScreeningService",
    "IValuationService",

    # Provider interfaces
    "IDataProvider",
    "ICacheProvider",
]