"""
CUSTOS Tenant Middleware

Resolves tenant from request header or subdomain.
"""

from typing import Optional
from uuid import UUID

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class TenantContext:
    """Tenant context for current request."""
    
    def __init__(
        self,
        tenant_id: UUID,
        tenant_slug: Optional[str] = None,
    ):
        self.tenant_id = tenant_id
        self.tenant_slug = tenant_slug


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware to resolve tenant from request.
    
    Resolution order:
    1. X-Tenant-ID header
    2. Subdomain (tenant.domain.com)
    3. Query parameter (for API testing)
    """
    
    # Paths that don't require tenant
    EXCLUDED_PATHS = [
        "/",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/v1/tenants/register",
        "/api/v1/tenants/by-slug",
    ]
    
    async def dispatch(self, request: Request, call_next):
        """Process request and resolve tenant."""
        path = request.url.path
        
        # Skip excluded paths
        if any(path.startswith(p) for p in self.EXCLUDED_PATHS):
            return await call_next(request)
        
        # Try to resolve tenant ID
        tenant_id = await self._resolve_tenant_id(request)
        
        if not tenant_id:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": "Tenant ID required. Provide X-Tenant-ID header.",
                    "code": "TENANT_REQUIRED",
                },
            )
        
        # Store in request state
        request.state.tenant_id = tenant_id
        
        return await call_next(request)
    
    async def _resolve_tenant_id(self, request: Request) -> Optional[UUID]:
        """Resolve tenant ID from request."""
        # Method 1: Header
        header_value = request.headers.get("X-Tenant-ID")
        if header_value:
            try:
                return UUID(header_value)
            except ValueError:
                pass
        
        # Method 2: Subdomain
        host = request.headers.get("host", "")
        if "." in host:
            subdomain = host.split(".")[0]
            # Would lookup tenant by slug here
            # tenant = await self._get_tenant_by_slug(subdomain)
            # return tenant.id if tenant else None
        
        # Method 3: Query param (dev only)
        tenant_query = request.query_params.get("tenant_id")
        if tenant_query:
            try:
                return UUID(tenant_query)
            except ValueError:
                pass
        
        return None


def get_tenant_id(request: Request) -> UUID:
    """Get tenant ID from request state."""
    return request.state.tenant_id


def get_tenant_context(request: Request) -> TenantContext:
    """Get full tenant context from request."""
    return TenantContext(
        tenant_id=request.state.tenant_id,
        tenant_slug=getattr(request.state, "tenant_slug", None),
    )
