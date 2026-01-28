"""
CUSTOS Billing Router
"""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth.dependencies import CurrentUser, require_permission
from app.users.rbac import Permission
from app.billing.service import BillingService
from app.billing.models import BillingCycle


router = APIRouter(tags=["Billing"])


@router.get("/plans")
async def list_plans(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """List available plans."""
    service = BillingService(db, user.tenant_id)
    plans = await service.get_plans()
    return {"plans": plans}


@router.get("/subscription")
async def get_subscription(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Get current subscription."""
    service = BillingService(db, user.tenant_id)
    subscription = await service.get_subscription()
    if not subscription:
        return {"subscription": None}
    return {"subscription": subscription}


@router.post("/subscribe")
async def subscribe(
    plan_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    billing_cycle: BillingCycle = BillingCycle.MONTHLY,
    _=Depends(require_permission(Permission.BILLING_MANAGE)),
):
    """Subscribe to plan."""
    service = BillingService(db, user.tenant_id)
    subscription = await service.subscribe(plan_id, billing_cycle)
    return {"subscription": subscription, "message": "Subscribed successfully"}


@router.post("/cancel")
async def cancel_subscription(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.BILLING_MANAGE)),
):
    """Cancel subscription."""
    service = BillingService(db, user.tenant_id)
    subscription = await service.cancel_subscription()
    return {"subscription": subscription, "message": "Subscription cancelled"}


@router.get("/usage")
async def get_usage(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Get usage statistics."""
    service = BillingService(db, user.tenant_id)
    usage = await service.get_usage()
    subscription = await service.get_subscription()
    
    plan = subscription.plan if subscription else None
    
    return {
        "usage": {
            "students": usage.student_count,
            "teachers": usage.teacher_count,
            "questions": usage.question_count,
            "ai_requests": usage.ai_requests_used,
        },
        "limits": {
            "students": plan.max_students if plan else 50,
            "teachers": plan.max_teachers if plan else 5,
            "questions": plan.max_questions if plan else 500,
            "ai_requests": plan.max_ai_requests if plan else 100,
        },
    }
