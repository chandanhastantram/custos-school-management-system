"""
CUSTOS Cache Decorators

Decorators for easy caching of async functions.

RULES:
- Never cache permission-dependent data
- Never cache student-private data
- Always include tenant_id in key
"""

import functools
import hashlib
import json
import logging
from typing import Callable, Optional, Union
from datetime import timedelta

from app.core.cache.backend import get_cache
from app.core.cache.keys import CacheTTL

logger = logging.getLogger(__name__)


def cached(
    key_builder: Callable[..., str],
    ttl: Union[int, timedelta] = CacheTTL.MEDIUM,
    skip_if: Optional[Callable[..., bool]] = None,
):
    """
    Cache decorator for async functions.
    
    Args:
        key_builder: Function that takes same args as decorated function
                     and returns cache key string
        ttl: Time to live in seconds or timedelta
        skip_if: Optional function that returns True to skip caching
        
    Example:
        @cached(
            key_builder=lambda tenant_id, class_id: f"class:{tenant_id}:{class_id}",
            ttl=3600
        )
        async def get_class(tenant_id: UUID, class_id: UUID):
            ...
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Check if we should skip caching
            if skip_if and skip_if(*args, **kwargs):
                return await func(*args, **kwargs)
            
            # Build cache key
            try:
                cache_key = key_builder(*args, **kwargs)
            except Exception as e:
                logger.debug(f"Failed to build cache key: {e}")
                return await func(*args, **kwargs)
            
            # Try to get from cache
            cache = await get_cache()
            cached_value = await cache.get(cache_key)
            
            if cached_value is not None:
                logger.debug(f"Cache HIT: {cache_key}")
                return cached_value
            
            logger.debug(f"Cache MISS: {cache_key}")
            
            # Call the function
            result = await func(*args, **kwargs)
            
            # Cache the result
            if result is not None:
                await cache.set(cache_key, result, ttl)
            
            return result
        
        # Attach cache control methods
        wrapper.cache_key_builder = key_builder
        wrapper.invalidate = lambda *args, **kwargs: _invalidate(
            key_builder(*args, **kwargs)
        )
        
        return wrapper
    
    return decorator


async def _invalidate(cache_key: str) -> bool:
    """Invalidate a specific cache key."""
    cache = await get_cache()
    return await cache.delete(cache_key)


def cached_property_async(ttl: Union[int, timedelta] = CacheTTL.MEDIUM):
    """
    Cache decorator for instance methods that need self.tenant_id.
    
    Uses hash of all arguments for cache key.
    
    Example:
        @cached_property_async(ttl=3600)
        async def get_data(self, class_id: UUID):
            ...
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            # Build key from function name and args
            tenant_id = getattr(self, 'tenant_id', 'unknown')
            args_hash = hashlib.md5(
                json.dumps([str(a) for a in args] + [f"{k}={v}" for k, v in sorted(kwargs.items())], sort_keys=True).encode()
            ).hexdigest()[:16]
            
            cache_key = f"custos:{tenant_id}:{func.__module__}.{func.__name__}:{args_hash}"
            
            # Try cache
            cache = await get_cache()
            cached_value = await cache.get(cache_key)
            
            if cached_value is not None:
                return cached_value
            
            # Call function
            result = await func(self, *args, **kwargs)
            
            # Cache result
            if result is not None:
                await cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    
    return decorator


class CacheAside:
    """
    Cache-aside pattern helper for manual cache management.
    
    Use when you need more control than decorators provide.
    
    Example:
        cache_aside = CacheAside()
        
        # Try cache first
        data = await cache_aside.get(key)
        if data is None:
            data = await fetch_from_db()
            await cache_aside.set(key, data, ttl=3600)
    """
    
    def __init__(self):
        self._cache = None
    
    async def _get_cache(self):
        if self._cache is None:
            self._cache = await get_cache()
        return self._cache
    
    async def get(self, key: str):
        """Get from cache."""
        cache = await self._get_cache()
        return await cache.get(key)
    
    async def set(self, key: str, value, ttl: int = CacheTTL.MEDIUM):
        """Set in cache."""
        cache = await self._get_cache()
        return await cache.set(key, value, ttl)
    
    async def delete(self, key: str):
        """Delete from cache."""
        cache = await self._get_cache()
        return await cache.delete(key)
    
    async def get_or_set(
        self,
        key: str,
        factory: Callable,
        ttl: int = CacheTTL.MEDIUM,
    ):
        """
        Get from cache or call factory and cache result.
        
        Args:
            key: Cache key
            factory: Async function to call if cache miss
            ttl: Time to live
        """
        value = await self.get(key)
        if value is not None:
            return value
        
        value = await factory()
        if value is not None:
            await self.set(key, value, ttl)
        
        return value
