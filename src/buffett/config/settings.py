"""Settings management with environment variable support and validation."""

import os
from functools import lru_cache
from typing import Dict, Any, Optional
from pathlib import Path

from pydantic import Field, validator
from pydantic_settings import BaseSettings

from ..exceptions.config import ConfigurationError


class ScreeningSettings(BaseSettings):
    """Screening configuration settings."""

    # Eligibility settings
    min_dividend_yield: float = Field(default=4.0, description="Minimum dividend yield percentage")
    min_dividend_years: int = Field(default=3, description="Minimum consecutive dividend years")
    dividend_payment_ratio_max: float = Field(default=0.7, description="Maximum dividend payment ratio")
    positive_cash_flow_years: int = Field(default=3, description="Minimum positive cash flow years")
    top_n_per_industry: int = Field(default=3, description="Top N companies per industry")
    top_n_by_revenue: int = Field(default=3, description="Top N companies by revenue")

    # Industry leader settings
    industry_leader_priority: bool = Field(default=True, description="Prioritize industry leaders")
    industry_leader_bonus: float = Field(default=0.5, description="Dividend yield bonus for industry leaders")
    min_industry_leaders: int = Field(default=1, description="Minimum industry leaders per industry")
    force_include_leaders: bool = Field(default=True, description="Force include industry leaders")

    # Valuation settings
    max_pe_percentile: int = Field(default=30, description="Maximum PE percentile")
    max_pb_percentile: int = Field(default=20, description="Maximum PB percentile")
    min_dividend_yield_percentile: int = Field(default=70, description="Minimum dividend yield percentile")
    min_valuation_criteria: int = Field(default=2, description="Minimum valuation criteria to meet")
    history_years: int = Field(default=5, description="Years of historical data for analysis")

    # Trend settings
    ma_week_30: int = Field(default=30, description="30-week moving average")
    ma_week_60: int = Field(default=60, description="60-week moving average")
    ma_distance_threshold: float = Field(default=0.5, description="Price-MA distance threshold")
    bollinger_period: int = Field(default=20, description="Bollinger Bands period")
    bollinger_std: float = Field(default=2.0, description="Bollinger Bands standard deviation")
    rsi_period: int = Field(default=14, description="RSI period")
    rsi_oversold: int = Field(default=30, description="RSI oversold threshold")
    rsi_overbought: int = Field(default=70, description="RSI overbought threshold")

    # Risk control settings
    stop_loss_ma_break: bool = Field(default=True, description="Stop loss on MA break")
    max_pe_percentile_stop: int = Field(default=80, description="Maximum PE percentile for stop")
    min_dividend_yield_stop: float = Field(default=3.0, description="Minimum dividend yield for stop")
    trend_acceleration_threshold: float = Field(default=0.5, description="Trend acceleration threshold")

    class Config:
        env_prefix = "BUFFETT_SCREENING_"
        case_sensitive = False

    @validator('min_dividend_yield', 'dividend_payment_ratio_max', 'industry_leader_bonus')
    def validate_positive_rates(cls, v: float) -> float:
        """Validate that rate settings are positive."""
        if v < 0:
            raise ValueError("Rate settings must be non-negative")
        return v

    @validator('min_dividend_years', 'positive_cash_flow_years', 'top_n_per_industry', 'top_n_by_revenue')
    def validate_positive_integers(cls, v: int) -> int:
        """Validate that count settings are positive."""
        if v <= 0:
            raise ValueError("Count settings must be positive")
        return v

    @validator('min_industry_leaders')
    def validate_min_industry_leaders(cls, v: int, values: Dict[str, Any]) -> int:
        """Validate minimum industry leaders against top N settings."""
        if v > values.get('top_n_per_industry', 3):
            raise ValueError("Minimum industry leaders cannot exceed top N per industry")
        return v

    @validator('max_pe_percentile', 'max_pb_percentile', 'min_dividend_yield_percentile', 'max_pe_percentile_stop')
    def validate_percentiles(cls, v: int) -> int:
        """Validate percentile ranges."""
        if v < 0 or v > 100:
            raise ValueError("Percentile values must be between 0 and 100")
        return v

    @validator('rsi_oversold', 'rsi_overbought')
    def validate_rsi_thresholds(cls, v: int) -> int:
        """Validate RSI thresholds."""
        if v < 0 or v > 100:
            raise ValueError("RSI thresholds must be between 0 and 100")
        return v


class DataSettings(BaseSettings):
    """Data configuration settings."""

    # Cache settings
    cache_duration_hours: int = Field(default=24, description="Data cache duration in hours")
    update_frequency_hours: int = Field(default=1, description="Data update frequency in hours")
    cache_dir: Optional[str] = Field(default=None, description="Cache directory path")

    # API settings
    max_retries: int = Field(default=3, description="Maximum number of retries for API calls")
    timeout_seconds: int = Field(default=30, description="Request timeout in seconds")
    rate_limit_requests_per_minute: int = Field(default=60, description="Rate limit requests per minute")

    # Data source settings
    data_source: str = Field(default="optimized_akshare", description="Data source type (akshare/optimized_akshare/mock/multi_source)")
    akshare_proxy: Optional[str] = Field(default=None, description="AKShare proxy URL")
    enable_data_validation: bool = Field(default=True, description="Enable data validation")
    data_quality_threshold: float = Field(default=0.8, description="Minimum data quality score")

    # Optimized data fetcher settings
    optimized_cache_ttl_hours: int = Field(default=24, description="Optimized cache TTL in hours")
    optimized_enable_cache: bool = Field(default=True, description="Enable optimized caching")

    class Config:
        env_prefix = "BUFFETT_DATA_"
        case_sensitive = False

    @validator('cache_duration_hours', 'update_frequency_hours', 'timeout_seconds')
    def validate_positive_time_values(cls, v: int) -> int:
        """Validate that time values are positive."""
        if v <= 0:
            raise ValueError("Time values must be positive")
        return v

    @validator('max_retries', 'rate_limit_requests_per_minute')
    def validate_positive_counts(cls, v: int) -> int:
        """Validate that count values are positive."""
        if v <= 0:
            raise ValueError("Count values must be positive")
        return v

    @validator('data_quality_threshold')
    def validate_quality_threshold(cls, v: float) -> float:
        """Validate data quality threshold range."""
        if v < 0 or v > 1:
            raise ValueError("Data quality threshold must be between 0 and 1")
        return v


class LoggingSettings(BaseSettings):
    """Logging configuration settings."""

    level: str = Field(default="INFO", description="Logging level")
    format: str = Field(
        default="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
        description="Log format"
    )
    file_path: Optional[str] = Field(default=None, description="Log file path")
    max_size: str = Field(default="10 MB", description="Maximum log file size")
    backup_count: int = Field(default=5, description="Number of backup log files")
    enable_console: bool = Field(default=True, description="Enable console logging")
    enable_file: bool = Field(default=True, description="Enable file logging")

    class Config:
        env_prefix = "BUFFETT_LOG_"
        case_sensitive = False

    @validator('level')
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v.upper()

    @validator('backup_count')
    def validate_backup_count(cls, v: int) -> int:
        """Validate backup count."""
        if v < 0:
            raise ValueError("Backup count cannot be negative")
        return v


class Settings(BaseSettings):
    """Main application settings."""

    # Application settings
    app_name: str = Field(default="Buffett Dividend Screener", description="Application name")
    version: str = Field(default="2.0.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    environment: str = Field(default="development", description="Environment (development/staging/production)")

    # Directory settings
    base_dir: Optional[str] = Field(default=None, description="Base directory path")
    data_dir: Optional[str] = Field(default=None, description="Data directory path")
    reports_dir: Optional[str] = Field(default=None, description="Reports directory path")

    # Sub-settings
    screening: ScreeningSettings = Field(default_factory=ScreeningSettings)
    data: DataSettings = Field(default_factory=DataSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)

    class Config:
        env_prefix = "BUFFETT_"
        case_sensitive = False
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # 允许额外的环境变量

    @validator('environment')
    def validate_environment(cls, v: str) -> str:
        """Validate environment value."""
        valid_envs = ["development", "staging", "production", "test"]
        if v.lower() not in valid_envs:
            raise ValueError(f"Environment must be one of {valid_envs}")
        return v.lower()

    def __init__(self, **data: Any):
        """Initialize settings with default directory setup."""
        super().__init__(**data)
        self._setup_directories()

    def _setup_directories(self) -> None:
        """Setup default directories based on environment."""
        if not self.base_dir:
            self.base_dir = str(Path(__file__).parent.parent.parent.parent)

        if not self.data_dir:
            self.data_dir = str(Path(self.base_dir) / "data")

        if not self.reports_dir:
            self.reports_dir = str(Path(self.base_dir) / "reports")

        # Ensure directories exist
        Path(self.data_dir).mkdir(parents=True, exist_ok=True)
        Path(self.reports_dir).mkdir(parents=True, exist_ok=True)

        # Setup cache directory
        if not self.data.cache_dir:
            self.data.cache_dir = str(Path(self.data_dir) / "cache")
        Path(self.data.cache_dir).mkdir(parents=True, exist_ok=True)

        # Setup log directory
        if self.logging.enable_file and not self.logging.file_path:
            self.logging.file_path = str(Path(self.data_dir) / "app.log")


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()