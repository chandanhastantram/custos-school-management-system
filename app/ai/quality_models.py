"""
CUSTOS AI Prompt Versioning

Manages versioned prompts for AI operations with tracking and A/B testing.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from uuid import UUID

from sqlalchemy import String, Text, Integer, Float, Boolean, DateTime, ForeignKey, Index, JSON
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import TenantBaseModel


class PromptType(str, Enum):
    """Type of AI prompt."""
    LESSON_PLAN = "lesson_plan"
    QUESTION_GEN = "question_gen"
    OCR_EXTRACT = "ocr_extract"
    DOUBT_SOLVER = "doubt_solver"


class PromptVersion(TenantBaseModel):
    """
    Versioned AI Prompts.
    
    Features:
    - Version tracking
    - A/B testing support
    - Performance metrics
    """
    __tablename__ = "prompt_versions"
    
    __table_args__ = (
        Index("ix_prompt_type_version", "tenant_id", "prompt_type", "version"),
        Index("ix_prompt_active", "tenant_id", "prompt_type", "is_active"),
    )
    
    # Prompt identification
    prompt_type: Mapped[PromptType] = mapped_column(
        SQLEnum(PromptType),
        nullable=False,
    )
    
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Prompt content
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    user_prompt_template: Mapped[str] = mapped_column(Text, nullable=False)
    response_schema: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Configuration
    model: Mapped[str] = mapped_column(String(50), default="gpt-4o")
    temperature: Mapped[float] = mapped_column(Float, default=0.7)
    max_tokens: Mapped[int] = mapped_column(Integer, default=2000)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # A/B testing
    traffic_percentage: Mapped[int] = mapped_column(Integer, default=100)  # 0-100
    
    # Performance metrics
    total_uses: Mapped[int] = mapped_column(Integer, default=0)
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    failure_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_tokens_used: Mapped[float] = mapped_column(Float, default=0.0)
    avg_quality_score: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Created by
    created_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )


class QuestionQualityRating(TenantBaseModel):
    """
    Teacher ratings for AI-generated questions.
    
    Used to:
    - Improve prompt tuning
    - Filter low-quality questions
    - Train better models
    """
    __tablename__ = "question_quality_ratings"
    
    __table_args__ = (
        Index("ix_qrating_question", "question_id"),
        Index("ix_qrating_teacher", "teacher_id"),
    )
    
    question_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    teacher_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Ratings (1-5 scale)
    accuracy_score: Mapped[int] = mapped_column(Integer, default=3)  # Factually correct
    clarity_score: Mapped[int] = mapped_column(Integer, default=3)   # Easy to understand
    difficulty_appropriate: Mapped[int] = mapped_column(Integer, default=3)  # Right level
    curriculum_aligned: Mapped[int] = mapped_column(Integer, default=3)  # Matches syllabus
    
    # Computed overall
    overall_score: Mapped[float] = mapped_column(Float, default=3.0)
    
    # Feedback
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=True)
    is_flagged: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Link to generation job
    gen_job_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
    )


class QuestionDuplicate(TenantBaseModel):
    """
    Tracks potential duplicate questions.
    """
    __tablename__ = "question_duplicates"
    
    __table_args__ = (
        Index("ix_qdupe_original", "original_question_id"),
        Index("ix_qdupe_duplicate", "duplicate_question_id"),
    )
    
    original_question_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    duplicate_question_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    similarity_score: Mapped[float] = mapped_column(Float, nullable=False)
    is_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    is_dismissed: Mapped[bool] = mapped_column(Boolean, default=False)
    
    detected_by: Mapped[str] = mapped_column(String(50), default="system")  # system or manual


class CurriculumAlignment(TenantBaseModel):
    """
    Tracks how well questions align with curriculum objectives.
    """
    __tablename__ = "curriculum_alignments"
    
    __table_args__ = (
        Index("ix_calign_question", "question_id"),
        Index("ix_calign_topic", "topic_id"),
    )
    
    question_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    topic_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("syllabus_topics.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Alignment scores (0-1)
    content_match: Mapped[float] = mapped_column(Float, default=0.0)
    bloom_level_match: Mapped[float] = mapped_column(Float, default=0.0)
    keyword_coverage: Mapped[float] = mapped_column(Float, default=0.0)
    
    overall_alignment: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Status
    is_aligned: Mapped[bool] = mapped_column(Boolean, default=True)
    needs_review: Mapped[bool] = mapped_column(Boolean, default=False)
