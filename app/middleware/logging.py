"""
CUSTOS Request Logging Middleware

Logs all incoming requests with timing and tracing.
"""

import time
import logging
import uuid as uuid_lib
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


logger = logging.getLogger("custos.requests")

# Context variable for request tracing
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")
tenant_id_ctx: ContextVar[str] = ContextVar("tenant_id", default="")


def get_request_id() -> str:
    """Get current request ID from context."""
    return request_id_ctx.get()


def get_tenant_id() -> str:
    """Get current tenant ID from context."""
    return tenant_id_ctx.get()


class RequestContextFilter(logging.Filter):
    """Logging filter that adds request context to log records."""
    
    def filter(self, record):
        record.request_id = get_request_id() or "-"
        record.tenant_id = get_tenant_id() or "-"
        return True


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for request logging with tracing.
    
    Features:
    - Generates unique request ID for tracing
    - Logs request method, path, duration
    - Adds request ID to response headers
    - Sets context variables for downstream logging
    """
    
    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = request.headers.get("X-Request-ID") or str(uuid_lib.uuid4())[:8]
        
        # Set context variables
        request_id_ctx.set(request_id)
        
        # Store in request state
        request.state.request_id = request_id
        
        # Get tenant from state (if set by TenantMiddleware)
        tenant_id = getattr(request.state, "tenant_id", None)
        if tenant_id:
            tenant_id_ctx.set(str(tenant_id))
        
        start_time = time.perf_counter()
        
        # Log request start
        logger.info(
            f"[{request_id}] {request.method} {request.url.path} - Started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client_ip": request.client.host if request.client else None,
            }
        )
        
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            # Add tracing headers to response
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
            
            # Log request completion
            log_level = logging.WARNING if response.status_code >= 400 else logging.INFO
            logger.log(
                log_level,
                f"[{request_id}] {request.method} {request.url.path} - "
                f"{response.status_code} ({duration_ms:.2f}ms)",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                }
            )
            
            return response
            
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                f"[{request_id}] {request.method} {request.url.path} - "
                f"Error: {str(e)} ({duration_ms:.2f}ms)",
                exc_info=True,
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration_ms,
                    "error": str(e),
                }
            )
            raise
        finally:
            # Clear context
            request_id_ctx.set("")
            tenant_id_ctx.set("")


def setup_logging(debug: bool = False):
    """Configure logging with request context."""
    log_format = (
        "%(asctime)s | %(levelname)-8s | "
        "[%(request_id)s] [tenant:%(tenant_id)s] | "
        "%(name)s:%(lineno)d | %(message)s"
    )
    
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(log_format))
    handler.addFilter(RequestContextFilter())
    
    root_logger = logging.getLogger("custos")
    root_logger.setLevel(logging.DEBUG if debug else logging.INFO)
    root_logger.addHandler(handler)
    
    # Also configure uvicorn access logs
    uvicorn_logger = logging.getLogger("uvicorn.access")
    uvicorn_logger.addFilter(RequestContextFilter())
