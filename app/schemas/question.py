"""
CUSTOS Question Schemas

Pydantic schemas for questions.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field

from app.models.question import QuestionType, BloomLevel, Difficulty


class QuestionBase(BaseModel):
    question_text: str = Field(..., min_length=1)
    question_type: QuestionType
    bloom_level: BloomLevel = BloomLevel.KNOWLEDGE
    difficulty: Difficulty = Difficulty.MEDIUM


class MCQOption(BaseModel):
    id: str
    text: str
    is_correct: bool = False


class QuestionCreate(QuestionBase):
    topic_id: UUID
    question_html: Optional[str] = None
    
    options: Optional[List[MCQOption]] = None
    correct_answer: Optional[str] = None
    
    explanation: Optional[str] = None
    solution_steps: Optional[List[str]] = None
    
    marks: float = 1.0
    negative_marks: float = 0.0
    time_limit_seconds: Optional[int] = None
    
    subtopic: Optional[str] = None
    tags: Optional[List[str]] = None


class QuestionUpdate(BaseModel):
    question_text: Optional[str] = None
    question_html: Optional[str] = None
    
    options: Optional[List[MCQOption]] = None
    correct_answer: Optional[str] = None
    
    explanation: Optional[str] = None
    solution_steps: Optional[List[str]] = None
    
    marks: Optional[float] = None
    difficulty: Optional[Difficulty] = None
    bloom_level: Optional[BloomLevel] = None
    
    subtopic: Optional[str] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None


class QuestionResponse(QuestionBase):
    id: UUID
    tenant_id: UUID
    topic_id: UUID
    created_by: UUID
    
    question_html: Optional[str] = None
    options: Optional[List[dict]] = None
    correct_answer: Optional[str] = None
    correct_options: Optional[List[str]] = None
    
    explanation: Optional[str] = None
    solution_steps: Optional[List[str]] = None
    
    marks: float
    negative_marks: float
    time_limit_seconds: Optional[int] = None
    
    subtopic: Optional[str] = None
    tags: Optional[List[str]] = None
    
    is_ai_generated: bool
    ai_confidence: Optional[float] = None
    is_reviewed: bool
    
    times_used: int
    avg_score: float
    is_active: bool
    
    created_at: datetime
    
    class Config:
        from_attributes = True


class QuestionListResponse(BaseModel):
    items: List[QuestionResponse]
    total: int
    page: int
    size: int
    pages: int


class QuestionFilter(BaseModel):
    topic_id: Optional[UUID] = None
    question_type: Optional[QuestionType] = None
    difficulty: Optional[Difficulty] = None
    bloom_level: Optional[BloomLevel] = None
    is_reviewed: Optional[bool] = None
    is_ai_generated: Optional[bool] = None
    search: Optional[str] = None


class QuestionAttemptCreate(BaseModel):
    question_id: UUID
    assignment_id: Optional[UUID] = None
    answer: Optional[str] = None
    selected_options: Optional[List[str]] = None
    time_taken_seconds: Optional[int] = None


class QuestionAttemptResponse(BaseModel):
    id: UUID
    question_id: UUID
    student_id: UUID
    assignment_id: Optional[UUID] = None
    
    answer: Optional[str] = None
    selected_options: Optional[List[str]] = None
    
    is_correct: Optional[bool] = None
    marks_obtained: float
    time_taken_seconds: Optional[int] = None
    
    needs_manual_grading: bool
    grader_feedback: Optional[str] = None
    
    attempted_at: datetime
    
    class Config:
        from_attributes = True


class QuestionGenerateRequest(BaseModel):
    """Request for AI question generation."""
    topic_id: UUID
    count: int = Field(default=5, ge=1, le=20)
    question_type: QuestionType = QuestionType.MCQ
    difficulty: Difficulty = Difficulty.MEDIUM
    bloom_levels: Optional[List[BloomLevel]] = None
    include_explanation: bool = True
