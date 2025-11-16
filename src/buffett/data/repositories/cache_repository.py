"""
Cache repository implementation.

This module implements the ICacheRepository interface for managing cache operations
with support for different storage backends.
"""

from typing import Any, Optional, List, Dict
import time
import json
from datetime import datetime, timedelta

from ...interfaces.repositories import ICacheRepository
from ...exceptions.data import CacheError


class MemoryCacheRepository(ICacheRepository):
    """In-memory cache repository implementation."""

    def __init__(self):
        """Initialize in-memory cache."""
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'clears': 0
        }

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            if key not in self._cache:
                self._stats['misses'] += 1
                return None

            cache_item = self._cache[key]

            # Check if item has expired
            if cache_item.get('expires_at') and datetime.now() > cache_item['expires_at']:
                del self._cache[key]
                self._stats['misses'] += 1
                return None

            self._stats['hits'] += 1
            return cache_item['value']

        except Exception as e:
            raise CacheError(f"Failed to get cache key '{key}': {str(e)}")

    async def set(self, key: str, value: Any, ttl_seconds: int = None) -> None:
        """Set value in cache with optional TTL."""
        try:
            expires_at = None
            if ttl_seconds is not None:
                expires_at = datetime.now() + timedelta(seconds=ttl_seconds)

            self._cache[key] = {
                'value': value,
                'created_at': datetime.now(),
                'expires_at': expires_at,
                'ttl_seconds': ttl_seconds
            }

            self._stats['sets'] += 1

        except Exception as e:
            raise CacheError(f"Failed to set cache key '{key}': {str(e)}")

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            if key in self._cache:
                del self._cache[key]
                self._stats['deletes'] += 1
                return True
            return False

        except Exception as e:
            raise CacheError(f"Failed to delete cache key '{key}': {str(e)}")

    async def clear(self) -> None:
        """Clear all cache entries."""
        try:
            self._cache.clear()
            self._stats['clears'] += 1

        except Exception as e:
            raise CacheError(f"Failed to clear cache: {str(e)}")

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            if key not in self._cache:
                return False

            # Check if item has expired
            cache_item = self._cache[key]
            if cache_item.get('expires_at') and datetime.now() > cache_item['expires_at']:
                del self._cache[key]
                return False

            return True

        except Exception as e:
            raise CacheError(f"Failed to check cache key '{key}': {str(e)}")

    async def get_ttl(self, key: str) -> Optional[int]:
        """Get remaining TTL for a key."""
        try:
            if key not in self._cache:
                return None

            cache_item = self._cache[key]

            if not cache_item.get('expires_at'):
                return None

            remaining_time = cache_item['expires_at'] - datetime.now()
            if remaining_time.total_seconds() <= 0:
                del self._cache[key]
                return None

            return int(remaining_time.total_seconds())

        except Exception as e:
            raise CacheError(f"Failed to get TTL for cache key '{key}': {str(e)}")

    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment a numeric value in cache."""
        try:
            current_value = await self.get(key)
            if current_value is None:
                new_value = amount
            else:
                if not isinstance(current_value, (int, float)):
                    raise CacheError(f"Cannot increment non-numeric value for key '{key}'")
                new_value = current_value + amount

            await self.set(key, new_value)
            return new_value

        except Exception as e:
            raise CacheError(f"Failed to increment cache key '{key}': {str(e)}")

    async def get_keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching a pattern."""
        try:
            import fnmatch

            matching_keys = []
            for key in self._cache.keys():
                if fnmatch.fnmatch(key, pattern):
                    # Check if key has expired
                    if await self.exists(key):
                        matching_keys.append(key)

            return matching_keys

        except Exception as e:
            raise CacheError(f"Failed to get keys matching pattern '{pattern}': {str(e)}")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self._stats['hits'] + self._stats['misses']
        hit_rate = (self._stats['hits'] / total_requests * 100) if total_requests > 0 else 0

        return {
            **self._stats,
            'total_keys': len(self._cache),
            'hit_rate_percent': round(hit_rate, 2),
            'memory_usage_kb': self._estimate_memory_usage()
        }

    def _estimate_memory_usage(self) -> int:
        """Estimate memory usage in KB."""
        try:
            total_size = 0
            for key, value in self._cache.items():
                # Rough estimation of memory usage
                total_size += len(str(key)) * 2  # Unicode characters
                total_size += len(json.dumps(value, default=str)) * 2
            return total_size // 1024  # Convert to KB
        except Exception:
            return 0

    async def cleanup_expired(self) -> int:
        """Clean up expired entries."""
        try:
            expired_keys = []
            now = datetime.now()

            for key, cache_item in self._cache.items():
                if cache_item.get('expires_at') and now > cache_item['expires_at']:
                    expired_keys.append(key)

            for key in expired_keys:
                del self._cache[key]

            return len(expired_keys)

        except Exception as e:
            raise CacheError(f"Failed to cleanup expired cache entries: {str(e)}")


class FileCacheRepository(ICacheRepository):
    """File-based cache repository implementation."""

    def __init__(self, cache_file: str = "cache.json"):
        """Initialize file-based cache."""
        self.cache_file = cache_file
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._load_cache()

    def _load_cache(self) -> None:
        """Load cache from file."""
        try:
            import os
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self._cache = json.load(f)
        except Exception:
            self._cache = {}

    def _save_cache(self) -> None:
        """Save cache to file."""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self._cache, f, indent=2, default=str)
        except Exception as e:
            raise CacheError(f"Failed to save cache to file: {str(e)}")

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            if key not in self._cache:
                return None

            cache_item = self._cache[key]

            # Parse dates
            if cache_item.get('expires_at'):
                cache_item['expires_at'] = datetime.fromisoformat(cache_item['expires_at'])

            # Check if item has expired
            if cache_item.get('expires_at') and datetime.now() > cache_item['expires_at']:
                del self._cache[key]
                self._save_cache()
                return None

            return cache_item['value']

        except Exception as e:
            raise CacheError(f"Failed to get cache key '{key}': {str(e)}")

    async def set(self, key: str, value: Any, ttl_seconds: int = None) -> None:
        """Set value in cache with optional TTL."""
        try:
            expires_at = None
            if ttl_seconds is not None:
                expires_at = datetime.now() + timedelta(seconds=ttl_seconds)

            self._cache[key] = {
                'value': value,
                'created_at': datetime.now().isoformat(),
                'expires_at': expires_at.isoformat() if expires_at else None,
                'ttl_seconds': ttl_seconds
            }

            self._save_cache()

        except Exception as e:
            raise CacheError(f"Failed to set cache key '{key}': {str(e)}")

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            if key in self._cache:
                del self._cache[key]
                self._save_cache()
                return True
            return False

        except Exception as e:
            raise CacheError(f"Failed to delete cache key '{key}': {str(e)}")

    async def clear(self) -> None:
        """Clear all cache entries."""
        try:
            self._cache.clear()
            self._save_cache()

        except Exception as e:
            raise CacheError(f"Failed to clear cache: {str(e)}")

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        value = await self.get(key)
        return value is not None

    async def get_ttl(self, key: str) -> Optional[int]:
        """Get remaining TTL for a key."""
        try:
            if key not in self._cache:
                return None

            cache_item = self._cache[key]

            if not cache_item.get('expires_at'):
                return None

            expires_at = datetime.fromisoformat(cache_item['expires_at'])
            remaining_time = expires_at - datetime.now()

            if remaining_time.total_seconds() <= 0:
                del self._cache[key]
                self._save_cache()
                return None

            return int(remaining_time.total_seconds())

        except Exception as e:
            raise CacheError(f"Failed to get TTL for cache key '{key}': {str(e)}")

    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment a numeric value in cache."""
        try:
            current_value = await self.get(key)
            if current_value is None:
                new_value = amount
            else:
                if not isinstance(current_value, (int, float)):
                    raise CacheError(f"Cannot increment non-numeric value for key '{key}'")
                new_value = current_value + amount

            await self.set(key, new_value)
            return new_value

        except Exception as e:
            raise CacheError(f"Failed to increment cache key '{key}': {str(e)}")

    async def get_keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching a pattern."""
        try:
            import fnmatch

            matching_keys = []
            for key in self._cache.keys():
                if fnmatch.fnmatch(key, pattern):
                    if await self.exists(key):
                        matching_keys.append(key)

            return matching_keys

        except Exception as e:
            raise CacheError(f"Failed to get keys matching pattern '{pattern}': {str(e)}")