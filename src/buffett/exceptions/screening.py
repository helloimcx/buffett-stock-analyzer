"""Screening-related exceptions for the Buffett dividend screening system."""

from .base import BuffettException


class ScreeningError(BuffettException):
    """Base class for all screening-related errors."""

    def __init__(self, message: str, stage: str = None, **kwargs):
        """
        Initialize screening error.

        Args:
            message: Human-readable error message
            stage: Screening stage where error occurred
            **kwargs: Additional context
        """
        context = kwargs.get("context", {})
        if stage:
            context["stage"] = stage

        super().__init__(
            message=message,
            error_code="SCREENING_ERROR",
            context=context
        )


class EligibilityError(ScreeningError):
    """Raised when eligibility screening operations fail."""

    def __init__(self, message: str, symbol: str = None, criterion: str = None, **kwargs):
        """
        Initialize eligibility error.

        Args:
            message: Human-readable error message
            symbol: Stock symbol that caused the error
            criterion: Specific eligibility criterion that failed
            **kwargs: Additional context
        """
        context = kwargs.get("context", {})
        if symbol:
            context["symbol"] = symbol
        if criterion:
            context["criterion"] = criterion

        super().__init__(
            message=message,
            stage="eligibility",
            context=context
        )


class ValuationError(ScreeningError):
    """Raised when valuation analysis operations fail."""

    def __init__(self, message: str, symbol: str = None, metric: str = None, **kwargs):
        """
        Initialize valuation error.

        Args:
            message: Human-readable error message
            symbol: Stock symbol that caused the error
            metric: Valuation metric that failed
            **kwargs: Additional context
        """
        context = kwargs.get("context", {})
        if symbol:
            context["symbol"] = symbol
        if metric:
            context["metric"] = metric

        super().__init__(
            message=message,
            stage="valuation",
            context=context
        )