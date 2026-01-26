"""
CUSTOS Assignment Models

Models for assignments, worksheets, and corrections.
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

from app.models.base import TenantSoftDeleteModel, TenantBaseModel

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.academic import Topic, Section
    from app.models.question import Question


class AssignmentType(str, Enum):
    HOMEWORK = "homework"
    CLASSWORK = "classwork"
    QUIZ = "quiz"
    TEST = "test"
    EXAM = "exam"
    PRACTICE = "practice"


class AssignmentStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    CLOSED = "closed"
    GRADED = "graded"


class Assignment(TenantSoftDeleteModel):
    """Assignment model."""
    __tablename__ = "assignments"
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    assignment_type: Mapped[AssignmentType] = mapped_column(SQLEnum(AssignmentType), nullable=False)
    status: Mapped[AssignmentStatus] = mapped_column(SQLEnum(AssignmentStatus), default=AssignmentStatus.DRAFT)
    
    section_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("sections.id"), nullable=False, index=True)
    subject_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False)
    topic_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("topics.id"), nullable=True)
    created_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    total_marks: Mapped[float] = mapped_column(Float, default=0.0)
    passing_marks: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    late_submission_allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    late_penalty_percent: Mapped[float] = mapped_column(Float, default=0.0)
    
    time_limit_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_attempts: Mapped[int] = mapped_column(Integer, default=1)
    shuffle_questions: Mapped[bool] = mapped_column(Boolean, default=False)
    show_answers_after: Mapped[bool] = mapped_column(Boolean, default=True)
    
    is_ai_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    
    section: Mapped["Section"] = relationship("Section", lazy="selectin")
    creator: Mapped["User"] = relationship("User", lazy="selectin")
    questions: Mapped[List["AssignmentQuestion"]] = relationship("AssignmentQuestion", back_populates="assignment")
    submissions: Mapped[List["AssignmentSubmission"]] = relationship("AssignmentSubmission", back_populates="assignment")


class AssignmentQuestion(TenantBaseModel):
    """Questions in an assignment."""
    __tablename__ = "assignment_questions"
    
    assignment_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("assignments.id"), nullable=False, index=True)
    question_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    order: Mapped[int] = mapped_column(Integer, default=0)
    marks: Mapped[float] = mapped_column(Float, default=1.0)
    
    assignment: Mapped["Assignment"] = relationship("Assignment", back_populates="questions")
    question: Mapped["Question"] = relationship("Question", lazy="selectin")


class SubmissionStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    LATE = "late"
    GRADED = "graded"


class AssignmentSubmission(TenantBaseModel):
    """Student submission for an assignment."""
    __tablename__ = "assignment_submissions"
    
    assignment_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("assignments.id"), nullable=False, index=True)
    student_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    status: Mapped[SubmissionStatus] = mapped_column(SQLEnum(SubmissionStatus), default=SubmissionStatus.NOT_STARTED)
    attempt_number: Mapped[int] = mapped_column(Integer, default=1)
    
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    total_marks: Mapped[float] = mapped_column(Float, default=0.0)
    marks_obtained: Mapped[float] = mapped_column(Float, default=0.0)
    percentage: Mapped[float] = mapped_column(Float, default=0.0)
    
    is_passed: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    time_taken_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    graded_by: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    graded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    assignment: Mapped["Assignment"] = relationship("Assignment", back_populates="submissions")
    student: Mapped["User"] = relationship("User", foreign_keys=[student_id], lazy="selectin")


class Worksheet(TenantSoftDeleteModel):
    """Generated worksheet."""
    __tablename__ = "worksheets"
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    section_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("sections.id"), nullable=False, index=True)
    subject_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False)
    topic_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("topics.id"), nullable=True)
    created_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    total_questions: Mapped[int] = mapped_column(Integer, default=0)
    total_marks: Mapped[float] = mapped_column(Float, default=0.0)
    estimated_time_minutes: Mapped[int] = mapped_column(Integer, default=30)
    
    is_ai_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    generation_params: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    pdf_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    answer_key_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    questions: Mapped[List["WorksheetQuestion"]] = relationship("WorksheetQuestion", back_populates="worksheet")


class WorksheetQuestion(TenantBaseModel):
    """Questions in a worksheet."""
    __tablename__ = "worksheet_questions"
    
    worksheet_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("worksheets.id"), nullable=False, index=True)
    question_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    order: Mapped[int] = mapped_column(Integer, default=0)
    
    worksheet: Mapped["Worksheet"] = relationship("Worksheet", back_populates="questions")
    question: Mapped["Question"] = relationship("Question", lazy="selectin")


class CorrectionStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class Correction(TenantBaseModel):
    """Manual correction record."""
    __tablename__ = "corrections"
    
    submission_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("assignment_submissions.id"), nullable=False)
    teacher_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    status: Mapped[CorrectionStatus] = mapped_column(SQLEnum(CorrectionStatus), default=CorrectionStatus.PENDING)
    corrections_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    time_spent_seconds: Mapped[int] = mapped_column(Integer, default=0)
    
    submission: Mapped["AssignmentSubmission"] = relationship("AssignmentSubmission", lazy="selectin")
    teacher: Mapped["User"] = relationship("User", lazy="selectin")
