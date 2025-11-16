"""Base exceptions for the Buffett dividend screening system."""


class BuffettException(Exception):
    """Base exception class for all Buffett system exceptions."""

    def __init__(self, message: str, error_code: str = None, context: dict = None):
        """
        Initialize base exception.

        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            context: Additional context information
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or {}

    def __str__(self) -> str:
        """Return string representation of the exception."""
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message

    def to_dict(self) -> dict:
        """Convert exception to dictionary for logging/serialization."""
        return {
            "exception_type": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "context": self.context,
        }