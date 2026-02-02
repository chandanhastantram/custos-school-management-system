"""
CUSTOS Analytics & Performance Intelligence Models

Deterministic analytics snapshots with strict role-based visibility.

CORE PRINCIPLES:
1. NO student-to-student comparison
2. Activity Score visible to students, Actual Score hidden
3. Strict role-based visibility
4. No AI - pure aggregation only
"""

from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

from sqlalchemy import String, Text, Boolean, Date, DateTime, ForeignKey, Index, Integer, Numeric
from sqlalchemy import Enum as SQLEnum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import TenantBaseModel


class AnalyticsPeriod(str, Enum):
    """Period type for analytics snapshots."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    TERM = "term"
    YEARLY = "yearly"


# ============================================
# Student Analytics Snapshot
# ============================================

class StudentAnalyticsSnapshot(TenantBaseModel):
    """
    Student Analytics Snapshot.
    
    Immutable snapshot of a student's performance for a period.
    Contains both Activity Score (visible) and Actual Score (hidden from students).
    
    VISIBILITY RULES:
    - Students: ONLY activity_score
    - Parents: Only their child's scores
    - Teachers: Class students' full data (no ranking)
    - Admin/Principal: Full visibility
    """
    __tablename__ = "analytics_student_snapshots"
    
    __table_args__ = (
        Index("ix_analytics_student_tenant", "tenant_id", "student_id"),
        Index("ix_analytics_student_class", "class_id"),
        Index("ix_analytics_student_period", "period_start", "period_end"),
    )
    
    student_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    class_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("classes.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    subject_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    academic_year_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("academic_years.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Period
    period_type: Mapped[AnalyticsPeriod] = mapped_column(
        SQLEnum(AnalyticsPeriod),
        default=AnalyticsPeriod.WEEKLY,
    )
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    
    # ------------------------------------------
    # ACTIVITY SCORE (VISIBLE TO STUDENTS)
    # ------------------------------------------
    # Measures participation, NOT correctness
    activity_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    
    # Activity breakdown
    daily_loop_participation_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    weekly_test_participation_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    lesson_eval_participation_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    attendance_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    
    # ------------------------------------------
    # ACTUAL PERFORMANCE SCORE (HIDDEN FROM STUDENTS)
    # ------------------------------------------
    # Measures mastery and correctness
    actual_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    
    # Performance breakdown
    daily_mastery_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    weekly_test_mastery_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    lesson_eval_mastery_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    
    # Overall mastery
    overall_mastery_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    
    # Raw counts (for transparency)
    daily_loops_total: Mapped[int] = mapped_column(Integer, default=0)
    daily_loops_completed: Mapped[int] = mapped_column(Integer, default=0)
    weekly_tests_total: Mapped[int] = mapped_column(Integer, default=0)
    weekly_tests_completed: Mapped[int] = mapped_column(Integer, default=0)
    lesson_evals_total: Mapped[int] = mapped_column(Integer, default=0)
    lesson_evals_completed: Mapped[int] = mapped_column(Integer, default=0)
    
    # Attendance raw
    school_days_total: Mapped[int] = mapped_column(Integer, default=0)
    school_days_present: Mapped[int] = mapped_column(Integer, default=0)
    
    # Topics/concepts analysis (NOT for comparison)
    weak_concepts_json: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    strong_concepts_json: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    
    # Generation metadata
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    generated_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )


# ============================================
# Teacher Analytics Snapshot
# ============================================

class TeacherAnalyticsSnapshot(TenantBaseModel):
    """
    Teacher Analytics Snapshot.
    
    Immutable snapshot of a teacher's teaching performance for a period.
    
    VISIBILITY RULES:
    - Teachers: Only their own data
    - Admin/Principal: Full visibility
    - Students/Parents: NO access
    """
    __tablename__ = "analytics_teacher_snapshots"
    
    __table_args__ = (
        Index("ix_analytics_teacher_tenant", "tenant_id", "teacher_id"),
        Index("ix_analytics_teacher_period", "period_start", "period_end"),
    )
    
    teacher_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    subject_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    class_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("classes.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    academic_year_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("academic_years.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Period
    period_type: Mapped[AnalyticsPeriod] = mapped_column(
        SQLEnum(AnalyticsPeriod),
        default=AnalyticsPeriod.WEEKLY,
    )
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    
    # Teaching coverage
    syllabus_coverage_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    lessons_planned: Mapped[int] = mapped_column(Integer, default=0)
    lessons_completed: Mapped[int] = mapped_column(Integer, default=0)
    
    # Schedule adherence
    schedule_adherence_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    periods_scheduled: Mapped[int] = mapped_column(Integer, default=0)
    periods_conducted: Mapped[int] = mapped_column(Integer, default=0)
    
    # Student engagement (aggregate, no individual data)
    student_participation_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    class_mastery_avg: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    
    # Assessment activity
    daily_loops_created: Mapped[int] = mapped_column(Integer, default=0)
    weekly_tests_created: Mapped[int] = mapped_column(Integer, default=0)
    lesson_evals_created: Mapped[int] = mapped_column(Integer, default=0)
    
    # Overall engagement score
    engagement_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    
    # Generation metadata
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    generated_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )


# ============================================
# Class Analytics Snapshot
# ============================================

class ClassAnalyticsSnapshot(TenantBaseModel):
    """
    Class Analytics Snapshot.
    
    Aggregate snapshot for a class (NO individual student data).
    
    VISIBILITY RULES:
    - Teachers: Only their assigned classes
    - Admin/Principal: All classes
    - Students/Parents: NO access
    """
    __tablename__ = "analytics_class_snapshots"
    
    __table_args__ = (
        Index("ix_analytics_class_tenant", "tenant_id", "class_id"),
        Index("ix_analytics_class_period", "period_start", "period_end"),
    )
    
    class_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("classes.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    subject_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    academic_year_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("academic_years.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Period
    period_type: Mapped[AnalyticsPeriod] = mapped_column(
        SQLEnum(AnalyticsPeriod),
        default=AnalyticsPeriod.WEEKLY,
    )
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    
    # Class size
    total_students: Mapped[int] = mapped_column(Integer, default=0)
    
    # Aggregate metrics (averages only, NO individual breakdown)
    avg_mastery_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    avg_activity_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    avg_attendance_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    
    # Participation rates
    daily_loop_participation_avg: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    weekly_test_participation_avg: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    lesson_eval_participation_avg: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    
    # Topic analysis (class-level patterns, NOT for comparison)
    common_weak_topics_json: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    common_strong_topics_json: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    
    # Counts (for context, NOT ranking)
    weak_topic_count: Mapped[int] = mapped_column(Integer, default=0)
    strong_topic_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Syllabus progress
    syllabus_coverage_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    
    # Generation metadata
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    generated_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
