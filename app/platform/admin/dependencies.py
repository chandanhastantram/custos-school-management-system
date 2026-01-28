"""
CUSTOS Platform Admin Dependencies

Authentication for platform-level admins.
"""

from typing import Annotated, Optional

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_token
from app.core.exceptions import AuthenticationError, AuthorizationError
from app.platform.admin.models import PlatformAdmin, PlatformRole, PLATFORM_PERMISSIONS


security = HTTPBearer(auto_error=False)


async def get_platform_admin(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
    db: AsyncSession = Depends(get_db),
) -> PlatformAdmin:
    """
    Get current platform admin from token.
    
    Platform admins have a special token with type='platform'.
    """
    if not credentials:
        raise AuthenticationError("Platform admin authentication required")
    
    payload = verify_token(credentials.credentials)
    if not payload:
        raise AuthenticationError("Invalid or expired token")
    
    # Check token type
    if payload.type != "platform":
        raise AuthenticationError("Invalid token type for platform access")
    
    # Get platform admin
    query = select(PlatformAdmin).where(
        PlatformAdmin.email == payload.email,
        PlatformAdmin.is_active == True,
    )
    result = await db.execute(query)
    admin = result.scalar_one_or_none()
    
    if not admin:
        raise AuthenticationError("Platform admin not found")
    
    return admin


def require_platform_role(role: str):
    """
    Dependency factory for platform role requirement.
    
    Usage:
        @router.delete("/tenants/{id}")
        async def delete_tenant(
            admin: PlatformAdmin = Depends(require_platform_role(PlatformRole.PLATFORM_OWNER)),
        ):
            ...
    """
    async def role_checker(
        admin: PlatformAdmin = Depends(get_platform_admin),
    ) -> PlatformAdmin:
        if admin.role != role and admin.role != PlatformRole.PLATFORM_OWNER:
            raise AuthorizationError(f"Platform role '{role}' required")
        return admin
    
    return role_checker


def require_platform_permission(permission: str):
    """
    Dependency factory for platform permission requirement.
    """
    async def permission_checker(
        admin: PlatformAdmin = Depends(get_platform_admin),
    ) -> PlatformAdmin:
        role_permissions = PLATFORM_PERMISSIONS.get(admin.role, [])
        
        if "platform:all" in role_permissions:
            return admin
        
        if permission not in role_permissions:
            raise AuthorizationError(f"Platform permission '{permission}' required")
        
        return admin
    
    return permission_checker


# Type alias
CurrentPlatformAdmin = Annotated[PlatformAdmin, Depends(get_platform_admin)]
