"""
CUSTOS Platform Control API

Admin endpoints for tenant control and enforcement.

Access: Platform admins only
"""

import logging
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Body
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.platform.admin.dependencies import CurrentPlatformAdmin
from app.platform.control.enforcement import (
    get_enforcement,
    FeatureCode,
    PlanTier,
)
from app.platform.control.limits import (
    get_limits,
    UsageType,
)
from app.platform.control.tenant_actions import (
    TenantActionService,
    TenantActionType,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/control", tags=["Platform Control"])


# ============================================
# Schemas
# ============================================

class SuspendRequest(BaseModel):
    reason: str


class ReadOnlyRequest(BaseModel):
    reason: str
    warning_message: Optional[str] = None


class FeatureToggleRequest(BaseModel):
    feature_code: str
    reason: str


class EmergencyDisableRequest(BaseModel):
    reason: str


# ============================================
# Tenant Control Endpoints
# ============================================

@router.post("/tenants/{tenant_id}/suspend")
async def suspend_tenant(
    tenant_id: UUID,
    request: SuspendRequest,
    admin: CurrentPlatformAdmin,
    db: AsyncSession = Depends(get_db),
):
    """
    Suspend a tenant.
    
    - All users lose access immediately
    - Data is preserved
    - Billing is stopped
    - Requires platform admin
    """
    service = TenantActionService(db)
    action = await service.suspend_tenant(
        tenant_id=tenant_id,
        admin_id=admin.id,
        reason=request.reason,
    )
    
    return {
        "success": True,
        "action": action.to_dict(),
        "message": f"Tenant {tenant_id} suspended",
    }


@router.post("/tenants/{tenant_id}/activate")
async def activate_tenant(
    tenant_id: UUID,
    admin: CurrentPlatformAdmin,
    db: AsyncSession = Depends(get_db),
    reason: str = Query(default="Reactivated by admin"),
):
    """Reactivate a suspended tenant."""
    service = TenantActionService(db)
    action = await service.activate_tenant(
        tenant_id=tenant_id,
        admin_id=admin.id,
        reason=reason,
    )
    
    return {
        "success": True,
        "action": action.to_dict(),
        "message": f"Tenant {tenant_id} activated",
    }


@router.post("/tenants/{tenant_id}/read-only")
async def set_read_only(
    tenant_id: UUID,
    request: ReadOnlyRequest,
    admin: CurrentPlatformAdmin,
    db: AsyncSession = Depends(get_db),
):
    """
    Set tenant to read-only mode.
    
    Users can view data but cannot create/update/delete.
    """
    service = TenantActionService(db)
    action = await service.set_read_only(
        tenant_id=tenant_id,
        admin_id=admin.id,
        reason=request.reason,
        warning_message=request.warning_message,
    )
    
    return {
        "success": True,
        "action": action.to_dict(),
        "message": f"Tenant {tenant_id} set to read-only",
    }


@router.delete("/tenants/{tenant_id}/read-only")
async def clear_read_only(
    tenant_id: UUID,
    admin: CurrentPlatformAdmin,
    db: AsyncSession = Depends(get_db),
    reason: str = Query(default="Read-only cleared"),
):
    """Remove read-only restriction from tenant."""
    service = TenantActionService(db)
    action = await service.clear_read_only(
        tenant_id=tenant_id,
        admin_id=admin.id,
        reason=reason,
    )
    
    return {
        "success": True,
        "action": action.to_dict(),
        "message": f"Read-only cleared for {tenant_id}",
    }


@router.post("/tenants/{tenant_id}/disable-feature")
async def disable_feature(
    tenant_id: UUID,
    request: FeatureToggleRequest,
    admin: CurrentPlatformAdmin,
    db: AsyncSession = Depends(get_db),
):
    """
    Disable a specific feature for a tenant.
    
    The feature will be blocked even if their plan includes it.
    """
    service = TenantActionService(db)
    action = await service.disable_feature(
        tenant_id=tenant_id,
        admin_id=admin.id,
        feature_code=request.feature_code,
        reason=request.reason,
    )
    
    return {
        "success": True,
        "action": action.to_dict(),
        "message": f"Feature '{request.feature_code}' disabled for {tenant_id}",
    }


@router.post("/tenants/{tenant_id}/enable-feature")
async def enable_feature(
    tenant_id: UUID,
    request: FeatureToggleRequest,
    admin: CurrentPlatformAdmin,
    db: AsyncSession = Depends(get_db),
):
    """Re-enable a previously disabled feature."""
    service = TenantActionService(db)
    action = await service.enable_feature(
        tenant_id=tenant_id,
        admin_id=admin.id,
        feature_code=request.feature_code,
        reason=request.reason,
    )
    
    return {
        "success": True,
        "action": action.to_dict(),
        "message": f"Feature '{request.feature_code}' enabled for {tenant_id}",
    }


@router.post("/tenants/{tenant_id}/emergency-disable-ai")
async def emergency_disable_ai(
    tenant_id: UUID,
    request: EmergencyDisableRequest,
    admin: CurrentPlatformAdmin,
    db: AsyncSession = Depends(get_db),
):
    """
    Emergency: Disable all AI features for a tenant.
    
    Use when:
    - Abuse detected
    - Excessive usage
    - Security concern
    """
    service = TenantActionService(db)
    action = await service.emergency_disable_all_ai(
        tenant_id=tenant_id,
        admin_id=admin.id,
        reason=request.reason,
    )
    
    return {
        "success": True,
        "action": action.to_dict(),
        "message": f"All AI features disabled for {tenant_id}",
        "warning": "This is an emergency action. Tenant will not have AI access.",
    }


@router.post("/tenants/{tenant_id}/restore-from-emergency")
async def restore_from_emergency(
    tenant_id: UUID,
    admin: CurrentPlatformAdmin,
    db: AsyncSession = Depends(get_db),
    reason: str = Query(default="Emergency restored"),
):
    """Restore tenant from emergency disable state."""
    service = TenantActionService(db)
    action = await service.restore_from_emergency(
        tenant_id=tenant_id,
        admin_id=admin.id,
        reason=reason,
    )
    
    return {
        "success": True,
        "action": action.to_dict(),
        "message": f"Tenant {tenant_id} restored from emergency state",
    }


@router.get("/tenants/{tenant_id}/restrictions")
async def get_tenant_restrictions(
    tenant_id: UUID,
    admin: CurrentPlatformAdmin,
    db: AsyncSession = Depends(get_db),
):
    """Get current restrictions for a tenant."""
    service = TenantActionService(db)
    restrictions = await service.get_tenant_restrictions(tenant_id)
    
    return {
        "tenant_id": str(tenant_id),
        "level": restrictions.level.value,
        "reason": restrictions.reason,
        "read_only": restrictions.read_only,
        "disabled_features": list(restrictions.disabled_features),
        "warning_message": restrictions.warning_message,
    }


# ============================================
# Usage Limits Endpoints
# ============================================

@router.get("/tenants/{tenant_id}/usage")
async def get_tenant_usage(
    tenant_id: UUID,
    admin: CurrentPlatformAdmin,
    tier: str = Query(default="free"),
):
    """Get usage summary for a tenant."""
    limits = get_limits()
    return {
        "tenant_id": str(tenant_id),
        "tier": tier,
        "usage": limits.get_usage_summary(tenant_id, tier),
    }


@router.post("/tenants/{tenant_id}/usage/reset")
async def reset_tenant_usage(
    tenant_id: UUID,
    admin: CurrentPlatformAdmin,
    usage_type: Optional[str] = Query(default=None),
):
    """
    Reset usage counters for a tenant.
    
    If usage_type specified, resets only that type.
    Otherwise resets all usage.
    """
    limits = get_limits()
    
    if usage_type:
        try:
            ut = UsageType(usage_type)
            limits.reset_usage(tenant_id, ut)
            return {"message": f"Reset {usage_type} usage for {tenant_id}"}
        except ValueError:
            return {"error": f"Unknown usage type: {usage_type}"}
    
    limits.reset_usage(tenant_id)
    return {"message": f"Reset all usage for {tenant_id}"}


@router.get("/billing-signals")
async def get_billing_signals(
    admin: CurrentPlatformAdmin,
    tenant_id: Optional[UUID] = Query(default=None),
    limit: int = Query(default=100, le=500),
):
    """
    Get billing signals generated by usage limits.
    
    These are signals only - no actual charges processed here.
    """
    limits = get_limits()
    signals = limits.get_billing_signals(tenant_id, limit)
    
    return {
        "signals": signals,
        "count": len(signals),
    }


@router.post("/billing-signals/clear")
async def clear_billing_signals(
    admin: CurrentPlatformAdmin,
):
    """Clear billing signals after processing."""
    limits = get_limits()
    limits.clear_billing_signals()
    
    return {"message": "Billing signals cleared"}


# ============================================
# Plan Enforcement Endpoints
# ============================================

@router.get("/features")
async def list_all_features(
    admin: CurrentPlatformAdmin,
):
    """List all feature codes and their tier requirements."""
    from app.platform.control.enforcement import PLAN_FEATURES
    
    features = []
    for code in FeatureCode:
        # Find minimum tier
        min_tier = None
        for tier in [PlanTier.FREE, PlanTier.STARTER, PlanTier.PROFESSIONAL, PlanTier.ENTERPRISE]:
            if code in PLAN_FEATURES.get(tier, set()):
                min_tier = tier
                break
        
        features.append({
            "code": code.value,
            "requires_tier": min_tier.value if min_tier else "enterprise",
        })
    
    return {"features": features}


@router.get("/plans")
async def list_plan_tiers(
    admin: CurrentPlatformAdmin,
):
    """List all plan tiers and their features."""
    from app.platform.control.enforcement import PLAN_FEATURES
    
    plans = {}
    for tier, features in PLAN_FEATURES.items():
        plans[tier.value] = {
            "features": [f.value for f in features],
            "feature_count": len(features),
        }
    
    return {"plans": plans}


@router.post("/cache/invalidate")
async def invalidate_enforcement_cache(
    admin: CurrentPlatformAdmin,
    tenant_id: Optional[UUID] = Query(default=None),
):
    """
    Invalidate plan enforcement cache.
    
    If tenant_id specified, invalidates only that tenant.
    Otherwise invalidates all.
    """
    enforcement = get_enforcement()
    
    if tenant_id:
        enforcement.invalidate_cache(tenant_id)
        return {"message": f"Cache invalidated for {tenant_id}"}
    
    enforcement.invalidate_all()
    return {"message": "All enforcement cache invalidated"}


# ============================================
# Admin Action Log
# ============================================

@router.get("/actions")
async def get_admin_actions(
    admin: CurrentPlatformAdmin,
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=100, le=500),
):
    """Get recent administrative actions on tenants."""
    service = TenantActionService(db)
    actions = service.get_recent_actions(limit)
    
    return {
        "actions": actions,
        "count": len(actions),
    }
