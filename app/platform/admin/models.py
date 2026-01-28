"""
CUSTOS Platform Admin

Platform-level (non-tenant-scoped) admin functionality.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import BaseModel  # NOT TenantBaseModel


class PlatformRole(str):
    """Platform-level roles (not tenant-scoped)."""
    PLATFORM_OWNER = "platform_owner"
    PLATFORM_ADMIN = "platform_admin"
    PLATFORM_SUPPORT = "platform_support"


class PlatformAdmin(BaseModel):
    """
    Platform administrator - global, not tenant-scoped.
    
    These users can:
    - Manage all tenants
    - View platform metrics
    - Handle support
    - Manage plans/billing
    """
    __tablename__ = "platform_admins"
    
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    role: Mapped[str] = mapped_column(String(50), default=PlatformRole.PLATFORM_ADMIN)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class PlatformSettings(BaseModel):
    """Global platform settings."""
    __tablename__ = "platform_settings"
    
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    value: Mapped[str] = mapped_column(String(1000), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)


# Platform permissions (not tenant-scoped)
PLATFORM_PERMISSIONS = {
    PlatformRole.PLATFORM_OWNER: [
        "platform:all",
        "tenants:manage",
        "tenants:suspend",
        "tenants:delete",
        "plans:manage",
        "billing:manage",
        "admins:manage",
        "metrics:view",
        "support:all",
    ],
    PlatformRole.PLATFORM_ADMIN: [
        "tenants:view",
        "tenants:manage",
        "plans:view",
        "billing:view",
        "metrics:view",
        "support:all",
    ],
    PlatformRole.PLATFORM_SUPPORT: [
        "tenants:view",
        "support:tickets",
        "support:users",
    ],
}
