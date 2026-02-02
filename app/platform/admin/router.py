"""
CUSTOS Platform Admin Router

Platform-level management endpoints.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.platform.admin.dependencies import (
    CurrentPlatformAdmin, 
    require_platform_permission,
)
from app.tenants.models import Tenant, TenantStatus
from app.billing.models import Plan, Subscription
from app.users.models import User
from app.platform.observability.router import router as observability_router
from app.platform.control.router import router as control_router


router = APIRouter(prefix="/platform", tags=["Platform Admin"])

# Include sub-routers
router.include_router(observability_router)
router.include_router(control_router)


@router.get("/stats")
async def get_platform_stats(
    admin: CurrentPlatformAdmin,
    db: AsyncSession = Depends(get_db),
):
    """Get platform-wide statistics."""
    # Tenant stats
    tenant_count = await db.execute(
        select(func.count()).select_from(Tenant).where(Tenant.is_deleted == False)
    )
    active_tenants = await db.execute(
        select(func.count()).select_from(Tenant).where(
            Tenant.status == TenantStatus.ACTIVE,
            Tenant.is_deleted == False,
        )
    )
    trial_tenants = await db.execute(
        select(func.count()).select_from(Tenant).where(
            Tenant.status == TenantStatus.TRIAL,
            Tenant.is_deleted == False,
        )
    )
    
    # User stats
    user_count = await db.execute(
        select(func.count()).select_from(User).where(User.is_deleted == False)
    )
    
    return {
        "tenants": {
            "total": tenant_count.scalar() or 0,
            "active": active_tenants.scalar() or 0,
            "trial": trial_tenants.scalar() or 0,
        },
        "users": {
            "total": user_count.scalar() or 0,
        },
    }


@router.get("/tenants")
async def list_all_tenants(
    admin: CurrentPlatformAdmin,
    db: AsyncSession = Depends(get_db),
    status: Optional[TenantStatus] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    """List all tenants (platform admin view)."""
    query = select(Tenant).where(Tenant.is_deleted == False)
    
    if status:
        query = query.where(Tenant.status == status)
    
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0
    
    skip = (page - 1) * size
    query = query.order_by(Tenant.created_at.desc()).offset(skip).limit(size)
    result = await db.execute(query)
    tenants = list(result.scalars().all())
    
    return {
        "items": tenants,
        "total": total,
        "page": page,
        "size": size,
    }


@router.post("/tenants/{tenant_id}/activate")
async def activate_tenant(
    tenant_id: UUID,
    admin: CurrentPlatformAdmin,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_platform_permission("tenants:manage")),
):
    """Activate tenant."""
    from app.tenants.service import TenantService
    service = TenantService(db)
    tenant = await service.activate(tenant_id)
    return {"tenant": tenant, "message": "Tenant activated"}


@router.post("/tenants/{tenant_id}/suspend")
async def suspend_tenant(
    tenant_id: UUID,
    admin: CurrentPlatformAdmin,
    db: AsyncSession = Depends(get_db),
    reason: Optional[str] = None,
    _=Depends(require_platform_permission("tenants:suspend")),
):
    """Suspend tenant."""
    from app.tenants.service import TenantService
    service = TenantService(db)
    tenant = await service.suspend(tenant_id, reason)
    return {"tenant": tenant, "message": "Tenant suspended"}


@router.get("/plans")
async def list_plans(
    admin: CurrentPlatformAdmin,
    db: AsyncSession = Depends(get_db),
):
    """List all plans."""
    query = select(Plan).order_by(Plan.display_order)
    result = await db.execute(query)
    return {"plans": list(result.scalars().all())}


@router.post("/plans")
async def create_plan(
    name: str,
    code: str,
    tier: str,
    price_monthly: float,
    price_yearly: float,
    admin: CurrentPlatformAdmin,
    db: AsyncSession = Depends(get_db),
    max_students: int = 50,
    max_teachers: int = 5,
    max_questions: int = 500,
    max_ai_requests: int = 100,
    _=Depends(require_platform_permission("plans:manage")),
):
    """Create new plan."""
    from app.billing.models import PlanTier
    
    plan = Plan(
        name=name,
        code=code,
        tier=PlanTier(tier),
        price_monthly=price_monthly,
        price_yearly=price_yearly,
        max_students=max_students,
        max_teachers=max_teachers,
        max_questions=max_questions,
        max_ai_requests=max_ai_requests,
    )
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return {"plan": plan}
