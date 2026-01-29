"""
CUSTOS Schedule Models

Schedule entries and academic calendar for schedule orchestration.
"""

from datetime import datetime, date
from enum import Enum
from typing import Optional, List
from uuid import UUID

from sqlalchemy import String, Text, Boolean, Integer, Date, ForeignKey, Index
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import TenantBaseModel


class ScheduleEntryStatus(str, Enum):
    """Schedule entry execution status."""
    PLANNED = "planned"
    COMPLETED = "completed"
    DELAYED = "delayed"
    SKIPPED = "skipped"


class CalendarDayType(str, Enum):
    """Type of calendar day."""
    WORKING = "working"
    HOLIDAY = "holiday"
    WEEKEND = "weekend"
    EXAM = "exam"
    EVENT = "event"


class AcademicCalendarDay(TenantBaseModel):
    """
    Academic Calendar Day - Working days, holidays, events.
    
    Used by schedule orchestration to skip non-working days.
    """
    __tablename__ = "academic_calendar_days"
    
    __table_args__ = (
        Index("ix_calendar_tenant_date", "tenant_id", "date"),
        Index("ix_calendar_year_date", "academic_year_id", "date"),
    )
    
    # Academic year binding
    academic_year_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("academic_years.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # The date
    date: Mapped[date] = mapped_column(Date, nullable=False)
    
    # Day type
    day_type: Mapped[CalendarDayType] = mapped_column(
        SQLEnum(CalendarDayType),
        default=CalendarDayType.WORKING,
        nullable=False,
    )
    
    # Is this a working day for classes?
    is_working_day: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Optional: Event/Holiday name
    name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class ScheduleEntry(TenantBaseModel):
    """
    Schedule Entry - Generated teaching schedule.
    
    Links: Timetable + Lesson Plan → Actual daily teaching plan.
    
    Answers: "On this date, period X, class Y, teach Topic Z"
    """
    __tablename__ = "schedule_entries"
    
    __table_args__ = (
        Index("ix_schedule_tenant_date", "tenant_id", "date"),
        Index("ix_schedule_class_date", "tenant_id", "class_id", "date"),
        Index("ix_schedule_teacher_date", "tenant_id", "teacher_id", "date"),
        Index("ix_schedule_lesson_plan", "lesson_plan_id"),
    )
    
    # Link to timetable entry (the period slot)
    timetable_entry_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("timetable_entries.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Link to lesson plan unit (the topic being taught)
    lesson_plan_unit_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lesson_plan_units.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Link to lesson plan (for quick filtering)
    lesson_plan_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lesson_plans.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Denormalized for quick access (avoids joins in queries)
    class_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("classes.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    section_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("sections.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    subject_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    teacher_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    topic_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("syllabus_topics.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # When
    date: Mapped[date] = mapped_column(Date, nullable=False)
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)  # 0-6
    period_number: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-12
    
    # Status
    status: Mapped[ScheduleEntryStatus] = mapped_column(
        SQLEnum(ScheduleEntryStatus),
        default=ScheduleEntryStatus.PLANNED,
        nullable=False,
    )
    
    # Optional notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Tracking when completed
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    completed_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
