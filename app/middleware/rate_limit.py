"""
CUSTOS Rate Limiting Middleware

Simple in-memory rate limiting with tenant tier support.
"""

import time
from collections import defaultdict
from typing import Dict, Optional
from dataclasses import dataclass

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import settings


@dataclass
class RateLimitConfig:
    """Rate limit configuration per tier."""
    requests_per_minute: int
    requests_per_hour: int


# Rate limits by plan tier
TIER_RATE_LIMITS: Dict[str, RateLimitConfig] = {
    "free": RateLimitConfig(requests_per_minute=30, requests_per_hour=500),
    "starter": RateLimitConfig(requests_per_minute=60, requests_per_hour=2000),
    "professional": RateLimitConfig(requests_per_minute=120, requests_per_hour=5000),
    "enterprise": RateLimitConfig(requests_per_minute=300, requests_per_hour=20000),
    "platform": RateLimitConfig(requests_per_minute=1000, requests_per_hour=100000),  # Platform admins
}

# Default for unauthenticated requests
DEFAULT_RATE_LIMIT = RateLimitConfig(requests_per_minute=20, requests_per_hour=200)


class RateLimiter:
    """Simple in-memory rate limiter with sliding window."""
    
    def __init__(self):
        self.requests: Dict[str, list] = defaultdict(list)
    
    def is_allowed(
        self, 
        key: str, 
        max_requests: int, 
        window_seconds: int,
    ) -> tuple[bool, int, int]:
        """
        Check if request is allowed.
        
        Returns:
            (allowed, remaining, retry_after)
        """
        now = time.time()
        window_start = now - window_seconds
        
        # Clean old requests
        self.requests[key] = [t for t in self.requests[key] if t > window_start]
        
        current_count = len(self.requests[key])
        remaining = max(0, max_requests - current_count - 1)
        
        if current_count >= max_requests:
            # Calculate retry after
            oldest = min(self.requests[key]) if self.requests[key] else now
            retry_after = int(oldest + window_seconds - now) + 1
            return False, 0, retry_after
        
        # Record this request
        self.requests[key].append(now)
        return True, remaining, 0
    
    def cleanup(self, max_age_seconds: int = 3600):
        """Clean up old entries."""
        now = time.time()
        cutoff = now - max_age_seconds
        
        keys_to_delete = []
        for key, timestamps in self.requests.items():
            self.requests[key] = [t for t in timestamps if t > cutoff]
            if not self.requests[key]:
                keys_to_delete.append(key)
        
        for key in keys_to_delete:
            del self.requests[key]


# Global rate limiter instance
rate_limiter = RateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware for rate limiting based on tenant tier.
    
    Features:
    - Per-tenant rate limiting
    - Different limits per subscription tier
    - Per-minute and per-hour windows
    - Returns retry-after header
    """
    
    # Paths excluded from rate limiting
    EXCLUDED_PATHS = [
        "/",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
    ]
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.default_rpm = requests_per_minute
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        
        # Skip excluded paths
        if any(path.startswith(p) for p in self.EXCLUDED_PATHS):
            return await call_next(request)
        
        # Determine rate limit key and tier
        tenant_id = getattr(request.state, "tenant_id", None)
        user_id = getattr(request.state, "user_id", None)
        plan_tier = getattr(request.state, "plan_tier", None)
        
        # Build rate limit key
        if tenant_id:
            key = f"tenant:{tenant_id}"
        elif request.client:
            key = f"ip:{request.client.host}"
        else:
            key = "anonymous"
        
        # Get rate limit config
        config = TIER_RATE_LIMITS.get(plan_tier, DEFAULT_RATE_LIMIT) if plan_tier else DEFAULT_RATE_LIMIT
        
        # Check per-minute limit
        allowed, remaining, retry_after = rate_limiter.is_allowed(
            f"{key}:minute",
            config.requests_per_minute,
            60,
        )
        
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "message": "Rate limit exceeded. Please slow down.",
                    "code": "RATE_LIMIT_EXCEEDED",
                    "details": {
                        "retry_after_seconds": retry_after,
                        "limit": config.requests_per_minute,
                        "window": "minute",
                    },
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(config.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + retry_after),
                },
            )
        
        # Check per-hour limit
        allowed_hour, remaining_hour, retry_after_hour = rate_limiter.is_allowed(
            f"{key}:hour",
            config.requests_per_hour,
            3600,
        )
        
        if not allowed_hour:
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "message": "Hourly rate limit exceeded.",
                    "code": "RATE_LIMIT_EXCEEDED",
                    "details": {
                        "retry_after_seconds": retry_after_hour,
                        "limit": config.requests_per_hour,
                        "window": "hour",
                    },
                },
                headers={
                    "Retry-After": str(retry_after_hour),
                    "X-RateLimit-Limit": str(config.requests_per_hour),
                    "X-RateLimit-Remaining": "0",
                },
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(config.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        
        return response
