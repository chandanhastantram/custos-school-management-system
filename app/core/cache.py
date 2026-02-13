"""
Redis Cache Configuration and Utilities

Provides caching layer for frequently accessed data.
"""

import json
import pickle
from typing import Any, Optional, Callable
from functools import wraps
import redis.asyncio as redis
from app.core.config import settings


class RedisCache:
    """Redis cache manager."""
    
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        self.enabled = settings.redis_enabled
    
    async def connect(self):
        """Connect to Redis."""
        if not self.enabled:
            return
        
        self.redis = await redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=False,
        )
    
    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis:
            await self.redis.close()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.redis:
            return None
        
        try:
            value = await self.redis.get(key)
            if value:
                return pickle.loads(value)
        except Exception:
            return None
        
        return None
    
    async def set(
        self,
        key: str,
        value: Any,
        expire: int = 300,  # 5 minutes default
    ) -> bool:
        """Set value in cache."""
        if not self.redis:
            return False
        
        try:
            serialized = pickle.dumps(value)
            await self.redis.set(key, serialized, ex=expire)
            return True
        except Exception:
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self.redis:
            return False
        
        try:
            await self.redis.delete(key)
            return True
        except Exception:
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        if not self.redis:
            return 0
        
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                return await self.redis.delete(*keys)
        except Exception:
            return 0
        
        return 0
    
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        if not self.redis:
            return False
        
        try:
            return await self.redis.exists(key) > 0
        except Exception:
            return False


# Global cache instance
cache = RedisCache()


def cached(
    key_prefix: str,
    expire: int = 300,
    key_builder: Optional[Callable] = None,
):
    """
    Decorator to cache function results.
    
    Args:
        key_prefix: Prefix for cache key
        expire: Expiration time in seconds
        key_builder: Optional function to build cache key from args
    
    Example:
        @cached("user", expire=600)
        async def get_user(user_id: str):
            # Expensive operation
            return user
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache key
            if key_builder:
                cache_key = f"{key_prefix}:{key_builder(*args, **kwargs)}"
            else:
                # Default: use first argument as key
                cache_key = f"{key_prefix}:{args[0] if args else 'default'}"
            
            # Try to get from cache
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Store in cache
            await cache.set(cache_key, result, expire)
            
            return result
        
        return wrapper
    return decorator


def cache_key(*args, **kwargs) -> str:
    """Build cache key from arguments."""
    parts = [str(arg) for arg in args]
    parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
    return ":".join(parts)


async def invalidate_cache(pattern: str):
    """Invalidate all cache keys matching pattern."""
    await cache.delete_pattern(pattern)
