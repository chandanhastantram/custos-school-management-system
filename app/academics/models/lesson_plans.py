"""
CUSTOS Lesson Planning Models

Lesson plans connect syllabus topics to teaching schedules.
"""

from datetime import datetime, date
from enum import Enum
from typing import Optional, List
from uuid import UUID

from sqlalchemy import String, Text, Boolean, Integer, Date, DateTime, ForeignKey, Index
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import TenantBaseModel


class LessonPlanStatus(str, Enum):
    """Lesson plan lifecycle status."""
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ProgressStatus(str, Enum):
    """Teaching progress status."""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DELAYED = "delayed"
    SKIPPED = "skipped"


class LessonPlan(TenantBaseModel):
    """
    Lesson Plan - Teacher's structured teaching plan.
    
    Links:
    - Teacher
    - Class/Section
    - Subject
    - Syllabus Subject (for topic selection)
    """
    __tablename__ = "lesson_plans"
    
    __table_args__ = (
        Index("ix_lesson_plan_teacher", "tenant_id", "teacher_id"),
        Index("ix_lesson_plan_class", "tenant_id", "class_id"),
        Index("ix_lesson_plan_status", "tenant_id", "status"),
    )
    
    # Teacher ownership
    teacher_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Class/Section target
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
    
    # Subject (from academic structure)
    subject_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Syllabus binding (for topic selection)
    syllabus_subject_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("syllabus_subjects.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Plan details
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Duration
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    
    # Status
    status: Mapped[LessonPlanStatus] = mapped_column(
        SQLEnum(LessonPlanStatus),
        default=LessonPlanStatus.DRAFT,
        nullable=False,
    )
    
    # Academic year binding
    academic_year_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("academic_years.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Calculated totals (updated when units change)
    total_periods: Mapped[int] = mapped_column(Integer, default=0)
    completed_periods: Mapped[int] = mapped_column(Integer, default=0)
    
    # Timestamps
    activated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Relationships
    units: Mapped[List["LessonPlanUnit"]] = relationship(
        "LessonPlanUnit",
        back_populates="lesson_plan",
        lazy="selectin",
        order_by="LessonPlanUnit.order",
    )


class LessonPlanUnit(TenantBaseModel):
    """
    Unit within a Lesson Plan - Maps to a Syllabus Topic.
    """
    __tablename__ = "lesson_plan_units"
    
    __table_args__ = (
        Index("ix_lesson_unit_plan", "lesson_plan_id", "order"),
    )
    
    lesson_plan_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lesson_plans.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Link to syllabus topic
    topic_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("syllabus_topics.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Order in plan
    order: Mapped[int] = mapped_column(Integer, default=0)
    
    # Teaching allocation
    estimated_periods: Mapped[int] = mapped_column(Integer, default=1)
    completed_periods: Mapped[int] = mapped_column(Integer, default=0)
    
    # Optional customization
    custom_title: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resources: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # URLs, materials
    
    # Status
    status: Mapped[ProgressStatus] = mapped_column(
        SQLEnum(ProgressStatus),
        default=ProgressStatus.PLANNED,
    )
    
    # Planned dates (optional, for detailed planning)
    planned_start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    planned_end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Relationships
    lesson_plan: Mapped["LessonPlan"] = relationship(
        "LessonPlan", back_populates="units"
    )
    progress_entries: Mapped[List["TeachingProgress"]] = relationship(
        "TeachingProgress",
        back_populates="unit",
        lazy="selectin",
        order_by="TeachingProgress.date.desc()",
    )


class TeachingProgress(TenantBaseModel):
    """
    Teaching Progress - Daily/session progress tracking.
    
    Records actual teaching vs planned.
    """
    __tablename__ = "teaching_progress"
    
    __table_args__ = (
        Index("ix_progress_unit_date", "lesson_plan_unit_id", "date"),
    )
    
    lesson_plan_unit_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lesson_plan_units.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # When
    date: Mapped[date] = mapped_column(Date, nullable=False)
    
    # What was covered
    periods_taught: Mapped[int] = mapped_column(Integer, default=1)
    
    # Status
    status: Mapped[ProgressStatus] = mapped_column(
        SQLEnum(ProgressStatus),
        default=ProgressStatus.COMPLETED,
    )
    
    # Details
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    topics_covered: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    homework_given: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Teacher who recorded (in case of substitution)
    recorded_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Relationships
    unit: Mapped["LessonPlanUnit"] = relationship(
        "LessonPlanUnit", back_populates="progress_entries"
    )
