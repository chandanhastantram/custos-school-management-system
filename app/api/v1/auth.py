"""
CUSTOS Auth API Endpoints

Authentication routes.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import http_400
from app.auth import AuthUser
from app.services.auth_service import AuthService
from app.schemas.auth import (
    LoginRequest, LoginResponse, RefreshTokenRequest, RefreshTokenResponse,
    PasswordChangeRequest, PasswordResetRequest, PasswordResetConfirm,
)
from app.schemas.common import SuccessResponse


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    x_tenant_id: Annotated[str, Header()],
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate user and return JWT tokens.
    
    Requires tenant ID in X-Tenant-ID header.
    """
    from uuid import UUID
    
    try:
        tenant_id = UUID(x_tenant_id)
    except ValueError:
        raise http_400("Invalid tenant ID")
    
    auth_service = AuthService(db)
    return await auth_service.login(request, tenant_id)


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """Refresh access token using refresh token."""
    auth_service = AuthService(db)
    token_pair = await auth_service.refresh_tokens(request.refresh_token)
    
    return RefreshTokenResponse(
        access_token=token_pair.access_token,
        expires_in=token_pair.expires_in,
    )


@router.post("/logout", response_model=SuccessResponse)
async def logout(current_user: AuthUser):
    """
    Log out current user.
    
    Note: JWT tokens are stateless, so logout is handled client-side
    by discarding tokens. This endpoint is for future token blacklisting.
    """
    return SuccessResponse(message="Logged out successfully")


@router.post("/change-password", response_model=SuccessResponse)
async def change_password(
    request: PasswordChangeRequest,
    current_user: AuthUser,
    db: AsyncSession = Depends(get_db),
):
    """Change password for authenticated user."""
    if request.new_password != request.confirm_password:
        raise http_400("Passwords do not match")
    
    auth_service = AuthService(db)
    await auth_service.change_password(
        user_id=current_user.user_id,
        tenant_id=current_user.tenant_id,
        current_password=request.current_password,
        new_password=request.new_password,
    )
    
    return SuccessResponse(message="Password changed successfully")


@router.post("/forgot-password", response_model=SuccessResponse)
async def forgot_password(
    request: PasswordResetRequest,
    x_tenant_id: Annotated[str, Header()],
    db: AsyncSession = Depends(get_db),
):
    """Request password reset email."""
    from uuid import UUID
    
    try:
        tenant_id = UUID(x_tenant_id)
    except ValueError:
        raise http_400("Invalid tenant ID")
    
    auth_service = AuthService(db)
    token = await auth_service.request_password_reset(request.email, tenant_id)
    
    # In production, send email with token
    # For dev, we just return success regardless
    
    return SuccessResponse(
        message="If the email exists, a password reset link has been sent"
    )


@router.post("/reset-password", response_model=SuccessResponse)
async def reset_password(
    request: PasswordResetConfirm,
    x_tenant_id: Annotated[str, Header()],
    db: AsyncSession = Depends(get_db),
):
    """Reset password using reset token."""
    from uuid import UUID
    
    if request.new_password != request.confirm_password:
        raise http_400("Passwords do not match")
    
    try:
        tenant_id = UUID(x_tenant_id)
    except ValueError:
        raise http_400("Invalid tenant ID")
    
    auth_service = AuthService(db)
    await auth_service.reset_password(
        token=request.token,
        new_password=request.new_password,
        tenant_id=tenant_id,
    )
    
    return SuccessResponse(message="Password reset successfully")


@router.get("/me")
async def get_current_user(current_user: AuthUser):
    """Get current authenticated user info."""
    return {
        "user_id": str(current_user.user_id),
        "email": current_user.email,
        "tenant_id": str(current_user.tenant_id),
        "roles": current_user.roles,
        "permissions": list(current_user.permissions),
    }
