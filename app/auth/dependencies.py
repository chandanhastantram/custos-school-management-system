"""
CUSTOS Auth Dependencies

FastAPI dependencies for authentication and authorization.
"""

from typing import Optional, Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import http_401, http_403
from app.auth.jwt import verify_access_token, TokenPayload
from app.auth.rbac import Permission, check_permission, check_any_permission


# HTTP Bearer token extractor
security = HTTPBearer(auto_error=False)


class CurrentUser:
    """Current authenticated user context."""
    
    def __init__(
        self,
        user_id: UUID,
        tenant_id: UUID,
        email: str,
        roles: list[str],
        permissions: set[str],
    ):
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.email = email
        self.roles = roles
        self.permissions = permissions
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if user has permission."""
        return permission.value in self.permissions
    
    def has_any_permission(self, permissions: list[Permission]) -> bool:
        """Check if user has any of the permissions."""
        return any(p.value in self.permissions for p in permissions)
    
    def has_all_permissions(self, permissions: list[Permission]) -> bool:
        """Check if user has all permissions."""
        return all(p.value in self.permissions for p in permissions)
    
    def has_role(self, role: str) -> bool:
        """Check if user has role."""
        return role in self.roles
    
    def is_admin(self) -> bool:
        """Check if user is any type of admin."""
        admin_roles = {"super_admin", "principal", "sub_admin"}
        return bool(set(self.roles) & admin_roles)
    
    def is_super_admin(self) -> bool:
        """Check if user is super admin."""
        return "super_admin" in self.roles


async def get_current_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
) -> CurrentUser:
    """
    Get current authenticated user from JWT token.
    
    Raises:
        HTTPException: If token is missing or invalid
    """
    if not credentials:
        raise http_401("Missing authentication token")
    
    token = credentials.credentials
    payload = verify_access_token(token)
    
    if not payload:
        raise http_401("Invalid or expired token")
    
    return CurrentUser(
        user_id=UUID(payload.sub),
        tenant_id=UUID(payload.tenant_id),
        email=payload.email,
        roles=payload.roles,
        permissions=set(payload.permissions),
    )


async def get_current_user_optional(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
) -> Optional[CurrentUser]:
    """Get current user if authenticated, None otherwise."""
    if not credentials:
        return None
    
    token = credentials.credentials
    payload = verify_access_token(token)
    
    if not payload:
        return None
    
    return CurrentUser(
        user_id=UUID(payload.sub),
        tenant_id=UUID(payload.tenant_id),
        email=payload.email,
        roles=payload.roles,
        permissions=set(payload.permissions),
    )


def require_permissions(*permissions: Permission):
    """
    Dependency factory requiring specific permissions.
    
    Usage:
        @router.get("/admin")
        async def admin_route(
            user: CurrentUser = Depends(require_permissions(Permission.ADMIN_VIEW))
        ):
            ...
    """
    async def dependency(
        current_user: Annotated[CurrentUser, Depends(get_current_user)],
    ) -> CurrentUser:
        for permission in permissions:
            if not current_user.has_permission(permission):
                raise http_403(
                    f"Permission denied. Required: {permission.value}",
                    required_permission=permission.value,
                )
        return current_user
    
    return dependency


def require_any_permission(*permissions: Permission):
    """Dependency requiring any of the specified permissions."""
    async def dependency(
        current_user: Annotated[CurrentUser, Depends(get_current_user)],
    ) -> CurrentUser:
        if not current_user.has_any_permission(list(permissions)):
            raise http_403(
                "Permission denied. Required one of: " + 
                ", ".join(p.value for p in permissions)
            )
        return current_user
    
    return dependency


def require_roles(*roles: str):
    """Dependency requiring specific roles."""
    async def dependency(
        current_user: Annotated[CurrentUser, Depends(get_current_user)],
    ) -> CurrentUser:
        if not any(current_user.has_role(role) for role in roles):
            raise http_403(
                "Role required: " + ", ".join(roles)
            )
        return current_user
    
    return dependency


def require_admin():
    """Dependency requiring admin role."""
    async def dependency(
        current_user: Annotated[CurrentUser, Depends(get_current_user)],
    ) -> CurrentUser:
        if not current_user.is_admin():
            raise http_403("Administrator access required")
        return current_user
    
    return dependency


def require_super_admin():
    """Dependency requiring super admin role."""
    async def dependency(
        current_user: Annotated[CurrentUser, Depends(get_current_user)],
    ) -> CurrentUser:
        if not current_user.is_super_admin():
            raise http_403("Super administrator access required")
        return current_user
    
    return dependency


class TenantContext:
    """Tenant context for request."""
    
    def __init__(self, tenant_id: UUID, user: CurrentUser):
        self.tenant_id = tenant_id
        self.user = user


async def get_tenant_context(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> TenantContext:
    """Get tenant context from current user."""
    return TenantContext(
        tenant_id=current_user.tenant_id,
        user=current_user,
    )


# Type aliases for cleaner dependency injection
AuthUser = Annotated[CurrentUser, Depends(get_current_user)]
OptionalUser = Annotated[Optional[CurrentUser], Depends(get_current_user_optional)]
TenantCtx = Annotated[TenantContext, Depends(get_tenant_context)]
