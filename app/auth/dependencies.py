"""
CUSTOS Auth Dependencies

FastAPI dependencies for authentication.
"""

from typing import Annotated, Callable, List, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import verify_token, TokenPayload
from app.core.exceptions import AuthenticationError, AuthorizationError
from app.auth.schemas import AuthContext


security = HTTPBearer(auto_error=False)


async def get_token_payload(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
) -> TokenPayload:
    """Extract and verify token from request."""
    if not credentials:
        raise AuthenticationError("Authentication required")
    
    payload = verify_token(credentials.credentials)
    if not payload:
        raise AuthenticationError("Invalid or expired token")
    
    if payload.type != "access":
        raise AuthenticationError("Invalid token type")
    
    return payload


async def get_current_user(
    payload: Annotated[TokenPayload, Depends(get_token_payload)],
    request: Request,
) -> AuthContext:
    """Get current authenticated user."""
    auth_context = AuthContext(
        user_id=UUID(payload.sub),
        tenant_id=UUID(payload.tenant_id),
        email=payload.email,
        roles=payload.roles,
        permissions=set(payload.permissions),
    )
    
    # Store in request state for middleware access
    request.state.user_id = auth_context.user_id
    request.state.auth_context = auth_context
    
    return auth_context


async def get_current_active_user(
    user: Annotated[AuthContext, Depends(get_current_user)],
) -> AuthContext:
    """Get current active user (not disabled)."""
    # Could add additional checks here (user status, etc.)
    return user


def require_permission(permission: str) -> Callable:
    """Dependency factory to require specific permission."""
    
    async def permission_checker(
        user: Annotated[AuthContext, Depends(get_current_user)],
    ) -> AuthContext:
        if not user.has_permission(permission):
            raise AuthorizationError(
                f"Permission '{permission}' required",
                details={"required": permission, "user_permissions": list(user.permissions)},
            )
        return user
    
    return permission_checker


def require_any_permission(permissions: List[str]) -> Callable:
    """Dependency factory to require any of the permissions."""
    
    async def permission_checker(
        user: Annotated[AuthContext, Depends(get_current_user)],
    ) -> AuthContext:
        if not user.has_any_permission(permissions):
            raise AuthorizationError(
                f"One of permissions required: {permissions}",
                details={"required": permissions},
            )
        return user
    
    return permission_checker


def require_all_permissions(permissions: List[str]) -> Callable:
    """Dependency factory to require all permissions."""
    
    async def permission_checker(
        user: Annotated[AuthContext, Depends(get_current_user)],
    ) -> AuthContext:
        if not user.has_all_permissions(permissions):
            raise AuthorizationError(
                f"All permissions required: {permissions}",
                details={"required": permissions},
            )
        return user
    
    return permission_checker


def require_role(role: str) -> Callable:
    """Dependency factory to require specific role."""
    
    async def role_checker(
        user: Annotated[AuthContext, Depends(get_current_user)],
    ) -> AuthContext:
        if not user.has_role(role):
            raise AuthorizationError(
                f"Role '{role}' required",
                details={"required": role, "user_roles": user.roles},
            )
        return user
    
    return role_checker


# Convenience type aliases
CurrentUser = Annotated[AuthContext, Depends(get_current_user)]
ActiveUser = Annotated[AuthContext, Depends(get_current_active_user)]

# Alias for backward compatibility
require_permissions = require_any_permission


def require_roles(roles: List[str]) -> Callable:
    """Dependency factory to require any of the specified roles."""
    
    async def role_checker(
        user: Annotated[AuthContext, Depends(get_current_user)],
    ) -> AuthContext:
        if not any(user.has_role(role) for role in roles):
            raise AuthorizationError(
                f"One of roles required: {roles}",
                details={"required": roles, "user_roles": user.roles},
            )
        return user
    
    return role_checker


