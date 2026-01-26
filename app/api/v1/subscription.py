"""
CUSTOS Subscription API Endpoints

Subscription and billing routes.
"""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth import TenantCtx, require_permissions, require_admin, Permission
from app.services.subscription_service import SubscriptionService
from app.schemas.billing import (
    PlanResponse, SubscriptionCreate, SubscriptionResponse, UsageLimitResponse,
)
from app.schemas.common import SuccessResponse


router = APIRouter(prefix="/subscription", tags=["Subscription"])


@router.get("/plans", response_model=list[PlanResponse])
async def list_plans(
    db: AsyncSession = Depends(get_db),
):
    """List available subscription plans."""
    from sqlalchemy import select
    from app.models.billing import Plan
    
    query = select(Plan).where(Plan.is_active == True, Plan.is_public == True)
    query = query.order_by(Plan.display_order)
    result = await db.execute(query)
    plans = list(result.scalars().all())
    
    return [PlanResponse.model_validate(p) for p in plans]


@router.get("/current", response_model=SubscriptionResponse)
async def get_current_subscription(
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
):
    """Get current subscription details."""
    service = SubscriptionService(db, ctx.tenant_id)
    subscription = await service.get_current_subscription()
    
    if not subscription:
        return SuccessResponse(success=False, message="No active subscription")
    
    return SubscriptionResponse.model_validate(subscription)


@router.get("/usage", response_model=UsageLimitResponse)
async def get_usage_limits(
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
):
    """Get current usage and limits."""
    service = SubscriptionService(db, ctx.tenant_id)
    usage = await service.get_usage_limits()
    subscription = await service.get_current_subscription()
    
    plan = subscription.plan if subscription else None
    
    return UsageLimitResponse(
        tenant_id=ctx.tenant_id,
        current_students=usage.current_students,
        max_students=plan.max_students if plan else 0,
        current_teachers=usage.current_teachers,
        max_teachers=plan.max_teachers if plan else 0,
        current_storage_mb=usage.current_storage_mb,
        max_storage_mb=(plan.max_storage_gb * 1024) if plan else 0,
        current_ai_tokens=usage.current_ai_tokens,
        max_ai_tokens=plan.ai_tokens_monthly if plan else 0,
        is_within_limits=True,  # Would need actual check
    )


@router.post("/subscribe", response_model=SubscriptionResponse)
async def create_subscription(
    data: SubscriptionCreate,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin()),
):
    """Create new subscription."""
    service = SubscriptionService(db, ctx.tenant_id)
    subscription = await service.create_subscription(data)
    return SubscriptionResponse.model_validate(subscription)


@router.post("/start-trial", response_model=SubscriptionResponse)
async def start_trial(
    plan_id: UUID,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin()),
):
    """Start trial subscription."""
    service = SubscriptionService(db, ctx.tenant_id)
    subscription = await service.start_trial(plan_id)
    return SubscriptionResponse.model_validate(subscription)


@router.post("/cancel", response_model=SuccessResponse)
async def cancel_subscription(
    reason: str = None,
    ctx: TenantCtx = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin()),
):
    """Cancel current subscription."""
    service = SubscriptionService(db, ctx.tenant_id)
    await service.cancel_subscription(reason)
    return SuccessResponse(message="Subscription cancelled")


@router.get("/check-feature/{feature}")
async def check_feature_access(
    feature: str,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
):
    """Check if tenant has access to a feature."""
    service = SubscriptionService(db, ctx.tenant_id)
    has_access = await service.check_feature_access(feature)
    
    return {
        "feature": feature,
        "has_access": has_access,
    }
