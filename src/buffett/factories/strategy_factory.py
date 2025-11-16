"""
Strategy factory implementation using the Factory pattern.

This module provides a centralized way to create strategy instances
for different data sources and screening approaches.
"""

from typing import Dict, Any, Optional, List, Union
from enum import Enum

from ..strategies.data_fetch_strategies import (
    DataFetchStrategy,
    AKShareStrategy,
    MockStrategy,
    MultiSourceStrategy,
    DataFetchContext
)
from ..strategies.optimized_data_fetch import (
    OptimizedDataFetcher,
    OptimizedAKShareStrategy
)
from ..exceptions.config import ConfigurationError


class DataSourceType(str, Enum):
    """Data source type enumeration."""
    AKSHARE = "akshare"
    OPTIMIZED_AKSHARE = "optimized_akshare"
    MOCK = "mock"
    MULTI_SOURCE = "multi_source"


class StrategyFactory:
    """Factory for creating strategy instances."""

    def __init__(self):
        """Initialize factory with default configurations."""
        self._default_configs = {
            DataSourceType.AKSHARE: {
                "timeout": 30,
                "proxy": None
            },
            DataSourceType.OPTIMIZED_AKSHARE: {
                "timeout": 30,
                "proxy": None,
                "cache_ttl_hours": 24,
                "enable_cache": True
            },
            DataSourceType.MOCK: {},
            DataSourceType.MULTI_SOURCE: {
                "strategies": ["optimized_akshare", "mock"],  # Priority order - 优先使用优化版本
                "enable_fallback": True
            }
        }

    def create_data_fetch_strategy(
        self,
        data_source_type: Union[DataSourceType, str],
        config: Optional[Dict[str, Any]] = None
    ) -> DataFetchStrategy:
        """
        Create a data fetch strategy.

        Args:
            data_source_type: Type of data source to use
            config: Configuration for the strategy

        Returns:
            Data fetch strategy instance

        Raises:
            ConfigurationError: If data source type is unsupported
        """
        # Convert string to enum if needed
        if isinstance(data_source_type, str):
            try:
                data_source_type = DataSourceType(data_source_type.lower())
            except ValueError:
                raise ConfigurationError(f"Unsupported data source type: {data_source_type}")

        # Merge with default config
        final_config = self._default_configs.get(data_source_type, {}).copy()
        if config:
            final_config.update(config)

        # Create strategy based on type
        if data_source_type == DataSourceType.AKSHARE:
            return self._create_akshare_strategy(final_config)
        elif data_source_type == DataSourceType.OPTIMIZED_AKSHARE:
            return self._create_optimized_akshare_strategy(final_config)
        elif data_source_type == DataSourceType.MOCK:
            return self._create_mock_strategy(final_config)
        elif data_source_type == DataSourceType.MULTI_SOURCE:
            return self._create_multi_source_strategy(final_config)
        else:
            raise ConfigurationError(f"Data source type {data_source_type} not implemented")

    def create_data_fetch_context(
        self,
        data_source_type: Union[DataSourceType, str] = DataSourceType.OPTIMIZED_AKSHARE,
        config: Optional[Dict[str, Any]] = None
    ) -> DataFetchContext:
        """Create a data fetch context with strategy."""
        strategy = self.create_data_fetch_strategy(data_source_type, config)
        return DataFetchContext(strategy)

    def _create_akshare_strategy(self, config: Dict[str, Any]) -> AKShareStrategy:
        """Create AKShare strategy instance."""
        timeout = config.get("timeout", 30)
        proxy = config.get("proxy")
        return AKShareStrategy(proxy=proxy, timeout=timeout)

    def _create_mock_strategy(self, config: Dict[str, Any]) -> MockStrategy:
        """Create mock strategy instance."""
        return MockStrategy()

    def _create_optimized_akshare_strategy(self, config: Dict[str, Any]) -> OptimizedAKShareStrategy:
        """Create optimized AKShare strategy instance."""
        timeout = config.get("timeout", 30)
        proxy = config.get("proxy")
        cache_ttl_hours = config.get("cache_ttl_hours", 24)
        enable_cache = config.get("enable_cache", True)

        return OptimizedAKShareStrategy(
            proxy=proxy,
            timeout=timeout,
            cache_ttl_hours=cache_ttl_hours,
            enable_cache=enable_cache
        )

    def _create_multi_source_strategy(self, config: Dict[str, Any]) -> MultiSourceStrategy:
        """Create multi-source strategy instance."""
        strategy_names = config.get("strategies", ["optimized_akshare", "mock"])
        enable_fallback = config.get("enable_fallback", True)

        # Create individual strategies
        strategies = []
        for strategy_name in strategy_names:
            strategy = self.create_data_fetch_strategy(strategy_name)
            strategies.append(strategy)

        return MultiSourceStrategy(strategies)

    def set_default_config(self, data_source_type: DataSourceType, config: Dict[str, Any]) -> None:
        """Set default configuration for a data source type."""
        self._default_configs[data_source_type] = config

    def get_default_config(self, data_source_type: DataSourceType) -> Dict[str, Any]:
        """Get default configuration for a data source type."""
        return self._default_configs.get(data_source_type, {}).copy()

    @classmethod
    def create_with_environment_config(cls) -> 'StrategyFactory':
        """Create factory configured from environment variables."""
        factory = cls()

        # Configure based on environment variables
        import os

        # Example: BUFFETT_DATA_SOURCE=akshare
        data_source = os.getenv('BUFFETT_DATA_SOURCE', 'akshare')

        # AKShare configuration
        akshare_config = {}
        if os.getenv('BUFFETT_AKSHARE_PROXY'):
            akshare_config['proxy'] = os.getenv('BUFFETT_AKSHARE_PROXY')
        if os.getenv('BUFFETT_AKSHARE_TIMEOUT'):
            akshare_config['timeout'] = int(os.getenv('BUFFETT_AKSHARE_TIMEOUT'))

        factory.set_default_config(DataSourceType.AKSHARE, akshare_config)

        return factory

    @classmethod
    def create_for_testing(cls) -> 'StrategyFactory':
        """Create factory optimized for testing."""
        factory = cls()

        # Use mock data source for testing
        test_config = {}
        factory.set_default_config(DataSourceType.MOCK, test_config)

        return factory

    @classmethod
    def create_for_development(cls) -> 'StrategyFactory':
        """Create factory optimized for development."""
        factory = cls()

        # Use mock with AKShare fallback for development
        dev_config = {
            "strategies": ["mock", "akshare"],
            "enable_fallback": True
        }
        factory.set_default_config(DataSourceType.MULTI_SOURCE, dev_config)

        return factory

    @classmethod
    def create_for_production(cls) -> 'StrategyFactory':
        """Create factory optimized for production."""
        factory = cls()

        # Use optimized AKShare with mock fallback for production
        prod_config = {
            "strategies": ["optimized_akshare", "mock"],
            "enable_fallback": True
        }
        factory.set_default_config(DataSourceType.MULTI_SOURCE, prod_config)

        return factory

    def get_available_data_sources(self) -> List[str]:
        """Get list of available data source types."""
        return [source_type.value for source_type in DataSourceType]

    def is_data_source_available(self, data_source_type: Union[DataSourceType, str]) -> bool:
        """Check if a data source type is supported."""
        if isinstance(data_source_type, str):
            try:
                data_source_type = DataSourceType(data_source_type.lower())
            except ValueError:
                return False
        return data_source_type in DataSourceType


# Global factory instance
default_strategy_factory = StrategyFactory()


def create_data_fetch_strategy(
    data_source_type: Union[DataSourceType, str],
    config: Optional[Dict[str, Any]] = None
) -> DataFetchStrategy:
    """Convenience function to create data fetch strategies using default factory."""
    return default_strategy_factory.create_data_fetch_strategy(data_source_type, config)


def create_data_fetch_context(
    data_source_type: Union[DataSourceType, str] = DataSourceType.OPTIMIZED_AKSHARE,
    config: Optional[Dict[str, Any]] = None
) -> DataFetchContext:
    """Convenience function to create data fetch contexts using default factory."""
    return default_strategy_factory.create_data_fetch_context(data_source_type, config)