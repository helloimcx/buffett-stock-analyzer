"""Data-related exceptions for the Buffett dividend screening system."""

from .base import BuffettException


class DataFetchError(BuffettException):
    """Raised when data fetching operations fail."""

    def __init__(self, message: str, source: str = None, retry_count: int = 0, **kwargs):
        """
        Initialize data fetch error.

        Args:
            message: Human-readable error message
            source: Data source where the error occurred
            retry_count: Number of retries attempted
            **kwargs: Additional context
        """
        context = kwargs.get("context", {})
        if source:
            context["source"] = source
        context["retry_count"] = retry_count

        super().__init__(
            message=message,
            error_code="DATA_FETCH_ERROR",
            context=context
        )


class CacheError(BuffettException):
    """Raised when cache operations fail."""

    def __init__(self, message: str, cache_key: str = None, operation: str = None, **kwargs):
        """
        Initialize cache error.

        Args:
            message: Human-readable error message
            cache_key: Cache key that caused the error
            operation: Cache operation (get, set, delete, etc.)
            **kwargs: Additional context
        """
        context = kwargs.get("context", {})
        if cache_key:
            context["cache_key"] = cache_key
        if operation:
            context["operation"] = operation

        super().__init__(
            message=message,
            error_code="CACHE_ERROR",
            context=context
        )


class ValidationError(BuffettException):
    """Raised when data validation fails."""

    def __init__(self, message: str, field: str = None, value=None, **kwargs):
        """
        Initialize validation error.

        Args:
            message: Human-readable error message
            field: Field that failed validation
            value: Invalid value
            **kwargs: Additional context
        """
        context = kwargs.get("context", {})
        if field:
            context["field"] = field
        if value is not None:
            context["value"] = str(value)

        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            context=context
        )