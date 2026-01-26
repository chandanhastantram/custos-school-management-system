"""
CUSTOS Redis Module

Redis client for caching, session storage, and pub/sub.
"""

from typing import Any, Optional
import json
from contextlib import asynccontextmanager
from redis.asyncio import Redis, ConnectionPool
from redis.asyncio.client import PubSub

from app.core.config import settings


# Connection pool for better performance
pool: Optional[ConnectionPool] = None

# Redis client instance
redis_client: Optional[Redis] = None


async def init_redis() -> Redis:
    """Initialize Redis connection pool and client."""
    global pool, redis_client
    
    pool = ConnectionPool.from_url(
        settings.redis_url,
        max_connections=50,
        decode_responses=True,
    )
    redis_client = Redis(connection_pool=pool)
    
    # Test connection
    await redis_client.ping()
    
    return redis_client


async def close_redis() -> None:
    """Close Redis connections."""
    global redis_client, pool
    
    if redis_client:
        await redis_client.close()
        redis_client = None
    
    if pool:
        await pool.disconnect()
        pool = None


def get_redis() -> Redis:
    """Get Redis client instance."""
    if redis_client is None:
        raise RuntimeError("Redis not initialized. Call init_redis() first.")
    return redis_client


class CacheManager:
    """
    Cache manager for application-level caching.
    
    Provides typed caching with automatic serialization.
    """
    
    def __init__(self, redis: Redis, prefix: str = "custos"):
        self._redis = redis
        self._prefix = prefix
    
    def _make_key(self, key: str) -> str:
        """Create prefixed cache key."""
        return f"{self._prefix}:{key}"
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        full_key = self._make_key(key)
        value = await self._redis.get(full_key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time-to-live in seconds (default from settings)
        """
        full_key = self._make_key(key)
        ttl = ttl or settings.redis_cache_ttl
        
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        elif not isinstance(value, str):
            value = json.dumps(value)
        
        return await self._redis.setex(full_key, ttl, value)
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        full_key = self._make_key(key)
        return await self._redis.delete(full_key) > 0
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        full_pattern = self._make_key(pattern)
        keys = await self._redis.keys(full_pattern)
        if keys:
            return await self._redis.delete(*keys)
        return 0
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        full_key = self._make_key(key)
        return await self._redis.exists(full_key) > 0
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment counter value."""
        full_key = self._make_key(key)
        return await self._redis.incrby(full_key, amount)
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration on key."""
        full_key = self._make_key(key)
        return await self._redis.expire(full_key, ttl)
    
    async def ttl(self, key: str) -> int:
        """Get remaining TTL for key."""
        full_key = self._make_key(key)
        return await self._redis.ttl(full_key)


class TenantCacheManager(CacheManager):
    """
    Tenant-aware cache manager.
    
    Automatically includes tenant_id in cache keys for isolation.
    """
    
    def __init__(self, redis: Redis, tenant_id: str, prefix: str = "custos"):
        super().__init__(redis, prefix)
        self._tenant_id = tenant_id
    
    def _make_key(self, key: str) -> str:
        """Create tenant-prefixed cache key."""
        return f"{self._prefix}:tenant:{self._tenant_id}:{key}"
    
    async def clear_tenant_cache(self) -> int:
        """Clear all cache entries for this tenant."""
        pattern = f"{self._prefix}:tenant:{self._tenant_id}:*"
        keys = await self._redis.keys(pattern)
        if keys:
            return await self._redis.delete(*keys)
        return 0


class RateLimiter:
    """
    Redis-based rate limiter using sliding window algorithm.
    """
    
    def __init__(self, redis: Redis, prefix: str = "ratelimit"):
        self._redis = redis
        self._prefix = prefix
    
    async def is_allowed(
        self,
        identifier: str,
        limit: int,
        window_seconds: int = 60,
    ) -> tuple[bool, int]:
        """
        Check if request is allowed under rate limit.
        
        Args:
            identifier: Unique identifier (e.g., user_id, IP)
            limit: Maximum requests allowed
            window_seconds: Time window in seconds
        
        Returns:
            Tuple of (is_allowed, remaining_requests)
        """
        key = f"{self._prefix}:{identifier}"
        
        current = await self._redis.incr(key)
        
        if current == 1:
            await self._redis.expire(key, window_seconds)
        
        remaining = max(0, limit - current)
        
        return current <= limit, remaining
    
    async def get_remaining(self, identifier: str, limit: int) -> int:
        """Get remaining requests for identifier."""
        key = f"{self._prefix}:{identifier}"
        current = await self._redis.get(key)
        if current is None:
            return limit
        return max(0, limit - int(current))
    
    async def reset(self, identifier: str) -> bool:
        """Reset rate limit for identifier."""
        key = f"{self._prefix}:{identifier}"
        return await self._redis.delete(key) > 0


class SessionStore:
    """
    Redis-based session storage for JWT refresh tokens.
    """
    
    def __init__(self, redis: Redis, prefix: str = "session"):
        self._redis = redis
        self._prefix = prefix
    
    async def create_session(
        self,
        user_id: str,
        refresh_token: str,
        expires_in: int,
        metadata: Optional[dict] = None,
    ) -> bool:
        """Create new session."""
        key = f"{self._prefix}:{user_id}:{refresh_token}"
        data = {
            "user_id": user_id,
            "refresh_token": refresh_token,
            "metadata": metadata or {},
        }
        return await self._redis.setex(key, expires_in, json.dumps(data))
    
    async def validate_session(
        self,
        user_id: str,
        refresh_token: str,
    ) -> Optional[dict]:
        """Validate session and return metadata."""
        key = f"{self._prefix}:{user_id}:{refresh_token}"
        data = await self._redis.get(key)
        if data:
            return json.loads(data)
        return None
    
    async def revoke_session(
        self,
        user_id: str,
        refresh_token: str,
    ) -> bool:
        """Revoke specific session."""
        key = f"{self._prefix}:{user_id}:{refresh_token}"
        return await self._redis.delete(key) > 0
    
    async def revoke_all_sessions(self, user_id: str) -> int:
        """Revoke all sessions for user."""
        pattern = f"{self._prefix}:{user_id}:*"
        keys = await self._redis.keys(pattern)
        if keys:
            return await self._redis.delete(*keys)
        return 0
    
    async def get_active_sessions(self, user_id: str) -> list[dict]:
        """Get all active sessions for user."""
        pattern = f"{self._prefix}:{user_id}:*"
        keys = await self._redis.keys(pattern)
        sessions = []
        for key in keys:
            data = await self._redis.get(key)
            if data:
                sessions.append(json.loads(data))
        return sessions


# Factory functions
def get_cache_manager() -> CacheManager:
    """Get cache manager instance."""
    return CacheManager(get_redis())


def get_tenant_cache_manager(tenant_id: str) -> TenantCacheManager:
    """Get tenant cache manager instance."""
    return TenantCacheManager(get_redis(), tenant_id)


def get_rate_limiter() -> RateLimiter:
    """Get rate limiter instance."""
    return RateLimiter(get_redis())


def get_session_store() -> SessionStore:
    """Get session store instance."""
    return SessionStore(get_redis())
