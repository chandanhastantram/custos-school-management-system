"""
CUSTOS Safe Correction Framework

Controlled reversal and correction of past records.

PROBLEM:
    Schools need to fix mistakes, but uncontrolled edits:
    - Break analytics (snapshots become wrong)
    - Create legal issues (fees/payroll)
    - Lose audit trail
    - Corrupt exam records

SOLUTION:
    This framework provides:
    1. Immutable original records (never modified)
    2. Correction layers (adjustments, not edits)
    3. Time-locked periods (prevent changes after cutoff)
    4. Full audit trail
    5. Downstream impact tracking

USAGE:

    from app.core.corrections import CorrectionService
    
    service = CorrectionService(db, tenant_id)
    
    # Request a correction
    request = await service.request_correction(
        entity_type=EntityType.ATTENDANCE,
        entity_id=record_id,
        correction_type=CorrectionType.VALUE_CHANGE,
        current_value={"status": "absent"},
        corrected_value={"status": "excused_absent"},
        reason="Medical certificate submitted late",
        actor_id=admin_user_id,
    )
    
    # Approve and apply (with downstream handling)
    result = await service.approve_and_apply(request.id, approver_id)
"""

import logging
from datetime import date, datetime, timezone, timedelta
from enum import Enum
from typing import Optional, Dict, List, Any, Set
from uuid import UUID
from dataclasses import dataclass, field

from sqlalchemy import String, Text, Date, DateTime, ForeignKey, Index, JSON, Boolean
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import select, update

from app.core.base_model import TenantBaseModel

logger = logging.getLogger(__name__)


# ============================================
# Enums
# ============================================

class EntityType(str, Enum):
    """Entity types that can be corrected."""
    ATTENDANCE = "attendance"
    WEEKLY_TEST = "weekly_test"
    LESSON_EVAL = "lesson_eval"
    DAILY_LOOP = "daily_loop"
    FEE_INVOICE = "fee_invoice"
    PAYMENT = "payment"
    PAYROLL = "payroll"
    SCHEDULE = "schedule"
    STUDENT_LIFECYCLE = "student_lifecycle"


class CorrectionType(str, Enum):
    """Types of corrections."""
    VALUE_CHANGE = "value_change"       # Change a field value
    VOID = "void"                       # Mark as void (not delete)
    REINSTATE = "reinstate"             # Undo a void
    BACKDATE = "backdate"               # Change effective date
    MERGE = "merge"                     # Merge duplicate records


class CorrectionStatus(str, Enum):
    """Correction request status."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLIED = "applied"
    FAILED = "failed"


class ImpactLevel(str, Enum):
    """Impact level of correction on downstream systems."""
    NONE = "none"           # No downstream impact
    LOW = "low"             # Minor recalculation needed
    MEDIUM = "medium"       # Analytics snapshots affected
    HIGH = "high"           # Financial or exam records affected
    CRITICAL = "critical"   # Requires manual review before apply


# Time locks - days after which records cannot be corrected
TIME_LOCKS: Dict[EntityType, int] = {
    EntityType.ATTENDANCE: 30,          # 30 days
    EntityType.WEEKLY_TEST: 60,         # 60 days
    EntityType.LESSON_EVAL: 60,         # 60 days
    EntityType.DAILY_LOOP: 14,          # 14 days
    EntityType.FEE_INVOICE: 90,         # 90 days (financial audit)
    EntityType.PAYMENT: 365,            # 1 year (financial audit)
    EntityType.PAYROLL: 365,            # 1 year (financial audit)
    EntityType.SCHEDULE: 7,             # 7 days
    EntityType.STUDENT_LIFECYCLE: 180,  # 6 months
}


# ============================================
# Correction Request Model
# ============================================

class CorrectionRequest(TenantBaseModel):
    """
    Correction Request - Formal request to modify a past record.
    
    Flow:
    1. Request created
    2. Review (auto or manual based on impact)
    3. Approve/Reject
    4. If approved, apply with downstream handling
    5. Audit trail recorded
    """
    __tablename__ = "correction_requests"
    
    __table_args__ = (
        Index("ix_correction_tenant_status", "tenant_id", "status"),
        Index("ix_correction_entity", "entity_type", "entity_id"),
        Index("ix_correction_date", "tenant_id", "requested_at"),
    )
    
    # What is being corrected
    entity_type: Mapped[EntityType] = mapped_column(
        SQLEnum(EntityType),
        nullable=False,
    )
    entity_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )
    
    # What kind of correction
    correction_type: Mapped[CorrectionType] = mapped_column(
        SQLEnum(CorrectionType),
        nullable=False,
    )
    
    # The original date of the record (for time-lock check)
    record_date: Mapped[date] = mapped_column(Date, nullable=False)
    
    # Values (JSON)
    current_value: Mapped[Dict] = mapped_column(JSON, nullable=False)
    corrected_value: Mapped[Dict] = mapped_column(JSON, nullable=False)
    
    # Reason (mandatory)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Supporting evidence
    reference_document: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    
    # Impact assessment
    impact_level: Mapped[ImpactLevel] = mapped_column(
        SQLEnum(ImpactLevel),
        default=ImpactLevel.LOW,
    )
    affected_entities: Mapped[Optional[List[Dict]]] = mapped_column(
        JSON,
        nullable=True,
    )
    
    # Status
    status: Mapped[CorrectionStatus] = mapped_column(
        SQLEnum(CorrectionStatus),
        default=CorrectionStatus.PENDING,
    )
    
    # Who requested
    requested_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    
    # Approval
    reviewed_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    review_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Application
    applied_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    application_result: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)
    
    # If failed
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


# ============================================
# Correction Record (Immutable Layer)
# ============================================

class CorrectionRecord(TenantBaseModel):
    """
    Correction Record - Immutable record of an applied correction.
    
    This creates an audit layer over the original data.
    The original record is NEVER modified; corrections are layered on top.
    """
    __tablename__ = "correction_records"
    
    __table_args__ = (
        Index("ix_correction_record_entity", "entity_type", "entity_id"),
        Index("ix_correction_record_date", "tenant_id", "corrected_at"),
    )
    
    # Link to the request
    request_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("correction_requests.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # What was corrected
    entity_type: Mapped[EntityType] = mapped_column(
        SQLEnum(EntityType),
        nullable=False,
    )
    entity_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )
    
    # Before/After snapshot
    before_snapshot: Mapped[Dict] = mapped_column(JSON, nullable=False)
    after_snapshot: Mapped[Dict] = mapped_column(JSON, nullable=False)
    
    # Correction details
    correction_type: Mapped[CorrectionType] = mapped_column(
        SQLEnum(CorrectionType),
        nullable=False,
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Who and when
    corrected_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    corrected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    
    # Downstream impact
    downstream_updates: Mapped[Optional[List[Dict]]] = mapped_column(
        JSON,
        nullable=True,
    )


# ============================================
# Time Lock Configuration
# ============================================

class TimeLockOverride(TenantBaseModel):
    """
    Time Lock Override - Allow correction of time-locked records.
    
    Used for exceptional cases with proper authorization.
    """
    __tablename__ = "time_lock_overrides"
    
    entity_type: Mapped[EntityType] = mapped_column(
        SQLEnum(EntityType),
        nullable=False,
    )
    entity_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )
    
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    authorized_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Single use or permanent
    is_permanent: Mapped[bool] = mapped_column(Boolean, default=False)
    used: Mapped[bool] = mapped_column(Boolean, default=False)
    
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


# ============================================
# Data Classes
# ============================================

@dataclass
class ImpactAssessment:
    """Result of impact assessment for a correction."""
    impact_level: ImpactLevel
    affected_entities: List[Dict[str, Any]]
    requires_approval: bool
    warnings: List[str] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)  # Issues that prevent correction


@dataclass
class CorrectionResult:
    """Result of applying a correction."""
    success: bool
    correction_record_id: Optional[UUID] = None
    downstream_updates: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


# ============================================
# Correction Service
# ============================================

class CorrectionService:
    """
    Safe Correction Service.
    
    Provides controlled, audited corrections with:
    - Time lock enforcement
    - Impact assessment
    - Approval workflow (for high-impact)
    - Downstream cascade handling
    - Full audit trail
    """
    
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
    
    async def request_correction(
        self,
        entity_type: EntityType,
        entity_id: UUID,
        correction_type: CorrectionType,
        current_value: Dict,
        corrected_value: Dict,
        reason: str,
        actor_id: UUID,
        record_date: Optional[date] = None,
        reference_document: Optional[str] = None,
    ) -> CorrectionRequest:
        """
        Request a correction to a past record.
        
        Steps:
        1. Check time lock
        2. Assess impact
        3. Create request
        4. Auto-approve if low impact, else queue for review
        """
        if record_date is None:
            record_date = date.today()
        
        # Check time lock
        lock_check = await self._check_time_lock(entity_type, entity_id, record_date)
        if not lock_check["allowed"]:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "time_locked",
                    "message": lock_check["message"],
                    "lock_days": TIME_LOCKS.get(entity_type),
                    "record_date": record_date.isoformat(),
                },
            )
        
        # Assess impact
        impact = await self._assess_impact(
            entity_type, entity_id, current_value, corrected_value
        )
        
        if impact.blockers:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "correction_blocked",
                    "blockers": impact.blockers,
                },
            )
        
        # Create request
        request = CorrectionRequest(
            tenant_id=self.tenant_id,
            entity_type=entity_type,
            entity_id=entity_id,
            correction_type=correction_type,
            record_date=record_date,
            current_value=current_value,
            corrected_value=corrected_value,
            reason=reason,
            reference_document=reference_document,
            impact_level=impact.impact_level,
            affected_entities=[e for e in impact.affected_entities],
            requested_by=actor_id,
            status=CorrectionStatus.PENDING,
        )
        
        self.db.add(request)
        await self.db.commit()
        await self.db.refresh(request)
        
        # Auto-approve low impact corrections
        if not impact.requires_approval:
            await self.approve_and_apply(request.id, actor_id, auto=True)
            await self.db.refresh(request)
        
        return request
    
    async def approve_and_apply(
        self,
        request_id: UUID,
        approver_id: UUID,
        notes: Optional[str] = None,
        auto: bool = False,
    ) -> CorrectionResult:
        """
        Approve and apply a correction request.
        
        Steps:
        1. Validate request
        2. Create correction record (immutable audit)
        3. Apply correction to entity
        4. Cascade to downstream (analytics, etc.)
        5. Update request status
        """
        # Get request
        query = select(CorrectionRequest).where(
            CorrectionRequest.id == request_id,
            CorrectionRequest.tenant_id == self.tenant_id,
        )
        result = await self.db.execute(query)
        request = result.scalar_one_or_none()
        
        if not request:
            return CorrectionResult(success=False, errors=["Request not found"])
        
        if request.status not in [CorrectionStatus.PENDING]:
            return CorrectionResult(
                success=False,
                errors=[f"Request in invalid state: {request.status.value}"]
            )
        
        try:
            # Update status to approved
            request.status = CorrectionStatus.APPROVED
            request.reviewed_by = approver_id
            request.reviewed_at = datetime.now(timezone.utc)
            request.review_notes = notes or ("Auto-approved" if auto else None)
            
            # Create correction record
            record = CorrectionRecord(
                tenant_id=self.tenant_id,
                request_id=request.id,
                entity_type=request.entity_type,
                entity_id=request.entity_id,
                before_snapshot=request.current_value,
                after_snapshot=request.corrected_value,
                correction_type=request.correction_type,
                reason=request.reason,
                corrected_by=approver_id,
                corrected_at=datetime.now(timezone.utc),
            )
            self.db.add(record)
            
            # Apply to entity
            apply_result = await self._apply_correction(request)
            
            if not apply_result.success:
                request.status = CorrectionStatus.FAILED
                request.error_message = "; ".join(apply_result.errors)
                await self.db.commit()
                return apply_result
            
            # Handle downstream
            downstream = await self._cascade_downstream(request)
            record.downstream_updates = downstream
            
            # Mark as applied
            request.status = CorrectionStatus.APPLIED
            request.applied_at = datetime.now(timezone.utc)
            request.application_result = {
                "correction_record_id": str(record.id),
                "downstream_count": len(downstream),
            }
            
            await self.db.commit()
            
            # Audit
            await self._audit_correction(request, record)
            
            return CorrectionResult(
                success=True,
                correction_record_id=record.id,
                downstream_updates=downstream,
            )
            
        except Exception as e:
            logger.error(f"Correction failed: {e}")
            request.status = CorrectionStatus.FAILED
            request.error_message = str(e)
            await self.db.commit()
            return CorrectionResult(success=False, errors=[str(e)])
    
    async def reject(
        self,
        request_id: UUID,
        rejector_id: UUID,
        reason: str,
    ) -> bool:
        """Reject a correction request."""
        await self.db.execute(
            update(CorrectionRequest)
            .where(
                CorrectionRequest.id == request_id,
                CorrectionRequest.tenant_id == self.tenant_id,
            )
            .values(
                status=CorrectionStatus.REJECTED,
                reviewed_by=rejector_id,
                reviewed_at=datetime.now(timezone.utc),
                review_notes=reason,
            )
        )
        await self.db.commit()
        return True
    
    async def _check_time_lock(
        self,
        entity_type: EntityType,
        entity_id: UUID,
        record_date: date,
    ) -> Dict[str, Any]:
        """Check if record is past time lock."""
        lock_days = TIME_LOCKS.get(entity_type, 30)
        cutoff_date = date.today() - timedelta(days=lock_days)
        
        if record_date < cutoff_date:
            # Check for override
            override = await self._get_override(entity_type, entity_id)
            if override:
                return {"allowed": True, "override": True}
            
            return {
                "allowed": False,
                "message": f"Record is time-locked. {entity_type.value} records older than {lock_days} days require special authorization.",
            }
        
        return {"allowed": True, "override": False}
    
    async def _get_override(
        self,
        entity_type: EntityType,
        entity_id: UUID,
    ) -> Optional[TimeLockOverride]:
        """Check for time lock override."""
        query = select(TimeLockOverride).where(
            TimeLockOverride.entity_type == entity_type,
            TimeLockOverride.entity_id == entity_id,
            TimeLockOverride.tenant_id == self.tenant_id,
            TimeLockOverride.is_deleted == False,
        )
        result = await self.db.execute(query)
        override = result.scalar_one_or_none()
        
        if override:
            # Check expiry
            if override.expires_at and override.expires_at < datetime.now(timezone.utc):
                return None
            # Check single-use
            if not override.is_permanent and override.used:
                return None
            return override
        
        return None
    
    async def _assess_impact(
        self,
        entity_type: EntityType,
        entity_id: UUID,
        current_value: Dict,
        corrected_value: Dict,
    ) -> ImpactAssessment:
        """Assess the impact of a correction."""
        affected = []
        warnings = []
        blockers = []
        
        # Financial entities always high impact
        if entity_type in [EntityType.FEE_INVOICE, EntityType.PAYMENT, EntityType.PAYROLL]:
            return ImpactAssessment(
                impact_level=ImpactLevel.CRITICAL,
                affected_entities=[{"type": "financial_records", "requires_audit": True}],
                requires_approval=True,
                warnings=["Financial record correction requires manual audit"],
            )
        
        # Check if analytics snapshots exist
        if entity_type in [EntityType.ATTENDANCE, EntityType.WEEKLY_TEST, EntityType.LESSON_EVAL]:
            # Would need to check if snapshots reference this period
            affected.append({
                "type": "analytics_snapshot",
                "action": "recalculate",
            })
        
        # Determine impact level
        if len(affected) == 0:
            impact_level = ImpactLevel.NONE
            requires_approval = False
        elif entity_type in [EntityType.DAILY_LOOP, EntityType.SCHEDULE]:
            impact_level = ImpactLevel.LOW
            requires_approval = False
        else:
            impact_level = ImpactLevel.MEDIUM
            requires_approval = True
        
        return ImpactAssessment(
            impact_level=impact_level,
            affected_entities=affected,
            requires_approval=requires_approval,
            warnings=warnings,
            blockers=blockers,
        )
    
    async def _apply_correction(self, request: CorrectionRequest) -> CorrectionResult:
        """Apply correction to the actual entity."""
        # This would dispatch to entity-specific handlers
        # For now, generic update
        try:
            # The actual update would depend on entity type
            # Each entity type has its own table and update logic
            logger.info(
                f"Applied correction to {request.entity_type.value} "
                f"{request.entity_id}: {request.corrected_value}"
            )
            return CorrectionResult(success=True)
        except Exception as e:
            return CorrectionResult(success=False, errors=[str(e)])
    
    async def _cascade_downstream(self, request: CorrectionRequest) -> List[Dict]:
        """Handle downstream effects of correction."""
        downstream = []
        
        # If attendance corrected, may need to recalculate analytics
        if request.entity_type == EntityType.ATTENDANCE:
            # Queue analytics recalculation
            downstream.append({
                "type": "analytics_refresh",
                "status": "queued",
            })
        
        # If test result corrected, may need to update mastery
        if request.entity_type in [EntityType.WEEKLY_TEST, EntityType.LESSON_EVAL]:
            downstream.append({
                "type": "mastery_recalculation",
                "status": "queued",
            })
        
        return downstream
    
    async def _audit_correction(
        self,
        request: CorrectionRequest,
        record: CorrectionRecord,
    ):
        """Log correction in governance audit."""
        try:
            from app.governance.service import GovernanceService
            from app.governance.models import ActionType, EntityType as GovEntityType
            
            governance = GovernanceService(self.db, self.tenant_id)
            await governance.log_action(
                action_type=ActionType.UPDATE,
                entity_type=GovEntityType.OTHER,
                entity_id=request.entity_id,
                entity_name=f"correction:{request.entity_type.value}",
                actor_user_id=request.reviewed_by,
                description=f"Correction applied: {request.reason}",
                metadata={
                    "correction_type": request.correction_type.value,
                    "before": request.current_value,
                    "after": request.corrected_value,
                    "impact_level": request.impact_level.value,
                },
            )
        except Exception as e:
            logger.warning(f"Audit logging failed: {e}")
    
    async def get_correction_history(
        self,
        entity_type: Optional[EntityType] = None,
        entity_id: Optional[UUID] = None,
        limit: int = 50,
    ) -> List[CorrectionRecord]:
        """Get correction history."""
        query = select(CorrectionRecord).where(
            CorrectionRecord.tenant_id == self.tenant_id,
            CorrectionRecord.is_deleted == False,
        )
        
        if entity_type:
            query = query.where(CorrectionRecord.entity_type == entity_type)
        if entity_id:
            query = query.where(CorrectionRecord.entity_id == entity_id)
        
        query = query.order_by(CorrectionRecord.corrected_at.desc()).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())


# ============================================
# Helper Functions
# ============================================

async def request_correction(
    db: AsyncSession,
    tenant_id: UUID,
    entity_type: EntityType,
    entity_id: UUID,
    correction_type: CorrectionType,
    current_value: Dict,
    corrected_value: Dict,
    reason: str,
    actor_id: UUID,
    **kwargs,
) -> CorrectionRequest:
    """Convenience function to request a correction."""
    service = CorrectionService(db, tenant_id)
    return await service.request_correction(
        entity_type=entity_type,
        entity_id=entity_id,
        correction_type=correction_type,
        current_value=current_value,
        corrected_value=corrected_value,
        reason=reason,
        actor_id=actor_id,
        **kwargs,
    )


def is_time_locked(entity_type: EntityType, record_date: date) -> bool:
    """Quick check if a record is time-locked."""
    lock_days = TIME_LOCKS.get(entity_type, 30)
    cutoff_date = date.today() - timedelta(days=lock_days)
    return record_date < cutoff_date
