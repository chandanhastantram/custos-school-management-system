"""
CUSTOS AI Lesson Plan Generator Schemas

Schemas for AI-assisted lesson plan generation.
"""

from datetime import date, datetime
from typing import Optional, List
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


class PacePreference(str, Enum):
    """Teaching pace preference."""
    SLOW = "slow"       # More time per topic
    NORMAL = "normal"   # Standard pacing
    FAST = "fast"       # Accelerated


class FocusPreference(str, Enum):
    """Teaching focus preference."""
    CONCEPTS = "concepts"     # Theoretical understanding
    PROBLEMS = "problems"     # Practice-heavy
    REVISION = "revision"     # Quick review
    BALANCED = "balanced"     # Mix of all


class AIJobStatus(str, Enum):
    """AI job processing status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# ============================================
# Request Schemas
# ============================================

class LessonPlanPreferences(BaseModel):
    """Teacher preferences for lesson plan generation."""
    pace: PacePreference = PacePreference.NORMAL
    focus: FocusPreference = FocusPreference.BALANCED
    periods_per_week: Optional[int] = None  # Override from timetable
    include_revision_periods: bool = True
    revision_percent: int = Field(default=10, ge=0, le=30)


class GenerateAILessonPlanRequest(BaseModel):
    """Request to generate AI lesson plan."""
    class_id: UUID
    subject_id: UUID
    syllabus_subject_id: UUID
    section_id: Optional[UUID] = None
    start_date: date
    end_date: date
    title: Optional[str] = None  # Auto-generated if not provided
    preferences: LessonPlanPreferences = Field(default_factory=LessonPlanPreferences)


# ============================================
# Response Schemas
# ============================================

class GeneratedUnitInfo(BaseModel):
    """Information about a generated unit."""
    topic_id: UUID
    topic_name: str
    estimated_periods: int
    notes: Optional[str] = None
    order: int


class GenerateAILessonPlanResponse(BaseModel):
    """Response from AI lesson plan generation."""
    job_id: UUID
    lesson_plan_id: UUID
    title: str
    total_units: int
    total_periods: int
    start_date: date
    end_date: date
    units: List[GeneratedUnitInfo] = []


class AILessonPlanJobResponse(BaseModel):
    """AI job status response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    teacher_id: UUID
    class_id: UUID
    subject_id: UUID
    syllabus_subject_id: UUID
    status: AIJobStatus
    ai_provider: str
    lesson_plan_id: Optional[UUID]
    error_message: Optional[str]
    tokens_used: int
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]


class AILessonPlanJobWithDetails(AILessonPlanJobResponse):
    """Job with additional details."""
    class_name: Optional[str] = None
    subject_name: Optional[str] = None
    teacher_name: Optional[str] = None
    input_snapshot: Optional[dict] = None
    output_snapshot: Optional[dict] = None


# ============================================
# AI Internal Schemas
# ============================================

class TopicForAI(BaseModel):
    """Topic info passed to AI."""
    topic_id: str
    name: str
    unit_name: str
    order: int
    description: Optional[str] = None


class CalendarInfo(BaseModel):
    """Calendar info passed to AI."""
    start_date: str
    end_date: str
    total_working_days: int
    holidays: List[str] = []


class TimetableInfo(BaseModel):
    """Timetable info passed to AI."""
    periods_per_week: int


class AIInputSnapshot(BaseModel):
    """Complete input snapshot for AI."""
    class_name: str
    subject_name: str
    topics: List[TopicForAI]
    calendar: CalendarInfo
    timetable: TimetableInfo
    preferences: LessonPlanPreferences
    total_available_periods: int


class AITopicAllocation(BaseModel):
    """AI-generated topic allocation."""
    topic_id: str
    estimated_periods: int
    notes: Optional[str] = None


class AIOutputSnapshot(BaseModel):
    """AI response snapshot."""
    allocations: List[AITopicAllocation]
    teaching_notes: Optional[str] = None
    suggested_sequence: Optional[str] = None


# ============================================
# Usage Schemas
# ============================================

class AIUsageResponse(BaseModel):
    """AI usage information."""
    month: int
    year: int
    ai_requests_used: int
    ai_requests_limit: int
    remaining: int
    percent_used: float
