"""
CUSTOS Tenant Actions

Platform owner controls for tenant management.

POWERS:
1. Pause / suspend tenant
2. Set read-only mode
3. Emergency feature disable
4. Restrict specific features
5. Force plan downgrade

All actions are AUDITED.
"""

import logging
from enum import Enum
from typing import Dict, Optional, List, Any, Set
from uuid import UUID
from datetime import datetime, timezone
from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update

logger = logging.getLogger(__name__)


class TenantActionType(str, Enum):
    """Types of administrative actions on tenants."""
    SUSPEND = "suspend"
    ACTIVATE = "activate"
    SET_READ_ONLY = "set_read_only"
    CLEAR_READ_ONLY = "clear_read_only"
    DISABLE_FEATURE = "disable_feature"
    ENABLE_FEATURE = "enable_feature"
    FORCE_DOWNGRADE = "force_downgrade"
    RESTRICT = "restrict"
    UNRESTRICT = "unrestrict"
    EMERGENCY_DISABLE = "emergency_disable"
    EMERGENCY_RESTORE = "emergency_restore"


class RestrictionLevel(str, Enum):
    """Levels of tenant restriction."""
    NONE = "none"           # Full access
    WARNING = "warning"     # Warning banner, full access
    LIMITED = "limited"     # Some features disabled
    READ_ONLY = "read_only" # Read only mode
    SUSPENDED = "suspended" # No access


@dataclass
class TenantAction:
    """Record of an administrative action."""
    action_type: TenantActionType
    tenant_id: UUID
    admin_id: UUID
    reason: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> dict:
        return {
            "action_type": self.action_type.value,
            "tenant_id": str(self.tenant_id),
            "admin_id": str(self.admin_id),
            "reason": self.reason,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class TenantRestriction:
    """Current restrictions on a tenant."""
    tenant_id: UUID
    level: RestrictionLevel = RestrictionLevel.NONE
    reason: Optional[str] = None
    disabled_features: Set[str] = field(default_factory=set)
    read_only: bool = False
    warning_message: Optional[str] = None
    restricted_at: Optional[datetime] = None
    restricted_by: Optional[UUID] = None
    expires_at: Optional[datetime] = None


class TenantActionService:
    """
    Platform owner controls for tenants.
    
    All actions are logged and can be audited.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._action_log: List[TenantAction] = []
    
    async def suspend_tenant(
        self,
        tenant_id: UUID,
        admin_id: UUID,
        reason: str,
    ) -> TenantAction:
        """
        Suspend a tenant.
        
        - All users lose access
        - Data preserved
        - Billing stopped
        """
        from app.tenants.models import Tenant, TenantStatus
        
        # Update tenant
        await self.db.execute(
            update(Tenant)
            .where(Tenant.id == tenant_id)
            .values(
                status=TenantStatus.SUSPENDED,
                metadata=Tenant.metadata + {"suspended_reason": reason, "suspended_at": datetime.now(timezone.utc).isoformat()},
            )
        )
        await self.db.commit()
        
        # Log action
        action = TenantAction(
            action_type=TenantActionType.SUSPEND,
            tenant_id=tenant_id,
            admin_id=admin_id,
            reason=reason,
        )
        
        await self._audit_action(action)
        
        # Invalidate cache
        self._invalidate_tenant_cache(tenant_id)
        
        return action
    
    async def activate_tenant(
        self,
        tenant_id: UUID,
        admin_id: UUID,
        reason: str = "Reactivated by admin",
    ) -> TenantAction:
        """Reactivate a suspended tenant."""
        from app.tenants.models import Tenant, TenantStatus
        
        await self.db.execute(
            update(Tenant)
            .where(Tenant.id == tenant_id)
            .values(
                status=TenantStatus.ACTIVE,
                metadata=Tenant.metadata + {"reactivated_at": datetime.now(timezone.utc).isoformat()},
            )
        )
        await self.db.commit()
        
        action = TenantAction(
            action_type=TenantActionType.ACTIVATE,
            tenant_id=tenant_id,
            admin_id=admin_id,
            reason=reason,
        )
        
        await self._audit_action(action)
        self._invalidate_tenant_cache(tenant_id)
        
        return action
    
    async def set_read_only(
        self,
        tenant_id: UUID,
        admin_id: UUID,
        reason: str,
        warning_message: Optional[str] = None,
    ) -> TenantAction:
        """
        Set tenant to read-only mode.
        
        - Users can view data
        - No create/update/delete operations
        - Warning displayed
        """
        from app.tenants.models import Tenant
        
        await self.db.execute(
            update(Tenant)
            .where(Tenant.id == tenant_id)
            .values(
                metadata=Tenant.metadata + {
                    "read_only": True,
                    "read_only_reason": reason,
                    "read_only_message": warning_message,
                    "read_only_at": datetime.now(timezone.utc).isoformat(),
                },
            )
        )
        await self.db.commit()
        
        action = TenantAction(
            action_type=TenantActionType.SET_READ_ONLY,
            tenant_id=tenant_id,
            admin_id=admin_id,
            reason=reason,
            details={"warning_message": warning_message},
        )
        
        await self._audit_action(action)
        self._invalidate_tenant_cache(tenant_id)
        
        return action
    
    async def clear_read_only(
        self,
        tenant_id: UUID,
        admin_id: UUID,
        reason: str = "Read-only mode cleared",
    ) -> TenantAction:
        """Remove read-only restriction."""
        from app.tenants.models import Tenant
        
        await self.db.execute(
            update(Tenant)
            .where(Tenant.id == tenant_id)
            .values(
                metadata=Tenant.metadata + {
                    "read_only": False,
                    "read_only_cleared_at": datetime.now(timezone.utc).isoformat(),
                },
            )
        )
        await self.db.commit()
        
        action = TenantAction(
            action_type=TenantActionType.CLEAR_READ_ONLY,
            tenant_id=tenant_id,
            admin_id=admin_id,
            reason=reason,
        )
        
        await self._audit_action(action)
        self._invalidate_tenant_cache(tenant_id)
        
        return action
    
    async def disable_feature(
        self,
        tenant_id: UUID,
        admin_id: UUID,
        feature_code: str,
        reason: str,
    ) -> TenantAction:
        """
        Disable a specific feature for a tenant.
        
        Even if their plan includes it.
        """
        from app.tenants.models import Tenant
        from sqlalchemy import select
        
        # Get current metadata
        query = select(Tenant).where(Tenant.id == tenant_id)
        result = await self.db.execute(query)
        tenant = result.scalar_one_or_none()
        
        if tenant:
            metadata = tenant.metadata or {}
            disabled = set(metadata.get("disabled_features", []))
            disabled.add(feature_code)
            metadata["disabled_features"] = list(disabled)
            
            await self.db.execute(
                update(Tenant)
                .where(Tenant.id == tenant_id)
                .values(metadata=metadata)
            )
            await self.db.commit()
        
        action = TenantAction(
            action_type=TenantActionType.DISABLE_FEATURE,
            tenant_id=tenant_id,
            admin_id=admin_id,
            reason=reason,
            details={"feature": feature_code},
        )
        
        await self._audit_action(action)
        self._invalidate_tenant_cache(tenant_id)
        
        return action
    
    async def enable_feature(
        self,
        tenant_id: UUID,
        admin_id: UUID,
        feature_code: str,
        reason: str = "Feature re-enabled",
    ) -> TenantAction:
        """Re-enable a previously disabled feature."""
        from app.tenants.models import Tenant
        from sqlalchemy import select
        
        query = select(Tenant).where(Tenant.id == tenant_id)
        result = await self.db.execute(query)
        tenant = result.scalar_one_or_none()
        
        if tenant:
            metadata = tenant.metadata or {}
            disabled = set(metadata.get("disabled_features", []))
            disabled.discard(feature_code)
            metadata["disabled_features"] = list(disabled)
            
            await self.db.execute(
                update(Tenant)
                .where(Tenant.id == tenant_id)
                .values(metadata=metadata)
            )
            await self.db.commit()
        
        action = TenantAction(
            action_type=TenantActionType.ENABLE_FEATURE,
            tenant_id=tenant_id,
            admin_id=admin_id,
            reason=reason,
            details={"feature": feature_code},
        )
        
        await self._audit_action(action)
        self._invalidate_tenant_cache(tenant_id)
        
        return action
    
    async def emergency_disable_all_ai(
        self,
        tenant_id: UUID,
        admin_id: UUID,
        reason: str,
    ) -> TenantAction:
        """
        Emergency: Disable all AI features for a tenant.
        
        Used when:
        - Abuse detected
        - Excessive usage
        - Security concern
        """
        ai_features = [
            "ai_lesson_plan",
            "ai_question_gen",
            "ai_doubt_solver",
            "ai_ocr",
            "ai_insight",
        ]
        
        from app.tenants.models import Tenant
        from sqlalchemy import select
        
        query = select(Tenant).where(Tenant.id == tenant_id)
        result = await self.db.execute(query)
        tenant = result.scalar_one_or_none()
        
        if tenant:
            metadata = tenant.metadata or {}
            disabled = set(metadata.get("disabled_features", []))
            disabled.update(ai_features)
            metadata["disabled_features"] = list(disabled)
            metadata["emergency_ai_disabled"] = True
            metadata["emergency_ai_disabled_at"] = datetime.now(timezone.utc).isoformat()
            
            await self.db.execute(
                update(Tenant)
                .where(Tenant.id == tenant_id)
                .values(metadata=metadata)
            )
            await self.db.commit()
        
        action = TenantAction(
            action_type=TenantActionType.EMERGENCY_DISABLE,
            tenant_id=tenant_id,
            admin_id=admin_id,
            reason=reason,
            details={"disabled_features": ai_features},
        )
        
        await self._audit_action(action)
        self._invalidate_tenant_cache(tenant_id)
        
        return action
    
    async def restore_from_emergency(
        self,
        tenant_id: UUID,
        admin_id: UUID,
        reason: str = "Emergency restored",
    ) -> TenantAction:
        """Restore from emergency disable."""
        from app.tenants.models import Tenant
        from sqlalchemy import select
        
        query = select(Tenant).where(Tenant.id == tenant_id)
        result = await self.db.execute(query)
        tenant = result.scalar_one_or_none()
        
        if tenant:
            metadata = tenant.metadata or {}
            metadata["disabled_features"] = []
            metadata["emergency_ai_disabled"] = False
            metadata["emergency_restored_at"] = datetime.now(timezone.utc).isoformat()
            
            await self.db.execute(
                update(Tenant)
                .where(Tenant.id == tenant_id)
                .values(metadata=metadata)
            )
            await self.db.commit()
        
        action = TenantAction(
            action_type=TenantActionType.EMERGENCY_RESTORE,
            tenant_id=tenant_id,
            admin_id=admin_id,
            reason=reason,
        )
        
        await self._audit_action(action)
        self._invalidate_tenant_cache(tenant_id)
        
        return action
    
    async def get_tenant_restrictions(self, tenant_id: UUID) -> TenantRestriction:
        """Get current restrictions for a tenant."""
        from app.tenants.models import Tenant, TenantStatus
        from sqlalchemy import select
        
        query = select(Tenant).where(Tenant.id == tenant_id)
        result = await self.db.execute(query)
        tenant = result.scalar_one_or_none()
        
        if not tenant:
            return TenantRestriction(
                tenant_id=tenant_id,
                level=RestrictionLevel.SUSPENDED,
                reason="Tenant not found",
            )
        
        metadata = tenant.metadata or {}
        
        # Determine restriction level
        if tenant.status == TenantStatus.SUSPENDED:
            level = RestrictionLevel.SUSPENDED
            reason = metadata.get("suspended_reason", "Account suspended")
        elif metadata.get("read_only"):
            level = RestrictionLevel.READ_ONLY
            reason = metadata.get("read_only_reason")
        elif metadata.get("disabled_features"):
            level = RestrictionLevel.LIMITED
            reason = "Some features disabled"
        else:
            level = RestrictionLevel.NONE
            reason = None
        
        return TenantRestriction(
            tenant_id=tenant_id,
            level=level,
            reason=reason,
            disabled_features=set(metadata.get("disabled_features", [])),
            read_only=metadata.get("read_only", False),
            warning_message=metadata.get("read_only_message"),
        )
    
    async def _audit_action(self, action: TenantAction):
        """Record action in audit log."""
        try:
            from app.governance.service import GovernanceService
            from app.governance.models import ActionType, EntityType
            
            # Get tenant ID from action
            governance = GovernanceService(self.db, action.tenant_id)
            
            await governance.log_action(
                action_type=ActionType.UPDATE,
                entity_type=EntityType.TENANT,
                entity_id=action.tenant_id,
                entity_name=f"tenant_action:{action.action_type.value}",
                actor_user_id=action.admin_id,
                description=action.reason,
                metadata=action.details,
            )
        except Exception as e:
            logger.warning(f"Failed to audit tenant action: {e}")
        
        # Store locally for retrieval
        self._action_log.append(action)
    
    def _invalidate_tenant_cache(self, tenant_id: UUID):
        """Invalidate plan enforcement cache for tenant."""
        try:
            from app.platform.control.enforcement import get_enforcement
            get_enforcement().invalidate_cache(tenant_id)
        except Exception as e:
            logger.warning(f"Failed to invalidate cache: {e}")
    
    def get_recent_actions(self, limit: int = 100) -> List[dict]:
        """Get recent administrative actions."""
        return [a.to_dict() for a in self._action_log[-limit:]]


async def is_read_only(tenant_id: UUID, db: AsyncSession) -> bool:
    """Quick check if tenant is in read-only mode."""
    from app.tenants.models import Tenant
    from sqlalchemy import select
    
    query = select(Tenant.metadata).where(Tenant.id == tenant_id)
    result = await db.execute(query)
    metadata = result.scalar_one_or_none()
    
    if metadata:
        return metadata.get("read_only", False)
    return False


async def is_feature_disabled(
    tenant_id: UUID,
    feature_code: str,
    db: AsyncSession,
) -> bool:
    """Quick check if a specific feature is disabled for tenant."""
    from app.tenants.models import Tenant
    from sqlalchemy import select
    
    query = select(Tenant.metadata).where(Tenant.id == tenant_id)
    result = await db.execute(query)
    metadata = result.scalar_one_or_none()
    
    if metadata:
        disabled = metadata.get("disabled_features", [])
        return feature_code in disabled
    return False
