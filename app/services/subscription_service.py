"""
CUSTOS Subscription Service

SaaS subscription and plan enforcement.
"""

from datetime import date, datetime, timezone, timedelta
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    SubscriptionError, SubscriptionRequiredError, 
    PlanLimitError, ResourceNotFoundError
)
from app.models.billing import (
    Plan, PlanType, Subscription, SubscriptionStatus, 
    BillingCycle, UsageLimit
)
from app.models.user import User, Role
from app.schemas.billing import SubscriptionCreate


class SubscriptionService:
    """Subscription management service."""
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
    
    async def get_plans(self, include_inactive: bool = False) -> List[Plan]:
        """Get available subscription plans."""
        query = select(Plan).where(Plan.is_public == True)
        if not include_inactive:
            query = query.where(Plan.is_active == True)
        query = query.order_by(Plan.display_order)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_current_subscription(self) -> Optional[Subscription]:
        """Get current tenant subscription."""
        query = select(Subscription).where(
            Subscription.tenant_id == self.tenant_id,
            Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL])
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_usage_limits(self) -> UsageLimit:
        """Get current usage limits for tenant."""
        today = datetime.now(timezone.utc)
        
        query = select(UsageLimit).where(
            UsageLimit.tenant_id == self.tenant_id,
            UsageLimit.year == today.year,
            UsageLimit.month == today.month,
        )
        result = await self.session.execute(query)
        usage = result.scalar_one_or_none()
        
        if not usage:
            usage = UsageLimit(
                tenant_id=self.tenant_id,
                year=today.year,
                month=today.month,
            )
            self.session.add(usage)
            await self.session.commit()
            await self.session.refresh(usage)
        
        return usage
    
    async def check_limit(self, resource: str, increment: int = 1) -> bool:
        """
        Check if resource limit allows operation.
        
        Args:
            resource: students, teachers, admins, storage_mb, ai_tokens
            increment: Amount to add
        
        Returns:
            True if within limits
        
        Raises:
            PlanLimitError: If limit exceeded
        """
        subscription = await self.get_current_subscription()
        
        if not subscription:
            raise SubscriptionRequiredError(resource)
        
        plan = subscription.plan
        usage = await self.get_usage_limits()
        
        limits = {
            "students": (usage.current_students, plan.max_students),
            "teachers": (usage.current_teachers, plan.max_teachers),
            "admins": (usage.current_admins, plan.max_admins),
            "storage_mb": (usage.current_storage_mb, plan.max_storage_gb * 1024),
            "ai_tokens": (usage.current_ai_tokens, plan.ai_tokens_monthly),
        }
        
        if resource not in limits:
            return True
        
        current, max_limit = limits[resource]
        
        if current + increment > max_limit:
            raise PlanLimitError(
                feature=resource,
                current_plan=plan.code,
                required_plan=self._get_next_plan(plan.plan_type),
            )
        
        return True
    
    async def increment_usage(self, resource: str, amount: int = 1) -> None:
        """Increment usage counter."""
        usage = await self.get_usage_limits()
        
        if resource == "students":
            usage.current_students += amount
        elif resource == "teachers":
            usage.current_teachers += amount
        elif resource == "admins":
            usage.current_admins += amount
        elif resource == "storage_mb":
            usage.current_storage_mb += amount
        elif resource == "ai_tokens":
            usage.current_ai_tokens += amount
        
        await self.session.commit()
    
    async def create_subscription(
        self,
        data: SubscriptionCreate,
    ) -> Subscription:
        """Create new subscription."""
        plan = await self.session.get(Plan, data.plan_id)
        if not plan:
            raise ResourceNotFoundError("Plan", str(data.plan_id))
        
        # Cancel existing subscription
        existing = await self.get_current_subscription()
        if existing:
            existing.status = SubscriptionStatus.CANCELLED
            existing.cancelled_at = datetime.now(timezone.utc)
        
        # Calculate dates
        start = date.today()
        if data.billing_cycle == BillingCycle.MONTHLY:
            end = start + timedelta(days=30)
            amount = plan.price_monthly
        else:
            end = start + timedelta(days=365)
            amount = plan.price_yearly
        
        subscription = Subscription(
            tenant_id=self.tenant_id,
            plan_id=plan.id,
            status=SubscriptionStatus.ACTIVE,
            billing_cycle=data.billing_cycle,
            start_date=start,
            end_date=end,
            next_billing_date=end,
            amount=amount,
        )
        
        self.session.add(subscription)
        await self.session.commit()
        await self.session.refresh(subscription)
        
        return subscription
    
    async def start_trial(self, plan_id: UUID) -> Subscription:
        """Start trial subscription."""
        plan = await self.session.get(Plan, plan_id)
        if not plan:
            raise ResourceNotFoundError("Plan", str(plan_id))
        
        start = date.today()
        trial_end = start + timedelta(days=settings.trial_days)
        
        subscription = Subscription(
            tenant_id=self.tenant_id,
            plan_id=plan.id,
            status=SubscriptionStatus.TRIAL,
            billing_cycle=BillingCycle.MONTHLY,
            start_date=start,
            end_date=trial_end,
            trial_end_date=trial_end,
            amount=0,
        )
        
        self.session.add(subscription)
        await self.session.commit()
        
        return subscription
    
    async def cancel_subscription(self, reason: Optional[str] = None) -> Subscription:
        """Cancel current subscription."""
        subscription = await self.get_current_subscription()
        if not subscription:
            raise SubscriptionError("No active subscription")
        
        subscription.status = SubscriptionStatus.CANCELLED
        subscription.cancelled_at = datetime.now(timezone.utc)
        subscription.cancellation_reason = reason
        subscription.auto_renew = False
        
        await self.session.commit()
        return subscription
    
    async def check_feature_access(self, feature: str) -> bool:
        """Check if tenant has access to a feature."""
        subscription = await self.get_current_subscription()
        
        if not subscription:
            return False
        
        plan = subscription.plan
        
        if plan.features and feature in plan.features:
            return True
        
        # Default feature access by plan
        feature_matrix = {
            PlanType.FREE: ["basic_reports"],
            PlanType.STARTER: ["basic_reports", "assignments", "worksheets"],
            PlanType.STANDARD: ["basic_reports", "assignments", "worksheets", "ai_basic"],
            PlanType.PREMIUM: ["basic_reports", "assignments", "worksheets", "ai_basic", "ai_advanced", "custom_reports"],
            PlanType.ENTERPRISE: ["*"],  # All features
        }
        
        allowed = feature_matrix.get(plan.plan_type, [])
        return "*" in allowed or feature in allowed
    
    def _get_next_plan(self, current: PlanType) -> Optional[str]:
        """Get next upgrade plan."""
        upgrade_path = {
            PlanType.FREE: "starter",
            PlanType.STARTER: "standard",
            PlanType.STANDARD: "premium",
            PlanType.PREMIUM: "enterprise",
        }
        return upgrade_path.get(current)
