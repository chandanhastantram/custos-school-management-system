"""
CUSTOS Lesson Planning Schemas

Pydantic schemas for lesson plan CRUD operations.
"""

from datetime import date, datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, field_validator

from app.academics.models.lesson_plans import LessonPlanStatus, ProgressStatus


# ============================================
# LessonPlan Schemas
# ============================================

class LessonPlanBase(BaseModel):
    """Base schema for LessonPlan."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    start_date: date
    end_date: date
    
    @field_validator("end_date")
    @classmethod
    def end_after_start(cls, v, info):
        if "start_date" in info.data and v < info.data["start_date"]:
            raise ValueError("end_date must be after start_date")
        return v


class LessonPlanCreate(LessonPlanBase):
    """Schema for creating a LessonPlan."""
    class_id: UUID
    section_id: Optional[UUID] = None
    subject_id: UUID
    syllabus_subject_id: Optional[UUID] = None
    academic_year_id: Optional[UUID] = None


class LessonPlanUpdate(BaseModel):
    """Schema for updating a LessonPlan."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    syllabus_subject_id: Optional[UUID] = None


class LessonPlanResponse(LessonPlanBase):
    """Schema for LessonPlan response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    teacher_id: UUID
    class_id: UUID
    section_id: Optional[UUID]
    subject_id: UUID
    syllabus_subject_id: Optional[UUID]
    academic_year_id: Optional[UUID]
    status: LessonPlanStatus
    total_periods: int
    completed_periods: int
    activated_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class LessonPlanWithUnits(LessonPlanResponse):
    """LessonPlan with units included."""
    units: List["LessonPlanUnitResponse"] = []
    progress_percent: Optional[float] = None


class LessonPlanSummary(BaseModel):
    """Summary view of lesson plan."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    title: str
    status: LessonPlanStatus
    start_date: date
    end_date: date
    total_periods: int
    completed_periods: int


# ============================================
# LessonPlanUnit Schemas
# ============================================

class LessonPlanUnitBase(BaseModel):
    """Base schema for LessonPlanUnit."""
    topic_id: UUID
    order: int = 0
    estimated_periods: int = Field(1, ge=1)
    custom_title: Optional[str] = None
    notes: Optional[str] = None
    resources: Optional[str] = None
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None


class LessonPlanUnitCreate(LessonPlanUnitBase):
    """Schema for creating a LessonPlanUnit."""
    pass


class BulkUnitCreate(BaseModel):
    """Schema for bulk creating units."""
    units: List[LessonPlanUnitBase]


class LessonPlanUnitUpdate(BaseModel):
    """Schema for updating a LessonPlanUnit."""
    order: Optional[int] = None
    estimated_periods: Optional[int] = Field(None, ge=1)
    custom_title: Optional[str] = None
    notes: Optional[str] = None
    resources: Optional[str] = None
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None


class LessonPlanUnitResponse(BaseModel):
    """Schema for LessonPlanUnit response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    lesson_plan_id: UUID
    topic_id: UUID
    order: int
    estimated_periods: int
    completed_periods: int
    custom_title: Optional[str]
    notes: Optional[str]
    resources: Optional[str]
    status: ProgressStatus
    planned_start_date: Optional[date]
    planned_end_date: Optional[date]
    created_at: datetime


class LessonPlanUnitWithProgress(LessonPlanUnitResponse):
    """Unit with progress entries."""
    progress_entries: List["TeachingProgressResponse"] = []


# ============================================
# TeachingProgress Schemas
# ============================================

class TeachingProgressBase(BaseModel):
    """Base schema for TeachingProgress."""
    date: date
    periods_taught: int = Field(1, ge=1)
    status: ProgressStatus = ProgressStatus.COMPLETED
    remarks: Optional[str] = None
    topics_covered: Optional[str] = None
    homework_given: Optional[str] = None


class TeachingProgressCreate(TeachingProgressBase):
    """Schema for creating TeachingProgress."""
    pass


class TeachingProgressUpdate(BaseModel):
    """Schema for updating TeachingProgress."""
    periods_taught: Optional[int] = Field(None, ge=1)
    status: Optional[ProgressStatus] = None
    remarks: Optional[str] = None
    topics_covered: Optional[str] = None
    homework_given: Optional[str] = None


class TeachingProgressResponse(TeachingProgressBase):
    """Schema for TeachingProgress response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    lesson_plan_unit_id: UUID
    recorded_by: Optional[UUID]
    created_at: datetime


# ============================================
# Utility Schemas
# ============================================

class ReorderUnitsRequest(BaseModel):
    """Schema for reordering units."""
    unit_ids: List[UUID]


class LessonPlanStats(BaseModel):
    """Statistics for lesson plans."""
    total_plans: int
    draft_plans: int
    active_plans: int
    completed_plans: int
    total_units: int
    completed_units: int
    total_periods: int
    completed_periods: int
    completion_rate: float


class TeacherPlansSummary(BaseModel):
    """Summary of teacher's plans."""
    teacher_id: UUID
    plans: List[LessonPlanSummary]
    stats: LessonPlanStats


# Resolve forward references
LessonPlanWithUnits.model_rebuild()
LessonPlanUnitWithProgress.model_rebuild()
