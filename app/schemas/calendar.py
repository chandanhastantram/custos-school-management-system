"""
CUSTOS Calendar Schemas

Calendar and timetable request/response schemas.
"""

from datetime import date, time, datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.calendar import EventType, RecurrenceType, DayOfWeek


class EventCreate(BaseModel):
    """Create calendar event."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    event_type: EventType = EventType.GENERAL
    start_date: date
    end_date: date
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    is_all_day: bool = False
    location: Optional[str] = None
    color: Optional[str] = None
    recurrence: Optional[RecurrenceType] = None
    recurrence_end: Optional[date] = None
    is_public: bool = True
    target_roles: Optional[List[str]] = None
    target_sections: Optional[List[UUID]] = None


class EventResponse(BaseModel):
    """Calendar event response."""
    id: UUID
    title: str
    description: Optional[str]
    event_type: str
    start_date: date
    end_date: date
    start_time: Optional[time]
    end_time: Optional[time]
    is_all_day: bool
    location: Optional[str]
    color: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class TimetableSlotCreate(BaseModel):
    """Create timetable slot."""
    day: DayOfWeek
    period_number: int = Field(..., ge=1)
    start_time: time
    end_time: time
    subject_id: Optional[UUID] = None
    teacher_id: Optional[UUID] = None
    room: Optional[str] = None
    is_break: bool = False


class TimetableCreate(BaseModel):
    """Create timetable."""
    section_id: UUID
    academic_year_id: UUID
    name: str = Field(..., min_length=1, max_length=100)
    effective_from: date
    slots: List[TimetableSlotCreate]


class TimetableResponse(BaseModel):
    """Timetable response."""
    id: UUID
    section_id: UUID
    name: str
    effective_from: date
    effective_to: Optional[date]
    is_active: bool
    
    class Config:
        from_attributes = True
