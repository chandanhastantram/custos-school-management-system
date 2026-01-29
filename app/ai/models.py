"""
CUSTOS AI Lesson Plan Generator Models

Models for tracking AI lesson plan generation jobs.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from sqlalchemy import String, Text, DateTime, ForeignKey, Index, JSON
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import TenantBaseModel


class AIJobStatus(str, Enum):
    """AI job processing status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AILessonPlanJob(TenantBaseModel):
    """
    AI Lesson Plan Generation Job.
    
    Tracks AI-assisted lesson plan generation with:
    - Input snapshot (syllabus, calendar, preferences)
    - Output snapshot (AI response)
    - Result (created lesson plan)
    
    Used for:
    - Auditing AI usage
    - Cost tracking
    - Debugging
    """
    __tablename__ = "ai_lesson_plan_jobs"
    
    __table_args__ = (
        Index("ix_ai_job_tenant_teacher", "tenant_id", "teacher_id"),
        Index("ix_ai_job_status", "tenant_id", "status"),
    )
    
    # Teacher who requested
    teacher_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Target class/subject
    class_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("classes.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    subject_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    syllabus_subject_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("syllabus_subjects.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Processing status
    status: Mapped[AIJobStatus] = mapped_column(
        SQLEnum(AIJobStatus),
        default=AIJobStatus.PENDING,
        nullable=False,
    )
    
    # AI provider used
    ai_provider: Mapped[str] = mapped_column(String(50), default="openai")
    
    # Input snapshot (syllabus topics, calendar, preferences)
    input_snapshot: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    
    # Output snapshot (AI raw response)
    output_snapshot: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
    )
    
    # Error message if failed
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Result - created lesson plan (if successful)
    lesson_plan_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lesson_plans.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Processing timestamps
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Token usage (for cost tracking)
    tokens_used: Mapped[int] = mapped_column(default=0)


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


class AIQuestionGenJob(TenantBaseModel):
    """
    AI Question Generation Job.
    
    Tracks AI-generated questions from syllabus topics with:
    - Input: topic, difficulty, type, count
    - Output: generated questions saved to QuestionBank
    - Cost tracking via tokens used
    """
    __tablename__ = "ai_question_gen_jobs"
    
    __table_args__ = (
        Index("ix_ai_qgen_tenant_teacher", "tenant_id", "requested_by"),
        Index("ix_ai_qgen_status", "tenant_id", "status"),
        Index("ix_ai_qgen_topic", "topic_id"),
    )
    
    # Teacher who requested
    requested_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Target syllabus topic
    topic_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("syllabus_topics.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Linking IDs for context
    subject_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    class_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("classes.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Generation parameters
    difficulty: Mapped[QuestionGenDifficulty] = mapped_column(
        SQLEnum(QuestionGenDifficulty),
        default=QuestionGenDifficulty.MIXED,
        nullable=False,
    )
    
    question_type: Mapped[QuestionGenType] = mapped_column(
        SQLEnum(QuestionGenType),
        default=QuestionGenType.MCQ,
        nullable=False,
    )
    
    count: Mapped[int] = mapped_column(default=10)
    
    # Processing status
    status: Mapped[AIJobStatus] = mapped_column(
        SQLEnum(AIJobStatus),
        default=AIJobStatus.PENDING,
        nullable=False,
    )
    
    # AI provider used
    ai_provider: Mapped[str] = mapped_column(String(50), default="openai")
    
    # Input snapshot (topic context, preferences)
    input_snapshot: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    
    # Output snapshot (AI raw response)
    output_snapshot: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
    )
    
    # IDs of created questions (result)
    created_question_ids: Mapped[Optional[list]] = mapped_column(
        JSON,
        nullable=True,
    )
    
    questions_created: Mapped[int] = mapped_column(default=0)
    
    # Error message if failed
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Processing timestamps
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Token usage (for cost tracking)
    tokens_used: Mapped[int] = mapped_column(default=0)
