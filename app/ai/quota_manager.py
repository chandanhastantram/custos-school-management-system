"""
CUSTOS AI Quota Management

Per-plan AI quotas with subscription tier limits.
"""

from datetime import datetime
from typing import Optional, Dict
from uuid import UUID
from enum import Enum

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UsageLimitExceededError


class SubscriptionTier(str, Enum):
    """Subscription tier levels."""
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


# Per-plan AI request limits (monthly)
TIER_AI_LIMITS: Dict[SubscriptionTier, dict] = {
    SubscriptionTier.FREE: {
        "ai_requests": 25,
        "ocr_requests": 5,
        "lesson_plan_gen": 3,
        "question_gen": 10,
        "max_questions_per_gen": 20,
    },
    SubscriptionTier.STARTER: {
        "ai_requests": 100,
        "ocr_requests": 25,
        "lesson_plan_gen": 10,
        "question_gen": 50,
        "max_questions_per_gen": 50,
    },
    SubscriptionTier.PROFESSIONAL: {
        "ai_requests": 500,
        "ocr_requests": 100,
        "lesson_plan_gen": 50,
        "question_gen": 200,
        "max_questions_per_gen": 100,
    },
    SubscriptionTier.ENTERPRISE: {
        "ai_requests": 2000,
        "ocr_requests": 500,
        "lesson_plan_gen": 200,
        "question_gen": 1000,
        "max_questions_per_gen": 200,
    },
}


class AIQuotaManager:
    """
    Manages AI quotas per subscription tier.
    
    Features:
    - Per-plan limits
    - Monthly reset
    - Quota checking before AI calls
    - Usage tracking
    """
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
        self._tier: Optional[SubscriptionTier] = None
    
    async def get_tenant_tier(self) -> SubscriptionTier:
        """Get tenant's subscription tier."""
        if self._tier:
            return self._tier
        
        from app.billing.models import Subscription, SubscriptionStatus
        
        query = select(Subscription).where(
            Subscription.tenant_id == self.tenant_id,
            Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL]),
            Subscription.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        subscription = result.scalar_one_or_none()
        
        if subscription and subscription.tier:
            # tier is a PlanTier enum, map to SubscriptionTier
            tier_value = subscription.tier.value if hasattr(subscription.tier, 'value') else str(subscription.tier)
        else:
            tier_value = SubscriptionTier.STARTER.value  # Default
        
        try:
            self._tier = SubscriptionTier(tier_value)
        except ValueError:
            self._tier = SubscriptionTier.STARTER
        
        return self._tier
    
    async def get_limits(self) -> dict:
        """Get AI limits for tenant's tier."""
        tier = await self.get_tenant_tier()
        return TIER_AI_LIMITS.get(tier, TIER_AI_LIMITS[SubscriptionTier.STARTER])
    
    async def get_usage(self) -> dict:
        """Get current month's AI usage."""
        from app.billing.models import UsageLimit
        
        now = datetime.now()
        query = select(UsageLimit).where(
            UsageLimit.tenant_id == self.tenant_id,
            UsageLimit.year == now.year,
            UsageLimit.month == now.month,
        )
        result = await self.session.execute(query)
        usage = result.scalar_one_or_none()
        
        if usage:
            return {
                "ai_requests": usage.ai_requests_used,
                "ocr_requests": getattr(usage, 'ocr_requests_used', 0),
                "lesson_plan_gen": getattr(usage, 'lesson_plan_gen_used', 0),
                "question_gen": getattr(usage, 'question_gen_used', 0),
            }
        
        return {
            "ai_requests": 0,
            "ocr_requests": 0,
            "lesson_plan_gen": 0,
            "question_gen": 0,
        }
    
    async def check_quota(
        self,
        quota_type: str = "ai_requests",
        count: int = 1,
    ) -> None:
        """
        Check if quota is available.
        
        Raises UsageLimitExceededError if exceeded.
        """
        limits = await self.get_limits()
        usage = await self.get_usage()
        
        limit = limits.get(quota_type, limits.get("ai_requests", 100))
        used = usage.get(quota_type, usage.get("ai_requests", 0))
        
        if used + count > limit:
            tier = await self.get_tenant_tier()
            raise UsageLimitExceededError(
                f"{quota_type} ({tier.value})",
                used,
                limit,
            )
    
    async def increment_usage(
        self,
        quota_type: str = "ai_requests",
        count: int = 1,
    ) -> None:
        """Increment usage counter."""
        from app.billing.models import UsageLimit
        
        now = datetime.now()
        query = select(UsageLimit).where(
            UsageLimit.tenant_id == self.tenant_id,
            UsageLimit.year == now.year,
            UsageLimit.month == now.month,
        )
        result = await self.session.execute(query)
        usage = result.scalar_one_or_none()
        
        if not usage:
            usage = UsageLimit(
                tenant_id=self.tenant_id,
                year=now.year,
                month=now.month,
            )
            self.session.add(usage)
        
        # Increment the appropriate counter
        current = getattr(usage, f"{quota_type}_used", 0) if hasattr(usage, f"{quota_type}_used") else 0
        
        if quota_type == "ai_requests":
            usage.ai_requests_used = current + count
        elif hasattr(usage, f"{quota_type}_used"):
            setattr(usage, f"{quota_type}_used", current + count)
        else:
            usage.ai_requests_used += count
        
        await self.session.flush()
    
    async def get_quota_status(self) -> dict:
        """Get complete quota status."""
        tier = await self.get_tenant_tier()
        limits = await self.get_limits()
        usage = await self.get_usage()
        
        status = {
            "tier": tier.value,
            "limits": limits,
            "usage": usage,
            "remaining": {},
            "percent_used": {},
        }
        
        for key in limits:
            limit_val = limits[key]
            used_val = usage.get(key, 0)
            status["remaining"][key] = max(0, limit_val - used_val)
            status["percent_used"][key] = round((used_val / limit_val) * 100, 2) if limit_val > 0 else 0
        
        return status
