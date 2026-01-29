"""
CUSTOS Daily Learning Loop Schemas

Pydantic schemas for daily loop operations.
"""

from datetime import datetime, date
from typing import Optional, List
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


# ============================================
# Enums
# ============================================

class MasteryLevel(str, Enum):
    """Mastery level categorization."""
    STRONG = "strong"      # >= 70%
    MODERATE = "moderate"  # 40-69%
    WEAK = "weak"          # < 40%


# ============================================
# Session Schemas
# ============================================

class DailySessionCreate(BaseModel):
    """Schema for creating a daily loop session (usually auto-created)."""
    schedule_entry_id: UUID
    max_questions: int = Field(default=10, ge=1, le=50)
    time_limit_minutes: Optional[int] = Field(None, ge=1, le=120)


class DailySessionResponse(BaseModel):
    """Schema for daily loop session response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    schedule_entry_id: UUID
    class_id: UUID
    section_id: Optional[UUID]
    subject_id: UUID
    topic_id: UUID
    date: date
    is_active: bool
    max_questions: int
    time_limit_minutes: Optional[int]
    total_attempts: int
    unique_students: int
    avg_score_percent: Optional[float]
    created_at: datetime


class DailySessionWithDetails(DailySessionResponse):
    """Session with related entity names."""
    class_name: Optional[str] = None
    section_name: Optional[str] = None
    subject_name: Optional[str] = None
    topic_name: Optional[str] = None


class DailySessionWithQuestions(DailySessionResponse):
    """Session with questions for the student to attempt."""
    questions: List["QuestionForAttempt"] = []


# ============================================
# Attempt Schemas
# ============================================

class AttemptSubmit(BaseModel):
    """Schema for submitting a single attempt."""
    question_id: UUID
    selected_option: str = Field(..., max_length=500)
    time_taken_seconds: int = Field(default=0, ge=0)


class AttemptBulkSubmit(BaseModel):
    """Schema for submitting multiple attempts at once."""
    session_id: UUID
    attempts: List[AttemptSubmit]


class AttemptResponse(BaseModel):
    """Schema for attempt response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    session_id: UUID
    student_id: UUID
    question_id: UUID
    selected_option: str
    is_correct: bool
    time_taken_seconds: int
    attempt_number: int
    created_at: datetime


class AttemptWithFeedback(AttemptResponse):
    """Attempt with immediate feedback."""
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    question_text: Optional[str] = None


# ============================================
# Mastery Schemas
# ============================================

class StudentMasteryResponse(BaseModel):
    """Schema for student topic mastery."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    student_id: UUID
    topic_id: UUID
    total_attempts: int
    correct_attempts: int
    mastery_percent: float
    current_streak: int
    best_streak: int
    last_attempt_date: Optional[date]
    created_at: datetime
    updated_at: datetime


class MasteryWithDetails(StudentMasteryResponse):
    """Mastery with topic details."""
    topic_name: Optional[str] = None
    mastery_level: MasteryLevel = MasteryLevel.WEAK
    
    def __init__(self, **data):
        super().__init__(**data)
        # Calculate mastery level
        if self.mastery_percent >= 70:
            self.mastery_level = MasteryLevel.STRONG
        elif self.mastery_percent >= 40:
            self.mastery_level = MasteryLevel.MODERATE
        else:
            self.mastery_level = MasteryLevel.WEAK


class StudentMasterySummary(BaseModel):
    """Summary of student mastery across topics."""
    student_id: UUID
    total_topics_attempted: int
    strong_topics: int
    moderate_topics: int
    weak_topics: int
    overall_mastery_percent: float
    topics: List[MasteryWithDetails] = []


# ============================================
# Strong/Weak Analysis Schemas
# ============================================

class StrongWeakQuestion(BaseModel):
    """A question categorized as strong or weak for a student."""
    question_id: UUID
    question_text: Optional[str] = None
    total_attempts: int
    correct_attempts: int
    accuracy_percent: float
    is_strong: bool  # True if accuracy >= 70%


class StrongWeakAnalysis(BaseModel):
    """Analysis of strong and weak questions for a student on a topic."""
    student_id: UUID
    topic_id: UUID
    topic_name: Optional[str] = None
    overall_mastery_percent: float
    mastery_level: MasteryLevel
    strong_questions: List[StrongWeakQuestion] = []
    weak_questions: List[StrongWeakQuestion] = []
    moderate_questions: List[StrongWeakQuestion] = []


# ============================================
# Question For Attempt Schema
# ============================================

class QuestionOption(BaseModel):
    """A single MCQ option."""
    key: str  # A, B, C, D
    text: str


class QuestionForAttempt(BaseModel):
    """Question data sent to student for attempting."""
    id: UUID
    question_type: str
    question_text: str
    question_html: Optional[str] = None
    options: List[QuestionOption] = []
    marks: float = 1.0
    time_limit_seconds: Optional[int] = None
    difficulty: Optional[str] = None


# ============================================
# Today's Session Schema
# ============================================

class TodaySessionInfo(BaseModel):
    """Information about today's sessions for a student."""
    date: date
    sessions: List[DailySessionWithDetails] = []
    total_questions_attempted: int
    total_questions_correct: int
    accuracy_percent: float


# ============================================
# Stats Schema
# ============================================

class DailyLoopStats(BaseModel):
    """Statistics for daily loops."""
    total_sessions: int
    total_attempts: int
    unique_students: int
    avg_accuracy_percent: float
    sessions_today: int
    attempts_today: int


# Update forward references
DailySessionWithQuestions.model_rebuild()
