"""
CUSTOS Observability Metrics

Lightweight, in-memory metrics collection.

Tracks per-tenant:
- Request counts
- Error counts
- AI usage
- Cache hit ratio
- Circuit breaker opens
- Response times

NO EXTERNAL DEPENDENCIES - just Python counters.
"""

import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID
from dataclasses import dataclass, field
from threading import Lock
from collections import defaultdict
from enum import Enum

logger = logging.getLogger(__name__)


class MetricType(str, Enum):
    """Types of metrics collected."""
    REQUEST = "request"
    ERROR = "error"
    AI_CALL = "ai_call"
    AI_TOKENS = "ai_tokens"
    CACHE_HIT = "cache_hit"
    CACHE_MISS = "cache_miss"
    CIRCUIT_OPEN = "circuit_open"
    DB_QUERY = "db_query"
    RESPONSE_TIME = "response_time"


@dataclass
class MetricPoint:
    """Single metric data point."""
    value: float
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class TenantMetrics:
    """Metrics for a single tenant."""
    tenant_id: UUID
    
    # Counters
    request_count: int = 0
    error_count: int = 0
    ai_call_count: int = 0
    ai_tokens_used: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    circuit_opens: int = 0
    db_queries: int = 0
    
    # Response times (rolling window)
    response_times: List[float] = field(default_factory=list)
    
    # Per-endpoint error tracking
    endpoint_errors: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    
    # Per-feature stats
    feature_calls: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    feature_errors: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    
    # Time tracking
    window_start: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def reset(self):
        """Reset all counters for new window."""
        self.request_count = 0
        self.error_count = 0
        self.ai_call_count = 0
        self.ai_tokens_used = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.circuit_opens = 0
        self.db_queries = 0
        self.response_times = []
        self.endpoint_errors = defaultdict(int)
        self.feature_calls = defaultdict(int)
        self.feature_errors = defaultdict(int)
        self.window_start = datetime.now(timezone.utc)
    
    @property
    def cache_hit_ratio(self) -> float:
        """Calculate cache hit ratio."""
        total = self.cache_hits + self.cache_misses
        if total == 0:
            return 0.0
        return self.cache_hits / total
    
    @property
    def error_rate(self) -> float:
        """Calculate error rate."""
        if self.request_count == 0:
            return 0.0
        return self.error_count / self.request_count
    
    @property
    def avg_response_time_ms(self) -> float:
        """Calculate average response time."""
        if not self.response_times:
            return 0.0
        return sum(self.response_times) / len(self.response_times)
    
    @property
    def p95_response_time_ms(self) -> float:
        """Calculate 95th percentile response time."""
        if not self.response_times:
            return 0.0
        sorted_times = sorted(self.response_times)
        idx = int(len(sorted_times) * 0.95)
        return sorted_times[min(idx, len(sorted_times) - 1)]
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "tenant_id": str(self.tenant_id),
            "window_start": self.window_start.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "counters": {
                "requests": self.request_count,
                "errors": self.error_count,
                "ai_calls": self.ai_call_count,
                "ai_tokens": self.ai_tokens_used,
                "cache_hits": self.cache_hits,
                "cache_misses": self.cache_misses,
                "circuit_opens": self.circuit_opens,
                "db_queries": self.db_queries,
            },
            "rates": {
                "cache_hit_ratio": round(self.cache_hit_ratio, 3),
                "error_rate": round(self.error_rate, 4),
            },
            "response_times": {
                "avg_ms": round(self.avg_response_time_ms, 2),
                "p95_ms": round(self.p95_response_time_ms, 2),
                "sample_count": len(self.response_times),
            },
            "top_errors": dict(
                sorted(
                    self.endpoint_errors.items(),
                    key=lambda x: x[1],
                    reverse=True,
                )[:10]
            ),
        }


class MetricsCollector:
    """
    Global metrics collector.
    
    Thread-safe singleton for collecting metrics across the application.
    Maintains per-tenant metrics with automatic window rotation.
    """
    
    _instance: Optional["MetricsCollector"] = None
    _lock = Lock()
    
    # Window duration for metrics aggregation
    WINDOW_DURATION_SECONDS = 300  # 5 minutes
    MAX_RESPONSE_TIMES = 1000  # Rolling window size
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._tenant_metrics: Dict[UUID, TenantMetrics] = {}
        self._platform_metrics = TenantMetrics(tenant_id=UUID(int=0))  # Global platform
        self._metrics_lock = Lock()
        self._initialized = True
    
    def _get_tenant_metrics(self, tenant_id: UUID) -> TenantMetrics:
        """Get or create tenant metrics."""
        if tenant_id not in self._tenant_metrics:
            self._tenant_metrics[tenant_id] = TenantMetrics(tenant_id=tenant_id)
        return self._tenant_metrics[tenant_id]
    
    def _check_window_rotation(self, metrics: TenantMetrics):
        """Check if we need to rotate the metrics window."""
        now = datetime.now(timezone.utc)
        if (now - metrics.window_start).total_seconds() > self.WINDOW_DURATION_SECONDS:
            # Archive current metrics (could write to DB here)
            metrics.reset()
    
    def record_request(
        self,
        tenant_id: UUID,
        endpoint: str,
        response_time_ms: float,
        is_error: bool = False,
        error_message: Optional[str] = None,
    ):
        """Record an API request."""
        with self._metrics_lock:
            metrics = self._get_tenant_metrics(tenant_id)
            self._check_window_rotation(metrics)
            
            metrics.request_count += 1
            metrics.last_updated = datetime.now(timezone.utc)
            
            # Response time (keep rolling window)
            if len(metrics.response_times) >= self.MAX_RESPONSE_TIMES:
                metrics.response_times.pop(0)
            metrics.response_times.append(response_time_ms)
            
            if is_error:
                metrics.error_count += 1
                metrics.endpoint_errors[endpoint] += 1
            
            # Also record platform-wide
            self._platform_metrics.request_count += 1
            if is_error:
                self._platform_metrics.error_count += 1
    
    def record_ai_call(
        self,
        tenant_id: UUID,
        tokens_used: int = 0,
        feature: str = "unknown",
    ):
        """Record an AI API call."""
        with self._metrics_lock:
            metrics = self._get_tenant_metrics(tenant_id)
            self._check_window_rotation(metrics)
            
            metrics.ai_call_count += 1
            metrics.ai_tokens_used += tokens_used
            metrics.feature_calls[feature] += 1
            metrics.last_updated = datetime.now(timezone.utc)
            
            self._platform_metrics.ai_call_count += 1
            self._platform_metrics.ai_tokens_used += tokens_used
    
    def record_cache_access(
        self,
        tenant_id: UUID,
        is_hit: bool,
    ):
        """Record a cache access."""
        with self._metrics_lock:
            metrics = self._get_tenant_metrics(tenant_id)
            self._check_window_rotation(metrics)
            
            if is_hit:
                metrics.cache_hits += 1
                self._platform_metrics.cache_hits += 1
            else:
                metrics.cache_misses += 1
                self._platform_metrics.cache_misses += 1
            
            metrics.last_updated = datetime.now(timezone.utc)
    
    def record_circuit_open(
        self,
        tenant_id: UUID,
        feature: str,
    ):
        """Record a circuit breaker opening."""
        with self._metrics_lock:
            metrics = self._get_tenant_metrics(tenant_id)
            self._check_window_rotation(metrics)
            
            metrics.circuit_opens += 1
            metrics.feature_errors[feature] += 1
            metrics.last_updated = datetime.now(timezone.utc)
            
            self._platform_metrics.circuit_opens += 1
    
    def record_db_query(self, tenant_id: UUID):
        """Record a database query."""
        with self._metrics_lock:
            metrics = self._get_tenant_metrics(tenant_id)
            metrics.db_queries += 1
            self._platform_metrics.db_queries += 1
    
    def record_feature_error(
        self,
        tenant_id: UUID,
        feature: str,
    ):
        """Record a feature-level error."""
        with self._metrics_lock:
            metrics = self._get_tenant_metrics(tenant_id)
            metrics.feature_errors[feature] += 1
            metrics.last_updated = datetime.now(timezone.utc)
    
    def get_tenant_metrics(self, tenant_id: UUID) -> dict:
        """Get metrics for a specific tenant."""
        with self._metrics_lock:
            if tenant_id not in self._tenant_metrics:
                return {"tenant_id": str(tenant_id), "no_data": True}
            return self._tenant_metrics[tenant_id].to_dict()
    
    def get_platform_metrics(self) -> dict:
        """Get platform-wide metrics."""
        with self._metrics_lock:
            return {
                "platform": self._platform_metrics.to_dict(),
                "active_tenants": len(self._tenant_metrics),
                "window_duration_seconds": self.WINDOW_DURATION_SECONDS,
            }
    
    def get_all_tenant_metrics(self) -> List[dict]:
        """Get metrics for all tenants."""
        with self._metrics_lock:
            return [m.to_dict() for m in self._tenant_metrics.values()]
    
    def get_top_tenants_by_requests(self, limit: int = 10) -> List[dict]:
        """Get top tenants by request count."""
        with self._metrics_lock:
            sorted_tenants = sorted(
                self._tenant_metrics.values(),
                key=lambda m: m.request_count,
                reverse=True,
            )
            return [m.to_dict() for m in sorted_tenants[:limit]]
    
    def get_top_tenants_by_errors(self, limit: int = 10) -> List[dict]:
        """Get top tenants by error count."""
        with self._metrics_lock:
            sorted_tenants = sorted(
                self._tenant_metrics.values(),
                key=lambda m: m.error_count,
                reverse=True,
            )
            return [m.to_dict() for m in sorted_tenants[:limit]]
    
    def get_top_tenants_by_ai_usage(self, limit: int = 10) -> List[dict]:
        """Get top tenants by AI token usage."""
        with self._metrics_lock:
            sorted_tenants = sorted(
                self._tenant_metrics.values(),
                key=lambda m: m.ai_tokens_used,
                reverse=True,
            )
            return [m.to_dict() for m in sorted_tenants[:limit]]
    
    def get_degraded_tenants(self, error_rate_threshold: float = 0.1) -> List[dict]:
        """Get tenants with high error rates (potentially degraded)."""
        with self._metrics_lock:
            degraded = [
                m for m in self._tenant_metrics.values()
                if m.error_rate > error_rate_threshold and m.request_count >= 10
            ]
            return [m.to_dict() for m in sorted(
                degraded,
                key=lambda m: m.error_rate,
                reverse=True,
            )]


# Global singleton
_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector."""
    global _collector
    if _collector is None:
        _collector = MetricsCollector()
    return _collector


# Convenience functions
def record_request(
    tenant_id: UUID,
    endpoint: str,
    response_time_ms: float,
    is_error: bool = False,
):
    """Record an API request."""
    get_metrics_collector().record_request(
        tenant_id=tenant_id,
        endpoint=endpoint,
        response_time_ms=response_time_ms,
        is_error=is_error,
    )


def record_ai_call(tenant_id: UUID, tokens_used: int = 0, feature: str = "unknown"):
    """Record an AI API call."""
    get_metrics_collector().record_ai_call(
        tenant_id=tenant_id,
        tokens_used=tokens_used,
        feature=feature,
    )


def record_cache_access(tenant_id: UUID, is_hit: bool):
    """Record a cache access."""
    get_metrics_collector().record_cache_access(tenant_id=tenant_id, is_hit=is_hit)


def record_circuit_open(tenant_id: UUID, feature: str):
    """Record a circuit breaker opening."""
    get_metrics_collector().record_circuit_open(tenant_id=tenant_id, feature=feature)
