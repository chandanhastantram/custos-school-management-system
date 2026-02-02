"""
CUSTOS Cache Backend

Redis abstraction with graceful fallback.

RULES:
- Never cache permission-dependent data
- Never cache student-private data
- Cache only read-heavy, deterministic data
- All keys must include tenant_id
"""

import json
import logging
from typing import Optional, Any, Union
from datetime import timedelta

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

from app.core.config import settings

logger = logging.getLogger(__name__)


class CacheBackend:
    """
    Redis cache backend with graceful degradation.
    
    If Redis is unavailable, operations silently fail.
    The system continues to work, just slower.
    """
    
    def __init__(self):
        self._client: Optional[Any] = None
        self._connected = False
        self._connection_attempted = False
    
    async def connect(self) -> bool:
        """
        Connect to Redis.
        
        Returns True if connected, False otherwise.
        Never raises - fail-soft design.
        """
        if not REDIS_AVAILABLE:
            logger.warning("Redis library not installed - caching disabled")
            return False
        
        if self._connection_attempted:
            return self._connected
        
        self._connection_attempted = True
        
        try:
            redis_url = getattr(settings, 'redis_url', None)
            if not redis_url:
                redis_url = "redis://localhost:6379/0"
            
            self._client = redis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_timeout=5.0,
                socket_connect_timeout=5.0,
            )
            
            # Test connection
            await self._client.ping()
            self._connected = True
            logger.info("Redis cache connected successfully")
            return True
            
        except Exception as e:
            logger.warning(f"Redis connection failed: {e} - caching disabled")
            self._client = None
            self._connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from Redis."""
        if self._client:
            try:
                await self._client.close()
            except Exception:
                pass
            self._client = None
            self._connected = False
    
    @property
    def is_connected(self) -> bool:
        """Check if Redis is connected."""
        return self._connected and self._client is not None
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Returns None if not found or Redis unavailable.
        Never raises.
        """
        if not self.is_connected:
            return None
        
        try:
            value = await self._client.get(key)
            if value is None:
                return None
            
            return json.loads(value)
            
        except Exception as e:
            logger.debug(f"Cache get failed for {key}: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Union[int, timedelta] = 3600,
    ) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache (must be JSON-serializable)
            ttl: Time to live in seconds or timedelta
            
        Returns True if cached, False otherwise.
        Never raises.
        """
        if not self.is_connected:
            return False
        
        try:
            if isinstance(ttl, timedelta):
                ttl = int(ttl.total_seconds())
            
            serialized = json.dumps(value, default=str)
            await self._client.setex(key, ttl, serialized)
            return True
            
        except Exception as e:
            logger.debug(f"Cache set failed for {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete key from cache.
        
        Returns True if deleted, False otherwise.
        Never raises.
        """
        if not self.is_connected:
            return False
        
        try:
            await self._client.delete(key)
            return True
            
        except Exception as e:
            logger.debug(f"Cache delete failed for {key}: {e}")
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching pattern.
        
        Returns count of deleted keys.
        Never raises.
        """
        if not self.is_connected:
            return 0
        
        try:
            keys = []
            async for key in self._client.scan_iter(match=pattern, count=100):
                keys.append(key)
            
            if keys:
                await self._client.delete(*keys)
            
            return len(keys)
            
        except Exception as e:
            logger.debug(f"Cache delete_pattern failed for {pattern}: {e}")
            return 0
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self.is_connected:
            return False
        
        try:
            return await self._client.exists(key) > 0
        except Exception:
            return False
    
    async def get_ttl(self, key: str) -> int:
        """Get remaining TTL for key. Returns -1 if not found."""
        if not self.is_connected:
            return -1
        
        try:
            return await self._client.ttl(key)
        except Exception:
            return -1
    
    async def health_check(self) -> dict:
        """
        Health check for cache.
        
        Returns status dict for monitoring.
        """
        if not REDIS_AVAILABLE:
            return {
                "status": "unavailable",
                "reason": "redis library not installed",
            }
        
        if not self.is_connected:
            # Try to reconnect
            await self.connect()
        
        if not self.is_connected:
            return {
                "status": "disconnected",
                "reason": "redis connection failed",
            }
        
        try:
            await self._client.ping()
            info = await self._client.info("memory")
            
            return {
                "status": "healthy",
                "used_memory": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
            }
        except Exception as e:
            return {
                "status": "error",
                "reason": str(e),
            }


# Global cache instance
cache = CacheBackend()


async def get_cache() -> CacheBackend:
    """Get cache instance, connecting if needed."""
    if not cache.is_connected:
        await cache.connect()
    return cache
