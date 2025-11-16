"""
Configuration management for the Buffett dividend screening system.

This package handles all configuration aspects including settings management,
environment variables, and configuration validation.
"""

from .settings import Settings, get_settings
from .industry import IndustryConfig

__all__ = [
    "Settings",
    "get_settings",
    "IndustryConfig",
]