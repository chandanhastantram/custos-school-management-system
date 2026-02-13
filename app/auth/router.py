"""
CUSTOS Auth Router

Authentication API endpoints.
"""

from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth.service import AuthService
from app.auth.schemas import (
    LoginRequest,
    TokenResponse,
    RefreshRequest,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    CurrentUser,
)
from app.auth.dependencies import CurrentUser as AuthUser
from app.users.service import UserService


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    x_tenant_id: Annotated[str, Header()],
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate user and return tokens.
    
    Returns access token (short-lived) and refresh token (long-lived).
    """
    service = AuthService(db, UUID(x_tenant_id))
    
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    return await service.login(data, ip_address, user_agent)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    data: RefreshRequest,
    x_tenant_id: Annotated[str, Header()],
    db: AsyncSession = Depends(get_db),
):
    """
    Refresh access token using refresh token.
    
    Old refresh token is revoked and new pair is issued.
    """
    service = AuthService(db, UUID(x_tenant_id))
    return await service.refresh_token(data.refresh_token)


@router.post("/logout")
async def logout(
    x_tenant_id: Annotated[str, Header()],
    user: AuthUser,
    db: AsyncSession = Depends(get_db),
    refresh_token: Optional[str] = None,
):
    """
    Logout user and revoke tokens.
    
    If refresh_token provided, only that token is revoked.
    Otherwise, all user tokens are revoked.
    """
    service = AuthService(db, UUID(x_tenant_id))
    await service.logout(user.user_id, refresh_token)
    return {"success": True, "message": "Logged out successfully"}


@router.post("/change-password")
async def change_password(
    data: ChangePasswordRequest,
    x_tenant_id: Annotated[str, Header()],
    user: AuthUser,
    db: AsyncSession = Depends(get_db),
):
    """
    Change current user's password.
    
    All existing refresh tokens are revoked.
    """
    service = AuthService(db, UUID(x_tenant_id))
    await service.change_password(user.user_id, data)
    return {"success": True, "message": "Password changed successfully"}


@router.post("/forgot-password")
async def forgot_password(
    data: ForgotPasswordRequest,
    x_tenant_id: Annotated[str, Header()],
    db: AsyncSession = Depends(get_db),
):
    """
    Request password reset email.
    
    If email exists, reset token is sent.
    Returns success regardless to prevent email enumeration.
    """
    # TODO: Implement password reset email
    return {
        "success": True,
        "message": "If an account exists with this email, you will receive reset instructions.",
    }


@router.post("/reset-password")
async def reset_password(
    data: ResetPasswordRequest,
    x_tenant_id: Annotated[str, Header()],
    db: AsyncSession = Depends(get_db),
):
    """
    Reset password using token from email.
    """
    # TODO: Implement password reset with token
    return {"success": True, "message": "Password reset successfully"}


@router.get("/me", response_model=CurrentUser)
async def get_current_user(
    user: AuthUser,
    db: AsyncSession = Depends(get_db),
):
    """
    Get current authenticated user info.
    
    Loads full profile details from the database while using
    roles and permissions from the auth context.
    """
    service = UserService(db, user.tenant_id)
    db_user = await service.get_user(user.user_id)
    
    return CurrentUser(
        id=db_user.id,
        tenant_id=db_user.tenant_id,
        email=db_user.email,
        first_name=db_user.first_name,
        last_name=db_user.last_name,
        roles=user.roles,
        permissions=list(user.permissions),
    )
