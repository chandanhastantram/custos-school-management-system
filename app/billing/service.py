"""
CUSTOS Billing Service
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundError, ValidationError
from app.billing.models import Plan, Subscription, UsageLimit, SubscriptionStatus, BillingCycle


class BillingService:
    """Subscription and billing management."""
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
    
    async def get_plans(self) -> List[Plan]:
        """Get all available plans."""
        query = select(Plan).where(Plan.is_active == True).order_by(Plan.display_order)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_plan(self, plan_id: UUID) -> Plan:
        """Get plan by ID."""
        plan = await self.session.get(Plan, plan_id)
        if not plan:
            raise ResourceNotFoundError("Plan", str(plan_id))
        return plan
    
    async def get_subscription(self) -> Optional[Subscription]:
        """Get current tenant subscription."""
        query = select(Subscription).where(
            Subscription.tenant_id == self.tenant_id
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def subscribe(
        self,
        plan_id: UUID,
        billing_cycle: BillingCycle = BillingCycle.MONTHLY,
    ) -> Subscription:
        """Subscribe to plan."""
        plan = await self.get_plan(plan_id)
        
        # Check existing subscription
        existing = await self.get_subscription()
        if existing and existing.status == SubscriptionStatus.ACTIVE:
            raise ValidationError("Already has active subscription")
        
        now = datetime.now(timezone.utc)
        if billing_cycle == BillingCycle.MONTHLY:
            period_end = now + timedelta(days=30)
        else:
            period_end = now + timedelta(days=365)
        
        subscription = Subscription(
            tenant_id=self.tenant_id,
            plan_id=plan_id,
            status=SubscriptionStatus.ACTIVE,
            billing_cycle=billing_cycle,
            current_period_start=now,
            current_period_end=period_end,
        )
        
        if existing:
            await self.session.delete(existing)
        
        self.session.add(subscription)
        await self.session.commit()
        await self.session.refresh(subscription)
        return subscription
    
    async def cancel_subscription(self) -> Subscription:
        """Cancel subscription."""
        subscription = await self.get_subscription()
        if not subscription:
            raise ResourceNotFoundError("Subscription", str(self.tenant_id))
        
        subscription.status = SubscriptionStatus.CANCELLED
        subscription.cancelled_at = datetime.now(timezone.utc)
        
        await self.session.commit()
        return subscription
    
    async def get_usage(self) -> UsageLimit:
        """Get current month usage."""
        now = datetime.now(timezone.utc)
        query = select(UsageLimit).where(
            UsageLimit.tenant_id == self.tenant_id,
            UsageLimit.year == now.year,
            UsageLimit.month == now.month,
        )
        result = await self.session.execute(query)
        usage = result.scalar_one_or_none()
        
        if not usage:
            # Create new usage record
            usage = UsageLimit(
                tenant_id=self.tenant_id,
                year=now.year,
                month=now.month,
            )
            self.session.add(usage)
            await self.session.commit()
            await self.session.refresh(usage)
        
        return usage
    
    async def check_limit(self, limit_type: str) -> bool:
        """Check if limit is exceeded."""
        subscription = await self.get_subscription()
        if not subscription:
            return False
        
        usage = await self.get_usage()
        plan = subscription.plan
        
        limits = {
            "students": (usage.student_count, plan.max_students),
            "teachers": (usage.teacher_count, plan.max_teachers),
            "questions": (usage.question_count, plan.max_questions),
            "ai_requests": (usage.ai_requests_used, plan.max_ai_requests),
        }
        
        current, max_limit = limits.get(limit_type, (0, 0))
        return current < max_limit
    
    async def increment_usage(self, usage_type: str, amount: int = 1) -> None:
        """Increment usage counter."""
        usage = await self.get_usage()
        
        if usage_type == "students":
            usage.student_count += amount
        elif usage_type == "teachers":
            usage.teacher_count += amount
        elif usage_type == "questions":
            usage.question_count += amount
        elif usage_type == "ai_requests":
            usage.ai_requests_used += amount
        
        await self.session.commit()
