"""
CUSTOS Feedback & Surveys Schemas

Pydantic schemas for survey management.
"""

from datetime import datetime
from typing import Optional, List, Any
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, field_validator


# ============================================
# Enums (for API)
# ============================================

class SurveyType(str, Enum):
    COURSE = "course"
    FACULTY = "faculty"
    GENERAL = "general"
    EXAM = "exam"
    EVENT = "event"
    CUSTOM = "custom"


class SurveyStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    CLOSED = "closed"
    ARCHIVED = "archived"


class QuestionType(str, Enum):
    RATING = "rating"
    LIKERT = "likert"
    TEXT = "text"
    MCQ = "mcq"
    YES_NO = "yes_no"
    SCALE = "scale"


class ResponseStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"


# ============================================
# Survey Question Schemas
# ============================================

class QuestionOptionBase(BaseModel):
    """Question option (for MCQ/Rating)."""
    value: Any
    label: str


class SurveyQuestionCreate(BaseModel):
    """Schema for creating a survey question."""
    question_text: str = Field(..., min_length=1, max_length=1000)
    question_type: QuestionType
    options: Optional[List[QuestionOptionBase]] = None
    min_value: Optional[int] = None
    max_value: Optional[int] = None
    is_required: bool = True
    display_order: int = 0
    help_text: Optional[str] = None
    category: Optional[str] = None


class SurveyQuestionUpdate(BaseModel):
    """Schema for updating a survey question."""
    question_text: Optional[str] = Field(None, min_length=1, max_length=1000)
    question_type: Optional[QuestionType] = None
    options: Optional[List[QuestionOptionBase]] = None
    min_value: Optional[int] = None
    max_value: Optional[int] = None
    is_required: Optional[bool] = None
    display_order: Optional[int] = None
    help_text: Optional[str] = None
    category: Optional[str] = None


class SurveyQuestionResponse(BaseModel):
    """Schema for survey question response."""
    id: UUID
    survey_id: UUID
    question_text: str
    question_type: QuestionType
    options: Optional[List[dict]] = None
    min_value: Optional[int] = None
    max_value: Optional[int] = None
    is_required: bool
    display_order: int
    help_text: Optional[str] = None
    category: Optional[str] = None
    
    model_config = {"from_attributes": True}


# ============================================
# Survey Schemas
# ============================================

class SurveyCreate(BaseModel):
    """Schema for creating a survey."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    survey_type: SurveyType
    start_date: datetime
    end_date: datetime
    is_anonymous: bool = True
    is_mandatory: bool = False
    allow_multiple_submissions: bool = False
    show_results_to_students: bool = False
    
    # Targeting
    academic_year_id: Optional[UUID] = None
    class_id: Optional[UUID] = None
    section_id: Optional[UUID] = None
    subject_id: Optional[UUID] = None
    faculty_id: Optional[UUID] = None
    
    # Optional: Create questions inline
    questions: Optional[List[SurveyQuestionCreate]] = None
    
    @field_validator("end_date")
    @classmethod
    def end_date_after_start(cls, v, info):
        if "start_date" in info.data and v <= info.data["start_date"]:
            raise ValueError("end_date must be after start_date")
        return v


class SurveyUpdate(BaseModel):
    """Schema for updating a survey."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_anonymous: Optional[bool] = None
    is_mandatory: Optional[bool] = None
    allow_multiple_submissions: Optional[bool] = None
    show_results_to_students: Optional[bool] = None
    status: Optional[SurveyStatus] = None
    
    # Targeting
    academic_year_id: Optional[UUID] = None
    class_id: Optional[UUID] = None
    section_id: Optional[UUID] = None
    subject_id: Optional[UUID] = None
    faculty_id: Optional[UUID] = None


class SurveyResponse(BaseModel):
    """Schema for survey response."""
    id: UUID
    tenant_id: UUID
    title: str
    description: Optional[str] = None
    survey_type: SurveyType
    start_date: datetime
    end_date: datetime
    is_anonymous: bool
    is_mandatory: bool
    allow_multiple_submissions: bool
    show_results_to_students: bool
    status: SurveyStatus
    
    # Targeting
    academic_year_id: Optional[UUID] = None
    class_id: Optional[UUID] = None
    section_id: Optional[UUID] = None
    subject_id: Optional[UUID] = None
    faculty_id: Optional[UUID] = None
    
    # Metadata
    created_by: Optional[UUID] = None
    published_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    total_responses: int = 0
    target_respondents: int = 0
    
    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}


class SurveyWithQuestions(SurveyResponse):
    """Survey with questions included."""
    questions: List[SurveyQuestionResponse] = []


class SurveyListResponse(BaseModel):
    """Paginated survey list."""
    surveys: List[SurveyResponse]
    total: int
    page: int
    page_size: int


# ============================================
# Answer Schemas
# ============================================

class AnswerCreate(BaseModel):
    """Schema for creating an answer to a question."""
    question_id: UUID
    rating_value: Optional[int] = Field(None, ge=1, le=10)
    text_value: Optional[str] = None
    selected_option: Optional[str] = None
    boolean_value: Optional[bool] = None
    numeric_value: Optional[float] = None


class AnswerResponse(BaseModel):
    """Schema for answer response."""
    id: UUID
    question_id: UUID
    rating_value: Optional[int] = None
    text_value: Optional[str] = None
    selected_option: Optional[str] = None
    boolean_value: Optional[bool] = None
    numeric_value: Optional[float] = None
    
    model_config = {"from_attributes": True}


# ============================================
# Survey Submission Schemas
# ============================================

class SubmitSurveyRequest(BaseModel):
    """Schema for submitting a survey response."""
    answers: List[AnswerCreate]
    
    @field_validator("answers")
    @classmethod
    def validate_answers(cls, v):
        if not v:
            raise ValueError("At least one answer is required")
        return v


class SurveySubmissionResponse(BaseModel):
    """Schema for survey submission response."""
    id: UUID
    survey_id: UUID
    student_id: UUID
    status: ResponseStatus
    started_at: datetime
    submitted_at: Optional[datetime] = None
    answers: List[AnswerResponse] = []
    
    model_config = {"from_attributes": True}


# ============================================
# Survey Results Schemas
# ============================================

class QuestionStats(BaseModel):
    """Statistics for a single question."""
    question_id: UUID
    question_text: str
    question_type: QuestionType
    total_responses: int
    
    # For rating/scale questions
    average_rating: Optional[float] = None
    min_rating: Optional[int] = None
    max_rating: Optional[int] = None
    rating_distribution: Optional[dict] = None  # {1: 5, 2: 10, 3: 20, ...}
    
    # For MCQ questions
    option_counts: Optional[dict] = None  # {"option1": 10, "option2": 20, ...}
    
    # For yes/no questions
    yes_count: Optional[int] = None
    no_count: Optional[int] = None


class SurveyResultsSummary(BaseModel):
    """Aggregated survey results."""
    survey_id: UUID
    survey_title: str
    survey_type: SurveyType
    total_responses: int
    target_respondents: int
    response_rate: float
    average_overall_rating: Optional[float] = None
    question_stats: List[QuestionStats] = []
    
    # Category-wise averages
    category_averages: Optional[dict] = None  # {"Teaching": 4.2, "Content": 3.8, ...}


# ============================================
# Student Survey View
# ============================================

class StudentSurveyItem(BaseModel):
    """Survey item for student view."""
    id: UUID
    title: str
    description: Optional[str] = None
    survey_type: SurveyType
    start_date: datetime
    end_date: datetime
    is_mandatory: bool
    is_submitted: bool
    submitted_at: Optional[datetime] = None
    
    # For context
    subject_name: Optional[str] = None
    faculty_name: Optional[str] = None


class StudentSurveyList(BaseModel):
    """List of surveys for a student."""
    pending: List[StudentSurveyItem] = []
    completed: List[StudentSurveyItem] = []


# ============================================
# Template Schemas
# ============================================

class SurveyTemplateCreate(BaseModel):
    """Schema for creating a survey template."""
    name: str = Field(..., min_length=1, max_length=255)
    code: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    survey_type: SurveyType
    questions: List[SurveyQuestionCreate]


class SurveyTemplateResponse(BaseModel):
    """Schema for template response."""
    id: UUID
    name: str
    code: str
    description: Optional[str] = None
    survey_type: SurveyType
    questions: List[dict]
    is_system: bool
    is_active: bool
    
    model_config = {"from_attributes": True}
