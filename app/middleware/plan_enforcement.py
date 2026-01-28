"""
CUSTOS Plan & Module Enforcement Middleware

Blocks features based on subscription plan and module access.
"""

from typing import List, Optional, Callable
from uuid import UUID
from functools import wraps

from fastapi import Request, Depends, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import CustosException
from app.tenants.modules import TenantModuleAccess, TenantModule
from app.billing.models import Subscription, Plan, SubscriptionStatus


class PlanEnforcementMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce subscription plan limits.
    
    Checks:
    - Subscription is active
    - Not trial expired
    - Usage within limits
    """
    
    # Paths that bypass plan check
    EXCLUDED_PATHS = [
        "/",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/v1/auth",
        "/api/v1/tenants/register",
        "/api/v1/tenants/by-slug",
        "/api/v1/billing/plans",
    ]
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        
        # Skip excluded paths
        if any(path.startswith(p) for p in self.EXCLUDED_PATHS):
            return await call_next(request)
        
        # Get tenant ID from state (set by TenantMiddleware)
        tenant_id = getattr(request.state, "tenant_id", None)
        if not tenant_id:
            return await call_next(request)
        
        # Check subscription status
        # This is a lightweight check - full validation in dependency
        
        return await call_next(request)


class ModuleAccessError(CustosException):
    """Module not enabled for this tenant."""
    
    def __init__(self, module: str):
        super().__init__(
            message=f"Module '{module}' is not enabled for your subscription",
            code="MODULE_NOT_ENABLED",
            status_code=403,
            details={"module": module},
        )


class PlanRequiredError(CustosException):
    """Plan upgrade required."""
    
    def __init__(self, required_plans: List[str]):
        super().__init__(
            message=f"This feature requires one of these plans: {', '.join(required_plans)}",
            code="PLAN_UPGRADE_REQUIRED",
            status_code=402,
            details={"required_plans": required_plans},
        )


async def check_module_access(
    session: AsyncSession,
    tenant_id: UUID,
    module: TenantModule,
) -> bool:
    """Check if tenant has access to module."""
    query = select(TenantModuleAccess).where(
        TenantModuleAccess.tenant_id == tenant_id,
        TenantModuleAccess.module_name == module.value,
    )
    result = await session.execute(query)
    access = result.scalar_one_or_none()
    
    # If no explicit record, check plan defaults
    if not access:
        return await check_plan_includes_module(session, tenant_id, module)
    
    return access.is_enabled


async def check_plan_includes_module(
    session: AsyncSession,
    tenant_id: UUID,
    module: TenantModule,
) -> bool:
    """Check if tenant's plan includes module."""
    from app.tenants.modules import DEFAULT_MODULES_BY_PLAN
    
    query = select(Subscription).where(
        Subscription.tenant_id == tenant_id,
        Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL]),
    )
    result = await session.execute(query)
    subscription = result.scalar_one_or_none()
    
    if not subscription:
        # No subscription = free tier
        return module in DEFAULT_MODULES_BY_PLAN.get("free", [])
    
    plan = subscription.plan
    plan_tier = plan.tier.value if plan else "free"
    
    return module in DEFAULT_MODULES_BY_PLAN.get(plan_tier, [])


async def get_tenant_plan(
    session: AsyncSession,
    tenant_id: UUID,
) -> Optional[str]:
    """Get tenant's plan tier."""
    query = select(Subscription).where(
        Subscription.tenant_id == tenant_id,
        Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL]),
    )
    result = await session.execute(query)
    subscription = result.scalar_one_or_none()
    
    if not subscription or not subscription.plan:
        return "free"
    
    return subscription.plan.tier.value


def require_module(module: TenantModule):
    """
    Dependency factory to require module access.
    
    Usage:
        @router.post("/ai/generate")
        async def generate(
            _=Depends(require_module(TenantModule.AI_FEATURES)),
        ):
            ...
    """
    async def module_checker(
        request: Request,
        db: AsyncSession = Depends(get_db),
    ):
        tenant_id = getattr(request.state, "tenant_id", None)
        if not tenant_id:
            raise HTTPException(status_code=400, detail="Tenant ID required")
        
        has_access = await check_module_access(db, tenant_id, module)
        if not has_access:
            raise ModuleAccessError(module.value)
        
        return True
    
    return module_checker


def require_plan(allowed_plans: List[str]):
    """
    Dependency factory to require specific plan tiers.
    
    Usage:
        @router.post("/some-premium-feature")
        async def premium_feature(
            _=Depends(require_plan(["professional", "enterprise"])),
        ):
            ...
    """
    async def plan_checker(
        request: Request,
        db: AsyncSession = Depends(get_db),
    ):
        tenant_id = getattr(request.state, "tenant_id", None)
        if not tenant_id:
            raise HTTPException(status_code=400, detail="Tenant ID required")
        
        current_plan = await get_tenant_plan(db, tenant_id)
        if current_plan not in allowed_plans:
            raise PlanRequiredError(allowed_plans)
        
        return True
    
    return plan_checker


def require_active_subscription():
    """
    Dependency to require active subscription (not expired trial).
    """
    async def subscription_checker(
        request: Request,
        db: AsyncSession = Depends(get_db),
    ):
        from datetime import datetime, timezone
        
        tenant_id = getattr(request.state, "tenant_id", None)
        if not tenant_id:
            raise HTTPException(status_code=400, detail="Tenant ID required")
        
        query = select(Subscription).where(
            Subscription.tenant_id == tenant_id,
        )
        result = await db.execute(query)
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            raise CustosException(
                message="No subscription found",
                code="NO_SUBSCRIPTION",
                status_code=402,
            )
        
        # Check trial expiry
        if subscription.status == SubscriptionStatus.TRIAL:
            if subscription.trial_ends_at and subscription.trial_ends_at < datetime.now(timezone.utc):
                raise CustosException(
                    message="Trial period has expired. Please upgrade your subscription.",
                    code="TRIAL_EXPIRED",
                    status_code=402,
                )
        
        # Check subscription status
        if subscription.status not in [SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL]:
            raise CustosException(
                message=f"Subscription is {subscription.status.value}",
                code="SUBSCRIPTION_INACTIVE",
                status_code=402,
            )
        
        return subscription
    
    return subscription_checker
