"""
CUSTOS Request Logging Middleware

Logs all HTTP requests and responses.
"""

import time
import logging
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


logger = logging.getLogger("custos.requests")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all HTTP requests.
    
    Logs:
    - Method, path, status code
    - Processing time
    - Client IP
    - User ID (if authenticated)
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process and log request."""
        start_time = time.time()
        
        # Get client info
        client_ip = request.client.host if request.client else "unknown"
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000
        
        # Get user ID if available
        user_id = getattr(request.state, "user_id", None)
        tenant_id = getattr(request.state, "tenant_id", None)
        
        # Log request
        log_data = {
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": round(duration_ms, 2),
            "client_ip": client_ip,
            "tenant_id": str(tenant_id) if tenant_id else None,
            "user_id": str(user_id) if user_id else None,
        }
        
        if response.status_code >= 400:
            logger.warning(f"Request: {log_data}")
        else:
            logger.info(f"Request: {log_data}")
        
        # Add timing header
        response.headers["X-Process-Time"] = f"{duration_ms:.2f}ms"
        
        return response


class SlowRequestMiddleware(BaseHTTPMiddleware):
    """
    Middleware to detect and log slow requests.
    """
    
    SLOW_REQUEST_THRESHOLD_MS = 1000  # 1 second
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check for slow requests."""
        start_time = time.time()
        
        response = await call_next(request)
        
        duration_ms = (time.time() - start_time) * 1000
        
        if duration_ms > self.SLOW_REQUEST_THRESHOLD_MS:
            logger.warning(
                f"Slow request detected: {request.method} {request.url.path} "
                f"took {duration_ms:.2f}ms"
            )
        
        return response
