"""
CUSTOS Lesson Evaluation & Adaptive Models

Models for lesson-wise evaluation and adaptive learning recommendations.
"""

from datetime import datetime, date
from enum import Enum
from typing import Optional, List
from uuid import UUID

from sqlalchemy import String, Text, Boolean, Integer, Float, Date, ForeignKey, Index, JSON
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import TenantBaseModel


class LessonEvaluationStatus(str, Enum):
    """Lesson evaluation lifecycle status."""
    CREATED = "created"       # Paper generated
    CONDUCTED = "conducted"   # Test was conducted
    EVALUATED = "evaluated"   # Results submitted and processed


class RecommendationType(str, Enum):
    """Types of adaptive recommendations."""
    REVISION = "revision"                 # Review the topic
    EXTRA_DAILY_LOOP = "extra_daily_loop" # More daily practice
    REMEDIAL_CLASS = "remedial_class"     # Need special attention


class RecommendationPriority(str, Enum):
    """Priority levels for recommendations."""
    LOW = "low"       # Mastery 60-75%
    MEDIUM = "medium" # Mastery 40-60%
    HIGH = "high"     # Mastery < 40%


class LessonEvaluation(TenantBaseModel):
    """
    Lesson Evaluation - End-of-chapter/lesson test.
    
    Conducted after completing a lesson plan to measure overall mastery.
    """
    __tablename__ = "lesson_evaluations"
    
    __table_args__ = (
        Index("ix_lesson_eval_tenant_class", "tenant_id", "class_id"),
        Index("ix_lesson_eval_lesson_plan", "lesson_plan_id"),
        Index("ix_lesson_eval_status", "tenant_id", "status"),
    )
    
    # Link to lesson plan
    lesson_plan_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lesson_plans.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Target class/subject
    class_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("classes.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    section_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("sections.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    subject_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Chapter/Unit being evaluated
    chapter_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("syllabus_units.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Who created
    created_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Test details
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Test date
    test_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Status
    status: Mapped[LessonEvaluationStatus] = mapped_column(
        SQLEnum(LessonEvaluationStatus),
        default=LessonEvaluationStatus.CREATED,
        nullable=False,
    )
    
    # Configuration
    total_questions: Mapped[int] = mapped_column(Integer, default=25)
    total_marks: Mapped[float] = mapped_column(Float, default=25.0)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=45)
    
    # Stats
    students_appeared: Mapped[int] = mapped_column(Integer, default=0)
    avg_score_percent: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Timestamps
    conducted_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    evaluated_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    
    # Relationships
    questions: Mapped[List["LessonEvaluationQuestion"]] = relationship(
        "LessonEvaluationQuestion",
        back_populates="lesson_evaluation",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="LessonEvaluationQuestion.question_number",
    )
    results: Mapped[List["LessonEvaluationResult"]] = relationship(
        "LessonEvaluationResult",
        back_populates="lesson_evaluation",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class LessonEvaluationQuestion(TenantBaseModel):
    """
    Lesson Evaluation Question - Maps question to test paper.
    """
    __tablename__ = "lesson_evaluation_questions"
    
    __table_args__ = (
        Index("ix_lesson_eval_question", "lesson_evaluation_id", "question_number"),
    )
    
    lesson_evaluation_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lesson_evaluations.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    question_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Position on paper
    question_number: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Marks for this question
    marks: Mapped[float] = mapped_column(Float, default=1.0)
    
    # Topic this question tests (for per-topic analysis)
    topic_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("syllabus_topics.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Relationships
    lesson_evaluation: Mapped["LessonEvaluation"] = relationship(
        "LessonEvaluation", back_populates="questions"
    )


class LessonEvaluationResult(TenantBaseModel):
    """
    Lesson Evaluation Result - Individual student's result.
    
    IMPORTANT: participation_status determines mastery impact:
    - PARTICIPATED: Normal evaluation
    - EXCUSED_ABSENT: marks=NULL, NOT counted against student
    - UNEXCUSED_ABSENT: marks=0, counts as zero
    """
    __tablename__ = "lesson_evaluation_results"
    
    __table_args__ = (
        Index("ix_lesson_eval_result_test", "lesson_evaluation_id"),
        Index("ix_lesson_eval_result_student", "student_id"),
    )
    
    lesson_evaluation_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lesson_evaluations.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    student_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Participation status (NEW - for academic fairness)
    participation_status: Mapped[str] = mapped_column(
        String(20),
        default="participated",
        nullable=False,
    )
    
    # Absence reason (when not participated)
    absence_reason: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    
    # Marks (NULL if excused absent, 0 if unexcused absent)
    total_marks: Mapped[float] = mapped_column(Float, nullable=False)
    marks_obtained: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Wrong questions (by question_number)
    wrong_questions: Mapped[List[int]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )
    
    # Computed (NULL if not participated)
    percentage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Submitted by
    submitted_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Relationships
    lesson_evaluation: Mapped["LessonEvaluation"] = relationship(
        "LessonEvaluation", back_populates="results"
    )


class LessonMasterySnapshot(TenantBaseModel):
    """
    Lesson Mastery Snapshot - Point-in-time mastery after lesson evaluation.
    
    Captures mastery at the end of a chapter for historical tracking.
    """
    __tablename__ = "lesson_mastery_snapshots"
    
    __table_args__ = (
        Index("ix_lesson_mastery_student", "tenant_id", "student_id"),
        Index("ix_lesson_mastery_chapter", "tenant_id", "chapter_id"),
    )
    
    student_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # The chapter/unit that was evaluated
    chapter_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("syllabus_units.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Link to the lesson evaluation
    lesson_evaluation_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lesson_evaluations.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Mastery at this point
    mastery_percent: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Component scores (from different sources)
    daily_mastery: Mapped[float] = mapped_column(Float, default=0.0)
    weekly_mastery: Mapped[float] = mapped_column(Float, default=0.0)
    lesson_mastery: Mapped[float] = mapped_column(Float, default=0.0)
    
    # When evaluated
    evaluated_at: Mapped[datetime] = mapped_column(nullable=False)


class AdaptiveRecommendation(TenantBaseModel):
    """
    Adaptive Recommendation - Action items for improvement.
    
    Generated based on mastery thresholds:
    - < 40%: REMEDIAL_CLASS + HIGH priority
    - 40-60%: EXTRA_DAILY_LOOP + MEDIUM priority
    - 60-75%: REVISION + LOW priority
    """
    __tablename__ = "adaptive_recommendations"
    
    __table_args__ = (
        Index("ix_adaptive_rec_student", "tenant_id", "student_id"),
        Index("ix_adaptive_rec_topic", "tenant_id", "topic_id"),
        Index("ix_adaptive_rec_priority", "tenant_id", "priority"),
    )
    
    student_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    topic_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("syllabus_topics.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Source evaluation (optional)
    lesson_evaluation_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lesson_evaluations.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Recommendation details
    recommendation_type: Mapped[RecommendationType] = mapped_column(
        SQLEnum(RecommendationType),
        nullable=False,
    )
    
    priority: Mapped[RecommendationPriority] = mapped_column(
        SQLEnum(RecommendationPriority),
        nullable=False,
    )
    
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Current mastery when recommendation was created
    current_mastery: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Status
    is_actioned: Mapped[bool] = mapped_column(Boolean, default=False)
    actioned_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    actioned_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
