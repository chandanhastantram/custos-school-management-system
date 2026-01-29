"""
CUSTOS Timetable Router

API endpoints for timetable management.
"""

from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth.dependencies import CurrentUser, require_permission
from app.users.rbac import Permission, SystemRole
from app.scheduling.services.timetable_service import TimetableService
from app.scheduling.schemas.timetable import (
    TimetableCreate,
    TimetableUpdate,
    TimetableResponse,
    TimetableWithEntries,
    TimetableEntryCreate,
    TimetableEntryBulkCreate,
    TimetableEntryUpdate,
    TimetableEntryResponse,
    ClassTimetableView,
    TeacherTimetableView,
    TimetableStats,
)


router = APIRouter(tags=["Timetable"])


# ============================================
# Timetable CRUD Endpoints
# ============================================

@router.post("", response_model=TimetableResponse, status_code=201)
async def create_timetable(
    data: TimetableCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.TIMETABLE_CREATE)),
):
    """
    Create a new timetable (Admin/Principal only).
    
    Creates a timetable template for a specific academic year.
    """
    service = TimetableService(db, user.tenant_id)
    return await service.create_timetable(data)


@router.get("", response_model=dict)
async def list_timetables(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    academic_year_id: Optional[UUID] = None,
    is_active: Optional[bool] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    _=Depends(require_permission(Permission.TIMETABLE_VIEW)),
):
    """
    List timetables with filters.
    """
    service = TimetableService(db, user.tenant_id)
    timetables, total = await service.list_timetables(
        academic_year_id=academic_year_id,
        is_active=is_active,
        page=page,
        size=size,
    )
    
    return {
        "items": [TimetableResponse.model_validate(t) for t in timetables],
        "total": total,
        "page": page,
        "size": size,
    }


@router.get("/stats", response_model=TimetableStats)
async def get_timetable_stats(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    academic_year_id: Optional[UUID] = None,
    _=Depends(require_permission(Permission.TIMETABLE_VIEW)),
):
    """Get timetable statistics."""
    service = TimetableService(db, user.tenant_id)
    return await service.get_stats(academic_year_id)


@router.get("/{timetable_id}", response_model=TimetableWithEntries)
async def get_timetable(
    timetable_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.TIMETABLE_VIEW)),
):
    """Get timetable details with all entries."""
    service = TimetableService(db, user.tenant_id)
    timetable = await service.get_timetable(timetable_id, include_entries=True)
    
    if not timetable:
        raise HTTPException(status_code=404, detail="Timetable not found")
    
    return timetable


@router.patch("/{timetable_id}", response_model=TimetableResponse)
async def update_timetable(
    timetable_id: UUID,
    data: TimetableUpdate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.TIMETABLE_UPDATE)),
):
    """Update a timetable (Admin/Principal only)."""
    service = TimetableService(db, user.tenant_id)
    return await service.update_timetable(timetable_id, data)


@router.delete("/{timetable_id}", status_code=204)
async def delete_timetable(
    timetable_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.TIMETABLE_DELETE)),
):
    """Delete a timetable (Admin/Principal only)."""
    service = TimetableService(db, user.tenant_id)
    await service.delete_timetable(timetable_id)


@router.post("/{timetable_id}/activate", response_model=TimetableResponse)
async def activate_timetable(
    timetable_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.TIMETABLE_UPDATE)),
):
    """Activate a timetable."""
    service = TimetableService(db, user.tenant_id)
    return await service.activate_timetable(timetable_id)


@router.post("/{timetable_id}/deactivate", response_model=TimetableResponse)
async def deactivate_timetable(
    timetable_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.TIMETABLE_UPDATE)),
):
    """Deactivate a timetable."""
    service = TimetableService(db, user.tenant_id)
    return await service.deactivate_timetable(timetable_id)


# ============================================
# Entry Endpoints
# ============================================

@router.post("/{timetable_id}/entries", response_model=TimetableEntryResponse, status_code=201)
async def add_timetable_entry(
    timetable_id: UUID,
    data: TimetableEntryCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.TIMETABLE_CREATE)),
):
    """
    Add an entry to the timetable.
    
    Validates:
    - No teacher conflict (same day+period)
    - No class conflict (same day+period)
    - Teaching assignment exists
    """
    service = TimetableService(db, user.tenant_id)
    return await service.add_entry(timetable_id, data)


@router.post("/{timetable_id}/entries/bulk", response_model=List[TimetableEntryResponse], status_code=201)
async def add_timetable_entries_bulk(
    timetable_id: UUID,
    data: TimetableEntryBulkCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.TIMETABLE_CREATE)),
):
    """
    Add multiple entries at once.
    
    Invalid entries are skipped silently.
    """
    service = TimetableService(db, user.tenant_id)
    entries = await service.add_entries_bulk(timetable_id, data)
    return [TimetableEntryResponse.model_validate(e) for e in entries]


@router.get("/{timetable_id}/entries", response_model=List[TimetableEntryResponse])
async def list_timetable_entries(
    timetable_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    class_id: Optional[UUID] = None,
    teacher_id: Optional[UUID] = None,
    day_of_week: Optional[int] = Query(None, ge=0, le=6),
    _=Depends(require_permission(Permission.TIMETABLE_VIEW)),
):
    """List entries for a timetable with optional filters."""
    service = TimetableService(db, user.tenant_id)
    entries = await service.list_entries(
        timetable_id,
        class_id=class_id,
        teacher_id=teacher_id,
        day_of_week=day_of_week,
    )
    return [TimetableEntryResponse.model_validate(e) for e in entries]


@router.get("/entries/{entry_id}", response_model=TimetableEntryResponse)
async def get_timetable_entry(
    entry_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.TIMETABLE_VIEW)),
):
    """Get a specific timetable entry."""
    service = TimetableService(db, user.tenant_id)
    entry = await service.get_entry(entry_id)
    
    if not entry:
        raise HTTPException(status_code=404, detail="Timetable entry not found")
    
    return entry


@router.patch("/entries/{entry_id}", response_model=TimetableEntryResponse)
async def update_timetable_entry(
    entry_id: UUID,
    data: TimetableEntryUpdate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.TIMETABLE_UPDATE)),
):
    """Update a timetable entry."""
    service = TimetableService(db, user.tenant_id)
    return await service.update_entry(entry_id, data)


@router.delete("/entries/{entry_id}", status_code=204)
async def delete_timetable_entry(
    entry_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.TIMETABLE_DELETE)),
):
    """Delete a timetable entry."""
    service = TimetableService(db, user.tenant_id)
    await service.delete_entry(entry_id)


# ============================================
# View Endpoints
# ============================================

@router.get("/class/{class_id}", response_model=ClassTimetableView)
async def get_class_timetable(
    class_id: UUID,
    academic_year_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    section_id: Optional[UUID] = None,
    max_periods: int = Query(8, ge=1, le=12),
    _=Depends(require_permission(Permission.TIMETABLE_VIEW)),
):
    """
    Get formatted timetable view for a class.
    
    Returns a structured weekly schedule with all periods.
    """
    service = TimetableService(db, user.tenant_id)
    return await service.get_class_timetable(
        class_id=class_id,
        academic_year_id=academic_year_id,
        section_id=section_id,
        max_periods=max_periods,
    )


@router.get("/teacher/{teacher_id}", response_model=TeacherTimetableView)
async def get_teacher_timetable(
    teacher_id: UUID,
    academic_year_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    max_periods: int = Query(8, ge=1, le=12),
    _=Depends(require_permission(Permission.TIMETABLE_VIEW)),
):
    """
    Get formatted timetable view for a teacher.
    
    Returns all classes the teacher teaches across the week.
    """
    service = TimetableService(db, user.tenant_id)
    return await service.get_teacher_timetable(
        teacher_id=teacher_id,
        academic_year_id=academic_year_id,
        max_periods=max_periods,
    )


@router.get("/my-timetable", response_model=TeacherTimetableView)
async def get_my_timetable(
    academic_year_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    max_periods: int = Query(8, ge=1, le=12),
):
    """
    Get current user's timetable (for teachers).
    
    Requires no special permission - users can always view their own timetable.
    """
    service = TimetableService(db, user.tenant_id)
    return await service.get_teacher_timetable(
        teacher_id=user.id,
        academic_year_id=academic_year_id,
        max_periods=max_periods,
    )
