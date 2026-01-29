"""
CUSTOS AI Question Generation Schemas

Pydantic schemas for AI question generation requests and responses.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


class QuestionGenDifficulty(str, Enum):
    """Question generation difficulty level."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    MIXED = "mixed"


class QuestionGenType(str, Enum):
    """Question generation type."""
    MCQ = "mcq"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"
    LONG_ANSWER = "long_answer"
    NUMERICAL = "numerical"
    FILL_BLANK = "fill_blank"
    MIXED = "mixed"


class AIQuestionGenJobStatus(str, Enum):
    """Job status enum."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# ============================================
# Request Schemas
# ============================================

class GenerateQuestionsRequest(BaseModel):
    """Request to generate AI questions."""
    class_id: UUID = Field(..., description="Target class ID")
    subject_id: UUID = Field(..., description="Target subject ID")
    topic_id: UUID = Field(..., description="Syllabus topic to generate from")
    difficulty: QuestionGenDifficulty = Field(
        default=QuestionGenDifficulty.MIXED,
        description="Difficulty level for questions"
    )
    question_type: QuestionGenType = Field(
        default=QuestionGenType.MCQ,
        description="Type of questions to generate"
    )
    count: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Number of questions to generate (max 50)"
    )


# ============================================
# Response Schemas
# ============================================

class GenerateQuestionsResponse(BaseModel):
    """Response from question generation."""
    job_id: UUID
    status: AIQuestionGenJobStatus
    questions_created: int
    question_ids: List[str] = []
    tokens_used: int = 0


class AIQuestionGenJobResponse(BaseModel):
    """Question generation job summary."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    requested_by: UUID
    topic_id: UUID
    subject_id: UUID
    class_id: UUID
    difficulty: QuestionGenDifficulty
    question_type: QuestionGenType
    count: int
    status: AIQuestionGenJobStatus
    ai_provider: str
    questions_created: int
    tokens_used: int
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class AIQuestionGenJobWithDetails(AIQuestionGenJobResponse):
    """Job with additional details and snapshots."""
    input_snapshot: Optional[dict] = None
    output_snapshot: Optional[dict] = None
    created_question_ids: Optional[List[str]] = None


# ============================================
# Usage Response
# ============================================

class QuestionGenUsageResponse(BaseModel):
    """Question generation usage statistics."""
    tier: str
    question_gen: dict = Field(
        ...,
        description="Usage stats for question generation quota"
    )
    max_questions_per_gen: int = Field(
        ...,
        description="Maximum questions allowed per generation request"
    )


# ============================================
# List Response
# ============================================

class QuestionGenJobListResponse(BaseModel):
    """Paginated list of question generation jobs."""
    items: List[AIQuestionGenJobResponse]
    total: int
    page: int
    size: int
    pages: int = 0
    
    def __init__(self, **data):
        super().__init__(**data)
        if self.size > 0:
            self.pages = (self.total + self.size - 1) // self.size
