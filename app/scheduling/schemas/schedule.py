"""
CUSTOS Schedule Schemas

Pydantic schemas for schedule orchestration.
"""

from datetime import datetime, date
from typing import Optional, List
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


# ============================================
# Enums
# ============================================

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


# ============================================
# Academic Calendar Schemas
# ============================================

class CalendarDayBase(BaseModel):
    """Base schema for calendar day."""
    date: date
    day_type: CalendarDayType = CalendarDayType.WORKING
    is_working_day: bool = True
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None


class CalendarDayCreate(CalendarDayBase):
    """Schema for creating a calendar day."""
    academic_year_id: UUID


class CalendarDayBulkCreate(BaseModel):
    """Schema for bulk creating calendar days."""
    academic_year_id: UUID
    days: List[CalendarDayBase]


class CalendarDayUpdate(BaseModel):
    """Schema for updating a calendar day."""
    day_type: Optional[CalendarDayType] = None
    is_working_day: Optional[bool] = None
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None


class CalendarDayResponse(BaseModel):
    """Schema for calendar day response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    academic_year_id: UUID
    date: date
    day_type: CalendarDayType
    is_working_day: bool
    name: Optional[str]
    description: Optional[str]
    created_at: datetime


# ============================================
# Schedule Entry Schemas
# ============================================

class ScheduleEntryCreate(BaseModel):
    """Schema for manually creating a schedule entry (rarely used)."""
    timetable_entry_id: UUID
    lesson_plan_unit_id: UUID
    lesson_plan_id: UUID
    class_id: UUID
    section_id: Optional[UUID] = None
    subject_id: UUID
    teacher_id: UUID
    topic_id: UUID
    date: date
    day_of_week: int = Field(..., ge=0, le=6)
    period_number: int = Field(..., ge=1, le=12)
    status: ScheduleEntryStatus = ScheduleEntryStatus.PLANNED
    notes: Optional[str] = None


class ScheduleEntryUpdate(BaseModel):
    """Schema for updating a schedule entry."""
    status: Optional[ScheduleEntryStatus] = None
    notes: Optional[str] = None


class ScheduleEntryResponse(BaseModel):
    """Schema for schedule entry response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    timetable_entry_id: UUID
    lesson_plan_unit_id: UUID
    lesson_plan_id: UUID
    class_id: UUID
    section_id: Optional[UUID]
    subject_id: UUID
    teacher_id: UUID
    topic_id: UUID
    date: date
    day_of_week: int
    period_number: int
    status: ScheduleEntryStatus
    notes: Optional[str]
    completed_at: Optional[datetime]
    completed_by: Optional[UUID]
    created_at: datetime
    updated_at: datetime


class ScheduleEntryWithDetails(ScheduleEntryResponse):
    """Schedule entry with related entity names."""
    class_name: Optional[str] = None
    section_name: Optional[str] = None
    subject_name: Optional[str] = None
    teacher_name: Optional[str] = None
    topic_name: Optional[str] = None
    day_name: Optional[str] = None


# ============================================
# Schedule Generation Schemas
# ============================================

class GenerateScheduleRequest(BaseModel):
    """Request to generate schedule from lesson plan."""
    start_date: Optional[date] = None  # Override lesson plan start date
    end_date: Optional[date] = None    # Override lesson plan end date
    regenerate: bool = False           # If true, delete existing and regenerate


class GenerateScheduleResult(BaseModel):
    """Result of schedule generation."""
    lesson_plan_id: UUID
    total_entries_created: int
    start_date: date
    end_date: date
    units_scheduled: int
    periods_scheduled: int
    working_days_used: int
    warnings: List[str] = []


# ============================================
# View Schemas
# ============================================

class DailyPeriodSlot(BaseModel):
    """A single period slot in daily schedule view."""
    period_number: int
    entry_id: Optional[UUID] = None
    subject_id: Optional[UUID] = None
    subject_name: Optional[str] = None
    topic_id: Optional[UUID] = None
    topic_name: Optional[str] = None
    teacher_id: Optional[UUID] = None
    teacher_name: Optional[str] = None
    class_id: Optional[UUID] = None
    class_name: Optional[str] = None
    status: Optional[ScheduleEntryStatus] = None


class DailySchedule(BaseModel):
    """Schedule for a single day."""
    date: date
    day_of_week: int
    day_name: str
    is_working_day: bool
    periods: List[DailyPeriodSlot]


class ClassScheduleView(BaseModel):
    """Schedule view for a class (date range)."""
    class_id: UUID
    class_name: Optional[str] = None
    section_id: Optional[UUID] = None
    section_name: Optional[str] = None
    start_date: date
    end_date: date
    daily_schedules: List[DailySchedule]


class TeacherScheduleView(BaseModel):
    """Schedule view for a teacher (date range)."""
    teacher_id: UUID
    teacher_name: Optional[str] = None
    start_date: date
    end_date: date
    daily_schedules: List[DailySchedule]
    total_periods: int


class StudentScheduleView(BaseModel):
    """Schedule view for a student (uses class schedule)."""
    student_id: UUID
    student_name: Optional[str] = None
    class_id: UUID
    class_name: Optional[str] = None
    section_id: Optional[UUID] = None
    section_name: Optional[str] = None
    start_date: date
    end_date: date
    daily_schedules: List[DailySchedule]


# ============================================
# Stats Schema
# ============================================

class ScheduleStats(BaseModel):
    """Statistics for schedule entries."""
    total_entries: int
    planned_entries: int
    completed_entries: int
    delayed_entries: int
    skipped_entries: int
    completion_rate: float  # 0.0 to 1.0
