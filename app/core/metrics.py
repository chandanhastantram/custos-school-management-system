"""
Performance Monitoring and Metrics

Provides Prometheus metrics and performance tracking.
"""

from typing import Callable
from functools import wraps
import time
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response
from fastapi.routing import APIRoute


# Metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"]
)

http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "HTTP requests currently in progress",
    ["method", "endpoint"]
)

database_queries_total = Counter(
    "database_queries_total",
    "Total database queries",
    ["operation", "table"]
)

database_query_duration_seconds = Histogram(
    "database_query_duration_seconds",
    "Database query duration in seconds",
    ["operation", "table"]
)

cache_hits_total = Counter(
    "cache_hits_total",
    "Total cache hits",
    ["cache_type"]
)

cache_misses_total = Counter(
    "cache_misses_total",
    "Total cache misses",
    ["cache_type"]
)

active_users = Gauge(
    "active_users",
    "Number of active users",
    ["tenant_id"]
)

ai_requests_total = Counter(
    "ai_requests_total",
    "Total AI API requests",
    ["provider", "model", "status"]
)

ai_request_duration_seconds = Histogram(
    "ai_request_duration_seconds",
    "AI request duration in seconds",
    ["provider", "model"]
)


class MetricsRoute(APIRoute):
    """Custom route class that tracks metrics."""
    
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()
        
        async def custom_route_handler(request: Request) -> Response:
            method = request.method
            endpoint = request.url.path
            
            # Track in-progress requests
            http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()
            
            # Track request duration
            start_time = time.time()
            
            try:
                response = await original_route_handler(request)
                status = response.status_code
                
                # Record metrics
                http_requests_total.labels(
                    method=method,
                    endpoint=endpoint,
                    status=status
                ).inc()
                
                duration = time.time() - start_time
                http_request_duration_seconds.labels(
                    method=method,
                    endpoint=endpoint
                ).observe(duration)
                
                return response
            
            finally:
                http_requests_in_progress.labels(method=method, endpoint=endpoint).dec()
        
        return custom_route_handler


def track_db_query(operation: str, table: str):
    """Decorator to track database query metrics."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            database_queries_total.labels(operation=operation, table=table).inc()
            
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                database_query_duration_seconds.labels(
                    operation=operation,
                    table=table
                ).observe(duration)
        
        return wrapper
    return decorator


def track_cache(cache_type: str = "redis"):
    """Decorator to track cache hit/miss metrics."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            
            if result is not None:
                cache_hits_total.labels(cache_type=cache_type).inc()
            else:
                cache_misses_total.labels(cache_type=cache_type).inc()
            
            return result
        
        return wrapper
    return decorator


def track_ai_request(provider: str, model: str):
    """Decorator to track AI request metrics."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                
                ai_requests_total.labels(
                    provider=provider,
                    model=model,
                    status=status
                ).inc()
                
                ai_request_duration_seconds.labels(
                    provider=provider,
                    model=model
                ).observe(duration)
        
        return wrapper
    return decorator


async def get_metrics() -> Response:
    """Get Prometheus metrics."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
