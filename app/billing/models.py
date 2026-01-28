"""
CUSTOS Billing Models

Plan, Subscription, Usage tracking.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, TYPE_CHECKING
from uuid import UUID

from sqlalchemy import String, Text, Boolean, Integer, Float, DateTime, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import BaseModel, TenantBaseModel

if TYPE_CHECKING:
    from app.tenants.models import Tenant


class PlanTier(str, Enum):
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class BillingCycle(str, Enum):
    MONTHLY = "monthly"
    YEARLY = "yearly"


class SubscriptionStatus(str, Enum):
    TRIAL = "trial"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class Plan(BaseModel):
    """Subscription plan."""
    __tablename__ = "plans"
    
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    tier: Mapped[PlanTier] = mapped_column(SQLEnum(PlanTier), default=PlanTier.FREE)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Pricing
    price_monthly: Mapped[float] = mapped_column(Float, default=0)
    price_yearly: Mapped[float] = mapped_column(Float, default=0)
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    
    # Limits
    max_students: Mapped[int] = mapped_column(Integer, default=50)
    max_teachers: Mapped[int] = mapped_column(Integer, default=5)
    max_questions: Mapped[int] = mapped_column(Integer, default=500)
    max_ai_requests: Mapped[int] = mapped_column(Integer, default=100)
    max_storage_mb: Mapped[int] = mapped_column(Integer, default=1000)
    
    # Features
    features: Mapped[dict] = mapped_column(JSON, default=dict)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)


class Subscription(TenantBaseModel):
    """Tenant subscription."""
    __tablename__ = "subscriptions"
    
    plan_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("plans.id"))
    
    status: Mapped[SubscriptionStatus] = mapped_column(
        SQLEnum(SubscriptionStatus), default=SubscriptionStatus.TRIAL
    )
    billing_cycle: Mapped[BillingCycle] = mapped_column(SQLEnum(BillingCycle), default=BillingCycle.MONTHLY)
    
    current_period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    current_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    trial_ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Payment
    payment_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    external_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Stripe/Razorpay ID
    
    # Relationships
    plan: Mapped["Plan"] = relationship("Plan", lazy="selectin")
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="subscription")


class UsageLimit(TenantBaseModel):
    """Usage tracking per tenant."""
    __tablename__ = "usage_limits"
    
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Usage counts
    student_count: Mapped[int] = mapped_column(Integer, default=0)
    teacher_count: Mapped[int] = mapped_column(Integer, default=0)
    question_count: Mapped[int] = mapped_column(Integer, default=0)
    ai_requests_used: Mapped[int] = mapped_column(Integer, default=0)
    storage_used_mb: Mapped[float] = mapped_column(Float, default=0)
