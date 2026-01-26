"""
CUSTOS Calendar API Endpoints

Calendar events and timetable routes.
"""

from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth import AuthUser, TenantCtx, require_permissions, Permission
from app.services.calendar_service import CalendarService
from app.schemas.calendar import (
    EventCreate, EventResponse,
    TimetableCreate, TimetableResponse,
)
from app.schemas.common import SuccessResponse
from app.models.calendar import EventType, DayOfWeek


router = APIRouter(prefix="/calendar", tags=["Calendar"])


# ==================== Events ====================

@router.get("/events", response_model=list[EventResponse])
async def list_events(
    start_date: date,
    end_date: date,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    event_type: Optional[EventType] = None,
    section_id: Optional[UUID] = None,
):
    """Get events within date range."""
    service = CalendarService(db, ctx.tenant_id)
    events = await service.get_events(start_date, end_date, event_type, section_id)
    return [EventResponse.model_validate(e) for e in events]


@router.post("/events", response_model=EventResponse)
async def create_event(
    data: EventCreate,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    _: AuthUser = Depends(require_permissions(Permission.CALENDAR_CREATE)),
):
    """Create calendar event."""
    service = CalendarService(db, ctx.tenant_id)
    event = await service.create_event(data, ctx.user.user_id)
    return EventResponse.model_validate(event)


@router.get("/events/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: UUID,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
):
    """Get event by ID."""
    service = CalendarService(db, ctx.tenant_id)
    event = await service.get_event(event_id)
    return EventResponse.model_validate(event)


@router.put("/events/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: UUID,
    data: EventCreate,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    _: AuthUser = Depends(require_permissions(Permission.CALENDAR_UPDATE)),
):
    """Update event."""
    service = CalendarService(db, ctx.tenant_id)
    event = await service.update_event(event_id, data.model_dump())
    return EventResponse.model_validate(event)


@router.delete("/events/{event_id}", response_model=SuccessResponse)
async def delete_event(
    event_id: UUID,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    _: AuthUser = Depends(require_permissions(Permission.CALENDAR_DELETE)),
):
    """Delete event."""
    service = CalendarService(db, ctx.tenant_id)
    await service.delete_event(event_id)
    return SuccessResponse(message="Event deleted")


# ==================== Holidays ====================

@router.get("/holidays")
async def list_holidays(
    start_date: date,
    end_date: date,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
):
    """Get holidays in date range."""
    service = CalendarService(db, ctx.tenant_id)
    holidays = await service.get_holidays(start_date, end_date)
    return {"holidays": holidays}


@router.post("/holidays")
async def create_holiday(
    name: str,
    holiday_date: date,
    description: str = None,
    ctx: TenantCtx = None,
    db: AsyncSession = Depends(get_db),
    _: AuthUser = Depends(require_permissions(Permission.CALENDAR_CREATE)),
):
    """Create holiday."""
    service = CalendarService(db, ctx.tenant_id)
    holiday = await service.create_holiday(name, holiday_date, description)
    return {"id": str(holiday.id), "name": holiday.name, "date": str(holiday.date)}


@router.get("/holidays/check")
async def check_holiday(
    check_date: date,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
):
    """Check if date is a holiday."""
    service = CalendarService(db, ctx.tenant_id)
    is_holiday = await service.is_holiday(check_date)
    return {"date": str(check_date), "is_holiday": is_holiday}


# ==================== Timetables ====================

@router.post("/timetables", response_model=TimetableResponse)
async def create_timetable(
    data: TimetableCreate,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    _: AuthUser = Depends(require_permissions(Permission.TIMETABLE_CREATE)),
):
    """Create timetable for section."""
    service = CalendarService(db, ctx.tenant_id)
    timetable = await service.create_timetable(data)
    return TimetableResponse.model_validate(timetable)


@router.get("/timetables/section/{section_id}")
async def get_section_timetable(
    section_id: UUID,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
):
    """Get timetable for section."""
    service = CalendarService(db, ctx.tenant_id)
    timetable = await service.get_timetable(section_id)
    
    if not timetable:
        return {"timetable": None, "slots": []}
    
    slots = await service.get_timetable_slots(timetable.id)
    
    return {
        "timetable": TimetableResponse.model_validate(timetable),
        "slots": slots,
    }


@router.get("/timetables/{timetable_id}/slots")
async def get_timetable_slots(
    timetable_id: UUID,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    day: Optional[DayOfWeek] = None,
):
    """Get slots for timetable."""
    service = CalendarService(db, ctx.tenant_id)
    slots = await service.get_timetable_slots(timetable_id, day)
    return {"slots": slots}


@router.get("/timetables/teacher/{teacher_id}")
async def get_teacher_schedule(
    teacher_id: UUID,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    day: Optional[DayOfWeek] = None,
):
    """Get teacher's schedule."""
    service = CalendarService(db, ctx.tenant_id)
    slots = await service.get_teacher_schedule(teacher_id, day)
    return {"slots": slots}


@router.get("/timetables/section/{section_id}/today")
async def get_today_schedule(
    section_id: UUID,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
):
    """Get today's schedule for section."""
    service = CalendarService(db, ctx.tenant_id)
    slots = await service.get_today_schedule(section_id)
    return {"slots": slots}
