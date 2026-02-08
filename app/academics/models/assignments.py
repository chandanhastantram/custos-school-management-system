"""
CUSTOS Assignment Models
"""

from datetime import datetime, date
from enum import Enum
from typing import Optional, List
from uuid import UUID

from sqlalchemy import String, Text, Boolean, Integer, Float, Date, DateTime, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import TenantBaseModel


class AssignmentType(str, Enum):
    HOMEWORK = "homework"
    CLASSWORK = "classwork"
    TEST = "test"
    QUIZ = "quiz"
    PROJECT = "project"
    EXAM = "exam"


class AssignmentStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    CLOSED = "closed"
    ARCHIVED = "archived"


class Assignment(TenantBaseModel):
    """Assignment."""
    __tablename__ = "assignments"
    
    section_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("sections.id"))
    subject_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("subjects.id"))
    created_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    assignment_type: Mapped[AssignmentType] = mapped_column(SQLEnum(AssignmentType), default=AssignmentType.HOMEWORK)
    status: Mapped[AssignmentStatus] = mapped_column(SQLEnum(AssignmentStatus), default=AssignmentStatus.DRAFT)
    
    total_marks: Mapped[float] = mapped_column(Float, default=100)
    passing_marks: Mapped[float] = mapped_column(Float, default=35)
    
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    time_limit_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_attempts: Mapped[int] = mapped_column(Integer, default=1)
    
    allow_late_submission: Mapped[bool] = mapped_column(Boolean, default=False)
    late_penalty_percent: Mapped[float] = mapped_column(Float, default=0)
    
    shuffle_questions: Mapped[bool] = mapped_column(Boolean, default=False)
    show_answers_after: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    questions: Mapped[List["AssignmentQuestion"]] = relationship("AssignmentQuestion", back_populates="assignment")
    submissions: Mapped[List["Submission"]] = relationship("Submission", back_populates="assignment")


class AssignmentQuestion(TenantBaseModel):
    """Question in assignment."""
    __tablename__ = "assignment_questions"
    
    assignment_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("assignments.id", ondelete="CASCADE"))
    question_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("questions.id"))
    
    order: Mapped[int] = mapped_column(Integer, default=0)
    marks: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Relationships
    assignment: Mapped["Assignment"] = relationship("Assignment", back_populates="questions")


class SubmissionStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    GRADED = "graded"
    RETURNED = "returned"


class Submission(TenantBaseModel):
    """Student submission."""
    __tablename__ = "submissions"
    
    assignment_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("assignments.id"))
    student_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    
    status: Mapped[SubmissionStatus] = mapped_column(SQLEnum(SubmissionStatus), default=SubmissionStatus.NOT_STARTED)
    
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    attempt_number: Mapped[int] = mapped_column(Integer, default=1)
    
    total_marks: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    marks_obtained: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    percentage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    is_late: Mapped[bool] = mapped_column(Boolean, default=False)
    late_penalty_applied: Mapped[float] = mapped_column(Float, default=0)
    
    graded_by: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    graded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # File attachments
    file_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    file_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    file_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Relationships
    assignment: Mapped["Assignment"] = relationship("Assignment", back_populates="submissions")
    answers: Mapped[List["SubmissionAnswer"]] = relationship("SubmissionAnswer", back_populates="submission")


class SubmissionAnswer(TenantBaseModel):
    """Answer to a question in submission."""
    __tablename__ = "submission_answers"
    
    submission_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("submissions.id", ondelete="CASCADE"))
    question_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("questions.id"))
    
    answer_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    answer_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    is_correct: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    marks_obtained: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    auto_graded: Mapped[bool] = mapped_column(Boolean, default=False)
    teacher_feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    submission: Mapped["Submission"] = relationship("Submission", back_populates="answers")
