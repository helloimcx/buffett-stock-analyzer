"""pytest configuration and shared fixtures."""

import pytest
import pandas as pd
from typing import Generator, Dict, Any
from unittest.mock import Mock

# Import only what we need for basic testing
from src.buffett.models.stock import Stock, StockInfo, DividendData, PriceData


@pytest.fixture
def sample_stock() -> Stock:
    """Create a sample stock for testing."""
    return Stock(
        symbol="000001.SZ",
        name="平安银行",
        market="SZ"
    )


@pytest.fixture
def sample_stock_info() -> StockInfo:
    """Create a sample stock info for testing."""
    return StockInfo(
        symbol="000001.SZ",
        name="平安银行",
        industry="银行",
        market_cap=1000000000000.0,
        current_price=10.50,
        pe_ratio=8.5,
        pb_ratio=0.8,
        dividend_yield=4.2
    )


@pytest.fixture
def sample_dividend_data() -> list[DividendData]:
    """Create sample dividend data for testing."""
    return [
        DividendData(
            symbol="000001.SZ",
            year=2024,
            cash_dividend=2.0,
            is_annual_report=True
        ),
        DividendData(
            symbol="000001.SZ",
            year=2023,
            cash_dividend=1.8,
            is_annual_report=True
        ),
        DividendData(
            symbol="000001.SZ",
            year=2022,
            cash_dividend=1.5,
            is_annual_report=True
        ),
    ]


@pytest.fixture
def sample_price_data() -> pd.DataFrame:
    """Create sample price data for testing."""
    import datetime

    dates = pd.date_range(
        start=datetime.datetime(2024, 1, 1),
        periods=100,
        freq='D'
    )

    # Generate synthetic price data
    base_price = 10.0
    prices = []
    for i, date in enumerate(dates):
        # Simple random walk
        if i == 0:
            close = base_price
        else:
            change = (hash(str(date)) % 21 - 10) / 1000  # -0.01 to 0.01
            close = max(prices[-1]["close"] * (1 + change), 1.0)

        high = close * 1.02
        low = close * 0.98
        open_price = close * 1.01

        prices.append({
            "date": date,
            "open": open_price,
            "high": high,
            "low": low,
            "close": close,
            "volume": 1000000 + (hash(str(date)) % 500000),
            "amount": close * 1000000
        })

    return pd.DataFrame(prices).set_index("date")




@pytest.fixture
def mock_data_fetcher() -> Mock:
    """Create a mock data fetcher for testing."""
    fetcher = Mock()

    # Configure mock methods
    fetcher.get_all_stock_list.return_value = pd.DataFrame([
        {"symbol": "000001.SZ", "name": "平安银行", "code": "000001"},
        {"symbol": "000002.SZ", "name": "万科A", "code": "000002"},
        {"symbol": "600036.SH", "name": "招商银行", "code": "600036"},
    ])

    fetcher.get_stock_dividend_data.return_value = pd.DataFrame([
        {"分红年度": 2024, "现金分红": 2.0, "是否年报": True},
        {"分红年度": 2023, "现金分红": 1.8, "是否年报": True},
        {"分红年度": 2022, "现金分红": 1.5, "是否年报": True},
    ])

    fetcher.get_stock_price_data.return_value = pd.DataFrame(
        {"close": [10.5, 10.3, 10.7, 11.0]},
        index=pd.date_range("2024-01-01", periods=4)
    )

    fetcher.get_stock_basic_info.return_value = {
        "总市值": "1000亿",
        "行业": "银行",
        "最新价": 10.5
    }

    return fetcher


@pytest.fixture
def test_config_overrides() -> Dict[str, Any]:
    """Test configuration overrides."""
    return {
        "BUFFETT_SCREENING_MIN_DIVIDEND_YIELD": 3.5,
        "BUFFETT_SCREENING_INDUSTRY_LEADER_PRIORITY": True,
        "BUFFETT_DATA_CACHE_DURATION_HOURS": 1,
        "BUFFETT_LOG_LEVEL": "DEBUG",
    }


@pytest.fixture
def disable_external_api_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    """Disable external API calls during testing."""
    # Mock any external API calls to prevent real network requests
    import akshare
    monkeypatch.setattr(akshare, "stock_info_a_code_name", Mock(return_value=pd.DataFrame()))
    monkeypatch.setattr(akshare, "stock_dividend_cninfo", Mock(return_value=pd.DataFrame()))
    monkeypatch.setattr(akshare, "stock_zh_a_hist", Mock(return_value=pd.DataFrame()))


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Setup common test environment."""
    # Set test environment variables
    monkeypatch.setenv("BUFFETT_ENVIRONMENT", "test")
    monkeypatch.setenv("BUFFETT_DEBUG", "true")

    # Disable logging during tests unless explicitly needed
    import logging
    logging.getLogger().setLevel(logging.CRITICAL)


@pytest.fixture
def temp_cache_dir(tmp_path_factory) -> str:
    """Create a temporary cache directory for testing."""
    return str(tmp_path_factory.mktemp("cache"))