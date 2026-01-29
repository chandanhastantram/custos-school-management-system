"""
CUSTOS Schedule Router

API endpoints for schedule orchestration.
"""

from datetime import date, timedelta
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth.dependencies import CurrentUser, require_permission
from app.users.rbac import Permission, SystemRole
from app.scheduling.services.schedule_service import ScheduleService
from app.scheduling.schemas.schedule import (
    ScheduleEntryStatus,
    CalendarDayCreate,
    CalendarDayBulkCreate,
    CalendarDayUpdate,
    CalendarDayResponse,
    ScheduleEntryResponse,
    ScheduleEntryUpdate,
    GenerateScheduleRequest,
    GenerateScheduleResult,
    ClassScheduleView,
    TeacherScheduleView,
    ScheduleStats,
)


router = APIRouter(tags=["Schedule"])


# ============================================
# Schedule Generation Endpoints
# ============================================

@router.post("/generate/{lesson_plan_id}", response_model=GenerateScheduleResult)
async def generate_schedule(
    lesson_plan_id: UUID,
    request: GenerateScheduleRequest,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.SCHEDULE_GENERATE)),
):
    """
    Generate schedule from a lesson plan.
    
    This links:
    - Lesson plan units (topics in order)
    - Timetable entries (class periods)
    - Academic calendar (working days)
    
    To create: "On date X, period Y, class Z, teach Topic W"
    
    Set regenerate=true to delete existing schedule and regenerate.
    """
    service = ScheduleService(db, user.tenant_id)
    return await service.generate_schedule(lesson_plan_id, request)


# ============================================
# Schedule View Endpoints
# ============================================

@router.get("/class/{class_id}", response_model=ClassScheduleView)
async def get_class_schedule(
    class_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    section_id: Optional[UUID] = None,
    max_periods: int = Query(8, ge=1, le=12),
    _=Depends(require_permission(Permission.SCHEDULE_VIEW)),
):
    """
    Get schedule view for a class.
    
    Returns daily schedules with period slots for the date range.
    Default date range is current week.
    """
    # Default to current week
    if not start_date:
        today = date.today()
        start_date = today - timedelta(days=today.weekday())  # Monday
    if not end_date:
        end_date = start_date + timedelta(days=6)  # Sunday
    
    service = ScheduleService(db, user.tenant_id)
    return await service.get_class_schedule(
        class_id=class_id,
        start_date=start_date,
        end_date=end_date,
        section_id=section_id,
        max_periods=max_periods,
    )


@router.get("/teacher/{teacher_id}", response_model=TeacherScheduleView)
async def get_teacher_schedule(
    teacher_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    max_periods: int = Query(8, ge=1, le=12),
    _=Depends(require_permission(Permission.SCHEDULE_VIEW)),
):
    """
    Get schedule view for a teacher.
    
    Returns daily schedules showing all classes the teacher has.
    """
    if not start_date:
        today = date.today()
        start_date = today - timedelta(days=today.weekday())
    if not end_date:
        end_date = start_date + timedelta(days=6)
    
    service = ScheduleService(db, user.tenant_id)
    return await service.get_teacher_schedule(
        teacher_id=teacher_id,
        start_date=start_date,
        end_date=end_date,
        max_periods=max_periods,
    )


@router.get("/my-schedule", response_model=TeacherScheduleView)
async def get_my_schedule(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    max_periods: int = Query(8, ge=1, le=12),
):
    """
    Get current user's schedule (for teachers).
    
    No special permission required - users can always view their own schedule.
    """
    if not start_date:
        today = date.today()
        start_date = today - timedelta(days=today.weekday())
    if not end_date:
        end_date = start_date + timedelta(days=6)
    
    service = ScheduleService(db, user.tenant_id)
    return await service.get_teacher_schedule(
        teacher_id=user.id,
        start_date=start_date,
        end_date=end_date,
        max_periods=max_periods,
    )


@router.get("/student/{student_id}", response_model=ClassScheduleView)
async def get_student_schedule(
    student_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    max_periods: int = Query(8, ge=1, le=12),
    _=Depends(require_permission(Permission.SCHEDULE_VIEW)),
):
    """
    Get schedule view for a student.
    
    This returns the student's class schedule.
    Note: Requires student's class_id to be looked up (TODO).
    """
    # TODO: Look up student's class_id from enrollment
    # For now, we'd need this to be passed or looked up
    raise HTTPException(
        status_code=501,
        detail="Student schedule lookup requires enrollment integration. Use class schedule endpoint instead.",
    )


# ============================================
# Schedule Entry Endpoints
# ============================================

@router.get("", response_model=dict)
async def list_schedule_entries(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    lesson_plan_id: Optional[UUID] = None,
    class_id: Optional[UUID] = None,
    teacher_id: Optional[UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    status: Optional[ScheduleEntryStatus] = None,
    page: int = Query(1, ge=1),
    size: int = Query(100, ge=1, le=500),
    _=Depends(require_permission(Permission.SCHEDULE_VIEW)),
):
    """List schedule entries with filters."""
    service = ScheduleService(db, user.tenant_id)
    
    # Non-admins can only see their own schedules
    user_roles = [r.code for r in user.roles] if user.roles else []
    admin_roles = {SystemRole.SUPER_ADMIN.value, SystemRole.PRINCIPAL.value, SystemRole.SUB_ADMIN.value}
    
    if not any(r in admin_roles for r in user_roles):
        # Teachers see their own
        if SystemRole.TEACHER.value in user_roles:
            teacher_id = user.id
    
    entries, total = await service.list_entries(
        lesson_plan_id=lesson_plan_id,
        class_id=class_id,
        teacher_id=teacher_id,
        start_date=start_date,
        end_date=end_date,
        status=status,
        page=page,
        size=size,
    )
    
    return {
        "items": [ScheduleEntryResponse.model_validate(e) for e in entries],
        "total": total,
        "page": page,
        "size": size,
    }


@router.get("/stats", response_model=ScheduleStats)
async def get_schedule_stats(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    lesson_plan_id: Optional[UUID] = None,
    class_id: Optional[UUID] = None,
    teacher_id: Optional[UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    _=Depends(require_permission(Permission.SCHEDULE_VIEW)),
):
    """Get schedule statistics."""
    service = ScheduleService(db, user.tenant_id)
    return await service.get_stats(
        lesson_plan_id=lesson_plan_id,
        class_id=class_id,
        teacher_id=teacher_id,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/{entry_id}", response_model=ScheduleEntryResponse)
async def get_schedule_entry(
    entry_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.SCHEDULE_VIEW)),
):
    """Get a specific schedule entry."""
    service = ScheduleService(db, user.tenant_id)
    entry = await service.get_entry(entry_id)
    
    if not entry:
        raise HTTPException(status_code=404, detail="Schedule entry not found")
    
    return entry


@router.patch("/{entry_id}/status", response_model=ScheduleEntryResponse)
async def update_entry_status(
    entry_id: UUID,
    status: ScheduleEntryStatus,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.SCHEDULE_UPDATE)),
):
    """
    Update schedule entry status.
    
    Status transitions:
    - PLANNED → COMPLETED (after teaching)
    - PLANNED → DELAYED (if postponed)
    - PLANNED → SKIPPED (if cancelled)
    """
    service = ScheduleService(db, user.tenant_id)
    return await service.update_entry_status(entry_id, status, user.id)


@router.patch("/{entry_id}", response_model=ScheduleEntryResponse)
async def update_schedule_entry(
    entry_id: UUID,
    data: ScheduleEntryUpdate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.SCHEDULE_UPDATE)),
):
    """Update a schedule entry."""
    service = ScheduleService(db, user.tenant_id)
    return await service.update_entry(entry_id, data)


# ============================================
# Academic Calendar Endpoints
# ============================================

@router.post("/calendar", response_model=CalendarDayResponse, status_code=201)
async def create_calendar_day(
    data: CalendarDayCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.SCHEDULE_GENERATE)),
):
    """Create a calendar day entry (holiday, event, etc.)."""
    service = ScheduleService(db, user.tenant_id)
    return await service.create_calendar_day(data)


@router.post("/calendar/bulk", response_model=List[CalendarDayResponse], status_code=201)
async def create_calendar_days_bulk(
    data: CalendarDayBulkCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.SCHEDULE_GENERATE)),
):
    """Create multiple calendar day entries at once."""
    service = ScheduleService(db, user.tenant_id)
    days = await service.create_calendar_days_bulk(data)
    return [CalendarDayResponse.model_validate(d) for d in days]


@router.get("/calendar", response_model=List[CalendarDayResponse])
async def list_calendar_days(
    academic_year_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    is_working_day: Optional[bool] = None,
    _=Depends(require_permission(Permission.SCHEDULE_VIEW)),
):
    """List calendar days for an academic year."""
    service = ScheduleService(db, user.tenant_id)
    days = await service.list_calendar_days(
        academic_year_id=academic_year_id,
        start_date=start_date,
        end_date=end_date,
        is_working_day=is_working_day,
    )
    return [CalendarDayResponse.model_validate(d) for d in days]


@router.get("/calendar/{day_id}", response_model=CalendarDayResponse)
async def get_calendar_day(
    day_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.SCHEDULE_VIEW)),
):
    """Get a specific calendar day."""
    service = ScheduleService(db, user.tenant_id)
    day = await service.get_calendar_day(day_id)
    
    if not day:
        raise HTTPException(status_code=404, detail="Calendar day not found")
    
    return day


@router.patch("/calendar/{day_id}", response_model=CalendarDayResponse)
async def update_calendar_day(
    day_id: UUID,
    data: CalendarDayUpdate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.SCHEDULE_GENERATE)),
):
    """Update a calendar day."""
    service = ScheduleService(db, user.tenant_id)
    return await service.update_calendar_day(day_id, data)


@router.delete("/calendar/{day_id}", status_code=204)
async def delete_calendar_day(
    day_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.SCHEDULE_GENERATE)),
):
    """Delete a calendar day."""
    service = ScheduleService(db, user.tenant_id)
    await service.delete_calendar_day(day_id)
