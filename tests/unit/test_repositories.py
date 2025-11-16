"""Tests for repository implementations."""

import pytest
import pandas as pd
from datetime import datetime, date

from src.buffett.data.repositories.stock_repository import StockRepository
from src.buffett.data.repositories.dividend_repository import DividendRepository
from src.buffett.data.repositories.cache_repository import MemoryCacheRepository
from src.buffett.models.stock import Stock, DividendData


class TestStockRepository:
    """Test cases for StockRepository."""

    def setup_method(self):
        """Set up test repository."""
        self.test_data = pd.DataFrame([
            {'symbol': '000001.SZ', 'name': '平安银行', 'code': '000001', 'market': 'SZ'},
            {'symbol': '000002.SZ', 'name': '万科A', 'code': '000002', 'market': 'SZ'},
            {'symbol': '600036.SH', 'name': '招商银行', 'code': '600036', 'market': 'SH'},
        ])
        self.repo = StockRepository(self.test_data)

    @pytest.mark.asyncio
    async def test_get_all_stocks(self):
        """Test getting all stocks."""
        stocks = await self.repo.get_all_stocks()
        assert len(stocks) == 3
        assert stocks[0].symbol == '000001.SZ'
        assert stocks[0].name == '平安银行'

    @pytest.mark.asyncio
    async def test_get_stock_by_symbol(self):
        """Test getting stock by symbol."""
        stock = await self.repo.get_stock_by_symbol('000001.SZ')
        assert stock is not None
        assert stock.symbol == '000001.SZ'
        assert stock.name == '平安银行'
        assert stock.code == '000001'

    @pytest.mark.asyncio
    async def test_get_nonexistent_stock(self):
        """Test getting non-existent stock."""
        stock = await self.repo.get_stock_by_symbol('999999.SZ')
        assert stock is None

    @pytest.mark.asyncio
    async def test_get_stocks_by_market(self):
        """Test getting stocks by market."""
        sz_stocks = await self.repo.get_stocks_by_market('SZ')
        assert len(sz_stocks) == 2
        assert all(stock.market == 'SZ' for stock in sz_stocks)

    @pytest.mark.asyncio
    async def test_save_stock(self):
        """Test saving a stock."""
        new_stock = Stock(symbol='600000.SH', name='浦发银行')
        await self.repo.save_stock(new_stock)

        # Verify it was saved
        retrieved = await self.repo.get_stock_by_symbol('600000.SH')
        assert retrieved is not None
        assert retrieved.name == '浦发银行'

    @pytest.mark.asyncio
    async def test_save_stocks(self):
        """Test saving multiple stocks."""
        stocks = [
            Stock(symbol='600000.SH', name='浦发银行'),
            Stock(symbol='000001.SH', name='上证指数'),
        ]
        await self.repo.save_stocks(stocks)

        # Verify they were saved
        for stock in stocks:
            retrieved = await self.repo.get_stock_by_symbol(stock.symbol)
            assert retrieved is not None

    def test_cache_stats(self):
        """Test cache statistics."""
        stats = self.repo.get_cache_stats()
        assert 'cached_items' in stats
        assert 'total_stocks' in stats
        assert stats['total_stocks'] == 3


class TestDividendRepository:
    """Test cases for DividendRepository."""

    def setup_method(self):
        """Set up test repository."""
        self.test_data = pd.DataFrame([
            {
                'symbol': '000001.SZ',
                'year': 2024,
                'cash_dividend': 2.0,
                'stock_dividend': 0.0,
                'is_annual_report': True
            },
            {
                'symbol': '000001.SZ',
                'year': 2023,
                'cash_dividend': 1.8,
                'stock_dividend': 0.0,
                'is_annual_report': True
            },
            {
                'symbol': '000002.SZ',
                'year': 2024,
                'cash_dividend': 1.5,
                'stock_dividend': 0.0,
                'is_annual_report': True
            },
        ])
        self.repo = DividendRepository(self.test_data)

    @pytest.mark.asyncio
    async def test_get_dividend_history(self):
        """Test getting dividend history."""
        dividends = await self.repo.get_dividend_history('000001.SZ')
        assert len(dividends) == 2
        assert dividends[0].year == 2024  # Most recent first
        assert dividends[0].cash_dividend == 2.0

    @pytest.mark.asyncio
    async def test_get_dividend_history_with_year_filter(self):
        """Test getting dividend history with year filter."""
        dividends = await self.repo.get_dividend_history('000001.SZ', start_year=2024)
        assert len(dividends) == 1
        assert dividends[0].year == 2024

    @pytest.mark.asyncio
    async def test_save_dividend_data(self):
        """Test saving dividend data."""
        dividend = DividendData(
            symbol='000001.SZ',
            year=2022,
            cash_dividend=1.5,
            is_annual_report=True
        )
        await self.repo.save_dividend_data(dividend)

        # Verify it was saved
        dividends = await self.repo.get_dividend_history('000001.SZ')
        assert len(dividends) == 3
        years = [d.year for d in dividends]
        assert 2022 in years

    @pytest.mark.asyncio
    async def test_get_latest_dividend_yield(self):
        """Test getting latest dividend yield."""
        yield_amount = await self.repo.get_latest_dividend_yield('000001.SZ')
        assert yield_amount == 2.0

    @pytest.mark.asyncio
    async def test_get_latest_dividend_yield_nonexistent(self):
        """Test getting latest dividend yield for non-existent stock."""
        yield_amount = await self.repo.get_latest_dividend_yield('999999.SZ')
        assert yield_amount is None

    @pytest.mark.asyncio
    async def test_get_stocks_with_consistent_dividends(self):
        """Test getting stocks with consistent dividends."""
        consistent_stocks = await self.repo.get_stocks_with_consistent_dividends(min_years=2)
        assert '000001.SZ' in consistent_stocks

    def test_dividend_statistics(self):
        """Test dividend statistics calculation."""
        stats = self.repo.get_dividend_statistics('000001.SZ')
        assert stats['annual_dividends'] == 2
        assert stats['avg_cash_dividend'] == 1.9
        assert stats['consistency_years'] == 2


class TestMemoryCacheRepository:
    """Test cases for MemoryCacheRepository."""

    def setup_method(self):
        """Set up test cache."""
        self.cache = MemoryCacheRepository()

    @pytest.mark.asyncio
    async def test_set_and_get(self):
        """Test setting and getting values."""
        await self.cache.set('test_key', 'test_value')
        value = await self.cache.get('test_key')
        assert value == 'test_value'

    @pytest.mark.asyncio
    async def test_get_nonexistent(self):
        """Test getting non-existent key."""
        value = await self.cache.get('nonexistent')
        assert value is None

    @pytest.mark.asyncio
    async def test_set_with_ttl(self):
        """Test setting value with TTL."""
        await self.cache.set('ttl_key', 'ttl_value', ttl_seconds=1)
        value = await self.cache.get('ttl_key')
        assert value == 'ttl_value'

        # Wait for expiration (would need time.sleep in real test)
        # For now, just test the TTL setting logic

    @pytest.mark.asyncio
    async def test_delete(self):
        """Test deleting keys."""
        await self.cache.set('delete_key', 'delete_value')
        assert await self.cache.exists('delete_key')

        deleted = await self.cache.delete('delete_key')
        assert deleted is True
        assert not await self.cache.exists('delete_key')

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self):
        """Test deleting non-existent key."""
        deleted = await self.cache.delete('nonexistent')
        assert deleted is False

    @pytest.mark.asyncio
    async def test_clear(self):
        """Test clearing cache."""
        await self.cache.set('key1', 'value1')
        await self.cache.set('key2', 'value2')

        await self.cache.clear()

        assert not await self.cache.exists('key1')
        assert not await self.cache.exists('key2')

    @pytest.mark.asyncio
    async def test_exists(self):
        """Test checking if key exists."""
        assert not await self.cache.exists('test_key')

        await self.cache.set('test_key', 'test_value')
        assert await self.cache.exists('test_key')

    @pytest.mark.asyncio
    async def test_increment(self):
        """Test incrementing numeric values."""
        # Increment non-existent key
        result = await self.cache.increment('counter', 5)
        assert result == 5

        # Increment existing key
        result = await self.cache.increment('counter', 3)
        assert result == 8

    @pytest.mark.asyncio
    async def test_get_keys(self):
        """Test getting keys with pattern matching."""
        await self.cache.set('test:1', 'value1')
        await self.cache.set('test:2', 'value2')
        await self.cache.set('other:1', 'value3')

        keys = await self.cache.get_keys('test:*')
        assert len(keys) == 2
        assert all(key.startswith('test:') for key in keys)

    def test_stats(self):
        """Test cache statistics."""
        stats = self.cache.get_stats()
        assert 'hits' in stats
        assert 'misses' in stats
        assert 'sets' in stats
        assert 'total_keys' in stats
        assert 'hit_rate_percent' in stats