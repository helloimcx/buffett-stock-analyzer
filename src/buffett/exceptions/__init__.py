"""
Custom exceptions for the Buffett dividend screening system.

This package defines all custom exception classes used throughout the application
to provide better error handling and debugging capabilities.
"""

from .base import BuffettException
from .data import DataFetchError, CacheError, ValidationError
from .screening import ScreeningError, EligibilityError, ValuationError
from .config import ConfigurationError

__all__ = [
    "BuffettException",
    "DataFetchError",
    "CacheError",
    "ValidationError",
    "ScreeningError",
    "EligibilityError",
    "ValuationError",
    "ConfigurationError",
]