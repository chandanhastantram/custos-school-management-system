"""
CUSTOS Weekly Evaluation Schemas

Pydantic schemas for weekly offline tests.
"""

from datetime import datetime, date
from typing import Optional, List
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


# ============================================
# Enums
# ============================================

class WeeklyTestStatus(str, Enum):
    """Weekly test lifecycle status."""
    CREATED = "created"
    CONDUCTED = "conducted"
    EVALUATED = "evaluated"


class QuestionStrengthType(str, Enum):
    """Whether question was from strong or weak pool."""
    STRONG = "strong"
    WEAK = "weak"
    MODERATE = "moderate"


# ============================================
# Weekly Test Schemas
# ============================================

class WeeklyTestCreate(BaseModel):
    """Schema for creating a weekly test."""
    class_id: UUID
    section_id: Optional[UUID] = None
    subject_id: UUID
    topic_ids: List[UUID]
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    start_date: date  # Start of week for daily loop data
    end_date: date    # End of week for daily loop data
    test_date: Optional[date] = None  # When test will be conducted
    total_questions: int = Field(default=20, ge=5, le=100)
    total_marks: float = Field(default=20.0, ge=1)
    duration_minutes: int = Field(default=30, ge=10, le=180)
    strong_percent: int = Field(default=40, ge=0, le=100)
    weak_percent: int = Field(default=60, ge=0, le=100)


class WeeklyTestUpdate(BaseModel):
    """Schema for updating a weekly test."""
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    test_date: Optional[date] = None
    status: Optional[WeeklyTestStatus] = None


class WeeklyTestResponse(BaseModel):
    """Schema for weekly test response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    class_id: UUID
    section_id: Optional[UUID]
    subject_id: UUID
    topic_ids: List[str]
    created_by: Optional[UUID]
    title: str
    description: Optional[str]
    start_date: date
    end_date: date
    test_date: Optional[date]
    status: WeeklyTestStatus
    total_questions: int
    total_marks: float
    duration_minutes: int
    strong_percent: int
    weak_percent: int
    students_appeared: int
    avg_score_percent: Optional[float]
    conducted_at: Optional[datetime]
    evaluated_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class WeeklyTestWithDetails(WeeklyTestResponse):
    """Weekly test with class/subject names."""
    class_name: Optional[str] = None
    section_name: Optional[str] = None
    subject_name: Optional[str] = None
    creator_name: Optional[str] = None


# ============================================
# Weekly Test Question Schemas
# ============================================

class WeeklyTestQuestionResponse(BaseModel):
    """Schema for a question in the weekly test."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    weekly_test_id: UUID
    question_id: UUID
    question_number: int
    strength_type: QuestionStrengthType
    marks: float


class WeeklyTestQuestionWithContent(WeeklyTestQuestionResponse):
    """Question with full content for paper generation."""
    question_text: Optional[str] = None
    question_html: Optional[str] = None
    options: Optional[List[dict]] = None
    correct_answer: Optional[str] = None  # Only for answer key


class WeeklyTestPaper(BaseModel):
    """Full test paper for printing/display."""
    test_id: UUID
    title: str
    class_name: Optional[str] = None
    subject_name: Optional[str] = None
    test_date: Optional[date] = None
    total_marks: float
    duration_minutes: int
    questions: List[WeeklyTestQuestionWithContent]
    # Stats
    strong_count: int
    weak_count: int


class WeeklyTestAnswerKey(BaseModel):
    """Answer key for the test."""
    test_id: UUID
    title: str
    questions: List[WeeklyTestQuestionWithContent]


# ============================================
# Result Submission Schemas
# ============================================

class StudentResultSubmit(BaseModel):
    """Schema for submitting a single student's result."""
    student_id: UUID
    marks_obtained: float = Field(..., ge=0)
    attempted_questions: List[int] = []  # Question numbers attempted
    wrong_questions: List[int] = []       # Question numbers answered wrong


class BulkResultSubmit(BaseModel):
    """Schema for submitting multiple student results at once."""
    results: List[StudentResultSubmit]


class WeeklyTestResultResponse(BaseModel):
    """Schema for weekly test result response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    weekly_test_id: UUID
    student_id: UUID
    total_marks: float
    marks_obtained: float
    attempted_questions: List[int]
    wrong_questions: List[int]
    percentage: float
    submitted_by: Optional[UUID]
    created_at: datetime


class WeeklyTestResultWithDetails(WeeklyTestResultResponse):
    """Result with student name and performance breakdown."""
    student_name: Optional[str] = None
    strong_correct: Optional[int] = None
    strong_total: Optional[int] = None
    weak_correct: Optional[int] = None
    weak_total: Optional[int] = None


# ============================================
# Performance Schemas
# ============================================

class WeeklyPerformanceResponse(BaseModel):
    """Schema for weekly student performance."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    weekly_test_id: UUID
    student_id: UUID
    strong_total: int
    strong_correct: int
    strong_accuracy: float
    weak_total: int
    weak_correct: int
    weak_accuracy: float
    mastery_delta: float
    overall_accuracy: float
    created_at: datetime
    updated_at: datetime


class StudentWeeklyHistory(BaseModel):
    """Historical weekly test performance for a student."""
    student_id: UUID
    student_name: Optional[str] = None
    tests: List[WeeklyTestResultWithDetails] = []
    avg_percentage: float
    total_tests: int


# ============================================
# Generate Paper Request/Response
# ============================================

class GeneratePaperRequest(BaseModel):
    """Request to generate weekly paper."""
    shuffle_questions: bool = True  # Randomize order
    include_moderate: bool = False  # Include moderate questions if not enough strong/weak


class GeneratePaperResult(BaseModel):
    """Result of paper generation."""
    weekly_test_id: UUID
    total_questions_generated: int
    strong_questions: int
    weak_questions: int
    moderate_questions: int
    warnings: List[str] = []


# ============================================
# Stats Schema
# ============================================

class WeeklyTestStats(BaseModel):
    """Statistics for weekly tests."""
    total_tests: int
    tests_created: int
    tests_conducted: int
    tests_evaluated: int
    total_students_evaluated: int
    avg_score_percent: float
