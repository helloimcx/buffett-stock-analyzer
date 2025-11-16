"""
Repository factory implementation using the Factory pattern.

This module provides a centralized way to create repository instances
with different configurations and data sources.
"""

from typing import Dict, Any, Optional, Union
import pandas as pd
from enum import Enum

from ..interfaces.repositories import IStockRepository, IDividendRepository, IPriceRepository, ICacheRepository
from ..data.repositories.stock_repository import StockRepository
from ..data.repositories.dividend_repository import DividendRepository
from ..data.repositories.price_repository import PriceRepository
from ..data.repositories.cache_repository import MemoryCacheRepository, FileCacheRepository
from ..exceptions.config import ConfigurationError


class RepositoryType(str, Enum):
    """Repository type enumeration."""
    STOCK = "stock"
    DIVIDEND = "dividend"
    PRICE = "price"
    CACHE_MEMORY = "cache_memory"
    CACHE_FILE = "cache_file"


class CacheBackend(str, Enum):
    """Cache backend enumeration."""
    MEMORY = "memory"
    FILE = "file"


class RepositoryFactory:
    """Factory for creating repository instances."""

    def __init__(self):
        """Initialize factory with default configurations."""
        self._default_configs = {
            RepositoryType.STOCK: {},
            RepositoryType.DIVIDEND: {},
            RepositoryType.PRICE: {},
            RepositoryType.CACHE_MEMORY: {},
            RepositoryType.CACHE_FILE: {"cache_file": "cache.json"}
        }

    def create_repository(
        self,
        repository_type: Union[RepositoryType, str],
        config: Optional[Dict[str, Any]] = None,
        strategy: Optional[Any] = None
    ) -> Union[IStockRepository, IDividendRepository, IPriceRepository, ICacheRepository]:
        """
        Create a repository instance.

        Args:
            repository_type: Type of repository to create
            config: Configuration for the repository
            strategy: Optional shared strategy for caching

        Returns:
            Repository instance

        Raises:
            ConfigurationError: If repository type is unsupported or config is invalid
        """
        # Convert string to enum if needed
        if isinstance(repository_type, str):
            try:
                repository_type = RepositoryType(repository_type.lower())
            except ValueError:
                raise ConfigurationError(f"Unsupported repository type: {repository_type}")

        # Merge with default config
        final_config = self._default_configs.get(repository_type, {}).copy()
        if config:
            final_config.update(config)

        # Create repository based on type
        if repository_type == RepositoryType.STOCK:
            return self._create_stock_repository(final_config, strategy)
        elif repository_type == RepositoryType.DIVIDEND:
            return self._create_dividend_repository(final_config)
        elif repository_type == RepositoryType.PRICE:
            return self._create_price_repository(final_config)
        elif repository_type == RepositoryType.CACHE_MEMORY:
            return self._create_memory_cache_repository(final_config)
        elif repository_type == RepositoryType.CACHE_FILE:
            return self._create_file_cache_repository(final_config)
        else:
            raise ConfigurationError(f"Repository type {repository_type} not implemented")

    def create_stock_repository(
        self,
        data_source: Optional[pd.DataFrame] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> IStockRepository:
        """Create a stock repository."""
        final_config = config or {}
        final_config["data_source"] = data_source
        return self._create_stock_repository(final_config)

    def create_dividend_repository(
        self,
        data_source: Optional[pd.DataFrame] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> IDividendRepository:
        """Create a dividend repository."""
        final_config = config or {}
        final_config["data_source"] = data_source
        return self._create_dividend_repository(final_config)

    def create_cache_repository(
        self,
        backend: Union[CacheBackend, str] = CacheBackend.MEMORY,
        config: Optional[Dict[str, Any]] = None
    ) -> ICacheRepository:
        """Create a cache repository."""
        # Convert string to enum if needed
        if isinstance(backend, str):
            try:
                backend = CacheBackend(backend.lower())
            except ValueError:
                raise ConfigurationError(f"Unsupported cache backend: {backend}")

        final_config = config or {}

        if backend == CacheBackend.MEMORY:
            return self._create_memory_cache_repository(final_config)
        elif backend == CacheBackend.FILE:
            return self._create_file_cache_repository(final_config)
        else:
            raise ConfigurationError(f"Cache backend {backend} not implemented")

    def _create_stock_repository(self, config: Dict[str, Any], strategy: Optional[Any] = None) -> IStockRepository:
        """Create stock repository instance."""
        data_source = config.get("data_source")
        return StockRepository(data_source=data_source, strategy=strategy)

    def _create_dividend_repository(self, config: Dict[str, Any]) -> IDividendRepository:
        """Create dividend repository instance."""
        data_source = config.get("data_source")
        return DividendRepository(data_source=data_source)

    def _create_price_repository(self, config: Dict[str, Any]) -> IPriceRepository:
        """Create price repository instance."""
        data_source = config.get("data_source")
        return PriceRepository(data_source=data_source)

    def _create_memory_cache_repository(self, config: Dict[str, Any]) -> ICacheRepository:
        """Create memory cache repository instance."""
        return MemoryCacheRepository()

    def _create_file_cache_repository(self, config: Dict[str, Any]) -> ICacheRepository:
        """Create file cache repository instance."""
        cache_file = config.get("cache_file", "cache.json")
        return FileCacheRepository(cache_file=cache_file)

    def set_default_config(self, repository_type: RepositoryType, config: Dict[str, Any]) -> None:
        """Set default configuration for a repository type."""
        self._default_configs[repository_type] = config

    def get_default_config(self, repository_type: RepositoryType) -> Dict[str, Any]:
        """Get default configuration for a repository type."""
        return self._default_configs.get(repository_type, {}).copy()

    def register_custom_repository(
        self,
        repository_type: str,
        factory_func: callable
    ) -> None:
        """
        Register a custom repository factory function.

        Args:
            repository_type: Name of the custom repository type
            factory_func: Function that creates the repository instance
        """
        # This would be extended for more advanced factory patterns
        pass

    @classmethod
    def create_with_environment_config(cls) -> 'RepositoryFactory':
        """Create factory configured from environment variables."""
        factory = cls()

        # Configure based on environment variables
        import os

        # Example: BUFFETT_CACHE_BACKEND=file
        cache_backend = os.getenv('BUFFETT_CACHE_BACKEND', 'memory')
        cache_config = {}
        if cache_backend == 'file':
            cache_config['cache_file'] = os.getenv('BUFFETT_CACHE_FILE', 'cache.json')

        factory.set_default_config(
            RepositoryType.CACHE_FILE,
            cache_config
        )

        return factory

    @classmethod
    def create_for_testing(cls) -> 'RepositoryFactory':
        """Create factory optimized for testing."""
        factory = cls()

        # Use in-memory repositories for testing
        test_config = {
            "data_source": pd.DataFrame(),  # Empty data for testing
        }

        factory.set_default_config(RepositoryType.STOCK, test_config)
        factory.set_default_config(RepositoryType.DIVIDEND, test_config)
        factory.set_default_config(RepositoryType.PRICE, test_config)

        return factory

    @classmethod
    def create_for_production(cls) -> 'RepositoryFactory':
        """Create factory optimized for production."""
        factory = cls()

        # Production configurations
        production_config = {
            "enable_caching": True,
            "batch_size": 1000,
        }

        factory.set_default_config(RepositoryType.STOCK, production_config)
        factory.set_default_config(RepositoryType.DIVIDEND, production_config)
        factory.set_default_config(RepositoryType.PRICE, production_config)

        return factory


# Global factory instance
default_repository_factory = RepositoryFactory()


def create_repository(
    repository_type: Union[RepositoryType, str],
    config: Optional[Dict[str, Any]] = None
) -> Union[IStockRepository, IDividendRepository, IPriceRepository, ICacheRepository]:
    """Convenience function to create repositories using default factory."""
    return default_repository_factory.create_repository(repository_type, config)