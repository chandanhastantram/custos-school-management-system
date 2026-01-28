"""
CUSTOS Curriculum Models

Subject, Syllabus, Topic, Lesson.
"""

from datetime import date, datetime
from enum import Enum
from typing import Optional, List, TYPE_CHECKING
from uuid import UUID

from sqlalchemy import String, Text, Boolean, Integer, Float, Date, DateTime, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import TenantBaseModel


class Subject(TenantBaseModel):
    """Subject."""
    __tablename__ = "subjects"
    
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True)
    credits: Mapped[float] = mapped_column(Float, default=1.0)
    
    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class SyllabusStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    COMPLETED = "completed"


class Syllabus(TenantBaseModel):
    """Syllabus for a subject in a class."""
    __tablename__ = "syllabi"
    
    class_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("classes.id"))
    subject_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("subjects.id"))
    academic_year_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("academic_years.id"))
    
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    total_hours: Mapped[int] = mapped_column(Integer, default=0)
    
    status: Mapped[SyllabusStatus] = mapped_column(SQLEnum(SyllabusStatus), default=SyllabusStatus.DRAFT)
    
    # Relationships
    topics: Mapped[List["Topic"]] = relationship("Topic", back_populates="syllabus")


class TopicStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class Topic(TenantBaseModel):
    """Topic within syllabus."""
    __tablename__ = "topics"
    
    syllabus_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("syllabi.id"))
    parent_topic_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("topics.id"), nullable=True)
    
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    order: Mapped[int] = mapped_column(Integer, default=0)
    estimated_hours: Mapped[float] = mapped_column(Float, default=1.0)
    
    learning_objectives: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    keywords: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    
    status: Mapped[TopicStatus] = mapped_column(SQLEnum(TopicStatus), default=TopicStatus.NOT_STARTED)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    syllabus: Mapped["Syllabus"] = relationship("Syllabus", back_populates="topics")


class LessonStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class Lesson(TenantBaseModel):
    """Lesson plan."""
    __tablename__ = "lessons"
    
    topic_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("topics.id"))
    teacher_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=45)
    
    objectives: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resources: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    activities: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    homework: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    scheduled_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[LessonStatus] = mapped_column(SQLEnum(LessonStatus), default=LessonStatus.DRAFT)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
