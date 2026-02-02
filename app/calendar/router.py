"""
CUSTOS Calendar Router

API endpoints for school calendar.
"""

from datetime import date
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth.dependencies import CurrentUser, require_permission
from app.users.rbac import Permission
from app.calendar.service import CalendarService
from app.calendar.models import EventType
from app.calendar.schemas import (
    EventCreate,
    EventUpdate,
    EventResponse,
    EventListItem,
    MonthlyCalendar,
)


router = APIRouter(tags=["Calendar"])


@router.post("/events", response_model=EventResponse, status_code=201)
async def create_event(
    data: EventCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.CALENDAR_CREATE)),
):
    """Create a calendar event."""
    service = CalendarService(db, user.tenant_id)
    event = await service.create_event(data, user.user_id)
    return EventResponse.model_validate(event)


@router.get("/events", response_model=List[EventListItem])
async def list_events(
    start_date: date,
    end_date: date,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    event_type: Optional[EventType] = None,
    _=Depends(require_permission(Permission.CALENDAR_VIEW)),
):
    """List calendar events within date range."""
    service = CalendarService(db, user.tenant_id)
    events = await service.list_events(start_date, end_date, event_type)
    
    return [
        EventListItem(
            id=e.id,
            title=e.title,
            event_type=e.event_type,
            start_date=e.start_date,
            end_date=e.end_date,
            is_all_day=e.is_all_day,
            is_holiday=e.is_holiday,
            color=e.color,
        )
        for e in events
    ]


@router.get("/events/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.CALENDAR_VIEW)),
):
    """Get a calendar event by ID."""
    service = CalendarService(db, user.tenant_id)
    event = await service.get_event(event_id)
    return EventResponse.model_validate(event)


@router.patch("/events/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: UUID,
    data: EventUpdate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.CALENDAR_UPDATE)),
):
    """Update a calendar event."""
    service = CalendarService(db, user.tenant_id)
    event = await service.update_event(event_id, data)
    return EventResponse.model_validate(event)


@router.delete("/events/{event_id}")
async def delete_event(
    event_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.CALENDAR_DELETE)),
):
    """Delete a calendar event."""
    service = CalendarService(db, user.tenant_id)
    await service.delete_event(event_id)
    return {"success": True, "message": "Event deleted"}


@router.get("/monthly/{year}/{month}", response_model=MonthlyCalendar)
async def get_monthly_calendar(
    year: int,
    month: int,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.CALENDAR_VIEW)),
):
    """Get calendar view for a specific month."""
    if not 1 <= month <= 12:
        raise HTTPException(status_code=400, detail="Invalid month")
    
    service = CalendarService(db, user.tenant_id)
    events = await service.get_monthly_events(year, month)
    
    from datetime import date as date_type
    from calendar import monthrange
    start = date_type(year, month, 1)
    _, last_day = monthrange(year, month)
    end = date_type(year, month, last_day)
    holidays = await service.get_holidays(start, end)
    
    return MonthlyCalendar(
        year=year,
        month=month,
        events=[
            EventListItem(
                id=e.id,
                title=e.title,
                event_type=e.event_type,
                start_date=e.start_date,
                end_date=e.end_date,
                is_all_day=e.is_all_day,
                is_holiday=e.is_holiday,
                color=e.color,
            )
            for e in events
        ],
        holidays=holidays,
    )


@router.get("/holidays")
async def get_holidays(
    start_date: date,
    end_date: date,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Get holiday dates within range."""
    service = CalendarService(db, user.tenant_id)
    holidays = await service.get_holidays(start_date, end_date)
    return {"holidays": [h.isoformat() for h in holidays]}


@router.get("/upcoming", response_model=List[EventListItem])
async def get_upcoming_events(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    limit: int = Query(10, ge=1, le=50),
    event_type: Optional[EventType] = None,
):
    """Get upcoming events from today."""
    service = CalendarService(db, user.tenant_id)
    events = await service.get_upcoming_events(limit, event_type)
    
    return [
        EventListItem(
            id=e.id,
            title=e.title,
            event_type=e.event_type,
            start_date=e.start_date,
            end_date=e.end_date,
            is_all_day=e.is_all_day,
            is_holiday=e.is_holiday,
            color=e.color,
        )
        for e in events
    ]
