"""
CUSTOS Calendar Models

Models for events and timetables.
"""

from datetime import datetime, date, time
from enum import Enum
from typing import Optional, List, TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    String, Text, Boolean, Integer, DateTime, Date, Time,
    ForeignKey, Enum as SQLEnum, JSON,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TenantSoftDeleteModel, TenantBaseModel

if TYPE_CHECKING:
    from app.models.user import User


class EventType(str, Enum):
    HOLIDAY = "holiday"
    EXAM = "exam"
    MEETING = "meeting"
    ACTIVITY = "activity"
    DEADLINE = "deadline"
    REMINDER = "reminder"
    OTHER = "other"


class RecurrenceType(str, Enum):
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class Event(TenantSoftDeleteModel):
    """Calendar event."""
    __tablename__ = "events"
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    event_type: Mapped[EventType] = mapped_column(SQLEnum(EventType), nullable=False)
    
    start_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    end_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    is_all_day: Mapped[bool] = mapped_column(Boolean, default=True)
    
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    
    recurrence: Mapped[RecurrenceType] = mapped_column(SQLEnum(RecurrenceType), default=RecurrenceType.NONE)
    recurrence_end: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)
    target_roles: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    target_sections: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    
    created_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    creator: Mapped["User"] = relationship("User", lazy="selectin")


class DayOfWeek(str, Enum):
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class Timetable(TenantSoftDeleteModel):
    """Class timetable."""
    __tablename__ = "timetables"
    
    section_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("sections.id"), nullable=False, index=True)
    academic_year_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("academic_years.id"), nullable=False)
    
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    periods_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    slots: Mapped[List["TimetableSlot"]] = relationship("TimetableSlot", back_populates="timetable")


class TimetableSlot(TenantBaseModel):
    """Individual period in timetable."""
    __tablename__ = "timetable_slots"
    
    timetable_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("timetables.id"), nullable=False, index=True)
    
    day: Mapped[DayOfWeek] = mapped_column(SQLEnum(DayOfWeek), nullable=False)
    period_number: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    
    subject_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("subjects.id"), nullable=True)
    teacher_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    room: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_break: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    timetable: Mapped["Timetable"] = relationship("Timetable", back_populates="slots")
