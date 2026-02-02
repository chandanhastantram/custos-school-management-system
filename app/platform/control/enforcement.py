"""
CUSTOS Plan Enforcement

Runtime feature gating based on tenant subscription plan.

RULES:
1. Every feature check is fast (in-memory cache)
2. Clear "why unavailable" responses
3. Graceful degradation when plans change
4. No hard crashes on limit exceed

USAGE:

    from app.platform.control import check_feature, require_feature, FeatureCode
    
    # Check if feature available
    if check_feature(tenant_id, FeatureCode.AI_LESSON_PLAN):
        result = await generate_lesson_plan()
    else:
        return {"error": "Upgrade plan for AI lesson planning"}
    
    # Or as decorator
    @require_feature(FeatureCode.AI_OCR)
    async def process_ocr(tenant_id, file_id):
        ...
"""

import logging
from enum import Enum
from typing import Dict, Optional, Any, List, Set
from uuid import UUID
from datetime import datetime, timezone
from dataclasses import dataclass, field
from functools import wraps

from fastapi import HTTPException

logger = logging.getLogger(__name__)


class FeatureCode(str, Enum):
    """
    All gated features in CUSTOS.
    
    Feature codes are tied to plan tiers.
    """
    # Core (always available)
    USERS_BASIC = "users_basic"
    CLASSES_BASIC = "classes_basic"
    ATTENDANCE_BASIC = "attendance_basic"
    
    # Tier 1 - Starter
    SYLLABUS = "syllabus"
    TIMETABLE = "timetable"
    ASSIGNMENTS = "assignments"
    PARENT_ACCESS = "parent_access"
    
    # Tier 2 - Professional
    AI_LESSON_PLAN = "ai_lesson_plan"
    AI_QUESTION_GEN = "ai_question_gen"
    AI_DOUBT_SOLVER = "ai_doubt_solver"
    ANALYTICS_BASIC = "analytics_basic"
    FEE_MANAGEMENT = "fee_management"
    GAMIFICATION = "gamification"
    
    # Tier 3 - Enterprise
    AI_OCR = "ai_ocr"
    AI_INSIGHT = "ai_insight"
    ANALYTICS_ADVANCED = "analytics_advanced"
    CUSTOM_REPORTS = "custom_reports"
    API_ACCESS = "api_access"
    BULK_IMPORT = "bulk_import"
    WHITE_LABEL = "white_label"
    
    # Add-ons (separate purchase)
    SMS_NOTIFICATIONS = "sms_notifications"
    VIDEO_CONFERENCING = "video_conferencing"
    ADVANCED_SECURITY = "advanced_security"


class PlanTier(str, Enum):
    """Subscription plan tiers."""
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"


# Feature availability by plan tier
PLAN_FEATURES: Dict[PlanTier, Set[FeatureCode]] = {
    PlanTier.FREE: {
        FeatureCode.USERS_BASIC,
        FeatureCode.CLASSES_BASIC,
        FeatureCode.ATTENDANCE_BASIC,
    },
    PlanTier.STARTER: {
        FeatureCode.USERS_BASIC,
        FeatureCode.CLASSES_BASIC,
        FeatureCode.ATTENDANCE_BASIC,
        FeatureCode.SYLLABUS,
        FeatureCode.TIMETABLE,
        FeatureCode.ASSIGNMENTS,
        FeatureCode.PARENT_ACCESS,
    },
    PlanTier.PROFESSIONAL: {
        FeatureCode.USERS_BASIC,
        FeatureCode.CLASSES_BASIC,
        FeatureCode.ATTENDANCE_BASIC,
        FeatureCode.SYLLABUS,
        FeatureCode.TIMETABLE,
        FeatureCode.ASSIGNMENTS,
        FeatureCode.PARENT_ACCESS,
        FeatureCode.AI_LESSON_PLAN,
        FeatureCode.AI_QUESTION_GEN,
        FeatureCode.AI_DOUBT_SOLVER,
        FeatureCode.ANALYTICS_BASIC,
        FeatureCode.FEE_MANAGEMENT,
        FeatureCode.GAMIFICATION,
    },
    PlanTier.ENTERPRISE: {
        # All features
        *[f for f in FeatureCode if not f.value.startswith("video_") and f != FeatureCode.WHITE_LABEL],
    },
    PlanTier.CUSTOM: set(),  # Configured per tenant
}


@dataclass
class FeatureCheckResult:
    """Result of a feature availability check."""
    available: bool
    feature: FeatureCode
    reason: Optional[str] = None
    upgrade_tier: Optional[PlanTier] = None
    limit_info: Optional[dict] = None
    
    def to_dict(self) -> dict:
        return {
            "available": self.available,
            "feature": self.feature.value,
            "reason": self.reason,
            "upgrade_tier": self.upgrade_tier.value if self.upgrade_tier else None,
            "limit_info": self.limit_info,
        }


@dataclass
class TenantPlanInfo:
    """Cached plan information for a tenant."""
    tenant_id: UUID
    tier: PlanTier
    features: Set[FeatureCode]
    add_ons: Set[FeatureCode] = field(default_factory=set)
    custom_limits: Dict[str, int] = field(default_factory=dict)
    is_trial: bool = False
    trial_ends_at: Optional[datetime] = None
    is_suspended: bool = False
    is_read_only: bool = False
    disabled_features: Set[FeatureCode] = field(default_factory=set)
    cached_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class PlanEnforcement:
    """
    Plan enforcement engine.
    
    Manages feature gating based on tenant subscription.
    Uses in-memory cache for fast lookups.
    """
    
    _instance: Optional["PlanEnforcement"] = None
    
    # Cache TTL in seconds
    CACHE_TTL = 300  # 5 minutes
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._plan_cache: Dict[UUID, TenantPlanInfo] = {}
        self._initialized = True
    
    async def get_plan_info(self, tenant_id: UUID, db=None) -> TenantPlanInfo:
        """
        Get plan info for a tenant.
        
        Uses cache if available and fresh.
        """
        # Check cache
        if tenant_id in self._plan_cache:
            cached = self._plan_cache[tenant_id]
            age = (datetime.now(timezone.utc) - cached.cached_at).total_seconds()
            if age < self.CACHE_TTL:
                return cached
        
        # Load from database
        plan_info = await self._load_plan_info(tenant_id, db)
        self._plan_cache[tenant_id] = plan_info
        return plan_info
    
    async def _load_plan_info(self, tenant_id: UUID, db=None) -> TenantPlanInfo:
        """Load plan info from database."""
        if db is None:
            # Return default if no DB session
            return TenantPlanInfo(
                tenant_id=tenant_id,
                tier=PlanTier.FREE,
                features=PLAN_FEATURES[PlanTier.FREE],
            )
        
        try:
            from sqlalchemy import select
            from app.tenants.models import Tenant, TenantStatus
            from app.billing.models import Subscription, Plan
            
            # Get tenant
            query = select(Tenant).where(
                Tenant.id == tenant_id,
                Tenant.is_deleted == False,
            )
            result = await db.execute(query)
            tenant = result.scalar_one_or_none()
            
            if not tenant:
                return TenantPlanInfo(
                    tenant_id=tenant_id,
                    tier=PlanTier.FREE,
                    features=set(),
                    is_suspended=True,
                )
            
            # Determine tier from subscription
            tier = PlanTier.FREE
            is_trial = tenant.status == TenantStatus.TRIAL
            
            # Get active subscription
            sub_query = select(Subscription).where(
                Subscription.tenant_id == tenant_id,
                Subscription.is_active == True,
            )
            sub_result = await db.execute(sub_query)
            subscription = sub_result.scalar_one_or_none()
            
            if subscription:
                # Get plan tier from subscription
                plan_query = select(Plan).where(Plan.id == subscription.plan_id)
                plan_result = await db.execute(plan_query)
                plan = plan_result.scalar_one_or_none()
                if plan:
                    tier = PlanTier(plan.tier.value)
            
            # Get features for tier
            features = PLAN_FEATURES.get(tier, set()).copy()
            
            # Add any tenant-specific add-ons
            add_ons = set()
            if tenant.metadata and tenant.metadata.get("add_ons"):
                for addon in tenant.metadata.get("add_ons", []):
                    try:
                        add_ons.add(FeatureCode(addon))
                        features.add(FeatureCode(addon))
                    except ValueError:
                        pass
            
            # Check for disabled features
            disabled = set()
            if tenant.metadata and tenant.metadata.get("disabled_features"):
                for feat in tenant.metadata.get("disabled_features", []):
                    try:
                        disabled.add(FeatureCode(feat))
                        features.discard(FeatureCode(feat))
                    except ValueError:
                        pass
            
            return TenantPlanInfo(
                tenant_id=tenant_id,
                tier=tier,
                features=features,
                add_ons=add_ons,
                is_trial=is_trial,
                trial_ends_at=tenant.trial_ends_at if hasattr(tenant, 'trial_ends_at') else None,
                is_suspended=tenant.status == TenantStatus.SUSPENDED,
                is_read_only=tenant.metadata.get("read_only", False) if tenant.metadata else False,
                disabled_features=disabled,
            )
            
        except Exception as e:
            logger.warning(f"Failed to load plan info for {tenant_id}: {e}")
            return TenantPlanInfo(
                tenant_id=tenant_id,
                tier=PlanTier.FREE,
                features=PLAN_FEATURES[PlanTier.FREE],
            )
    
    def check_feature(
        self,
        plan_info: TenantPlanInfo,
        feature: FeatureCode,
    ) -> FeatureCheckResult:
        """
        Check if a feature is available for a tenant.
        
        Returns structured result with reason if unavailable.
        """
        # Check suspended
        if plan_info.is_suspended:
            return FeatureCheckResult(
                available=False,
                feature=feature,
                reason="Account is suspended. Please contact support.",
            )
        
        # Check explicitly disabled
        if feature in plan_info.disabled_features:
            return FeatureCheckResult(
                available=False,
                feature=feature,
                reason="This feature has been disabled for your account.",
            )
        
        # Check feature availability
        if feature in plan_info.features:
            return FeatureCheckResult(
                available=True,
                feature=feature,
            )
        
        # Feature not available - determine upgrade path
        upgrade_tier = self._get_upgrade_tier(feature)
        
        return FeatureCheckResult(
            available=False,
            feature=feature,
            reason=f"This feature requires the {upgrade_tier.value.title()} plan or higher.",
            upgrade_tier=upgrade_tier,
        )
    
    def _get_upgrade_tier(self, feature: FeatureCode) -> PlanTier:
        """Determine minimum tier required for a feature."""
        for tier in [PlanTier.STARTER, PlanTier.PROFESSIONAL, PlanTier.ENTERPRISE]:
            if feature in PLAN_FEATURES.get(tier, set()):
                return tier
        return PlanTier.ENTERPRISE
    
    def invalidate_cache(self, tenant_id: UUID):
        """Invalidate cached plan info for a tenant."""
        if tenant_id in self._plan_cache:
            del self._plan_cache[tenant_id]
    
    def invalidate_all(self):
        """Invalidate all cached plan info."""
        self._plan_cache.clear()
    
    def get_available_features(self, plan_info: TenantPlanInfo) -> List[str]:
        """Get list of available feature codes for a tenant."""
        return [f.value for f in plan_info.features]
    
    def get_unavailable_features(self, plan_info: TenantPlanInfo) -> List[dict]:
        """Get list of unavailable features with upgrade info."""
        all_features = set(FeatureCode)
        unavailable = all_features - plan_info.features
        
        return [
            {
                "feature": f.value,
                "requires_tier": self._get_upgrade_tier(f).value,
            }
            for f in unavailable
        ]


# Global instance
_enforcement: Optional[PlanEnforcement] = None


def get_enforcement() -> PlanEnforcement:
    """Get the global plan enforcement instance."""
    global _enforcement
    if _enforcement is None:
        _enforcement = PlanEnforcement()
    return _enforcement


async def check_feature(
    tenant_id: UUID,
    feature: FeatureCode,
    db=None,
) -> FeatureCheckResult:
    """
    Check if a feature is available for a tenant.
    
    Convenience function for common use case.
    """
    enforcement = get_enforcement()
    plan_info = await enforcement.get_plan_info(tenant_id, db)
    return enforcement.check_feature(plan_info, feature)


def require_feature(feature: FeatureCode):
    """
    Decorator to require a feature for an endpoint.
    
    Raises 403 if feature not available.
    
    Usage:
        @router.post("/ai/lesson-plan")
        @require_feature(FeatureCode.AI_LESSON_PLAN)
        async def generate_lesson_plan(request: Request):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract tenant_id from request or kwargs
            request = kwargs.get("request")
            tenant_id = None
            
            if request and hasattr(request.state, "tenant_id"):
                tenant_id = request.state.tenant_id
            elif "tenant_id" in kwargs:
                tenant_id = kwargs["tenant_id"]
            
            if not tenant_id:
                raise HTTPException(
                    status_code=400,
                    detail="Tenant context required",
                )
            
            # Check feature
            result = await check_feature(tenant_id, feature)
            
            if not result.available:
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "feature_unavailable",
                        "message": result.reason,
                        "feature": feature.value,
                        "upgrade_to": result.upgrade_tier.value if result.upgrade_tier else None,
                    },
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


class FeatureGate:
    """
    Context manager for feature gating.
    
    Usage:
        async with FeatureGate(tenant_id, FeatureCode.AI_OCR, db) as gate:
            if gate.available:
                result = await do_ocr()
            else:
                result = gate.fallback_response
    """
    
    def __init__(
        self,
        tenant_id: UUID,
        feature: FeatureCode,
        db=None,
        fallback: Any = None,
    ):
        self.tenant_id = tenant_id
        self.feature = feature
        self.db = db
        self.fallback = fallback
        self.available = False
        self.result: Optional[FeatureCheckResult] = None
    
    async def __aenter__(self):
        self.result = await check_feature(self.tenant_id, self.feature, self.db)
        self.available = self.result.available
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return False
    
    @property
    def fallback_response(self) -> dict:
        """Get fallback response for unavailable feature."""
        if self.fallback is not None:
            return self.fallback
        
        return {
            "error": "feature_unavailable",
            "message": self.result.reason if self.result else "Feature not available",
            "feature": self.feature.value,
        }
