"""
Service interface definitions.

This module defines abstract base classes for application services following
the SOLID principles, particularly the Interface Segregation Principle.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import pandas as pd
from datetime import date

from ..models.stock import Stock, StockInfo, DividendData
from ..models.screening import EligibilityResult, ScreeningCriteria


class IDataFetchService(ABC):
    """Service interface for data fetching operations."""

    @abstractmethod
    async def fetch_all_stocks(self) -> pd.DataFrame:
        """Fetch all available stocks from data source."""
        pass

    @abstractmethod
    async def fetch_stock_info(self, symbol: str) -> Optional[StockInfo]:
        """Fetch detailed stock information."""
        pass

    @abstractmethod
    async def fetch_dividend_data(self, symbol: str) -> List[DividendData]:
        """Fetch dividend history for a stock."""
        pass

    @abstractmethod
    async def fetch_price_data(
        self,
        symbol: str,
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """Fetch price data for a stock within date range."""
        pass

    @abstractmethod
    async def is_data_available(self, symbol: str) -> bool:
        """Check if data is available for a stock."""
        pass


class IScreeningService(ABC):
    """Service interface for stock screening operations."""

    @abstractmethod
    async def screen_dividend_eligibility(
        self,
        stocks: List[Stock],
        criteria: ScreeningCriteria = None
    ) -> List[EligibilityResult]:
        """Screen stocks for dividend eligibility."""
        pass

    @abstractmethod
    async def screen_by_dividend_yield(
        self,
        stocks: List[Stock],
        min_yield: float = 4.0
    ) -> pd.DataFrame:
        """Screen stocks by minimum dividend yield."""
        pass

    @abstractmethod
    async def screen_industry_leaders(
        self,
        stocks: List[StockInfo],
        top_n_per_industry: int = 3
    ) -> List[StockInfo]:
        """Screen for industry leaders by market cap."""
        pass

    @abstractmethod
    async def apply_valuation_filters(
        self,
        stocks: List[StockInfo],
        max_pe_percentile: int = 30,
        max_pb_percentile: int = 20
    ) -> List[StockInfo]:
        """Apply valuation filters to stocks."""
        pass


class IValuationService(ABC):
    """Service interface for valuation analysis."""

    @abstractmethod
    async def calculate_pe_percentile(self, pe_ratio: float, industry: str) -> float:
        """Calculate PE ratio percentile within industry."""
        pass

    @abstractmethod
    async def calculate_pb_percentile(self, pb_ratio: float, industry: str) -> float:
        """Calculate PB ratio percentile within industry."""
        pass

    @abstractmethod
    async def calculate_dividend_yield_percentile(
        self,
        dividend_yield: float,
        industry: str
    ) -> float:
        """Calculate dividend yield percentile within industry."""
        pass

    @abstractmethod
    async def get_valuation_summary(self, symbol: str) -> Dict[str, Any]:
        """Get comprehensive valuation summary for a stock."""
        pass

    @abstractmethod
    async def compare_with_industry_peers(
        self,
        symbol: str,
        metrics: List[str] = None
    ) -> Dict[str, Any]:
        """Compare stock metrics with industry peers."""
        pass


class IAnalysisService(ABC):
    """Service interface for financial analysis."""

    @abstractmethod
    async def analyze_financial_health(self, symbol: str) -> Dict[str, Any]:
        """Analyze financial health of a company."""
        pass

    @abstractmethod
    async def calculate_dividend_sustainability(self, symbol: str) -> float:
        """Calculate dividend sustainability score (0-100)."""
        pass

    @abstractmethod
    async def detect_dividend_trends(self, symbol: str, years: int = 5) -> Dict[str, Any]:
        """Detect trends in dividend payments over time."""
        pass

    @abstractmethod
    async def generate_risk_metrics(self, symbol: str) -> Dict[str, Any]:
        """Generate risk metrics for a stock."""
        pass


class IReportingService(ABC):
    """Service interface for generating reports."""

    @abstractmethod
    async def generate_screening_report(
        self,
        results: List[EligibilityResult]
    ) -> Dict[str, Any]:
        """Generate a comprehensive screening report."""
        pass

    @abstractmethod
    async def export_to_excel(
        self,
        data: pd.DataFrame,
        filename: str,
        sheet_name: str = "Data"
    ) -> str:
        """Export data to Excel file."""
        pass

    @abstractmethod
    async def generate_summary_statistics(
        self,
        stocks: List[StockInfo]
    ) -> Dict[str, Any]:
        """Generate summary statistics for a list of stocks."""
        pass