"""
CUSTOS Feedback & Surveys Models

Survey management for Course, Faculty, and General feedback collection.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from uuid import UUID

from sqlalchemy import (
    String, Text, Boolean, Integer, Float, DateTime, JSON,
    ForeignKey, UniqueConstraint, Index,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import TenantBaseModel


# ============================================
# Enums
# ============================================

class SurveyType(str, Enum):
    """Types of surveys."""
    COURSE = "course"           # Course/Subject feedback
    FACULTY = "faculty"         # Faculty/Teacher evaluation
    GENERAL = "general"         # General institution feedback
    EXAM = "exam"              # Post-exam feedback
    EVENT = "event"            # Event feedback
    CUSTOM = "custom"          # Custom surveys


class SurveyStatus(str, Enum):
    """Survey status."""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    CLOSED = "closed"
    ARCHIVED = "archived"


class QuestionType(str, Enum):
    """Types of survey questions."""
    RATING = "rating"           # 1-5 star rating
    LIKERT = "likert"          # Strongly Disagree to Strongly Agree
    TEXT = "text"              # Open text response
    MCQ = "mcq"                # Multiple choice
    YES_NO = "yes_no"          # Boolean
    SCALE = "scale"            # Numeric scale (e.g., 1-10)


class ResponseStatus(str, Enum):
    """Response status."""
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"


# ============================================
# Survey
# ============================================

class Survey(TenantBaseModel):
    """
    Survey definition.
    
    Used for Course, Faculty, and General feedback collection.
    """
    __tablename__ = "surveys"
    __table_args__ = (
        Index("ix_survey_tenant_type", "tenant_id", "survey_type"),
        Index("ix_survey_tenant_status", "tenant_id", "status"),
    )
    
    # Basic Info
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    survey_type: Mapped[SurveyType] = mapped_column(
        SQLEnum(SurveyType, name="survey_type_enum"),
        nullable=False,
    )
    
    # Timing
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Settings
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=True)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=False)
    allow_multiple_submissions: Mapped[bool] = mapped_column(Boolean, default=False)
    show_results_to_students: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Targeting (for Course/Faculty feedback)
    academic_year_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("academic_years.id", ondelete="SET NULL"),
        nullable=True,
    )
    class_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("classes.id", ondelete="SET NULL"),
        nullable=True,
    )
    section_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("sections.id", ondelete="SET NULL"),
        nullable=True,
    )
    subject_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="SET NULL"),
        nullable=True,  # For course feedback
    )
    faculty_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,  # For faculty feedback
    )
    
    # Status
    status: Mapped[SurveyStatus] = mapped_column(
        SQLEnum(SurveyStatus, name="survey_status_enum"),
        default=SurveyStatus.DRAFT,
    )
    
    # Metadata
    created_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    closed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Response tracking
    total_responses: Mapped[int] = mapped_column(Integer, default=0)
    target_respondents: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    questions: Mapped[List["SurveyQuestion"]] = relationship(
        "SurveyQuestion",
        back_populates="survey",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="SurveyQuestion.display_order",
    )
    responses: Mapped[List["SurveyResponse"]] = relationship(
        "SurveyResponse",
        back_populates="survey",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )


# ============================================
# Survey Question
# ============================================

class SurveyQuestion(TenantBaseModel):
    """
    Survey question.
    
    Supports various question types: rating, likert, text, MCQ, etc.
    """
    __tablename__ = "survey_questions"
    __table_args__ = (
        Index("ix_survey_question_survey", "survey_id"),
    )
    
    survey_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("surveys.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[QuestionType] = mapped_column(
        SQLEnum(QuestionType, name="question_type_enum"),
        nullable=False,
    )
    
    # For MCQ/Rating questions
    options: Mapped[Optional[List[dict]]] = mapped_column(JSON, nullable=True)
    # e.g., [{"value": 1, "label": "Poor"}, {"value": 5, "label": "Excellent"}]
    
    # For scale questions
    min_value: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_value: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Settings
    is_required: Mapped[bool] = mapped_column(Boolean, default=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    help_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Category (for grouping questions)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Relationships
    survey: Mapped["Survey"] = relationship("Survey", back_populates="questions")
    answers: Mapped[List["SurveyAnswer"]] = relationship(
        "SurveyAnswer",
        back_populates="question",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )


# ============================================
# Survey Response
# ============================================

class SurveyResponse(TenantBaseModel):
    """
    Survey response from a student.
    
    Groups all answers from a single submission.
    """
    __tablename__ = "survey_responses"
    __table_args__ = (
        UniqueConstraint(
            "survey_id", "student_id",
            name="uq_survey_response_student"
        ),
        Index("ix_survey_response_survey", "survey_id"),
        Index("ix_survey_response_student", "student_id"),
    )
    
    survey_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("surveys.id", ondelete="CASCADE"),
        nullable=False,
    )
    student_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Status
    status: Mapped[ResponseStatus] = mapped_column(
        SQLEnum(ResponseStatus, name="response_status_enum"),
        default=ResponseStatus.IN_PROGRESS,
    )
    
    # Timestamps
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    submitted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Metadata (for anonymous tracking)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    survey: Mapped["Survey"] = relationship("Survey", back_populates="responses")
    answers: Mapped[List["SurveyAnswer"]] = relationship(
        "SurveyAnswer",
        back_populates="response",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


# ============================================
# Survey Answer
# ============================================

class SurveyAnswer(TenantBaseModel):
    """
    Individual answer to a survey question.
    """
    __tablename__ = "survey_answers"
    __table_args__ = (
        UniqueConstraint(
            "response_id", "question_id",
            name="uq_survey_answer_question"
        ),
        Index("ix_survey_answer_response", "response_id"),
        Index("ix_survey_answer_question", "question_id"),
    )
    
    response_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("survey_responses.id", ondelete="CASCADE"),
        nullable=False,
    )
    question_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("survey_questions.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Answer values (one will be populated based on question type)
    rating_value: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    text_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    selected_option: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    boolean_value: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    numeric_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Relationships
    response: Mapped["SurveyResponse"] = relationship("SurveyResponse", back_populates="answers")
    question: Mapped["SurveyQuestion"] = relationship("SurveyQuestion", back_populates="answers")


# ============================================
# Survey Template (Predefined Questions)
# ============================================

class SurveyTemplate(TenantBaseModel):
    """
    Reusable survey template.
    
    Pre-defined question sets for common survey types.
    """
    __tablename__ = "survey_templates"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "code",
            name="uq_survey_template_code"
        ),
    )
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    survey_type: Mapped[SurveyType] = mapped_column(
        SQLEnum(SurveyType, name="survey_type_enum"),
        nullable=False,
    )
    
    # Template questions stored as JSON
    questions: Mapped[List[dict]] = mapped_column(JSON, default=list)
    # e.g., [{"question_text": "...", "question_type": "rating", "is_required": true}]
    
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
