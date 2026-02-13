"""
CUSTOS Correction API

Safe reversal and correction endpoints.

Access: Admin only (requires CORRECTION_MANAGE permission)
"""

import logging
from datetime import date
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth.dependencies import CurrentUser, require_permission
from app.core.dependencies import get_current_tenant_id
from app.core.corrections import (
    CorrectionService,
    EntityType,
    CorrectionType,
    CorrectionStatus,
    ImpactLevel,
    TIME_LOCKS,
    is_time_locked,
)
from app.users.rbac import Permission

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/corrections", tags=["Corrections"])


# ============================================
# Schemas
# ============================================

class CorrectionRequestCreate(BaseModel):
    """Request to create a correction."""
    entity_type: EntityType
    entity_id: UUID
    correction_type: CorrectionType
    record_date: date
    current_value: dict
    corrected_value: dict
    reason: str = Field(..., min_length=10, max_length=1000)
    reference_document: Optional[str] = None


class CorrectionApproval(BaseModel):
    """Approval or rejection of a correction."""
    notes: Optional[str] = None


class CorrectionResponse(BaseModel):
    """Response for a correction request."""
    id: UUID
    entity_type: str
    entity_id: UUID
    correction_type: str
    status: str
    impact_level: str
    reason: str
    requested_at: str
    reviewed_at: Optional[str]
    applied_at: Optional[str]


class TimeLockInfo(BaseModel):
    """Time lock information for an entity type."""
    entity_type: str
    lock_days: int
    cutoff_date: date


# ============================================
# Endpoints
# ============================================

@router.post("/request")
async def create_correction_request(
    request: CorrectionRequestCreate,
    user: CurrentUser = None,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    """
    Request a correction to a past record.
    
    - Time-locked records require special authorization
    - High-impact corrections require approval
    - Low-impact corrections are auto-approved
    """
    service = CorrectionService(db, tenant_id)
    
    correction = await service.request_correction(
        entity_type=request.entity_type,
        entity_id=request.entity_id,
        correction_type=request.correction_type,
        current_value=request.current_value,
        corrected_value=request.corrected_value,
        reason=request.reason,
        actor_id=user.user_id,
        record_date=request.record_date,
        reference_document=request.reference_document,
    )
    
    return {
        "id": str(correction.id),
        "status": correction.status.value,
        "impact_level": correction.impact_level.value,
        "requires_approval": correction.status == CorrectionStatus.PENDING,
    }


@router.post("/{request_id}/approve")
async def approve_correction(
    request_id: UUID,
    approval: CorrectionApproval,
    user: CurrentUser = None,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    _=Depends(require_permission(Permission.CORRECTION_APPROVE)),
):
    """
    Approve and apply a pending correction.
    
    Requires the CORRECTION_APPROVE permission (typically admins/principals).
    """
    service = CorrectionService(db, tenant_id)
    result = await service.approve_and_apply(
        request_id=request_id,
        approver_id=user.user_id,
        notes=approval.notes,
    )
    
    if not result.success:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "correction_failed",
                "errors": result.errors,
            },
        )
    
    return {
        "success": True,
        "correction_record_id": str(result.correction_record_id) if result.correction_record_id else None,
        "downstream_updates": result.downstream_updates,
    }


@router.post("/{request_id}/reject")
async def reject_correction(
    request_id: UUID,
    reason: str = Query(..., min_length=5),
    user: CurrentUser = None,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    """Reject a pending correction request."""
    service = CorrectionService(db, tenant_id)
    await service.reject(request_id, user.user_id, reason)
    
    return {"success": True, "message": "Correction rejected"}


@router.get("/pending")
async def get_pending_corrections(
    entity_type: Optional[EntityType] = Query(default=None),
    limit: int = Query(default=50, le=100),
    user: CurrentUser = None,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    """Get pending correction requests."""
    from sqlalchemy import select
    from app.core.corrections import CorrectionRequest
    
    query = select(CorrectionRequest).where(
        CorrectionRequest.tenant_id == tenant_id,
        CorrectionRequest.status == CorrectionStatus.PENDING,
    )
    
    if entity_type:
        query = query.where(CorrectionRequest.entity_type == entity_type)
    
    query = query.order_by(CorrectionRequest.requested_at.desc()).limit(limit)
    
    result = await db.execute(query)
    requests = result.scalars().all()
    
    return {
        "count": len(requests),
        "requests": [
            {
                "id": str(r.id),
                "entity_type": r.entity_type.value,
                "entity_id": str(r.entity_id),
                "correction_type": r.correction_type.value,
                "impact_level": r.impact_level.value,
                "reason": r.reason,
                "requested_at": r.requested_at.isoformat() if r.requested_at else None,
            }
            for r in requests
        ],
    }


@router.get("/history")
async def get_correction_history(
    entity_type: Optional[EntityType] = Query(default=None),
    entity_id: Optional[UUID] = Query(default=None),
    limit: int = Query(default=50, le=100),
    user: CurrentUser = None,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    """Get history of applied corrections."""
    service = CorrectionService(db, tenant_id)
    records = await service.get_correction_history(entity_type, entity_id, limit)
    
    return {
        "count": len(records),
        "records": [
            {
                "id": str(r.id),
                "entity_type": r.entity_type.value,
                "entity_id": str(r.entity_id),
                "correction_type": r.correction_type.value,
                "reason": r.reason,
                "corrected_at": r.corrected_at.isoformat() if r.corrected_at else None,
            }
            for r in records
        ],
    }


@router.get("/time-locks")
async def get_time_lock_info(
    user: CurrentUser = None,
):
    """
    Get time lock configuration for all entity types.
    
    Records older than lock_days cannot be corrected without special authorization.
    """
    from datetime import timedelta
    
    locks = []
    today = date.today()
    
    for entity_type, lock_days in TIME_LOCKS.items():
        locks.append({
            "entity_type": entity_type.value,
            "lock_days": lock_days,
            "cutoff_date": (today - timedelta(days=lock_days)).isoformat(),
        })
    
    return {"time_locks": locks}


@router.get("/check-lock")
async def check_time_lock(
    entity_type: EntityType,
    record_date: date,
    user: CurrentUser = None,
):
    """
    Check if a specific record date is time-locked.
    """
    locked = is_time_locked(entity_type, record_date)
    lock_days = TIME_LOCKS.get(entity_type, 30)
    
    return {
        "entity_type": entity_type.value,
        "record_date": record_date.isoformat(),
        "is_locked": locked,
        "lock_days": lock_days,
        "message": f"Records older than {lock_days} days require special authorization" if locked else "Record can be corrected",
    }


@router.get("/{record_id}")
async def get_correction_detail(
    record_id: UUID,
    user: CurrentUser = None,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    """Get detailed view of a correction record."""
    from sqlalchemy import select
    from app.core.corrections import CorrectionRecord
    
    query = select(CorrectionRecord).where(
        CorrectionRecord.id == record_id,
        CorrectionRecord.tenant_id == tenant_id,
    )
    
    result = await db.execute(query)
    record = result.scalar_one_or_none()
    
    if not record:
        raise HTTPException(status_code=404, detail="Correction record not found")
    
    return {
        "id": str(record.id),
        "entity_type": record.entity_type.value,
        "entity_id": str(record.entity_id),
        "correction_type": record.correction_type.value,
        "before_snapshot": record.before_snapshot,
        "after_snapshot": record.after_snapshot,
        "reason": record.reason,
        "corrected_by": str(record.corrected_by) if record.corrected_by else None,
        "corrected_at": record.corrected_at.isoformat() if record.corrected_at else None,
        "downstream_updates": record.downstream_updates,
    }
