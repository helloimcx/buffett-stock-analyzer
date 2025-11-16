"""Stock-related data models with type validation."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

from pydantic import BaseModel, Field, field_validator, ValidationInfo, model_validator


class Market(str, Enum):
    """Stock market enum."""
    SH = "SH"  # Shanghai Stock Exchange
    SZ = "SZ"  # Shenzhen Stock Exchange
    BJ = "BJ"  # Beijing Stock Exchange
    UNKNOWN = "UNKNOWN"  # Unknown market


class Stock(BaseModel):
    """Stock basic information model."""

    symbol: str = Field(..., description="Stock symbol with market suffix, e.g., '000001.SZ'")
    name: str = Field(..., description="Stock name")
    code: str = Field(..., description="Stock code without market suffix")
    market: Market = Field(..., description="Stock market")

    @field_validator('symbol')
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        """Validate stock symbol format."""
        if not v or '.' not in v:
            raise ValueError("Symbol must contain market suffix, e.g., '000001.SZ'")
        return v.upper()

    @model_validator(mode='before')
    @classmethod
    def extract_code_and_market_from_symbol(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract stock code and market from symbol if not provided."""
        if isinstance(data, dict):
            symbol = data.get('symbol', '')
            if symbol and '.' in symbol:
                # Extract code if not provided
                if 'code' not in data or data['code'] is None:
                    data['code'] = symbol.split('.')[0].zfill(6)
                else:
                    # Pad provided code to 6 digits
                    data['code'] = str(data['code']).zfill(6)

                # Extract market if not provided
                if 'market' not in data or data['market'] is None:
                    market_suffix = symbol.split('.')[1].upper()
                    try:
                        data['market'] = Market(market_suffix)
                    except ValueError:
                        data['market'] = Market.UNKNOWN
        return data


class StockInfo(BaseModel):
    """Detailed stock information model."""

    symbol: str = Field(..., description="Stock symbol")
    name: str = Field(..., description="Stock name")
    industry: str = Field(..., description="Industry classification")
    market_cap: Optional[float] = Field(None, description="Market capitalization")
    total_assets: Optional[float] = Field(None, description="Total assets")
    total_liabilities: Optional[float] = Field(None, description="Total liabilities")
    current_price: Optional[float] = Field(None, description="Current stock price")
    pe_ratio: Optional[float] = Field(None, description="Price-to-earnings ratio")
    pb_ratio: Optional[float] = Field(None, description="Price-to-book ratio")
    dividend_yield: Optional[float] = Field(None, description="Current dividend yield")
    listing_date: Optional[datetime] = Field(None, description="Listing date")

    @field_validator('market_cap', 'total_assets', 'total_liabilities', 'current_price')
    @classmethod
    def validate_positive_amounts(cls, v: Optional[float]) -> Optional[float]:
        """Validate that monetary amounts are positive."""
        if v is not None and v <= 0:
            raise ValueError("Monetary amounts must be positive")
        return v

    @field_validator('pe_ratio', 'pb_ratio', 'dividend_yield')
    @classmethod
    def validate_ratios(cls, v: Optional[float]) -> Optional[float]:
        """Validate that ratios are non-negative."""
        if v is not None and v < 0:
            raise ValueError("Ratios must be non-negative")
        return v


class DividendData(BaseModel):
    """Dividend data model."""

    symbol: str = Field(..., description="Stock symbol")
    year: int = Field(..., description="Dividend year")
    cash_dividend: float = Field(..., description="Cash dividend amount per 10 shares")
    stock_dividend: float = Field(default=0.0, description="Stock dividend ratio")
    is_annual_report: bool = Field(default=False, description="Whether this is annual report data")
    record_date: Optional[datetime] = Field(None, description="Record date")
    ex_dividend_date: Optional[datetime] = Field(None, description="Ex-dividend date")
    payment_date: Optional[datetime] = Field(None, description="Payment date")

    @field_validator('year')
    @classmethod
    def validate_year(cls, v: int) -> int:
        """Validate dividend year."""
        current_year = datetime.now().year
        if v < 1990 or v > current_year + 1:
            raise ValueError(f"Year must be between 1990 and {current_year + 1}")
        return v

    @field_validator('cash_dividend')
    @classmethod
    def validate_cash_dividend(cls, v: float) -> float:
        """Validate cash dividend amount."""
        if v < 0:
            raise ValueError("Cash dividend cannot be negative")
        return v


class PriceData(BaseModel):
    """Stock price data model."""

    symbol: str = Field(..., description="Stock symbol")
    date: datetime = Field(..., description="Price date")
    open: float = Field(..., description="Opening price")
    high: float = Field(..., description="Highest price")
    low: float = Field(..., description="Lowest price")
    close: float = Field(..., description="Closing price")
    volume: int = Field(..., description="Trading volume")
    amount: float = Field(..., description="Trading amount")

    @field_validator('open', 'high', 'low', 'close', 'amount')
    @classmethod
    def validate_positive_prices(cls, v: float) -> float:
        """Validate that price-related fields are positive."""
        if v <= 0:
            raise ValueError("Price and amount must be positive")
        return v

    @field_validator('volume')
    @classmethod
    def validate_volume(cls, v: int) -> int:
        """Validate trading volume."""
        if v < 0:
            raise ValueError("Volume cannot be negative")
        return v

    @field_validator('high')
    @classmethod
    def validate_high_price(cls, v: float, info: ValidationInfo) -> float:
        """Validate that high price is not lower than other prices."""
        data = info.data
        if 'low' in data and v < data['low']:
            raise ValueError("High price cannot be lower than low price")
        if 'open' in data and v < data['open']:
            raise ValueError("High price cannot be lower than open price")
        if 'close' in data and v < data['close']:
            raise ValueError("High price cannot be lower than close price")
        return v

    @field_validator('low')
    @classmethod
    def validate_low_price(cls, v: float, info: ValidationInfo) -> float:
        """Validate that low price is not higher than other prices."""
        data = info.data
        if 'open' in data and v > data['open']:
            raise ValueError("Low price cannot be higher than open price")
        if 'close' in data and v > data['close']:
            raise ValueError("Low price cannot be higher than close price")
        return v