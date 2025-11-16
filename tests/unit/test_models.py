"""Unit tests for data models."""

import pytest
from datetime import datetime
from pydantic import ValidationError

from src.buffett.models.stock import Stock, StockInfo, DividendData, PriceData
from src.buffett.models.screening import EligibilityResult, ScreeningStatus
from src.buffett.models.industry import IndustryLeader, IndustryConfig


class TestStock:
    """Test Stock model."""

    def test_valid_stock_creation(self, sample_stock: Stock) -> None:
        """Test creating a valid stock."""
        assert sample_stock.symbol == "000001.SZ"
        assert sample_stock.name == "平安银行"
        assert sample_stock.code == "000001"
        assert sample_stock.market.value == "SZ"

    def test_invalid_symbol_format(self) -> None:
        """Test that invalid symbol format raises validation error."""
        with pytest.raises(ValidationError):
            Stock(name="测试", symbol="INVALID")

    def test_code_extraction(self) -> None:
        """Test that stock code is extracted from symbol."""
        stock = Stock(symbol="600000.SH", name="浦发银行")
        assert stock.code == "600000"

    def test_code_padding(self) -> None:
        """Test that stock code is padded to 6 digits."""
        stock = Stock(symbol="1.SH", name="测试", code="1")
        assert stock.code == "000001"


class TestStockInfo:
    """Test StockInfo model."""

    def test_valid_stock_info(self, sample_stock_info: StockInfo) -> None:
        """Test creating valid stock info."""
        assert sample_stock_info.symbol == "000001.SZ"
        assert sample_stock_info.industry == "银行"
        assert sample_stock_info.market_cap == 1000000000000.0
        assert sample_stock_info.current_price == 10.50

    def test_negative_market_cap(self) -> None:
        """Test that negative market cap raises validation error."""
        with pytest.raises(ValidationError):
            StockInfo(
                symbol="000001.SZ",
                name="测试",
                industry="测试",
                market_cap=-1000.0
            )

    def test_negative_price(self) -> None:
        """Test that negative price raises validation error."""
        with pytest.raises(ValidationError):
            StockInfo(
                symbol="000001.SZ",
                name="测试",
                industry="测试",
                current_price=-10.0
            )

    def test_invalid_pe_ratio(self) -> None:
        """Test that negative PE ratio raises validation error."""
        with pytest.raises(ValidationError):
            StockInfo(
                symbol="000001.SZ",
                name="测试",
                industry="测试",
                pe_ratio=-5.0
            )


class TestDividendData:
    """Test DividendData model."""

    def test_valid_dividend_data(self) -> None:
        """Test creating valid dividend data."""
        dividend = DividendData(
            symbol="000001.SZ",
            year=2024,
            cash_dividend=2.0,
            is_annual_report=True
        )
        assert dividend.symbol == "000001.SZ"
        assert dividend.year == 2024
        assert dividend.cash_dividend == 2.0
        assert dividend.is_annual_report is True

    def test_invalid_year(self) -> None:
        """Test that invalid year raises validation error."""
        with pytest.raises(ValidationError):
            DividendData(
                symbol="000001.SZ",
                year=1800,  # Too early
                cash_dividend=2.0
            )

    def test_negative_cash_dividend(self) -> None:
        """Test that negative cash dividend raises validation error."""
        with pytest.raises(ValidationError):
            DividendData(
                symbol="000001.SZ",
                year=2024,
                cash_dividend=-1.0
            )


class TestPriceData:
    """Test PriceData model."""

    def test_valid_price_data(self) -> None:
        """Test creating valid price data."""
        price = PriceData(
            symbol="000001.SZ",
            date=datetime.now(),
            open=10.0,
            high=10.5,
            low=9.8,
            close=10.2,
            volume=1000000,
            amount=10200000.0
        )
        assert price.symbol == "000001.SZ"
        assert price.open == 10.0
        assert price.high == 10.5
        assert price.low == 9.8
        assert price.close == 10.2

    def test_invalid_price_relationship(self) -> None:
        """Test that invalid price relationships raise validation error."""
        with pytest.raises(ValidationError):
            PriceData(
                symbol="000001.SZ",
                date=datetime.now(),
                open=10.0,
                high=9.5,  # High lower than open
                low=9.8,
                close=10.2,
                volume=1000000,
                amount=10200000.0
            )

    def test_negative_volume(self) -> None:
        """Test that negative volume raises validation error."""
        with pytest.raises(ValidationError):
            PriceData(
                symbol="000001.SZ",
                date=datetime.now(),
                open=10.0,
                high=10.5,
                low=9.8,
                close=10.2,
                volume=-1000,  # Negative volume
                amount=10200000.0
            )


class TestEligibilityResult:
    """Test EligibilityResult model."""

    def test_valid_eligibility_result(self, sample_eligibility_result: EligibilityResult) -> None:
        """Test creating valid eligibility result."""
        assert sample_eligibility_result.symbol == "000001.SZ"
        assert sample_eligibility_result.status == ScreeningStatus.PASSED
        assert sample_eligibility_result.score == 85.5
        assert sample_eligibility_result.is_industry_leader is True

    def test_invalid_score(self) -> None:
        """Test that invalid score raises validation error."""
        with pytest.raises(ValidationError):
            EligibilityResult(
                symbol="000001.SZ",
                name="测试",
                screening_stage="eligibility",
                status=ScreeningStatus.PASSED,
                score=150.0  # Score too high
            )

    def test_negative_dividend_rate(self) -> None:
        """Test that negative dividend rate raises validation error."""
        with pytest.raises(ValidationError):
            EligibilityResult(
                symbol="000001.SZ",
                name="测试",
                screening_stage="eligibility",
                status=ScreeningStatus.PASSED,
                avg_dividend_rate=-5.0  # Negative rate
            )


class TestIndustryLeader:
    """Test IndustryLeader model."""

    def test_valid_industry_leader(self) -> None:
        """Test creating valid industry leader."""
        leader = IndustryLeader(
            symbol="601398.SH",
            name="工商银行",
            market_cap_tier=1
        )
        assert leader.symbol == "601398.SH"
        assert leader.name == "工商银行"
        assert leader.market_cap_tier == 1

    def test_invalid_market_cap_tier(self) -> None:
        """Test that invalid market cap tier raises validation error."""
        with pytest.raises(ValidationError):
            IndustryLeader(
                symbol="601398.SH",
                name="工商银行",
                market_cap_tier=5  # Invalid tier
            )


class TestIndustryConfig:
    """Test IndustryConfig model."""

    def test_valid_industry_config(self, sample_industry_config: IndustryConfig) -> None:
        """Test creating valid industry config."""
        assert sample_industry_config.industry_name == "银行"
        assert len(sample_industry_config.leaders) == 2
        assert sample_industry_config.default_top_n == 3
        assert sample_industry_config.is_enabled is True

    def test_empty_leaders_list(self) -> None:
        """Test that empty leaders list raises validation error."""
        with pytest.raises(ValidationError):
            IndustryConfig(
                industry_name="测试行业",
                leaders=[],  # Empty leaders list
                default_top_n=3
            )

    def test_invalid_default_top_n(self) -> None:
        """Test that invalid default top N raises validation error."""
        with pytest.raises(ValidationError):
            IndustryConfig(
                industry_name="测试行业",
                leaders=[
                    IndustryLeader(symbol="TEST.SH", name="测试", market_cap_tier=1)
                ],
                default_top_n=0  # Invalid top N
            )