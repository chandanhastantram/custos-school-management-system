"""
CUSTOS Auth Schemas

Authentication request/response schemas.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Login request."""
    email: EmailStr
    password: str = Field(..., min_length=1)
    remember_me: bool = False


class TokenResponse(BaseModel):
    """Token response after successful login."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RefreshRequest(BaseModel):
    """Token refresh request."""
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    """Change password request."""
    current_password: str
    new_password: str = Field(..., min_length=8)


class ForgotPasswordRequest(BaseModel):
    """Forgot password request."""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Reset password with token."""
    token: str
    new_password: str = Field(..., min_length=8)


class CurrentUser(BaseModel):
    """Current authenticated user."""
    id: UUID
    tenant_id: UUID
    email: str
    first_name: str
    last_name: str
    roles: List[str]
    permissions: List[str]
    
    class Config:
        from_attributes = True


# Alias for backward compatibility
UserResponse = CurrentUser


class AuthContext(BaseModel):
    """Authentication context for request."""
    user_id: UUID
    tenant_id: UUID
    email: str
    roles: List[str]
    permissions: set[str]
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has permission."""
        return permission in self.permissions
    
    def has_role(self, role: str) -> bool:
        """Check if user has role."""
        return role in self.roles
    
    def has_any_permission(self, permissions: List[str]) -> bool:
        """Check if user has any of the permissions."""
        return bool(self.permissions & set(permissions))
    
    def has_all_permissions(self, permissions: List[str]) -> bool:
        """Check if user has all permissions."""
        return set(permissions).issubset(self.permissions)
