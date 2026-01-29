"""
CUSTOS Weekly Evaluation Models

Models for weekly offline tests with 40/60 strong/weak question split.
"""

from datetime import datetime, date
from enum import Enum
from typing import Optional, List
from uuid import UUID

from sqlalchemy import String, Text, Boolean, Integer, Float, Date, ForeignKey, Index, JSON
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import TenantBaseModel


class WeeklyTestStatus(str, Enum):
    """Weekly test lifecycle status."""
    CREATED = "created"       # Paper generated, not yet conducted
    CONDUCTED = "conducted"   # Test was conducted offline
    EVALUATED = "evaluated"   # Results submitted and processed


class QuestionStrengthType(str, Enum):
    """Whether question was selected from strong or weak pool."""
    STRONG = "strong"  # Student accuracy >= 70%
    WEAK = "weak"      # Student accuracy < 40%
    MODERATE = "moderate"  # 40-70% (optional filler)


class WeeklyTest(TenantBaseModel):
    """
    Weekly Test - Offline evaluation paper.
    
    Generated from daily loop data using 40% strong + 60% weak questions.
    Conducted offline, results uploaded manually.
    """
    __tablename__ = "weekly_tests"
    
    __table_args__ = (
        Index("ix_weekly_test_tenant_class", "tenant_id", "class_id"),
        Index("ix_weekly_test_status", "tenant_id", "status"),
        Index("ix_weekly_test_date", "tenant_id", "start_date", "end_date"),
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
    
    # Topics covered (from daily loops in this period)
    topic_ids: Mapped[List[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
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
    
    # Date range (for which week's daily loops to use)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    
    # Test date (when it will be conducted)
    test_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Status
    status: Mapped[WeeklyTestStatus] = mapped_column(
        SQLEnum(WeeklyTestStatus),
        default=WeeklyTestStatus.CREATED,
        nullable=False,
    )
    
    # Configuration
    total_questions: Mapped[int] = mapped_column(Integer, default=20)
    total_marks: Mapped[float] = mapped_column(Float, default=20.0)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=30)
    
    # 40/60 split config
    strong_percent: Mapped[int] = mapped_column(Integer, default=40)
    weak_percent: Mapped[int] = mapped_column(Integer, default=60)
    
    # Stats (updated after evaluation)
    students_appeared: Mapped[int] = mapped_column(Integer, default=0)
    avg_score_percent: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Timestamps
    conducted_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    evaluated_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    
    # Relationships
    questions: Mapped[List["WeeklyTestQuestion"]] = relationship(
        "WeeklyTestQuestion",
        back_populates="weekly_test",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="WeeklyTestQuestion.question_number",
    )
    results: Mapped[List["WeeklyTestResult"]] = relationship(
        "WeeklyTestResult",
        back_populates="weekly_test",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class WeeklyTestQuestion(TenantBaseModel):
    """
    Weekly Test Question - Maps question bank item to test paper.
    
    Stores:
    - question_number (sequential on paper)
    - strength_type (whether from strong or weak pool)
    """
    __tablename__ = "weekly_test_questions"
    
    __table_args__ = (
        Index("ix_weekly_question_test", "weekly_test_id", "question_number"),
    )
    
    weekly_test_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("weekly_tests.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    question_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Position on paper (1, 2, 3, ...)
    question_number: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # From which pool was this selected?
    strength_type: Mapped[QuestionStrengthType] = mapped_column(
        SQLEnum(QuestionStrengthType),
        nullable=False,
    )
    
    # Marks for this question
    marks: Mapped[float] = mapped_column(Float, default=1.0)
    
    # Relationships
    weekly_test: Mapped["WeeklyTest"] = relationship(
        "WeeklyTest", back_populates="questions"
    )


class WeeklyTestResult(TenantBaseModel):
    """
    Weekly Test Result - Individual student's result.
    
    Submitted manually by teacher after offline evaluation.
    """
    __tablename__ = "weekly_test_results"
    
    __table_args__ = (
        Index("ix_weekly_result_test", "weekly_test_id"),
        Index("ix_weekly_result_student", "student_id"),
    )
    
    weekly_test_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("weekly_tests.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    student_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Marks
    total_marks: Mapped[float] = mapped_column(Float, nullable=False)
    marks_obtained: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Which questions were attempted (by question_number)
    attempted_questions: Mapped[List[int]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )
    
    # Which questions were wrong (by question_number)
    wrong_questions: Mapped[List[int]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )
    
    # Computed
    percentage: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Submitted by
    submitted_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Relationships
    weekly_test: Mapped["WeeklyTest"] = relationship(
        "WeeklyTest", back_populates="results"
    )


class WeeklyStudentPerformance(TenantBaseModel):
    """
    Weekly Student Performance - Detailed breakdown of strong/weak performance.
    
    Used to update StudentTopicMastery after weekly evaluation.
    """
    __tablename__ = "weekly_student_performance"
    
    __table_args__ = (
        Index("ix_weekly_perf_student", "tenant_id", "student_id"),
        Index("ix_weekly_perf_test", "weekly_test_id"),
    )
    
    weekly_test_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("weekly_tests.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    student_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Performance on strong questions (40%)
    strong_total: Mapped[int] = mapped_column(Integer, default=0)
    strong_correct: Mapped[int] = mapped_column(Integer, default=0)
    strong_accuracy: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Performance on weak questions (60%)
    weak_total: Mapped[int] = mapped_column(Integer, default=0)
    weak_correct: Mapped[int] = mapped_column(Integer, default=0)
    weak_accuracy: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Mastery delta (how much mastery changed because of this weekly test)
    mastery_delta: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Overall
    overall_accuracy: Mapped[float] = mapped_column(Float, default=0.0)
