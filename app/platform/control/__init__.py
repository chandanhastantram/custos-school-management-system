"""
CUSTOS Platform Control

Business & operational readiness layer.

FEATURES:
1. Plan Enforcement - Feature gating by subscription tier
2. Usage Limits - Soft/hard limits with billing signals
3. Tenant Actions - Admin controls (suspend, read-only, etc.)

USAGE:

1. Feature gating:

    from app.platform.control import check_feature, require_feature, FeatureCode
    
    # Check availability
    result = await check_feature(tenant_id, FeatureCode.AI_LESSON_PLAN, db)
    if not result.available:
        return {"error": result.reason, "upgrade_to": result.upgrade_tier}
    
    # Or as decorator
    @require_feature(FeatureCode.AI_OCR)
    async def process_ocr(...):
        ...

2. Usage limits:

    from app.platform.control import check_usage, record_usage, UsageType
    
    # Check before action
    result = await check_usage(tenant_id, UsageType.AI_TOKENS, amount=500)
    if result.blocked:
        return {"error": result.message}
    
    # Record after action
    await record_usage(tenant_id, UsageType.AI_TOKENS, amount=500)

3. Tenant actions (admin):

    from app.platform.control import TenantActionService
    
    service = TenantActionService(db)
    await service.suspend_tenant(tenant_id, admin_id, "Payment overdue")
    await service.set_read_only(tenant_id, admin_id, "Under review")
    await service.emergency_disable_all_ai(tenant_id, admin_id, "Abuse detected")
"""

# Enforcement
from app.platform.control.enforcement import (
    FeatureCode,
    PlanTier,
    FeatureCheckResult,
    TenantPlanInfo,
    PlanEnforcement,
    get_enforcement,
    check_feature,
    require_feature,
    FeatureGate,
    PLAN_FEATURES,
)

# Limits
from app.platform.control.limits import (
    UsageType,
    LimitType,
    UsageLimit,
    UsageCheckResult,
    BillingSignal,
    UsageLimits,
    get_limits,
    check_usage,
    record_usage,
    get_usage_summary,
    DEFAULT_LIMITS,
)

# Tenant Actions
from app.platform.control.tenant_actions import (
    TenantActionType,
    RestrictionLevel,
    TenantAction,
    TenantRestriction,
    TenantActionService,
    is_read_only,
    is_feature_disabled,
)

# Router (imported separately to avoid circular deps)
# from app.platform.control.router import router as control_router

__all__ = [
    # Enforcement
    "FeatureCode",
    "PlanTier",
    "FeatureCheckResult",
    "TenantPlanInfo",
    "PlanEnforcement",
    "get_enforcement",
    "check_feature",
    "require_feature",
    "FeatureGate",
    "PLAN_FEATURES",
    # Limits
    "UsageType",
    "LimitType",
    "UsageLimit",
    "UsageCheckResult",
    "BillingSignal",
    "UsageLimits",
    "get_limits",
    "check_usage",
    "record_usage",
    "get_usage_summary",
    "DEFAULT_LIMITS",
    # Tenant Actions
    "TenantActionType",
    "RestrictionLevel",
    "TenantAction",
    "TenantRestriction",
    "TenantActionService",
    "is_read_only",
    "is_feature_disabled",
]
