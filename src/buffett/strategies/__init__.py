"""
Strategy pattern implementations.

This package contains strategy pattern implementations for various
business operations, providing flexibility and extensibility.
"""

from .data_fetch_strategies import (
    DataFetchStrategy,
    AKShareStrategy,
    MockStrategy,
    MultiSourceStrategy
)

__all__ = [
    # Data fetch strategies
    "DataFetchStrategy",
    "AKShareStrategy",
    "MockStrategy",
    "MultiSourceStrategy",
]