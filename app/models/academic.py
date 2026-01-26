"""
CUSTOS Academic Models

Models for academic structure: Classes, Sections, Subjects, Lessons, Topics.
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


class AcademicYear(TenantBaseModel):
    """Academic year configuration."""
    __tablename__ = "academic_years"
    
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Class(TenantSoftDeleteModel):
    """Class/Grade model."""
    __tablename__ = "classes"
    
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    grade_level: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    academic_year_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False
    )
    
    sections: Mapped[List["Section"]] = relationship("Section", back_populates="class_", lazy="selectin")
    subjects: Mapped[List["ClassSubject"]] = relationship("ClassSubject", back_populates="class_", lazy="selectin")


class Section(TenantSoftDeleteModel):
    """Section within a class."""
    __tablename__ = "sections"
    
    class_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(20), nullable=False)
    code: Mapped[str] = mapped_column(String(10), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, default=40)
    room_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    class_teacher_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    
    class_: Mapped["Class"] = relationship("Class", back_populates="sections", lazy="selectin")
    class_teacher: Mapped[Optional["User"]] = relationship("User", lazy="selectin")


class Subject(TenantSoftDeleteModel):
    """Subject catalog."""
    __tablename__ = "subjects"
    
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    credits: Mapped[int] = mapped_column(Integer, default=1)
    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)


class ClassSubject(TenantBaseModel):
    """Subject assignment to a class."""
    __tablename__ = "class_subjects"
    
    class_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    subject_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    teacher_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    periods_per_week: Mapped[int] = mapped_column(Integer, default=5)
    is_elective: Mapped[bool] = mapped_column(Boolean, default=False)
    
    class_: Mapped["Class"] = relationship("Class", back_populates="subjects", lazy="selectin")
    subject: Mapped["Subject"] = relationship("Subject", lazy="selectin")
    teacher: Mapped[Optional["User"]] = relationship("User", lazy="selectin")


class SyllabusStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class Syllabus(TenantSoftDeleteModel):
    """Syllabus for a subject in a class."""
    __tablename__ = "syllabi"
    
    class_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("classes.id"), nullable=False, index=True)
    subject_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False, index=True)
    academic_year_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("academic_years.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    total_hours: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[SyllabusStatus] = mapped_column(SQLEnum(SyllabusStatus), default=SyllabusStatus.NOT_STARTED)
    completion_percentage: Mapped[float] = mapped_column(Float, default=0.0)
    
    topics: Mapped[List["Topic"]] = relationship("Topic", back_populates="syllabus", lazy="selectin")


class TopicStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REVISION = "revision"


class Topic(TenantBaseModel):
    """Topic within a syllabus."""
    __tablename__ = "topics"
    
    syllabus_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("syllabi.id"), nullable=False, index=True)
    parent_topic_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("topics.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    order: Mapped[int] = mapped_column(Integer, default=0)
    estimated_hours: Mapped[float] = mapped_column(Float, default=1.0)
    status: Mapped[TopicStatus] = mapped_column(SQLEnum(TopicStatus), default=TopicStatus.NOT_STARTED)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    learning_objectives: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, default=list)
    keywords: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, default=list)
    
    syllabus: Mapped["Syllabus"] = relationship("Syllabus", back_populates="topics", lazy="selectin")
    subtopics: Mapped[List["Topic"]] = relationship("Topic", back_populates="parent_topic", lazy="selectin")
    parent_topic: Mapped[Optional["Topic"]] = relationship("Topic", back_populates="subtopics", remote_side="Topic.id")
    lessons: Mapped[List["Lesson"]] = relationship("Lesson", back_populates="topic", lazy="selectin")


class LessonStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class Lesson(TenantSoftDeleteModel):
    """Lesson plan for a topic."""
    __tablename__ = "lessons"
    
    topic_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("topics.id"), nullable=False, index=True)
    teacher_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    objectives: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, default=list)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=45)
    content: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    resources: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, default=list)
    activities: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, default=list)
    assessment_plan: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    homework: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[LessonStatus] = mapped_column(SQLEnum(LessonStatus), default=LessonStatus.DRAFT)
    scheduled_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_ai_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_generation_params: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    topic: Mapped["Topic"] = relationship("Topic", back_populates="lessons", lazy="selectin")
    teacher: Mapped["User"] = relationship("User", lazy="selectin")
