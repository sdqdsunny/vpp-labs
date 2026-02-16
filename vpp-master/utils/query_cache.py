"""
Query Result Caching Utility

Provides caching mechanisms for frequently executed database queries
to improve performance and reduce database load.
"""

from functools import wraps
from datetime import datetime, timedelta
from typing import Any, Callable, Optional, Dict
import hashlib
import json
from utils.logger import setup_logger

logger = setup_logger(__name__)


class QueryCache:
    """
    Simple in-memory query result cache with TTL support.
    
    Caches query results with configurable time-to-live (TTL).
    Automatically invalidates expired entries.
    """
    
    def __init__(self, default_ttl_seconds: int = 300):
        """
        Initialize query cache.
        
        Args:
            default_ttl_seconds: Default time-to-live for cached entries in seconds
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl_seconds
        self.hits = 0
        self.misses = 0
    
    def _generate_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """
        Generate cache key from function name and arguments.
        
        Args:
            func_name: Name of the cached function
            args: Positional arguments
            kwargs: Keyword arguments
            
        Returns:
            Cache key string
        """
        # Create a hashable representation of arguments
        # Skip the first argument if it's a Session object (database session)
        filtered_args = []
        for arg in args:
            # Skip Session objects as they're not hashable and change each time
            if hasattr(arg, '__class__') and 'Session' not in arg.__class__.__name__:
                filtered_args.append(str(arg))
        
        key_data = {
            'func': func_name,
            'args': str(tuple(filtered_args)),
            'kwargs': str(sorted(kwargs.items()))
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache if it exists and hasn't expired.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found or expired
        """
        if key not in self.cache:
            self.misses += 1
            return None
        
        entry = self.cache[key]
        if datetime.utcnow() > entry['expires_at']:
            # Entry has expired, remove it
            del self.cache[key]
            self.misses += 1
            return None
        
        self.hits += 1
        return entry['value']
    
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """
        Set value in cache with optional TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time-to-live in seconds (uses default if not specified)
        """
        ttl = ttl_seconds or self.default_ttl
        self.cache[key] = {
            'value': value,
            'expires_at': datetime.utcnow() + timedelta(seconds=ttl),
            'created_at': datetime.utcnow()
        }
    
    def invalidate(self, key: str) -> None:
        """
        Invalidate a cache entry.
        
        Args:
            key: Cache key to invalidate
        """
        if key in self.cache:
            del self.cache[key]
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        return {
            'hits': self.hits,
            'misses': self.misses,
            'total_requests': total,
            'hit_rate': hit_rate,
            'cached_entries': len(self.cache)
        }


# Global cache instance
_query_cache = QueryCache(default_ttl_seconds=300)


def cached_query(ttl_seconds: Optional[int] = None):
    """
    Decorator for caching query results.
    
    Usage:
        @cached_query(ttl_seconds=300)
        def get_devices_by_type(device_type):
            # Query implementation
            pass
    
    Args:
        ttl_seconds: Time-to-live for cached results in seconds
        
    Returns:
        Decorated function with caching
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            key = _query_cache._generate_key(func.__name__, args, kwargs)
            
            # Try to get from cache
            cached_value = _query_cache.get(key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_value
            
            # Execute function and cache result
            logger.debug(f"Cache miss for {func.__name__}, executing query")
            result = func(*args, **kwargs)
            _query_cache.set(key, result, ttl_seconds)
            
            return result
        
        return wrapper
    
    return decorator


def invalidate_cache_for(func_name: str, args: tuple = (), kwargs: dict = None) -> None:
    """
    Invalidate cache entry for a specific function call.
    
    Args:
        func_name: Name of the cached function
        args: Positional arguments used in the call
        kwargs: Keyword arguments used in the call
    """
    if kwargs is None:
        kwargs = {}
    
    key = _query_cache._generate_key(func_name, args, kwargs)
    _query_cache.invalidate(key)
    logger.debug(f"Invalidated cache for {func_name}")


def clear_all_cache() -> None:
    """Clear all cached query results."""
    _query_cache.clear()
    logger.info("Cleared all query cache")


def get_cache_stats() -> Dict[str, Any]:
    """
    Get query cache statistics.
    
    Returns:
        Dictionary with cache statistics
    """
    return _query_cache.get_stats()
