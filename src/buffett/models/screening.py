"""Screening result data models with type validation."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

from pydantic import BaseModel, Field, validator

from .stock import Stock


class ScreeningCriteria(BaseModel):
    """Screening criteria configuration model."""

    min_dividend_yield: float = Field(default=4.0, description="Minimum dividend yield percentage")
    min_dividend_years: int = Field(default=3, description="Minimum consecutive dividend years")
    max_pe_percentile: int = Field(default=30, description="Maximum PE percentile")
    max_pb_percentile: int = Field(default=20, description="Maximum PB percentile")
    min_valuation_criteria: int = Field(default=2, description="Minimum valuation criteria to meet")
    industry_leader_priority: bool = Field(default=True, description="Prioritize industry leaders")
    top_n_per_industry: int = Field(default=3, description="Top N companies per industry")
    force_include_leaders: bool = Field(default=True, description="Force include industry leaders")
    min_market_cap: Optional[float] = Field(None, description="Minimum market capitalization")
    exclude_st: bool = Field(default=True, description="Exclude ST stocks")

    @validator('min_dividend_yield')
    def validate_min_yield(cls, v: float) -> float:
        """Validate minimum dividend yield."""
        if v < 0:
            raise ValueError("Minimum dividend yield must be non-negative")
        return v

    @validator('min_dividend_years')
    def validate_min_years(cls, v: int) -> int:
        """Validate minimum dividend years."""
        if v <= 0:
            raise ValueError("Minimum dividend years must be positive")
        return v

    @validator('max_pe_percentile', 'max_pb_percentile')
    def validate_percentiles(cls, v: int) -> int:
        """Validate percentile ranges."""
        if v < 0 or v > 100:
            raise ValueError("Percentiles must be between 0 and 100")
        return v

    @validator('min_valuation_criteria')
    def validate_min_criteria(cls, v: int) -> int:
        """Validate minimum valuation criteria."""
        if v < 1 or v > 3:  # PE, PB, Dividend Yield
            raise ValueError("Minimum valuation criteria must be between 1 and 3")
        return v

    @validator('top_n_per_industry')
    def validate_top_n(cls, v: int) -> int:
        """Validate top N per industry."""
        if v <= 0:
            raise ValueError("Top N per industry must be positive")
        return v

    @validator('min_market_cap')
    def validate_market_cap(cls, v: Optional[float]) -> Optional[float]:
        """Validate minimum market cap."""
        if v is not None and v <= 0:
            raise ValueError("Minimum market cap must be positive")
        return v


class ScreeningStatus(str, Enum):
    """Screening status enum."""
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


class TrendDirection(str, Enum):
    """Trend direction enum."""
    UP = "up"
    DOWN = "down"
    SIDEWAYS = "sideways"
    UNKNOWN = "unknown"


class ScreeningResult(BaseModel):
    """Base screening result model."""

    symbol: str = Field(..., description="Stock symbol")
    name: str = Field(..., description="Stock name")
    screening_stage: str = Field(..., description="Screening stage name")
    status: ScreeningStatus = Field(..., description="Screening status")
    score: Optional[float] = Field(None, description="Screening score (0-100)")
    reason: Optional[str] = Field(None, description="Reason for screening result")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    timestamp: datetime = Field(default_factory=datetime.now, description="Screening timestamp")

    @validator('score')
    def validate_score(cls, v: Optional[float]) -> Optional[float]:
        """Validate score range."""
        if v is not None and (v < 0 or v > 100):
            raise ValueError("Score must be between 0 and 100")
        return v


class EligibilityResult(ScreeningResult):
    """Eligibility screening result model."""

    avg_dividend_rate: Optional[float] = Field(None, description="Average dividend rate")
    min_dividend_rate: Optional[float] = Field(None, description="Minimum dividend rate")
    dividend_years: Optional[int] = Field(None, description="Number of dividend years")
    stability_score: Optional[float] = Field(None, description="Dividend stability score")
    industry_rank: Optional[int] = Field(None, description="Rank within industry")
    is_industry_leader: bool = Field(default=False, description="Is industry leader")
    leadership_tier: Optional[int] = Field(None, description="Leadership tier (1-3)")
    forced_inclusion: bool = Field(default=False, description="Was forcibly included")

    @validator('avg_dividend_rate', 'min_dividend_rate', 'stability_score')
    def validate_positive_rates(cls, v: Optional[float]) -> Optional[float]:
        """Validate that rates and scores are non-negative."""
        if v is not None and v < 0:
            raise ValueError("Rates and scores must be non-negative")
        return v

    @validator('dividend_years', 'industry_rank')
    def validate_positive_integers(cls, v: Optional[int]) -> Optional[int]:
        """Validate that counts and ranks are positive."""
        if v is not None and v <= 0:
            raise ValueError("Counts and ranks must be positive")
        return v

    @validator('leadership_tier')
    def validate_leadership_tier(cls, v: Optional[int]) -> Optional[int]:
        """Validate leadership tier range."""
        if v is not None and (v < 1 or v > 3):
            raise ValueError("Leadership tier must be between 1 and 3")
        return v


class ValuationResult(ScreeningResult):
    """Valuation analysis result model."""

    pe_ratio: Optional[float] = Field(None, description="Price-to-earnings ratio")
    pb_ratio: Optional[float] = Field(None, description="Price-to-book ratio")
    current_dividend_yield: Optional[float] = Field(None, description="Current dividend yield")
    pe_percentile: Optional[float] = Field(None, description="PE ratio percentile")
    pb_percentile: Optional[float] = Field(None, description="PB ratio percentile")
    dividend_yield_percentile: Optional[float] = Field(None, description="Dividend yield percentile")
    valuation_score: Optional[float] = Field(None, description="Overall valuation score")
    undervaluation_level: Optional[str] = Field(None, description="Undervaluation level")

    @validator('pe_ratio', 'pb_ratio', 'current_dividend_yield')
    def validate_positive_ratios(cls, v: Optional[float]) -> Optional[float]:
        """Validate that ratios are positive."""
        if v is not None and v <= 0:
            raise ValueError("Ratios must be positive")
        return v

    @validator('pe_percentile', 'pb_percentile', 'dividend_yield_percentile', 'valuation_score')
    def validate_percentiles(cls, v: Optional[float]) -> Optional[float]:
        """Validate percentile range."""
        if v is not None and (v < 0 or v > 100):
            raise ValueError("Percentiles must be between 0 and 100")
        return v


class TrendResult(ScreeningResult):
    """Trend analysis result model."""

    current_price: Optional[float] = Field(None, description="Current stock price")
    ma_short: Optional[float] = Field(None, description="Short-term moving average")
    ma_long: Optional[float] = Field(None, description="Long-term moving average")
    trend_direction: TrendDirection = Field(TrendDirection.UNKNOWN, description="Trend direction")
    rsi: Optional[float] = Field(None, description="RSI indicator")
    bollinger_position: Optional[str] = Field(None, description="Position relative to Bollinger bands")
    price_distance_from_ma: Optional[float] = Field(None, description="Price distance from moving average")
    trend_score: Optional[float] = Field(None, description="Trend analysis score")

    @validator('current_price', 'ma_short', 'ma_long')
    def validate_positive_prices(cls, v: Optional[float]) -> Optional[float]:
        """Validate that prices are positive."""
        if v is not None and v <= 0:
            raise ValueError("Prices must be positive")
        return v

    @validator('rsi', 'trend_score')
    def validate_indicators(cls, v: Optional[float]) -> Optional[float]:
        """Validate indicator ranges."""
        if v is not None:
            if v < 0 or v > 100:
                raise ValueError("RSI and trend scores must be between 0 and 100")
        return v

    @validator('price_distance_from_ma')
    def validate_price_distance(cls, v: Optional[float]) -> Optional[float]:
        """Validate price distance can be positive or negative."""
        return v  # Can be negative (price below MA) or positive (price above MA)


class RiskAssessment(BaseModel):
    """Risk assessment model."""

    symbol: str = Field(..., description="Stock symbol")
    risk_level: str = Field(..., description="Risk level (low/medium/high)")
    risk_score: float = Field(..., description="Risk score (0-100)")
    risk_factors: List[str] = Field(default_factory=list, description="Identified risk factors")
    stop_loss_price: Optional[float] = Field(None, description="Recommended stop loss price")
    max_position_size: Optional[float] = Field(None, description="Maximum recommended position size")
    volatility: Optional[float] = Field(None, description="Price volatility")
    beta: Optional[float] = Field(None, description="Beta coefficient")

    @validator('risk_score')
    def validate_risk_score(cls, v: float) -> float:
        """Validate risk score range."""
        if v < 0 or v > 100:
            raise ValueError("Risk score must be between 0 and 100")
        return v

    @validator('risk_level')
    def validate_risk_level(cls, v: str) -> str:
        """Validate risk level."""
        valid_levels = ["low", "medium", "high"]
        if v.lower() not in valid_levels:
            raise ValueError(f"Risk level must be one of {valid_levels}")
        return v.lower()

    @validator('stop_loss_price', 'max_position_size')
    def validate_positive_values(cls, v: Optional[float]) -> Optional[float]:
        """Validate that monetary values are positive."""
        if v is not None and v <= 0:
            raise ValueError("Monetary values must be positive")
        return v


class RiskResult(ScreeningResult):
    """Risk control result model extending ScreeningResult."""

    passed: bool = Field(..., description="Whether stock passed risk control")
    overall_trend_score: float = Field(0.0, description="Overall trend score from previous steps")
    risk_score: float = Field(..., description="Overall risk score (0-100, lower is better)")
    volatility_score: float = Field(..., description="Volatility risk score (0-100)")
    valuation_risk_score: float = Field(..., description="Valuation risk score (0-100)")
    liquidity_risk_score: float = Field(..., description="Liquidity risk score (0-100)")
    concentration_risk_score: float = Field(..., description="Concentration risk score (0-100)")
    current_price: float = Field(..., description="Current stock price")
    stop_loss_price: Optional[float] = Field(None, description="Recommended stop loss price")
    stop_loss_distance: float = Field(..., description="Stop loss distance in percentage")
    volatility_pct: float = Field(..., description="Annualized volatility percentage")
    risk_level: str = Field(..., description="Risk level classification")
    position_recommendation: Dict[str, Any] = Field(..., description="Position size recommendations")
    risk_factors: List[str] = Field(default_factory=list, description="Identified risk factors")

    @validator('risk_score', 'volatility_score', 'valuation_risk_score', 'liquidity_risk_score', 'concentration_risk_score')
    def validate_score_range(cls, v: float) -> float:
        """Validate score range."""
        if v < 0 or v > 100:
            raise ValueError("Risk scores must be between 0 and 100")
        return v

    @validator('risk_level')
    def validate_risk_level(cls, v: str) -> str:
        """Validate risk level."""
        valid_levels = ["低风险", "中等风险", "较高风险", "高风险"]
        if v not in valid_levels:
            raise ValueError(f"Risk level must be one of {valid_levels}")
        return v


class CompleteScreeningResult(BaseModel):
    """Complete screening result model for the full four-step investment strategy."""

    criteria: ScreeningCriteria = Field(..., description="Screening criteria used")
    eligibility_results: List[EligibilityResult] = Field(default_factory=list, description="Eligibility screening results")
    valuation_results: List[ValuationResult] = Field(default_factory=list, description="Valuation analysis results")
    trend_results: List[TrendResult] = Field(default_factory=list, description="Trend analysis results")
    risk_results: List[RiskResult] = Field(default_factory=list, description="Risk control results")
    final_candidates: List[Dict[str, Any]] = Field(default_factory=list, description="Final candidate stocks")
    summary: Dict[str, Any] = Field(default_factory=dict, description="Screening summary statistics")
    execution_time: float = Field(..., description="Total execution time in seconds")

    @validator('execution_time')
    def validate_execution_time(cls, v: float) -> float:
        """Validate execution time is non-negative."""
        if v < 0:
            raise ValueError("Execution time must be non-negative")
        return v