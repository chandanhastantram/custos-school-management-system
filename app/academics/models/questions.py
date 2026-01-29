"""
CUSTOS Question Models
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from uuid import UUID

from sqlalchemy import String, Text, Boolean, Integer, Float, DateTime, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import TenantBaseModel


class QuestionType(str, Enum):
    MCQ = "mcq"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"
    LONG_ANSWER = "long_answer"
    FILL_BLANK = "fill_blank"
    MATCH = "match"


class DifficultyLevel(str, Enum):
    VERY_EASY = "very_easy"
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    VERY_HARD = "very_hard"


class BloomLevel(str, Enum):
    REMEMBER = "remember"
    UNDERSTAND = "understand"
    APPLY = "apply"
    ANALYZE = "analyze"
    EVALUATE = "evaluate"
    CREATE = "create"


class QuestionStatus(str, Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class Question(TenantBaseModel):
    """Question bank item."""
    __tablename__ = "questions"
    
    subject_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("subjects.id"))
    topic_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("syllabus_topics.id"), nullable=True)
    created_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    
    question_type: Mapped[QuestionType] = mapped_column(SQLEnum(QuestionType), nullable=False)
    difficulty: Mapped[DifficultyLevel] = mapped_column(SQLEnum(DifficultyLevel), default=DifficultyLevel.MEDIUM)
    bloom_level: Mapped[BloomLevel] = mapped_column(SQLEnum(BloomLevel), default=BloomLevel.UNDERSTAND)
    
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_html: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # For MCQ
    options: Mapped[Optional[List[dict]]] = mapped_column(JSON, nullable=True)
    correct_answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    answer_explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    marks: Mapped[float] = mapped_column(Float, default=1.0)
    negative_marks: Mapped[float] = mapped_column(Float, default=0.0)
    time_limit_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    hints: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    
    status: Mapped[QuestionStatus] = mapped_column(SQLEnum(QuestionStatus), default=QuestionStatus.DRAFT)
    reviewed_by: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    success_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
