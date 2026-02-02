"""
CUSTOS Daily Learning Loop Models

Models for tracking daily MCQ sessions and student mastery.
"""

from datetime import datetime, date
from typing import Optional, List
from uuid import UUID

from sqlalchemy import String, Boolean, Integer, Float, Date, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import TenantBaseModel, BaseModel


class DailyLoopSession(TenantBaseModel):
    """
    Daily Loop Session - A set of MCQs for a scheduled class period.
    
    Links to ScheduleEntry → provides context for which topic is being practiced.
    Students submit attempts against this session.
    """
    __tablename__ = "daily_loop_sessions"
    
    __table_args__ = (
        Index("ix_daily_session_tenant_date", "tenant_id", "date"),
        Index("ix_daily_session_schedule", "schedule_entry_id"),
        Index("ix_daily_session_class", "tenant_id", "class_id", "date"),
        Index("ix_daily_session_topic", "tenant_id", "topic_id", "date"),
    )
    
    # Link to the schedule entry (tells us what topic for what class on what date)
    schedule_entry_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("schedule_entries.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Denormalized for quick access
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
    
    topic_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("syllabus_topics.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # The date this session is for
    date: Mapped[date] = mapped_column(Date, nullable=False)
    
    # Session status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Configuration (optional)
    max_questions: Mapped[int] = mapped_column(Integer, default=10)
    time_limit_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Stats (updated as attempts come in)
    total_attempts: Mapped[int] = mapped_column(Integer, default=0)
    unique_students: Mapped[int] = mapped_column(Integer, default=0)
    avg_score_percent: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Relationships
    attempts: Mapped[List["DailyLoopAttempt"]] = relationship(
        "DailyLoopAttempt",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class DailyLoopAttempt(BaseModel):
    """
    Daily Loop Attempt - A single question attempt by a student.
    
    Records: student + question + answer + correctness + time
    
    Note: Inherits from BaseModel (not TenantBaseModel) since tenant
    is derived from session. This keeps the table lean.
    """
    __tablename__ = "daily_loop_attempts"
    
    __table_args__ = (
        Index("ix_daily_attempt_session", "session_id"),
        Index("ix_daily_attempt_student", "student_id"),
        Index("ix_daily_attempt_question", "question_id"),
    )
    
    # Link to session
    session_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("daily_loop_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # The student who attempted
    student_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # The question attempted
    question_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # What the student selected (e.g., "A", "B", "C", "D" or text)
    selected_option: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # Was it correct?
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    
    # How long did they take?
    time_taken_seconds: Mapped[int] = mapped_column(Integer, default=0)
    
    # Optional: attempt number (if retries allowed)
    attempt_number: Mapped[int] = mapped_column(Integer, default=1)
    
    # Relationships
    session: Mapped["DailyLoopSession"] = relationship(
        "DailyLoopSession", back_populates="attempts"
    )


class StudentTopicMastery(TenantBaseModel):
    """
    Student Topic Mastery - Aggregated mastery data per student per topic.
    
    Updated after each attempt. Used for:
    - Strong/weak question identification
    - Adaptive question selection
    - Progress reporting
    
    FAIR MASTERY: excused absences are excluded from denominator.
    """
    __tablename__ = "student_topic_mastery"
    
    __table_args__ = (
        Index("ix_mastery_student", "tenant_id", "student_id"),
        Index("ix_mastery_topic", "tenant_id", "topic_id"),
        Index("ix_mastery_student_topic", "student_id", "topic_id", unique=True),
    )
    
    # Student
    student_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Topic
    topic_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("syllabus_topics.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Aggregated stats (only counts participated events)
    total_attempts: Mapped[int] = mapped_column(Integer, default=0)
    correct_attempts: Mapped[int] = mapped_column(Integer, default=0)
    
    # Participation tracking (NEW - for academic fairness)
    total_sessions: Mapped[int] = mapped_column(Integer, default=0)  # Total sessions scheduled
    participated_sessions: Mapped[int] = mapped_column(Integer, default=0)  # Actually participated
    excused_absence_count: Mapped[int] = mapped_column(Integer, default=0)  # Excused absences
    unexcused_absence_count: Mapped[int] = mapped_column(Integer, default=0)  # Unexcused absences
    
    # Computed mastery percentage (0.0 to 100.0)
    # Only from PARTICIPATED sessions (excused excluded from denominator)
    mastery_percent: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Streak tracking (optional)
    current_streak: Mapped[int] = mapped_column(Integer, default=0)
    best_streak: Mapped[int] = mapped_column(Integer, default=0)
    
    # Last activity
    last_attempt_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Strong/weak categorization thresholds:
    # - Strong: mastery_percent >= 70
    # - Weak: mastery_percent < 40
    # - Moderate: 40 <= mastery_percent < 70
