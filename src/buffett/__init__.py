"""
Buffett Dividend Stock Screening System

A comprehensive stock screening system implementing Warren Buffett's dividend investment strategy
for Chinese A-share market with industry leader prioritization.
"""

__version__ = "2.0.0"
__author__ = "Buffett Investment System"

# Simplified imports to avoid circular dependencies
# These will be expanded in Phase 2
from .models.stock import Stock
from .models.screening import EligibilityResult
from .models.industry import IndustryLeader

__all__ = [
    "Stock",
    "EligibilityResult",
    "IndustryLeader",
]