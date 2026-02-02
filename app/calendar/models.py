"""
CUSTOS Calendar Models

School calendar events and holidays.
"""

from datetime import datetime, date, time
from enum import Enum
from typing import Optional, List
from uuid import UUID

from sqlalchemy import String, Text, Boolean, Date, Time, DateTime, ForeignKey, Index, JSON
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import TenantBaseModel


class EventType(str, Enum):
    """Types of calendar events."""
    HOLIDAY = "holiday"
    EXAM = "exam"
    PTM = "ptm"  # Parent-Teacher Meeting
    SPORTS = "sports"
    CULTURAL = "cultural"
    MEETING = "meeting"
    DEADLINE = "deadline"
    VACATION = "vacation"
    OTHER = "other"


class EventScope(str, Enum):
    """Scope of the event."""
    SCHOOL = "school"  # All school
    CLASS = "class"    # Specific class
    SECTION = "section"  # Specific section
    TEACHER = "teacher"  # Teacher only
    STUDENT = "student"  # Student only


class CalendarEvent(TenantBaseModel):
    """
    School Calendar Event.
    
    Represents holidays, exams, PTMs, events, etc.
    """
    __tablename__ = "calendar_events"
    
    __table_args__ = (
        Index("ix_calendar_events_tenant", "tenant_id", "start_date"),
        Index("ix_calendar_events_type", "tenant_id", "event_type"),
    )
    
    # Event details
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Type and scope
    event_type: Mapped[EventType] = mapped_column(
        SQLEnum(EventType),
        default=EventType.OTHER,
    )
    scope: Mapped[EventScope] = mapped_column(
        SQLEnum(EventScope),
        default=EventScope.SCHOOL,
    )
    
    # Target (for class/section specific events)
    target_class_ids: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    target_section_ids: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    
    # Dates
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Time (for specific events)
    start_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    end_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    
    # All day event
    is_all_day: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Holiday (affects attendance)
    is_holiday: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Location
    location: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    
    # Color for display
    color: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Recurring
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    recurrence_pattern: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Academic year
    academic_year_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("academic_years.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Created by
    created_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Published
    is_published: Mapped[bool] = mapped_column(Boolean, default=True)
