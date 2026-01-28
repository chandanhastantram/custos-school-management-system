"""
CUSTOS Tenant Models

Tenant (school/institution) database models.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, TYPE_CHECKING
from uuid import UUID

from sqlalchemy import String, Text, Boolean, Integer, DateTime, JSON, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import BaseModel

if TYPE_CHECKING:
    from app.users.models import User
    from app.billing.models import Subscription


class TenantStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    TRIAL = "trial"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"


class TenantType(str, Enum):
    SCHOOL = "school"
    COLLEGE = "college"
    UNIVERSITY = "university"
    COACHING = "coaching"
    OTHER = "other"


class Tenant(BaseModel):
    """
    Tenant represents a school or institution.
    
    This is the root entity for multi-tenancy.
    All other entities reference this via tenant_id.
    """
    __tablename__ = "tenants"
    
    # Basic Info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    type: Mapped[TenantType] = mapped_column(SQLEnum(TenantType), default=TenantType.SCHOOL)
    
    # Contact
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Address
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    country: Mapped[str] = mapped_column(String(100), default="India")
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Branding
    logo: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    primary_color: Mapped[str] = mapped_column(String(7), default="#1E40AF")
    secondary_color: Mapped[str] = mapped_column(String(7), default="#3B82F6")
    
    # Settings
    timezone: Mapped[str] = mapped_column(String(50), default="Asia/Kolkata")
    locale: Mapped[str] = mapped_column(String(10), default="en-IN")
    date_format: Mapped[str] = mapped_column(String(20), default="DD/MM/YYYY")
    
    # Status
    status: Mapped[TenantStatus] = mapped_column(SQLEnum(TenantStatus), default=TenantStatus.PENDING)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Trial
    trial_ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Custom domain
    custom_domain: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    
    # Relationships
    users: Mapped[List["User"]] = relationship("User", back_populates="tenant", lazy="dynamic")
    subscription: Mapped[Optional["Subscription"]] = relationship(
        "Subscription", back_populates="tenant", uselist=False
    )
    
    @property
    def is_active(self) -> bool:
        """Check if tenant is active."""
        return self.status in (TenantStatus.ACTIVE, TenantStatus.TRIAL)


class TenantSettings(BaseModel):
    """Extended tenant settings stored as JSON."""
    __tablename__ = "tenant_settings"
    
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        unique=True,
        nullable=False,
    )
    
    # Academic settings
    academic_year_start_month: Mapped[int] = mapped_column(Integer, default=4)  # April
    grading_system: Mapped[str] = mapped_column(String(50), default="percentage")
    pass_percentage: Mapped[float] = mapped_column(default=35.0)
    
    # Feature toggles
    features: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # Email settings
    email_sender_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    email_sender_address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Notifications
    notification_settings: Mapped[dict] = mapped_column(JSON, default=dict)
