"""
CUSTOS Tenant Models

Models for tenant (school) management and subscriptions.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List, TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    String, Text, Boolean, Integer, DateTime, 
    ForeignKey, Enum as SQLEnum, JSON,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel, TimestampMixin, SoftDeleteMixin
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.billing import Subscription


class TenantStatus(str, Enum):
    """Tenant account status."""
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"


class TenantType(str, Enum):
    """Type of educational institution."""
    SCHOOL = "school"
    COLLEGE = "college"
    UNIVERSITY = "university"
    COACHING = "coaching"
    OTHER = "other"


class Tenant(BaseModel, SoftDeleteMixin):
    """
    Tenant model representing a school/institution.
    
    Each tenant is a separate organization with isolated data.
    """
    
    __tablename__ = "tenants"
    
    # Basic Information
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    
    slug: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )
    
    type: Mapped[TenantType] = mapped_column(
        SQLEnum(TenantType),
        default=TenantType.SCHOOL,
        nullable=False,
    )
    
    # Contact Details
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    
    phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )
    
    website: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    
    # Address
    address_line1: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    
    address_line2: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    
    city: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    
    state: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    
    country: Mapped[str] = mapped_column(
        String(100),
        default="India",
        nullable=False,
    )
    
    postal_code: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )
    
    # Branding
    logo_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    
    primary_color: Mapped[Optional[str]] = mapped_column(
        String(7),  # Hex color
        nullable=True,
    )
    
    # Status & Settings
    status: Mapped[TenantStatus] = mapped_column(
        SQLEnum(TenantStatus),
        default=TenantStatus.PENDING,
        nullable=False,
        index=True,
    )
    
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    
    settings: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        default=dict,
    )
    
    # Academic Configuration
    academic_year_start_month: Mapped[int] = mapped_column(
        Integer,
        default=4,  # April
        nullable=False,
    )
    
    timezone: Mapped[str] = mapped_column(
        String(50),
        default="Asia/Kolkata",
        nullable=False,
    )
    
    # Trial & Activation
    trial_ends_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    activated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    # Owner reference
    owner_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Relationships
    users: Mapped[List["User"]] = relationship(
        "User",
        back_populates="tenant",
        foreign_keys="User.tenant_id",
        lazy="selectin",
    )
    
    subscription: Mapped[Optional["Subscription"]] = relationship(
        "Subscription",
        back_populates="tenant",
        uselist=False,
        lazy="selectin",
    )
    
    def __repr__(self) -> str:
        return f"<Tenant(id={self.id}, name='{self.name}', slug='{self.slug}')>"
    
    @property
    def is_active(self) -> bool:
        """Check if tenant is active."""
        return self.status == TenantStatus.ACTIVE and not self.is_deleted
    
    @property
    def is_trial(self) -> bool:
        """Check if tenant is in trial period."""
        if not self.trial_ends_at:
            return False
        return datetime.now(timezone.utc) < self.trial_ends_at
    
    def activate(self) -> None:
        """Activate tenant account."""
        self.status = TenantStatus.ACTIVE
        self.activated_at = datetime.now(timezone.utc)
    
    def suspend(self) -> None:
        """Suspend tenant account."""
        self.status = TenantStatus.SUSPENDED


class TenantDomain(BaseModel):
    """
    Custom domains for tenants.
    
    Allows schools to use their own domain for access.
    """
    
    __tablename__ = "tenant_domains"
    
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    domain: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    
    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    
    verification_token: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    
    verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    # Relationship
    tenant: Mapped["Tenant"] = relationship(
        "Tenant",
        lazy="selectin",
    )


class TenantInvitation(BaseModel):
    """
    Invitation tokens for tenant setup.
    """
    
    __tablename__ = "tenant_invitations"
    
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    
    role_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    token: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    
    invited_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    
    accepted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    @property
    def is_expired(self) -> bool:
        """Check if invitation has expired."""
        return datetime.now(timezone.utc) > self.expires_at
    
    @property
    def is_accepted(self) -> bool:
        """Check if invitation was accepted."""
        return self.accepted_at is not None
