"""Industry-related data models with type validation."""

from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field, validator


class IndustryLeader(BaseModel):
    """Industry leader company model."""

    symbol: str = Field(..., description="Stock symbol")
    name: str = Field(..., description="Company name")
    market_cap_tier: int = Field(..., description="Market cap tier (1=highest, 3=lowest)")
    description: Optional[str] = Field(None, description="Company description")
    market_rank: Optional[int] = Field(None, description="Rank within industry by market cap")
    revenue_rank: Optional[int] = Field(None, description="Rank within industry by revenue")

    @validator('market_cap_tier')
    def validate_market_cap_tier(cls, v: int) -> int:
        """Validate market cap tier range."""
        if v < 1 or v > 3:
            raise ValueError("Market cap tier must be between 1 and 3")
        return v

    @validator('market_rank', 'revenue_rank')
    def validate_ranks(cls, v: Optional[int]) -> Optional[int]:
        """Validate rank values."""
        if v is not None and v <= 0:
            raise ValueError("Ranks must be positive")
        return v


class IndustryConfig(BaseModel):
    """Industry configuration model."""

    industry_name: str = Field(..., description="Industry name")
    leaders: List[IndustryLeader] = Field(..., description="List of industry leaders")
    default_top_n: int = Field(default=3, description="Default number of top companies to consider")
    keywords: List[str] = Field(default_factory=list, description="Industry keywords for classification")
    description: Optional[str] = Field(None, description="Industry description")
    is_enabled: bool = Field(default=True, description="Whether this industry is enabled for screening")

    @validator('default_top_n')
    def validate_default_top_n(cls, v: int) -> int:
        """Validate default top N value."""
        if v < 1 or v > 20:
            raise ValueError("Default top N must be between 1 and 20")
        return v

    @validator('leaders')
    def validate_leaders_not_empty(cls, v: List[IndustryLeader]) -> List[IndustryLeader]:
        """Validate that leaders list is not empty."""
        if not v:
            raise ValueError("Industry must have at least one leader")
        return v


class IndustryClassification(BaseModel):
    """Industry classification model."""

    symbol: str = Field(..., description="Stock symbol")
    primary_industry: str = Field(..., description="Primary industry classification")
    confidence_score: float = Field(..., description="Classification confidence score (0-1)")
    alternative_industries: List[str] = Field(default_factory=list, description="Alternative industry classifications")
    classification_method: str = Field(..., description="Method used for classification")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional classification metadata")

    @validator('confidence_score')
    def validate_confidence_score(cls, v: float) -> float:
        """Validate confidence score range."""
        if v < 0 or v > 1:
            raise ValueError("Confidence score must be between 0 and 1")
        return v


class IndustryMapping(BaseModel):
    """Industry keyword mapping model."""

    industry_name: str = Field(..., description="Industry name")
    keywords: List[str] = Field(..., description="Keywords for industry classification")
    patterns: List[str] = Field(default_factory=list, description="Regex patterns for classification")
    weight: float = Field(default=1.0, description="Classification weight")
    priority: int = Field(default=1, description="Classification priority (higher=more specific)")

    @validator('keywords')
    def validate_keywords_not_empty(cls, v: List[str]) -> List[str]:
        """Validate that keywords list is not empty."""
        if not v:
            raise ValueError("Industry mapping must have at least one keyword")
        return v

    @validator('weight')
    def validate_weight(cls, v: float) -> float:
        """Validate weight range."""
        if v <= 0:
            raise ValueError("Weight must be positive")
        return v

    @validator('priority')
    def validate_priority(cls, v: int) -> int:
        """Validate priority value."""
        if v <= 0:
            raise ValueError("Priority must be positive")
        return v