"""
CUSTOS AI Schemas
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field

from app.models.ai import AIFeature


class LessonPlanRequest(BaseModel):
    topic_id: UUID
    duration_minutes: int = Field(default=45, ge=15, le=180)
    include_activities: bool = True
    include_assessment: bool = True
    style: Optional[str] = None  # interactive, lecture, practical


class LessonPlanResponse(BaseModel):
    title: str
    objectives: List[str]
    content: dict
    activities: List[dict]
    assessment_plan: dict
    homework: Optional[str] = None
    resources: List[dict]
    
    tokens_used: int
    lesson_id: Optional[UUID] = None


class QuestionGenerationRequest(BaseModel):
    topic_id: UUID
    count: int = Field(default=5, ge=1, le=20)
    question_type: str = "mcq"
    difficulty: str = "medium"
    bloom_levels: Optional[List[str]] = None


class QuestionGenerationResponse(BaseModel):
    questions: List[dict]
    tokens_used: int
    saved_count: int


class WorksheetGenerationRequest(BaseModel):
    topic_id: UUID
    title: str
    question_count: int = Field(default=10, ge=5, le=30)
    difficulty_distribution: Optional[dict] = None
    include_answer_key: bool = True


class WorksheetGenerationResponse(BaseModel):
    worksheet_id: UUID
    title: str
    question_count: int
    total_marks: float
    tokens_used: int


class DoubtSolverRequest(BaseModel):
    question: str = Field(..., min_length=10, max_length=2000)
    subject_id: Optional[UUID] = None
    topic_id: Optional[UUID] = None
    context: Optional[str] = None


class DoubtSolverResponse(BaseModel):
    answer: str
    explanation: Optional[str] = None
    related_topics: List[str] = []
    follow_up_questions: List[str] = []
    tokens_used: int


class AIUsageResponse(BaseModel):
    tenant_id: UUID
    year: int
    month: int
    
    total_tokens: int
    limit_tokens: int
    remaining_tokens: int
    
    total_cost: float
    request_count: int
    
    usage_by_feature: dict
    is_limit_reached: bool
