"""
CUSTOS Student Lifecycle Router

API endpoints for student lifecycle management.

Access: Principal and Sub Admin only (STUDENT_LIFECYCLE_MANAGE)
"""

import logging
from datetime import date
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth.dependencies import CurrentUser
from app.users.rbac import Permission
from app.middleware.tenant import get_current_tenant_id
from app.students.lifecycle import StudentLifecycleState
from app.students.service import StudentLifecycleService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/students", tags=["Student Lifecycle"])


# ============================================
# Schemas
# ============================================

class LifecycleTransitionRequest(BaseModel):
    """Request to transition student lifecycle state."""
    new_state: StudentLifecycleState
    effective_date: date = Field(default_factory=date.today)
    reason: str = Field(..., min_length=5, max_length=500)
    reference_document: Optional[str] = None


class LifecycleEventResponse(BaseModel):
    """Response for lifecycle event."""
    id: UUID
    student_id: UUID
    previous_state: str
    new_state: str
    effective_date: date
    reason: str
    reference_document: Optional[str]
    created_at: str
    created_by_id: Optional[UUID]


class ResolvedStateResponse(BaseModel):
    """Current resolved state of a student."""
    student_id: UUID
    state: str
    effective_date: date
    is_active: bool
    reason: Optional[str]


# ============================================
# Endpoints
# ============================================

@router.get("/{student_id}/lifecycle/state")
async def get_student_state(
    student_id: UUID,
    as_of_date: Optional[date] = Query(default=None),
    user: CurrentUser = None,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
) -> ResolvedStateResponse:
    """
    Get current lifecycle state for a student.
    
    Supports date-effective resolution with optional as_of_date parameter.
    """
    service = StudentLifecycleService(db, tenant_id)
    resolved = await service.resolve_state(student_id, as_of_date)
    
    return ResolvedStateResponse(
        student_id=resolved.student_id,
        state=resolved.state.value,
        effective_date=resolved.effective_date,
        is_active=resolved.is_active,
        reason=resolved.reason,
    )


@router.post("/{student_id}/lifecycle/transition")
async def transition_student_state(
    student_id: UUID,
    request: LifecycleTransitionRequest,
    user: CurrentUser = None,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
) -> dict:
    """
    Transition student to a new lifecycle state.
    
    Requires STUDENT_LIFECYCLE_MANAGE permission.
    
    Examples:
    - Set INACTIVE for medical leave
    - Set TRANSFERRED_OUT when student leaves
    - Set GRADUATED at end of final year
    - Set ACTIVE to reactivate a student
    """
    # Check permission
    if not user or Permission.STUDENT_LIFECYCLE_MANAGE not in _get_user_permissions(user):
        raise HTTPException(
            status_code=403,
            detail="STUDENT_LIFECYCLE_MANAGE permission required",
        )
    
    service = StudentLifecycleService(db, tenant_id)
    
    event = await service.transition_state(
        student_id=student_id,
        new_state=request.new_state,
        effective_date=request.effective_date,
        reason=request.reason,
        actor_id=user.user_id,
        reference_document=request.reference_document,
    )
    
    return {
        "success": True,
        "event_id": str(event.id),
        "previous_state": event.previous_state.value,
        "new_state": event.new_state.value,
        "effective_date": event.effective_date.isoformat(),
        "message": f"Student transitioned to {event.new_state.value}",
    }


@router.get("/{student_id}/lifecycle/history")
async def get_lifecycle_history(
    student_id: UUID,
    limit: int = Query(default=50, le=100),
    user: CurrentUser = None,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
) -> List[LifecycleEventResponse]:
    """
    Get lifecycle event history for a student.
    
    Returns events in reverse chronological order.
    """
    service = StudentLifecycleService(db, tenant_id)
    events = await service.get_lifecycle_history(student_id, limit)
    
    return [
        LifecycleEventResponse(
            id=e.id,
            student_id=e.student_id,
            previous_state=e.previous_state.value,
            new_state=e.new_state.value,
            effective_date=e.effective_date,
            reason=e.reason,
            reference_document=e.reference_document,
            created_at=e.created_at.isoformat() if e.created_at else "",
            created_by_id=e.created_by_id,
        )
        for e in events
    ]


@router.get("/by-state/{state}")
async def get_students_by_state(
    state: StudentLifecycleState,
    user: CurrentUser = None,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
) -> dict:
    """
    Get all students in a specific lifecycle state.
    """
    service = StudentLifecycleService(db, tenant_id)
    student_ids = await service.get_students_by_state(state)
    
    return {
        "state": state.value,
        "count": len(student_ids),
        "student_ids": [str(sid) for sid in student_ids],
    }


@router.get("/active/count")
async def get_active_student_count(
    user: CurrentUser = None,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
) -> dict:
    """
    Get count of active students.
    """
    service = StudentLifecycleService(db, tenant_id)
    count = await service.get_active_student_count()
    
    return {
        "active_students": count,
    }


def _get_user_permissions(user) -> set:
    """Helper to get user permissions from context."""
    try:
        if hasattr(user, 'permissions'):
            return set(user.permissions)
        return set()
    except Exception:
        return set()
