"""
CUSTOS Billing Models

Models for subscriptions and plans.
"""

from datetime import datetime, date
from enum import Enum
from typing import Optional, List, TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    String, Text, Boolean, Integer, DateTime, Date,
    ForeignKey, Enum as SQLEnum, JSON, Float,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel, TenantBaseModel

if TYPE_CHECKING:
    from app.models.tenant import Tenant


class PlanType(str, Enum):
    FREE = "free"
    STARTER = "starter"
    STANDARD = "standard"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class Plan(BaseModel):
    """Subscription plan."""
    __tablename__ = "plans"
    
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    plan_type: Mapped[PlanType] = mapped_column(SQLEnum(PlanType), nullable=False)
    
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    price_monthly: Mapped[float] = mapped_column(Float, default=0.0)
    price_yearly: Mapped[float] = mapped_column(Float, default=0.0)
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    
    max_students: Mapped[int] = mapped_column(Integer, default=100)
    max_teachers: Mapped[int] = mapped_column(Integer, default=10)
    max_admins: Mapped[int] = mapped_column(Integer, default=3)
    max_storage_gb: Mapped[int] = mapped_column(Integer, default=5)
    ai_tokens_monthly: Mapped[int] = mapped_column(Integer, default=10000)
    
    features: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    limits: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)


class SubscriptionStatus(str, Enum):
    TRIAL = "trial"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class BillingCycle(str, Enum):
    MONTHLY = "monthly"
    YEARLY = "yearly"


class Subscription(TenantBaseModel):
    """Tenant subscription."""
    __tablename__ = "subscriptions"
    
    plan_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("plans.id"), nullable=False)
    
    status: Mapped[SubscriptionStatus] = mapped_column(SQLEnum(SubscriptionStatus), nullable=False)
    billing_cycle: Mapped[BillingCycle] = mapped_column(SQLEnum(BillingCycle), default=BillingCycle.MONTHLY)
    
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    trial_end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    next_billing_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    amount: Mapped[float] = mapped_column(Float, default=0.0)
    
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=True)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    cancellation_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    plan: Mapped["Plan"] = relationship("Plan", lazy="selectin")
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="subscription")


class UsageLimit(TenantBaseModel):
    """Current usage limits for a tenant."""
    __tablename__ = "usage_limits"
    
    current_students: Mapped[int] = mapped_column(Integer, default=0)
    current_teachers: Mapped[int] = mapped_column(Integer, default=0)
    current_admins: Mapped[int] = mapped_column(Integer, default=0)
    current_storage_mb: Mapped[int] = mapped_column(Integer, default=0)
    current_ai_tokens: Mapped[int] = mapped_column(Integer, default=0)
    
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
