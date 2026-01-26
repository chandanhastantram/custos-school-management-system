"""
CUSTOS Assignment Schemas

Pydantic schemas for assignments and worksheets.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field

from app.models.assignment import AssignmentType, AssignmentStatus, SubmissionStatus


class AssignmentBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    instructions: Optional[str] = None
    assignment_type: AssignmentType


class AssignmentCreate(AssignmentBase):
    section_id: UUID
    subject_id: UUID
    topic_id: Optional[UUID] = None
    
    start_date: datetime
    due_date: datetime
    
    total_marks: float = 0.0
    passing_marks: Optional[float] = None
    
    late_submission_allowed: bool = False
    late_penalty_percent: float = 0.0
    
    time_limit_minutes: Optional[int] = None
    max_attempts: int = 1
    shuffle_questions: bool = False
    show_answers_after: bool = True
    
    question_ids: Optional[List[UUID]] = None


class AssignmentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    instructions: Optional[str] = None
    
    due_date: Optional[datetime] = None
    passing_marks: Optional[float] = None
    
    late_submission_allowed: Optional[bool] = None
    show_answers_after: Optional[bool] = None
    
    status: Optional[AssignmentStatus] = None


class AssignmentResponse(AssignmentBase):
    id: UUID
    tenant_id: UUID
    section_id: UUID
    subject_id: UUID
    topic_id: Optional[UUID] = None
    created_by: UUID
    
    status: AssignmentStatus
    total_marks: float
    passing_marks: Optional[float] = None
    
    start_date: datetime
    due_date: datetime
    
    late_submission_allowed: bool
    time_limit_minutes: Optional[int] = None
    max_attempts: int
    
    question_count: int = 0
    submission_count: int = 0
    
    is_ai_generated: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class SubmissionBase(BaseModel):
    assignment_id: UUID


class SubmissionCreate(SubmissionBase):
    answers: List["AnswerSubmit"]


class AnswerSubmit(BaseModel):
    question_id: UUID
    answer: Optional[str] = None
    selected_options: Optional[List[str]] = None


class SubmissionResponse(BaseModel):
    id: UUID
    assignment_id: UUID
    student_id: UUID
    
    status: SubmissionStatus
    attempt_number: int
    
    started_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    
    total_marks: float
    marks_obtained: float
    percentage: float
    is_passed: Optional[bool] = None
    
    time_taken_seconds: Optional[int] = None
    feedback: Optional[str] = None
    
    class Config:
        from_attributes = True


class WorksheetCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    
    section_id: UUID
    subject_id: UUID
    topic_id: Optional[UUID] = None
    
    question_ids: List[UUID]
    estimated_time_minutes: int = 30


class WorksheetGenerateRequest(BaseModel):
    """AI worksheet generation request."""
    section_id: UUID
    subject_id: UUID
    topic_id: Optional[UUID] = None
    
    total_questions: int = Field(default=10, ge=5, le=50)
    difficulty_mix: Optional[dict] = None  # {"easy": 3, "medium": 5, "hard": 2}
    question_types: Optional[List[str]] = None


class WorksheetResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    title: str
    description: Optional[str] = None
    
    section_id: UUID
    subject_id: UUID
    topic_id: Optional[UUID] = None
    created_by: UUID
    
    total_questions: int
    total_marks: float
    estimated_time_minutes: int
    
    is_ai_generated: bool
    pdf_url: Optional[str] = None
    answer_key_url: Optional[str] = None
    
    created_at: datetime
    
    class Config:
        from_attributes = True


class CorrectionData(BaseModel):
    """Spreadsheet-style correction data."""
    submission_id: UUID
    corrections: List["QuestionCorrection"]


class QuestionCorrection(BaseModel):
    question_id: UUID
    marks_obtained: float
    feedback: Optional[str] = None


class BulkCorrectionRequest(BaseModel):
    """Bulk correction request."""
    corrections: List[CorrectionData]


# Update forward refs
SubmissionCreate.model_rebuild()
