"""Tests for caching mechanisms in data fetching strategies."""

import pytest
import pandas as pd
import tempfile
import shutil
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from src.buffett.strategies.data_fetch_strategies import AKShareStrategy, LocalCache
from src.buffett.data.repositories.stock_repository import StockRepository
from src.buffett.models.stock import Stock


class TestLocalCache:
    """Test cases for LocalCache implementation."""

    def setup_method(self):
        """Set up test cache with temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache = LocalCache(cache_dir=self.temp_dir, default_ttl_hours=1)

    def teardown_method(self):
        """Clean up temporary directory."""
        if self.temp_dir and hasattr(self.temp_dir, '__exit__'):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cache_stock_info(self):
        """Test caching and retrieving stock info."""
        symbol = "000001"
        stock_data = {
            "symbol": symbol,
            "name": "平安银行",
            "market_cap": 228000000000,
            "current_price": 10.50
        }

        # Cache the data
        self.cache.cache_stock_info(symbol, stock_data)

        # Retrieve from cache
        cached_data = self.cache.get_cached_stock_info(symbol)
        assert cached_data is not None
        assert cached_data["symbol"] == symbol
        assert cached_data["market_cap"] == 228000000000

    def test_cache_dividends(self):
        """Test caching and retrieving dividend data."""
        symbol = "000001.SH"
        dividend_data = pd.DataFrame([
            {
                "symbol": symbol,
                "year": 2024,
                "cash_dividend": 2.0,
                "stock_dividend": 0.0,
                "dividend_rate": 2.0
            },
            {
                "symbol": symbol,
                "year": 2023,
                "cash_dividend": 1.8,
                "stock_dividend": 0.0,
                "dividend_rate": 1.8
            }
        ])

        # Cache the data
        self.cache.cache_dividends(symbol, dividend_data)

        # Retrieve from cache
        cached_data = self.cache.get_cached_dividends(symbol)
        assert cached_data is not None
        assert len(cached_data) == 2
        assert cached_data.iloc[0]["year"] == 2024
        assert cached_data.iloc[0]["cash_dividend"] == 2.0

    def test_cache_miss(self):
        """Test cache miss scenarios."""
        # Test non-existent stock info
        result = self.cache.get_cached_stock_info("999999")
        assert result is None

        # Test non-existent dividend data
        result = self.cache.get_cached_dividends("999999.SH")
        assert result is None

    def test_cache_invalidation(self):
        """Test cache invalidation with TTL."""
        symbol = "000001"
        stock_data = {"symbol": symbol, "name": "Test Stock"}

        # Create cache with very short TTL for testing
        short_cache = LocalCache(
            cache_dir=self.temp_dir,
            default_ttl_hours=0.0001  # Very short TTL (0.36 seconds)
        )

        # Cache the data
        short_cache.cache_stock_info(symbol, stock_data)

        # Should be available immediately
        result = short_cache.get_cached_stock_info(symbol)
        assert result is not None

        # Wait for expiration
        import time
        time.sleep(1)

        # Should be expired now
        result = short_cache.get_cached_stock_info(symbol)
        assert result is None

    def test_cache_stats(self):
        """Test cache statistics."""
        stats = self.cache.get_cache_stats()
        assert "cache_dir" in stats
        assert "dividend_files" in stats
        assert "stock_files" in stats
        assert "total_size_mb" in stats

        # Cache some data
        self.cache.cache_stock_info("000001", {"name": "Test"})
        self.cache.cache_dividends("000002", pd.DataFrame())

        # Check updated stats
        stats = self.cache.get_cache_stats()
        assert stats["stock_files"] >= 1
        assert stats["dividend_files"] >= 1


class TestAKShareStrategyCaching:
    """Test cases for AKShare strategy caching."""

    @pytest.fixture
    def mock_strategy(self):
        """Create a mock AKShare strategy with caching."""
        temp_dir = tempfile.mkdtemp()
        cache = LocalCache(cache_dir=temp_dir, default_ttl_hours=24)
        strategy = AKShareStrategy(enable_cache=True)
        strategy.cache = cache
        yield strategy
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_fetch_stock_basic_info_with_cache(self, mock_strategy):
        """Test fetching stock basic info with caching."""
        symbol = "000001"
        stock_data = {
            "总市值": "228019538826.5",
            "流通市值": "200000000000",
            "最新": "10.50",
            "股票代码": "000001",
            "股票简称": "平安银行"
        }

        # Mock the API call
        with patch('akshare.stock_individual_info_em') as mock_api:
            mock_df = pd.DataFrame([
                {"item": "总市值", "value": "228019538826.5"},
                {"item": "流通市值", "value": "200000000000"},
                {"item": "最新", "value": "10.50"},
                {"item": "股票代码", "value": "000001"},
                {"item": "股票简称", "value": "平安银行"}
            ])
            mock_api.return_value = mock_df

            # First call should hit API
            result1 = await mock_strategy.fetch_stock_basic_info(symbol)
            assert result1 is not None
            assert result1["market_cap"] == 228019538826.5
            assert mock_api.call_count == 1

            # Second call should use cache
            result2 = await mock_strategy.fetch_stock_basic_info(symbol)
            assert result2 is not None
            assert result2["market_cap"] == 228019538826.5
            # API call count should not increase
            assert mock_api.call_count == 1

    @pytest.mark.asyncio
    async def test_fetch_dividend_data_with_cache(self, mock_strategy):
        """Test fetching dividend data with caching."""
        symbol = "000001.SH"

        # Mock the dividend data
        mock_dividend_data = pd.DataFrame([
            {
                "公告日期": "2024-04-25",
                "派息": "2.0",
                "送股": "0",
                "转增": "0",
                "股权登记日": "2024-04-30",
                "除权除息日": "2024-05-06"
            }
        ])

        # Mock the API call
        with patch('akshare.stock_history_dividend_detail') as mock_api:
            mock_api.return_value = mock_dividend_data

            # First call should hit API
            result1 = await mock_strategy.fetch_dividend_data(symbol)
            assert not result1.empty
            assert len(result1) == 1
            assert mock_api.call_count == 1

            # Second call should use cache
            result2 = await mock_strategy.fetch_dividend_data(symbol)
            assert not result2.empty
            assert len(result2) == 1
            # API call count should not increase
            assert mock_api.call_count == 1


class TestStockRepositoryCaching:
    """Test cases for StockRepository caching integration."""

    @pytest.fixture
    def mock_strategy(self):
        """Create a mock AKShare strategy."""
        strategy = Mock()
        strategy.fetch_stock_basic_info = AsyncMock()
        return strategy

    @pytest.fixture
    def stock_repo_with_strategy(self, mock_strategy):
        """Create StockRepository with shared strategy."""
        test_data = pd.DataFrame([
            {'symbol': '000001.SH', 'name': '平安银行', 'code': '000001', 'market': 'SH'},
            {'symbol': '000002.SZ', 'name': '万科A', 'code': '000002', 'market': 'SZ'},
        ])
        return StockRepository(data_source=test_data, strategy=mock_strategy)

    @pytest.mark.asyncio
    async def test_get_stock_info_uses_shared_strategy(self, stock_repo_with_strategy, mock_strategy):
        """Test that get_stock_info uses the shared strategy for caching."""
        symbol = "000001.SH"

        # Mock strategy response
        mock_strategy.fetch_stock_basic_info.return_value = {
            "market_cap": 228000000000,
            "current_price": 10.50,
            "industry": "银行"
        }

        # Get stock info
        stock_info = await stock_repo_with_strategy.get_stock_info(symbol)

        assert stock_info is not None
        assert stock_info.market_cap == 228000000000

        # Verify strategy was called with correct code
        mock_strategy.fetch_stock_basic_info.assert_called_once_with("000001")

    @pytest.mark.asyncio
    async def test_get_stock_info_handles_missing_strategy(self):
        """Test that get_stock_info works without strategy (fallback)."""
        test_data = pd.DataFrame([
            {'symbol': '000001.SH', 'name': '平安银行', 'code': '000001', 'market': 'SH'},
        ])
        repo = StockRepository(data_source=test_data)  # No strategy provided

        # Mock the strategy creation
        with patch('src.buffett.strategies.data_fetch_strategies.AKShareStrategy') as mock_strategy_class:
            mock_strategy = Mock()
            mock_strategy.fetch_stock_basic_info = AsyncMock(return_value=None)
            mock_strategy_class.return_value = mock_strategy

            # Get stock info
            stock_info = await repo.get_stock_info("000001.SH")

            # Should create strategy on-demand
            mock_strategy_class.assert_called_once()
            mock_strategy.fetch_stock_basic_info.assert_called_once_with("000001")

    @pytest.mark.asyncio
    async def test_market_cap_data_integration(self, stock_repo_with_strategy, mock_strategy):
        """Test market cap data integration in stock info."""
        symbol = "000001.SH"

        # Mock strategy response with market cap
        mock_strategy.fetch_stock_basic_info.return_value = {
            "market_cap": 150000000000,  # 150亿
            "current_price": 8.75,
            "industry": "房地产"
        }

        # Get stock info
        stock_info = await stock_repo_with_strategy.get_stock_info(symbol)

        assert stock_info is not None
        assert stock_info.market_cap == 150000000000  # Should be populated from strategy


class TestCachingErrorHandling:
    """Test cases for caching error handling."""

    @pytest.mark.asyncio
    async def test_cache_corruption_handling(self):
        """Test handling of corrupted cache files."""
        temp_dir = tempfile.mkdtemp()

        try:
            # Create corrupted cache file
            cache = LocalCache(cache_dir=temp_dir, default_ttl_hours=1)
            symbol = "000001"

            # Write corrupted data
            cache_path = cache._get_cache_path("stocks", symbol)
            with open(cache_path, 'w') as f:
                f.write("corrupted json data")

            # Should handle corruption gracefully
            result = cache.get_cached_stock_info(symbol)
            assert result is None

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_api_failure_fallback(self):
        """Test fallback behavior when API fails."""
        temp_dir = tempfile.mkdtemp()

        try:
            cache = LocalCache(cache_dir=temp_dir, default_ttl_hours=24)
            strategy = AKShareStrategy(enable_cache=True)
            strategy.cache = cache

            # Mock API failure
            with patch('akshare.stock_individual_info_em') as mock_api:
                mock_api.side_effect = Exception("API Error")

                # Should handle error gracefully
                result = await strategy.fetch_stock_basic_info("000001")
                assert result is None

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


# Integration test for the complete caching workflow
@pytest.mark.asyncio
async def test_complete_caching_workflow():
    """Test complete caching workflow from strategy to repository."""
    temp_dir = tempfile.mkdtemp()

    try:
        # Set up components
        cache = LocalCache(cache_dir=temp_dir, default_ttl_hours=24)
        strategy = AKShareStrategy(enable_cache=True)
        strategy.cache = cache

        test_data = pd.DataFrame([
            {'symbol': '000001.SH', 'name': '平安银行', 'code': '000001', 'market': 'SH'},
        ])
        repo = StockRepository(data_source=test_data, strategy=strategy)

        # Mock API response
        stock_info_data = {
            "总市值": "228019538826.5",
            "流通市值": "200000000000",
            "最新": "10.50",
            "行业": "银行"
        }

        with patch('akshare.stock_individual_info_em') as mock_api:
            mock_df = pd.DataFrame([
                {"item": key, "value": value}
                for key, value in stock_info_data.items()
            ])
            mock_api.return_value = mock_df

            # First call - should hit API and cache
            stock_info1 = await repo.get_stock_info("000001.SH")
            assert stock_info1 is not None
            assert stock_info1.market_cap == 228019538826.5
            assert mock_api.call_count == 1

            # Second call - should use cache
            stock_info2 = await repo.get_stock_info("000001.SH")
            assert stock_info2 is not None
            assert stock_info2.market_cap == 228019538826.5
            # API call count should not increase
            assert mock_api.call_count == 1

            # Verify data consistency
            assert stock_info1.symbol == stock_info2.symbol
            assert stock_info1.market_cap == stock_info2.market_cap

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)