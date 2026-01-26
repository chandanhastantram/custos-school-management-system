"""
CUSTOS Report Models

Models for reports and analytics.
"""

from datetime import datetime, date
from enum import Enum
from typing import Optional, List, TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    String, Text, Boolean, Integer, DateTime, Date,
    ForeignKey, Enum as SQLEnum, JSON, Float,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TenantBaseModel

if TYPE_CHECKING:
    from app.models.user import User


class ReportType(str, Enum):
    STUDENT_PERFORMANCE = "student_performance"
    CLASS_ANALYTICS = "class_analytics"
    TEACHER_EFFECTIVENESS = "teacher_effectiveness"
    SUBJECT_ANALYSIS = "subject_analysis"
    ATTENDANCE = "attendance"
    CUSTOM = "custom"


class ReportPeriod(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    CUSTOM = "custom"


class Report(TenantBaseModel):
    """Generated report."""
    __tablename__ = "reports"
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    report_type: Mapped[ReportType] = mapped_column(SQLEnum(ReportType), nullable=False)
    period: Mapped[ReportPeriod] = mapped_column(SQLEnum(ReportPeriod), nullable=False)
    
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    
    # Target entity
    student_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    teacher_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    class_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("classes.id"), nullable=True)
    section_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("sections.id"), nullable=True)
    subject_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("subjects.id"), nullable=True)
    
    # Report data
    data: Mapped[dict] = mapped_column(JSON, nullable=False)
    summary: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    insights: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    
    generated_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    pdf_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)


class StudentPerformance(TenantBaseModel):
    """Student performance metrics."""
    __tablename__ = "student_performances"
    
    student_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    subject_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("subjects.id"), nullable=True)
    
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    
    assignments_total: Mapped[int] = mapped_column(Integer, default=0)
    assignments_completed: Mapped[int] = mapped_column(Integer, default=0)
    assignments_passed: Mapped[int] = mapped_column(Integer, default=0)
    
    total_marks: Mapped[float] = mapped_column(Float, default=0.0)
    marks_obtained: Mapped[float] = mapped_column(Float, default=0.0)
    percentage: Mapped[float] = mapped_column(Float, default=0.0)
    
    questions_attempted: Mapped[int] = mapped_column(Integer, default=0)
    questions_correct: Mapped[int] = mapped_column(Integer, default=0)
    accuracy: Mapped[float] = mapped_column(Float, default=0.0)
    
    avg_time_per_question: Mapped[float] = mapped_column(Float, default=0.0)
    
    strength_topics: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    weakness_topics: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    
    rank_in_class: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rank_in_section: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    student: Mapped["User"] = relationship("User", lazy="selectin")


class TeacherEffectiveness(TenantBaseModel):
    """Teacher effectiveness metrics."""
    __tablename__ = "teacher_effectiveness"
    
    teacher_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    
    lessons_planned: Mapped[int] = mapped_column(Integer, default=0)
    lessons_completed: Mapped[int] = mapped_column(Integer, default=0)
    syllabus_completion: Mapped[float] = mapped_column(Float, default=0.0)
    
    assignments_created: Mapped[int] = mapped_column(Integer, default=0)
    assignments_graded: Mapped[int] = mapped_column(Integer, default=0)
    avg_grading_time_hours: Mapped[float] = mapped_column(Float, default=0.0)
    
    questions_created: Mapped[int] = mapped_column(Integer, default=0)
    questions_reviewed: Mapped[int] = mapped_column(Integer, default=0)
    
    avg_class_score: Mapped[float] = mapped_column(Float, default=0.0)
    class_pass_rate: Mapped[float] = mapped_column(Float, default=0.0)
    
    student_engagement_score: Mapped[float] = mapped_column(Float, default=0.0)
    feedback_score: Mapped[float] = mapped_column(Float, default=0.0)
    
    teacher: Mapped["User"] = relationship("User", lazy="selectin")
