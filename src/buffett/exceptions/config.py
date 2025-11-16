"""Configuration-related exceptions for the Buffett dividend screening system."""

from .base import BuffettException


class ConfigurationError(BuffettException):
    """Raised when configuration operations fail."""

    def __init__(self, message: str, config_key: str = None, config_value=None, **kwargs):
        """
        Initialize configuration error.

        Args:
            message: Human-readable error message
            config_key: Configuration key that caused the error
            config_value: Invalid configuration value
            **kwargs: Additional context
        """
        context = kwargs.get("context", {})
        if config_key:
            context["config_key"] = config_key
        if config_value is not None:
            context["config_value"] = str(config_value)

        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            context=context
        )