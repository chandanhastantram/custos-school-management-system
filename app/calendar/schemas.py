"""
CUSTOS Calendar Schemas

Pydantic schemas for calendar API.
"""

from datetime import datetime, date, time
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from app.calendar.models import EventType, EventScope


class EventCreate(BaseModel):
    """Schema for creating a calendar event."""
    title: str = Field(..., max_length=300)
    description: Optional[str] = None
    event_type: EventType = EventType.OTHER
    scope: EventScope = EventScope.SCHOOL
    target_class_ids: Optional[List[UUID]] = None
    target_section_ids: Optional[List[UUID]] = None
    start_date: date
    end_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    is_all_day: bool = True
    is_holiday: bool = False
    location: Optional[str] = Field(None, max_length=300)
    color: Optional[str] = Field(None, max_length=20)
    is_recurring: bool = False
    recurrence_pattern: Optional[dict] = None
    academic_year_id: Optional[UUID] = None


class EventUpdate(BaseModel):
    """Schema for updating a calendar event."""
    title: Optional[str] = Field(None, max_length=300)
    description: Optional[str] = None
    event_type: Optional[EventType] = None
    scope: Optional[EventScope] = None
    target_class_ids: Optional[List[UUID]] = None
    target_section_ids: Optional[List[UUID]] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    is_all_day: Optional[bool] = None
    is_holiday: Optional[bool] = None
    location: Optional[str] = Field(None, max_length=300)
    color: Optional[str] = Field(None, max_length=20)


class EventResponse(BaseModel):
    """Schema for calendar event response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    title: str
    description: Optional[str] = None
    event_type: EventType
    scope: EventScope
    target_class_ids: Optional[List[str]] = None
    target_section_ids: Optional[List[str]] = None
    start_date: date
    end_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    is_all_day: bool
    is_holiday: bool
    location: Optional[str] = None
    color: Optional[str] = None
    is_recurring: bool
    academic_year_id: Optional[UUID] = None
    is_published: bool
    created_at: datetime


class EventListItem(BaseModel):
    """Schema for listing events."""
    id: UUID
    title: str
    event_type: EventType
    start_date: date
    end_date: Optional[date] = None
    is_all_day: bool
    is_holiday: bool
    color: Optional[str] = None


class MonthlyCalendar(BaseModel):
    """Schema for monthly calendar view."""
    year: int
    month: int
    events: List[EventListItem] = []
    holidays: List[date] = []
