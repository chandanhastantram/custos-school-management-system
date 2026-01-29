"""
CUSTOS Lesson Evaluation & Adaptive Schemas

Pydantic schemas for lesson-wise evaluation and adaptive recommendations.
"""

from datetime import datetime, date
from typing import Optional, List
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


# ============================================
# Enums
# ============================================

class LessonEvaluationStatus(str, Enum):
    """Lesson evaluation lifecycle status."""
    CREATED = "created"
    CONDUCTED = "conducted"
    EVALUATED = "evaluated"


class RecommendationType(str, Enum):
    """Types of adaptive recommendations."""
    REVISION = "revision"
    EXTRA_DAILY_LOOP = "extra_daily_loop"
    REMEDIAL_CLASS = "remedial_class"


class RecommendationPriority(str, Enum):
    """Priority levels for recommendations."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# ============================================
# Lesson Evaluation Schemas
# ============================================

class LessonEvaluationCreate(BaseModel):
    """Schema for creating a lesson evaluation."""
    lesson_plan_id: UUID
    class_id: UUID
    section_id: Optional[UUID] = None
    subject_id: UUID
    chapter_id: Optional[UUID] = None
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    test_date: Optional[date] = None
    total_questions: int = Field(default=25, ge=5, le=100)
    total_marks: float = Field(default=25.0, ge=1)
    duration_minutes: int = Field(default=45, ge=10, le=180)


class LessonEvaluationUpdate(BaseModel):
    """Schema for updating a lesson evaluation."""
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    test_date: Optional[date] = None
    status: Optional[LessonEvaluationStatus] = None


class LessonEvaluationResponse(BaseModel):
    """Schema for lesson evaluation response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    lesson_plan_id: UUID
    class_id: UUID
    section_id: Optional[UUID]
    subject_id: UUID
    chapter_id: Optional[UUID]
    created_by: Optional[UUID]
    title: str
    description: Optional[str]
    test_date: Optional[date]
    status: LessonEvaluationStatus
    total_questions: int
    total_marks: float
    duration_minutes: int
    students_appeared: int
    avg_score_percent: Optional[float]
    conducted_at: Optional[datetime]
    evaluated_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class LessonEvaluationWithDetails(LessonEvaluationResponse):
    """Evaluation with class/subject names."""
    class_name: Optional[str] = None
    section_name: Optional[str] = None
    subject_name: Optional[str] = None
    chapter_name: Optional[str] = None
    creator_name: Optional[str] = None


# ============================================
# Evaluation Question Schemas
# ============================================

class LessonEvaluationQuestionResponse(BaseModel):
    """Schema for a question in the lesson evaluation."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    lesson_evaluation_id: UUID
    question_id: UUID
    question_number: int
    marks: float
    topic_id: Optional[UUID]


class LessonQuestionWithContent(LessonEvaluationQuestionResponse):
    """Question with full content for paper generation."""
    question_text: Optional[str] = None
    question_html: Optional[str] = None
    options: Optional[List[dict]] = None
    correct_answer: Optional[str] = None


class LessonEvaluationPaper(BaseModel):
    """Full lesson evaluation paper."""
    evaluation_id: UUID
    title: str
    class_name: Optional[str] = None
    subject_name: Optional[str] = None
    chapter_name: Optional[str] = None
    test_date: Optional[date] = None
    total_marks: float
    duration_minutes: int
    questions: List[LessonQuestionWithContent]


# ============================================
# Result Schemas
# ============================================

class LessonResultSubmit(BaseModel):
    """Schema for submitting a single student's result."""
    student_id: UUID
    marks_obtained: float = Field(..., ge=0)
    wrong_questions: List[int] = []


class BulkLessonResultSubmit(BaseModel):
    """Schema for submitting multiple student results at once."""
    results: List[LessonResultSubmit]


class LessonEvaluationResultResponse(BaseModel):
    """Schema for lesson evaluation result response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    lesson_evaluation_id: UUID
    student_id: UUID
    total_marks: float
    marks_obtained: float
    wrong_questions: List[int]
    percentage: float
    submitted_by: Optional[UUID]
    created_at: datetime


class LessonResultWithDetails(LessonEvaluationResultResponse):
    """Result with student name."""
    student_name: Optional[str] = None


# ============================================
# Mastery Snapshot Schemas
# ============================================

class LessonMasterySnapshotResponse(BaseModel):
    """Schema for lesson mastery snapshot."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    student_id: UUID
    chapter_id: UUID
    lesson_evaluation_id: Optional[UUID]
    mastery_percent: float
    daily_mastery: float
    weekly_mastery: float
    lesson_mastery: float
    evaluated_at: datetime
    created_at: datetime


class MasterySnapshotWithDetails(LessonMasterySnapshotResponse):
    """Mastery snapshot with chapter name."""
    chapter_name: Optional[str] = None


# ============================================
# Adaptive Recommendation Schemas
# ============================================

class AdaptiveRecommendationResponse(BaseModel):
    """Schema for adaptive recommendation."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    student_id: UUID
    topic_id: UUID
    lesson_evaluation_id: Optional[UUID]
    recommendation_type: RecommendationType
    priority: RecommendationPriority
    reason: str
    current_mastery: float
    is_actioned: bool
    actioned_at: Optional[datetime]
    actioned_by: Optional[UUID]
    created_at: datetime


class AdaptiveRecommendationWithDetails(AdaptiveRecommendationResponse):
    """Recommendation with topic name."""
    topic_name: Optional[str] = None
    student_name: Optional[str] = None


class AdaptiveRecommendationsForStudent(BaseModel):
    """All recommendations for a student."""
    student_id: UUID
    student_name: Optional[str] = None
    total_recommendations: int
    high_priority: int
    medium_priority: int
    low_priority: int
    recommendations: List[AdaptiveRecommendationWithDetails] = []


class ActionRecommendation(BaseModel):
    """Schema for marking a recommendation as actioned."""
    notes: Optional[str] = None


# ============================================
# Generate Paper Request/Response
# ============================================

class GenerateLessonPaperRequest(BaseModel):
    """Request to generate lesson paper."""
    shuffle_questions: bool = True


class GenerateLessonPaperResult(BaseModel):
    """Result of paper generation."""
    lesson_evaluation_id: UUID
    total_questions_generated: int
    topics_covered: int
    warnings: List[str] = []


# ============================================
# Mastery Calculation Schemas
# ============================================

class CalculateMasteryResult(BaseModel):
    """Result of mastery calculation."""
    student_id: UUID
    chapter_id: UUID
    daily_mastery: float
    weekly_mastery: float
    lesson_mastery: float
    combined_mastery: float
    recommendations_generated: int


# ============================================
# Stats Schema
# ============================================

class LessonEvaluationStats(BaseModel):
    """Statistics for lesson evaluations."""
    total_evaluations: int
    evaluations_created: int
    evaluations_conducted: int
    evaluations_evaluated: int
    total_students_evaluated: int
    avg_score_percent: float
    total_recommendations: int
    high_priority_recommendations: int
