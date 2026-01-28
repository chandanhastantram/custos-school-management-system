"""
CUSTOS Syllabus Engine Models

Core curriculum structure: Board → ClassLevel → Subject → Chapter → Topic
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy import String, Text, Boolean, Integer, Float, ForeignKey, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import TenantBaseModel


class Board(TenantBaseModel):
    """
    Educational Board (e.g., CBSE, ICSE, State Board).
    
    Top-level entity in syllabus hierarchy.
    """
    __tablename__ = "syllabus_boards"
    
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_board_tenant_code"),
        Index("ix_board_tenant_active", "tenant_id", "is_active"),
    )
    
    # Basic info
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Multi-language support
    name_vernacular: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    language_code: Mapped[str] = mapped_column(String(10), default="en")
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    
    # Versioning
    version: Mapped[int] = mapped_column(Integer, default=1)
    
    # Relationships
    class_levels: Mapped[List["ClassLevel"]] = relationship(
        "ClassLevel", 
        back_populates="board",
        lazy="selectin",
    )


class ClassLevel(TenantBaseModel):
    """
    Class/Grade Level within a Board (e.g., Class 10, Grade 12).
    """
    __tablename__ = "syllabus_class_levels"
    
    __table_args__ = (
        UniqueConstraint("tenant_id", "board_id", "code", name="uq_classlevel_board_code"),
        Index("ix_classlevel_board", "board_id", "is_active"),
    )
    
    board_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("syllabus_boards.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Basic info
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Multi-language
    name_vernacular: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Numeric grade (for sorting/filtering)
    grade_number: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    board: Mapped["Board"] = relationship("Board", back_populates="class_levels")
    subjects: Mapped[List["SyllabusSubject"]] = relationship(
        "SyllabusSubject",
        back_populates="class_level",
        lazy="selectin",
    )


class SyllabusSubject(TenantBaseModel):
    """
    Subject within a ClassLevel (e.g., Mathematics, Physics).
    
    Named SyllabusSubject to avoid conflict with existing Subject model.
    """
    __tablename__ = "syllabus_subjects"
    
    __table_args__ = (
        UniqueConstraint("tenant_id", "class_level_id", "code", name="uq_syllabussubject_classlevel_code"),
        Index("ix_syllabussubject_classlevel", "class_level_id", "is_active"),
    )
    
    class_level_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("syllabus_class_levels.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Basic info
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Multi-language
    name_vernacular: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # Subject metadata
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Science, Arts, etc.
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True)
    credits: Mapped[float] = mapped_column(Float, default=1.0)
    
    # Teaching hours
    total_hours: Mapped[int] = mapped_column(Integer, default=0)  # Calculated from chapters
    periods_per_week: Mapped[int] = mapped_column(Integer, default=5)
    
    # UI
    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)  # Hex color
    icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    
    # Versioning
    version: Mapped[int] = mapped_column(Integer, default=1)
    
    # Relationships
    class_level: Mapped["ClassLevel"] = relationship("ClassLevel", back_populates="subjects")
    chapters: Mapped[List["Chapter"]] = relationship(
        "Chapter",
        back_populates="subject",
        lazy="selectin",
        order_by="Chapter.order",
    )


class Chapter(TenantBaseModel):
    """
    Chapter within a Subject.
    """
    __tablename__ = "syllabus_chapters"
    
    __table_args__ = (
        UniqueConstraint("tenant_id", "subject_id", "code", name="uq_chapter_subject_code"),
        Index("ix_chapter_subject_order", "subject_id", "order"),
    )
    
    subject_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("syllabus_subjects.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Basic info
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Multi-language
    name_vernacular: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    
    # Ordering
    order: Mapped[int] = mapped_column(Integer, default=0)
    
    # Teaching hours
    estimated_hours: Mapped[float] = mapped_column(Float, default=0)  # Calculated from topics
    
    # Learning objectives
    learning_objectives: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    prerequisites: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    subject: Mapped["SyllabusSubject"] = relationship("SyllabusSubject", back_populates="chapters")
    topics: Mapped[List["SyllabusTopic"]] = relationship(
        "SyllabusTopic",
        back_populates="chapter",
        lazy="selectin",
        order_by="SyllabusTopic.order",
    )


class SyllabusTopic(TenantBaseModel):
    """
    Topic within a Chapter.
    
    The smallest unit of syllabus - represents a teachable concept.
    """
    __tablename__ = "syllabus_topics"
    
    __table_args__ = (
        UniqueConstraint("tenant_id", "chapter_id", "code", name="uq_topic_chapter_code"),
        Index("ix_topic_chapter_order", "chapter_id", "order"),
    )
    
    chapter_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("syllabus_chapters.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Basic info
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    code: Mapped[str] = mapped_column(String(30), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Multi-language
    name_vernacular: Mapped[Optional[str]] = mapped_column(String(400), nullable=True)
    
    # Ordering
    order: Mapped[int] = mapped_column(Integer, default=0)
    
    # Teaching hours
    estimated_hours: Mapped[float] = mapped_column(Float, default=1.0)
    estimated_periods: Mapped[int] = mapped_column(Integer, default=1)
    
    # Learning content
    learning_objectives: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    keywords: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Comma-separated
    
    # Difficulty & importance
    difficulty_level: Mapped[int] = mapped_column(Integer, default=3)  # 1-5
    importance_level: Mapped[int] = mapped_column(Integer, default=3)  # 1-5
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    chapter: Mapped["Chapter"] = relationship("Chapter", back_populates="topics")
    weightages: Mapped[List["TopicWeightage"]] = relationship(
        "TopicWeightage",
        back_populates="topic",
        lazy="selectin",
    )


class TopicWeightage(TenantBaseModel):
    """
    Topic weightage for exams/assessments.
    
    Allows different weightages for different exam types.
    """
    __tablename__ = "syllabus_topic_weightages"
    
    __table_args__ = (
        UniqueConstraint("tenant_id", "topic_id", "exam_type", name="uq_weightage_topic_exam"),
    )
    
    topic_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("syllabus_topics.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Exam type (e.g., "unit_test", "midterm", "final", "board")
    exam_type: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Weightage
    weightage_percent: Mapped[float] = mapped_column(Float, default=0)
    expected_marks: Mapped[float] = mapped_column(Float, default=0)
    
    # Question distribution
    mcq_count: Mapped[int] = mapped_column(Integer, default=0)
    short_answer_count: Mapped[int] = mapped_column(Integer, default=0)
    long_answer_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    topic: Mapped["SyllabusTopic"] = relationship("SyllabusTopic", back_populates="weightages")
