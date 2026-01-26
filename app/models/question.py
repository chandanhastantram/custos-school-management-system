"""
CUSTOS Question Models

Models for question bank and question engine.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    String, Text, Boolean, Integer, DateTime,
    ForeignKey, Enum as SQLEnum, JSON, Float,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TenantSoftDeleteModel, TenantBaseModel

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.academic import Topic


class QuestionType(str, Enum):
    """Type of question."""
    MCQ = "mcq"
    MCQ_MULTIPLE = "mcq_multiple"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"
    LONG_ANSWER = "long_answer"
    FILL_BLANK = "fill_blank"
    MATCH = "match"
    ORDERING = "ordering"


class BloomLevel(str, Enum):
    """Bloom's taxonomy levels."""
    KNOWLEDGE = "knowledge"
    COMPREHENSION = "comprehension"
    APPLICATION = "application"
    ANALYSIS = "analysis"
    SYNTHESIS = "synthesis"
    EVALUATION = "evaluation"


class Difficulty(str, Enum):
    """Question difficulty levels."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


class Question(TenantSoftDeleteModel):
    """Question bank item."""
    __tablename__ = "questions"
    
    topic_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("topics.id"), nullable=False, index=True)
    created_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_html: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    question_type: Mapped[QuestionType] = mapped_column(SQLEnum(QuestionType), nullable=False)
    bloom_level: Mapped[BloomLevel] = mapped_column(SQLEnum(BloomLevel), default=BloomLevel.KNOWLEDGE)
    difficulty: Mapped[Difficulty] = mapped_column(SQLEnum(Difficulty), default=Difficulty.MEDIUM)
    
    # MCQ Options
    options: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    correct_answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    correct_options: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    
    # Explanation
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    solution_steps: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    
    # Metadata
    marks: Mapped[float] = mapped_column(Float, default=1.0)
    negative_marks: Mapped[float] = mapped_column(Float, default=0.0)
    time_limit_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Tags
    subtopic: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    tags: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, default=list)
    
    # AI Generation
    is_ai_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Review
    is_reviewed: Mapped[bool] = mapped_column(Boolean, default=False)
    reviewed_by: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Stats
    times_used: Mapped[int] = mapped_column(Integer, default=0)
    avg_score: Mapped[float] = mapped_column(Float, default=0.0)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    topic: Mapped["Topic"] = relationship("Topic", lazy="selectin")
    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by], lazy="selectin")
    attempts: Mapped[List["QuestionAttempt"]] = relationship("QuestionAttempt", back_populates="question")


class QuestionAttempt(TenantBaseModel):
    """Student attempt on a question."""
    __tablename__ = "question_attempts"
    
    question_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("questions.id"), nullable=False, index=True)
    student_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    assignment_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("assignments.id"), nullable=True)
    
    answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    selected_options: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    
    is_correct: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    marks_obtained: Mapped[float] = mapped_column(Float, default=0.0)
    
    time_taken_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    attempted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Manual correction
    needs_manual_grading: Mapped[bool] = mapped_column(Boolean, default=False)
    graded_by: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    graded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    grader_feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    question: Mapped["Question"] = relationship("Question", back_populates="attempts", lazy="selectin")
    student: Mapped["User"] = relationship("User", foreign_keys=[student_id], lazy="selectin")
