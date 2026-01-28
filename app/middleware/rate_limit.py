"""
CUSTOS Rate Limiting Middleware

Token bucket rate limiting per tenant/user.
"""

import time
from collections import defaultdict
from typing import Dict, Tuple

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using token bucket algorithm.
    
    Limits requests per tenant and per user.
    """
    
    def __init__(self, app, requests_per_minute: int = 100):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.window_seconds = 60
        
        # In-memory buckets: {key: (count, window_start)}
        self._buckets: Dict[str, Tuple[int, float]] = defaultdict(lambda: (0, 0))
    
    async def dispatch(self, request: Request, call_next):
        """Check rate limit before processing."""
        # Get rate limit key
        key = self._get_key(request)
        
        # Check if limit exceeded
        if self._is_rate_limited(key):
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "message": "Rate limit exceeded. Please try again later.",
                    "code": "RATE_LIMIT_EXCEEDED",
                },
                headers={"Retry-After": str(self.window_seconds)},
            )
        
        # Increment counter
        self._increment(key)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        count, _ = self._buckets[key]
        remaining = max(0, self.requests_per_minute - count)
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        
        return response
    
    def _get_key(self, request: Request) -> str:
        """Get rate limit key from request."""
        # Use tenant_id if available, else client IP
        tenant_id = getattr(request.state, "tenant_id", None)
        if tenant_id:
            return f"tenant:{tenant_id}"
        
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"
    
    def _is_rate_limited(self, key: str) -> bool:
        """Check if key is rate limited."""
        count, window_start = self._buckets[key]
        current_time = time.time()
        
        # Reset window if expired
        if current_time - window_start > self.window_seconds:
            self._buckets[key] = (0, current_time)
            return False
        
        return count >= self.requests_per_minute
    
    def _increment(self, key: str) -> None:
        """Increment request counter."""
        count, window_start = self._buckets[key]
        current_time = time.time()
        
        if current_time - window_start > self.window_seconds:
            self._buckets[key] = (1, current_time)
        else:
            self._buckets[key] = (count + 1, window_start)
