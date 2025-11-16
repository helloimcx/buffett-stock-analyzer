"""Tests for design pattern implementations."""

import pytest
import pandas as pd
from datetime import date, datetime

from src.buffett.strategies.data_fetch_strategies import (
    DataFetchStrategy,
    MockStrategy,
    DataFetchContext
)
from src.buffett.factories.repository_factory import (
    RepositoryFactory,
    RepositoryType,
    CacheBackend
)
from src.buffett.factories.strategy_factory import (
    StrategyFactory,
    DataSourceType
)
from src.buffett.data.repositories.stock_repository import StockRepository
from src.buffett.data.repositories.cache_repository import MemoryCacheRepository


class TestDataFetchStrategy:
    """Test cases for data fetch strategies."""

    @pytest.mark.asyncio
    async def test_mock_strategy(self):
        """Test mock data fetch strategy."""
        strategy = MockStrategy()

        # Test stock list fetching
        stocks = await strategy.fetch_all_stocks()
        assert len(stocks) > 0
        assert 'symbol' in stocks.columns
        assert 'name' in stocks.columns

        # Test individual stock info
        info = await strategy.fetch_stock_basic_info('000001.SZ')
        assert info is not None
        assert info['symbol'] == '000001.SZ'

        # Test dividend data
        dividends = await strategy.fetch_dividend_data('000001.SZ')
        assert not dividends.empty

        # Test price data
        price_data = await strategy.fetch_price_data(
            '000001.SZ',
            date(2024, 1, 1),
            date(2024, 1, 31)
        )
        assert not price_data.empty
        assert 'symbol' in price_data.columns

        # Test connection
        assert await strategy.test_connection()

        # Test strategy name
        assert strategy.get_strategy_name() == "Mock"

    def test_data_fetch_context(self):
        """Test data fetch context."""
        strategy = MockStrategy()
        context = DataFetchContext(strategy)

        assert context.get_current_strategy_name() == "Mock"

        # Test strategy switching
        new_strategy = MockStrategy()
        context.set_strategy(new_strategy)
        assert context.get_current_strategy_name() == "Mock"


class TestRepositoryFactory:
    """Test cases for repository factory."""

    def setup_method(self):
        """Set up test factory."""
        self.factory = RepositoryFactory()

    def test_create_stock_repository(self):
        """Test creating stock repository."""
        repo = self.factory.create_repository(RepositoryType.STOCK)
        assert isinstance(repo, StockRepository)

    def test_create_stock_repository_with_data(self):
        """Test creating stock repository with data."""
        test_data = pd.DataFrame([
            {'symbol': '000001.SZ', 'name': 'Test Stock', 'market': 'SZ'}
        ])
        repo = self.factory.create_repository(RepositoryType.STOCK, {"data_source": test_data})
        assert isinstance(repo, StockRepository)

    def test_create_memory_cache_repository(self):
        """Test creating memory cache repository."""
        repo = self.factory.create_repository(RepositoryType.CACHE_MEMORY)
        assert isinstance(repo, MemoryCacheRepository)

    def test_create_repository_from_string(self):
        """Test creating repository from string type."""
        repo = self.factory.create_repository("stock")
        assert isinstance(repo, StockRepository)

    def test_unsupported_repository_type(self):
        """Test creating unsupported repository type."""
        with pytest.raises(Exception):  # Should raise ConfigurationError
            self.factory.create_repository("unsupported")

    def test_create_for_testing(self):
        """Test creating factory for testing."""
        test_factory = RepositoryFactory.create_for_testing()
        assert isinstance(test_factory, RepositoryFactory)

    def test_create_for_production(self):
        """Test creating factory for production."""
        prod_factory = RepositoryFactory.create_for_production()
        assert isinstance(prod_factory, RepositoryFactory)

    def test_set_default_config(self):
        """Test setting default configuration."""
        test_config = {"test_key": "test_value"}
        self.factory.set_default_config(RepositoryType.STOCK, test_config)

        retrieved_config = self.factory.get_default_config(RepositoryType.STOCK)
        assert retrieved_config["test_key"] == "test_value"


class TestStrategyFactory:
    """Test cases for strategy factory."""

    def setup_method(self):
        """Set up test factory."""
        self.factory = StrategyFactory()

    def test_create_mock_strategy(self):
        """Test creating mock strategy."""
        strategy = self.factory.create_data_fetch_strategy(DataSourceType.MOCK)
        assert isinstance(strategy, MockStrategy)

    def test_create_strategy_from_string(self):
        """Test creating strategy from string type."""
        strategy = self.factory.create_data_fetch_strategy("mock")
        assert isinstance(strategy, MockStrategy)

    def test_create_data_fetch_context(self):
        """Test creating data fetch context."""
        context = self.factory.create_data_fetch_context(DataSourceType.MOCK)
        assert context is not None

    def test_unsupported_data_source(self):
        """Test creating unsupported data source."""
        with pytest.raises(Exception):  # Should raise ConfigurationError
            self.factory.create_data_fetch_strategy("unsupported")

    def test_get_available_data_sources(self):
        """Test getting available data sources."""
        sources = self.factory.get_available_data_sources()
        assert "mock" in sources
        assert "akshare" in sources
        assert "multi_source" in sources

    def test_is_data_source_available(self):
        """Test checking data source availability."""
        assert self.factory.is_data_source_available("mock")
        assert self.factory.is_data_source_available("akshare")
        assert not self.factory.is_data_source_available("unsupported")

    def test_create_for_testing(self):
        """Test creating factory for testing."""
        test_factory = StrategyFactory.create_for_testing()
        assert isinstance(test_factory, StrategyFactory)

    def test_create_for_development(self):
        """Test creating factory for development."""
        dev_factory = StrategyFactory.create_for_development()
        assert isinstance(dev_factory, StrategyFactory)

    def test_create_for_production(self):
        """Test creating factory for production."""
        prod_factory = StrategyFactory.create_for_production()
        assert isinstance(prod_factory, StrategyFactory)

    def test_set_default_config(self):
        """Test setting default configuration."""
        test_config = {"test_key": "test_value"}
        self.factory.set_default_config(DataSourceType.MOCK, test_config)

        retrieved_config = self.factory.get_default_config(DataSourceType.MOCK)
        assert retrieved_config["test_key"] == "test_value"


class TestIntegrationDesignPatterns:
    """Integration tests for design patterns."""

    @pytest.mark.asyncio
    async def test_factory_strategy_integration(self):
        """Test integration between factory and strategy patterns."""
        # Create strategy using factory
        strategy_factory = StrategyFactory.create_for_testing()
        strategy = strategy_factory.create_data_fetch_strategy(DataSourceType.MOCK)

        # Create context with strategy
        context = DataFetchContext(strategy)

        # Use strategy through context
        stocks = await context.fetch_all_stocks()
        assert len(stocks) > 0

    @pytest.mark.asyncio
    async def test_repository_strategy_integration(self):
        """Test integration between repository and strategy patterns."""
        # Create repository using factory
        repo_factory = RepositoryFactory.create_for_testing()
        stock_repo = repo_factory.create_repository(RepositoryType.STOCK)

        # Create mock data and load into repository
        strategy = MockStrategy()
        mock_stocks = await strategy.fetch_all_stocks()
        stock_repo.load_from_dataframe(mock_stocks)

        # Verify data was loaded
        stocks = await stock_repo.get_all_stocks()
        assert len(stocks) > 0

    def test_convenience_functions(self):
        """Test convenience functions."""
        # Test repository convenience function
        from src.buffett.factories.repository_factory import create_repository
        repo = create_repository("cache_memory")
        assert isinstance(repo, MemoryCacheRepository)

        # Test strategy convenience function
        from src.buffett.factories.strategy_factory import create_data_fetch_strategy
        strategy = create_data_fetch_strategy("mock")
        assert isinstance(strategy, MockStrategy)