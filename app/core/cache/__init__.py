"""
CUSTOS Cache Module

Redis-based caching with graceful degradation.

RULES:
- Never cache permission-dependent data
- Never cache student-private data
- Cache only read-heavy, deterministic data
- All keys must include tenant_id
"""

from app.core.cache.backend import cache, get_cache, CacheBackend
from app.core.cache.keys import CacheKeys, CacheTTL, CachePrefix
from app.core.cache.decorators import cached, cached_property_async, CacheAside
from app.core.cache.invalidation import (
    CacheEvent,
    CacheInvalidator,
    invalidate_cache,
)

__all__ = [
    # Backend
    "cache",
    "get_cache",
    "CacheBackend",
    # Keys
    "CacheKeys",
    "CacheTTL",
    "CachePrefix",
    # Decorators
    "cached",
    "cached_property_async",
    "CacheAside",
    # Invalidation
    "CacheEvent",
    "CacheInvalidator",
    "invalidate_cache",
]
