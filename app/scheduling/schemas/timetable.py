"""
CUSTOS Timetable Schemas

Pydantic schemas for timetable CRUD operations.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID
from enum import IntEnum

from pydantic import BaseModel, Field, ConfigDict, field_validator


# ============================================
# Enums
# ============================================

class DayOfWeek(IntEnum):
    """Day of week enumeration."""
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


# ============================================
# Timetable Schemas
# ============================================

class TimetableBase(BaseModel):
    """Base schema for Timetable."""
    academic_year_id: UUID
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)


class TimetableCreate(TimetableBase):
    """Schema for creating a Timetable."""
    pass


class TimetableUpdate(BaseModel):
    """Schema for updating a Timetable."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class TimetableResponse(BaseModel):
    """Schema for Timetable response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    academic_year_id: UUID
    name: str
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class TimetableWithEntries(TimetableResponse):
    """Timetable with all entries."""
    entries: List["TimetableEntryResponse"] = []


# ============================================
# TimetableEntry Schemas
# ============================================

class TimetableEntryBase(BaseModel):
    """Base schema for TimetableEntry."""
    class_id: UUID
    section_id: Optional[UUID] = None
    subject_id: UUID
    teacher_id: UUID
    day_of_week: int = Field(..., ge=0, le=6)
    period_number: int = Field(..., ge=1, le=12)
    room: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, max_length=500)
    
    @field_validator("day_of_week")
    @classmethod
    def validate_day_of_week(cls, v: int) -> int:
        if v < 0 or v > 6:
            raise ValueError("day_of_week must be between 0 (Monday) and 6 (Sunday)")
        return v


class TimetableEntryCreate(TimetableEntryBase):
    """Schema for creating a TimetableEntry."""
    pass


class TimetableEntryBulkCreate(BaseModel):
    """Schema for bulk creating entries."""
    entries: List[TimetableEntryBase]


class TimetableEntryUpdate(BaseModel):
    """Schema for updating a TimetableEntry."""
    subject_id: Optional[UUID] = None
    teacher_id: Optional[UUID] = None
    room: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, max_length=500)


class TimetableEntryResponse(BaseModel):
    """Schema for TimetableEntry response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    timetable_id: UUID
    class_id: UUID
    section_id: Optional[UUID]
    subject_id: UUID
    teacher_id: UUID
    day_of_week: int
    period_number: int
    room: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime


class TimetableEntryWithDetails(TimetableEntryResponse):
    """Entry with related entity names."""
    class_name: Optional[str] = None
    section_name: Optional[str] = None
    subject_name: Optional[str] = None
    teacher_name: Optional[str] = None
    day_name: Optional[str] = None


# ============================================
# View Schemas (for Class/Teacher timetable view)
# ============================================

class PeriodSlot(BaseModel):
    """A single period slot in timetable view."""
    period_number: int
    subject_id: Optional[UUID] = None
    subject_name: Optional[str] = None
    teacher_id: Optional[UUID] = None
    teacher_name: Optional[str] = None
    class_id: Optional[UUID] = None
    class_name: Optional[str] = None
    room: Optional[str] = None
    entry_id: Optional[UUID] = None


class DaySchedule(BaseModel):
    """Schedule for a single day."""
    day_of_week: int
    day_name: str
    periods: List[PeriodSlot]


class ClassTimetableView(BaseModel):
    """Complete timetable view for a class."""
    class_id: UUID
    class_name: Optional[str] = None
    section_id: Optional[UUID] = None
    section_name: Optional[str] = None
    timetable_id: UUID
    timetable_name: str
    schedule: List[DaySchedule]


class TeacherTimetableView(BaseModel):
    """Complete timetable view for a teacher."""
    teacher_id: UUID
    teacher_name: Optional[str] = None
    schedule: List[DaySchedule]
    total_periods_per_week: int


# ============================================
# Validation Schemas
# ============================================

class TimetableConflict(BaseModel):
    """Represents a scheduling conflict."""
    conflict_type: str  # "teacher_clash", "class_clash"
    day_of_week: int
    period_number: int
    message: str
    existing_entry_id: Optional[UUID] = None


class TimetableValidationResult(BaseModel):
    """Result of timetable validation."""
    is_valid: bool
    conflicts: List[TimetableConflict] = []
    warnings: List[str] = []


# ============================================
# Stats Schema
# ============================================

class TimetableStats(BaseModel):
    """Statistics for timetables."""
    total_timetables: int
    active_timetables: int
    total_entries: int
    classes_with_timetable: int
    classes_without_timetable: int


# Update forward references
TimetableWithEntries.model_rebuild()
