"""
CUSTOS Learning Outcomes Models

Program Outcomes, Course Outcomes, CO-PO Mapping, and Attainment.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List
from uuid import UUID

from sqlalchemy import (
    String, Text, Integer, Float, Boolean, DateTime,
    ForeignKey, UniqueConstraint, Index, JSON
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import TenantBaseModel


# ============================================
# Enums
# ============================================

class OutcomeLevel(str, Enum):
    """Outcome attainment levels."""
    NOT_ATTAINED = "not_attained"
    PARTIALLY_ATTAINED = "partially_attained"
    ATTAINED = "attained"
    HIGHLY_ATTAINED = "highly_attained"


class CorrelationLevel(str, Enum):
    """CO-PO correlation levels."""
    LOW = "low"          # 1 - Slight correlation
    MEDIUM = "medium"    # 2 - Moderate correlation  
    HIGH = "high"        # 3 - Substantial correlation


class AssessmentMethod(str, Enum):
    """Methods for assessing outcomes."""
    INTERNAL_EXAM = "internal_exam"
    EXTERNAL_EXAM = "external_exam"
    ASSIGNMENT = "assignment"
    PROJECT = "project"
    LAB = "lab"
    QUIZ = "quiz"
    PRESENTATION = "presentation"
    VIVA = "viva"


# ============================================
# Program Outcome (PO)
# ============================================

class ProgramOutcome(TenantBaseModel):
    """
    Program Outcome (PO).
    
    High-level outcomes that graduates should achieve (e.g., PO1, PO2...).
    Typically 12 outcomes for engineering programs (as per NBA/ABET).
    """
    __tablename__ = "program_outcomes"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "program_id", "code",
            name="uq_po_program_code"
        ),
        Index("ix_po_program", "tenant_id", "program_id"),
        {"extend_existing": True},
    )
    
    # Program context (e.g., B.Tech CSE)
    program_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("classes.id", ondelete="CASCADE"),  # Using class as program
    )
    
    # PO identification
    code: Mapped[str] = mapped_column(String(10))  # PO1, PO2, etc.
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    
    # Display
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Target attainment (e.g., 60%)
    target_attainment: Mapped[float] = mapped_column(Float, default=60.0)
    
    # Relationships
    co_mappings: Mapped[List["COPOMapping"]] = relationship(
        "COPOMapping",
        back_populates="program_outcome",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


# ============================================
# Program Specific Outcome (PSO)
# ============================================

class ProgramSpecificOutcome(TenantBaseModel):
    """
    Program Specific Outcome (PSO).
    
    Additional outcomes specific to a program (beyond standard POs).
    """
    __tablename__ = "program_specific_outcomes"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "program_id", "code",
            name="uq_pso_program_code"
        ),
        Index("ix_pso_program", "tenant_id", "program_id"),
        {"extend_existing": True},
    )
    
    program_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("classes.id", ondelete="CASCADE"),
    )
    
    code: Mapped[str] = mapped_column(String(10))  # PSO1, PSO2, etc.
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    target_attainment: Mapped[float] = mapped_column(Float, default=60.0)


# ============================================
# Course Outcome (CO)
# ============================================

class CourseOutcome(TenantBaseModel):
    """
    Course Outcome (CO).
    
    Learning outcomes for a specific course/subject.
    """
    __tablename__ = "course_outcomes"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "subject_id", "code",
            name="uq_co_subject_code"
        ),
        Index("ix_co_subject", "tenant_id", "subject_id"),
        {"extend_existing": True},
    )
    
    # Subject/Course
    subject_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="CASCADE"),
    )
    
    # CO identification
    code: Mapped[str] = mapped_column(String(10))  # CO1, CO2, etc.
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    
    # Bloom's taxonomy level
    blooms_level: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )  # Remember, Understand, Apply, Analyze, Evaluate, Create
    
    # Display
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Target attainment
    target_attainment: Mapped[float] = mapped_column(Float, default=60.0)
    
    # Relationships
    po_mappings: Mapped[List["COPOMapping"]] = relationship(
        "COPOMapping",
        back_populates="course_outcome",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


# ============================================
# CO-PO Mapping
# ============================================

class COPOMapping(TenantBaseModel):
    """
    Course Outcome to Program Outcome mapping.
    
    Defines how each CO contributes to POs (correlation matrix).
    """
    __tablename__ = "co_po_mappings"
    __table_args__ = (
        UniqueConstraint(
            "course_outcome_id", "program_outcome_id",
            name="uq_co_po_mapping"
        ),
        Index("ix_copo_co", "course_outcome_id"),
        Index("ix_copo_po", "program_outcome_id"),
        {"extend_existing": True},
    )
    
    course_outcome_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("course_outcomes.id", ondelete="CASCADE"),
    )
    program_outcome_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("program_outcomes.id", ondelete="CASCADE"),
    )
    
    # Correlation level (1, 2, 3 or Low, Medium, High)
    correlation_level: Mapped[CorrelationLevel] = mapped_column(
        SQLEnum(CorrelationLevel, name="correlation_level_enum"),
        default=CorrelationLevel.MEDIUM
    )
    correlation_value: Mapped[int] = mapped_column(Integer, default=2)  # 1, 2, or 3
    
    # Justification
    justification: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    course_outcome: Mapped["CourseOutcome"] = relationship(
        "CourseOutcome", back_populates="po_mappings"
    )
    program_outcome: Mapped["ProgramOutcome"] = relationship(
        "ProgramOutcome", back_populates="co_mappings"
    )


# ============================================
# CO Assessment Configuration
# ============================================

class COAssessmentConfig(TenantBaseModel):
    """
    Configuration for how COs are assessed.
    
    Maps assessment methods to COs with weightages.
    """
    __tablename__ = "co_assessment_configs"
    __table_args__ = (
        Index("ix_co_assessment_co", "course_outcome_id"),
        {"extend_existing": True},
    )
    
    course_outcome_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("course_outcomes.id", ondelete="CASCADE"),
    )
    
    # Assessment method
    assessment_method: Mapped[AssessmentMethod] = mapped_column(
        SQLEnum(AssessmentMethod, name="assessment_method_enum"),
    )
    
    # Weightage (percentage)
    weightage: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Max marks for this assessment
    max_marks: Mapped[float] = mapped_column(Float, default=100.0)
    
    # Target marks for attainment
    target_marks: Mapped[float] = mapped_column(Float, default=60.0)
    
    # Exam/Assessment ID (optional link to specific exam)
    assessment_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )


# ============================================
# Student CO Attainment
# ============================================

class StudentCOAttainment(TenantBaseModel):
    """
    Individual student's CO attainment.
    
    Tracks marks/scores for each CO for a student.
    """
    __tablename__ = "student_co_attainments"
    __table_args__ = (
        UniqueConstraint(
            "student_id", "course_outcome_id", "academic_year_id",
            name="uq_student_co_attainment"
        ),
        Index("ix_student_co_student", "tenant_id", "student_id"),
        Index("ix_student_co_co", "course_outcome_id"),
        {"extend_existing": True},
    )
    
    student_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    course_outcome_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("course_outcomes.id", ondelete="CASCADE"),
    )
    subject_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="CASCADE"),
    )
    academic_year_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("academic_years.id", ondelete="CASCADE"),
    )
    
    # Marks breakdown (JSON: {assessment_method: marks_scored})
    marks_breakdown: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Calculated attainment
    total_marks_scored: Mapped[float] = mapped_column(Float, default=0.0)
    max_marks: Mapped[float] = mapped_column(Float, default=100.0)
    attainment_percentage: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Attainment level
    attainment_level: Mapped[OutcomeLevel] = mapped_column(
        SQLEnum(OutcomeLevel, name="outcome_level_enum"),
        default=OutcomeLevel.NOT_ATTAINED
    )
    
    # Is target attained?
    is_attained: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Calculation timestamp
    calculated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


# ============================================
# CO Attainment Summary (Course Level)
# ============================================

class COAttainmentSummary(TenantBaseModel):
    """
    Course-level CO attainment summary.
    
    Aggregated attainment for a CO across all students in a batch.
    """
    __tablename__ = "co_attainment_summaries"
    __table_args__ = (
        UniqueConstraint(
            "course_outcome_id", "academic_year_id", "batch_id",
            name="uq_co_attainment_summary"
        ),
        Index("ix_co_summary_batch", "tenant_id", "batch_id"),
        {"extend_existing": True},
    )
    
    course_outcome_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("course_outcomes.id", ondelete="CASCADE"),
    )
    subject_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="CASCADE"),
    )
    academic_year_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("academic_years.id", ondelete="CASCADE"),
    )
    batch_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("sections.id", ondelete="CASCADE"),  # Batch/section
    )
    
    # Student counts
    total_students: Mapped[int] = mapped_column(Integer, default=0)
    students_attained: Mapped[int] = mapped_column(Integer, default=0)
    
    # Attainment statistics
    average_attainment: Mapped[float] = mapped_column(Float, default=0.0)
    attainment_percentage: Mapped[float] = mapped_column(Float, default=0.0)  # % students who attained
    
    # Direct attainment (from internal assessments)
    direct_attainment: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Indirect attainment (from surveys/feedback)
    indirect_attainment: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Final attainment (weighted average)
    final_attainment: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Target met?
    target_attainment: Mapped[float] = mapped_column(Float, default=60.0)
    is_target_met: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Calculation info
    calculated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    calculated_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )


# ============================================
# PO Attainment Summary
# ============================================

class POAttainmentSummary(TenantBaseModel):
    """
    Program Outcome attainment summary.
    
    Aggregated PO attainment from all contributing COs.
    """
    __tablename__ = "po_attainment_summaries"
    __table_args__ = (
        UniqueConstraint(
            "program_outcome_id", "academic_year_id", "batch_id",
            name="uq_po_attainment_summary"
        ),
        Index("ix_po_summary_batch", "tenant_id", "batch_id"),
        {"extend_existing": True},
    )
    
    program_outcome_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("program_outcomes.id", ondelete="CASCADE"),
    )
    program_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("classes.id", ondelete="CASCADE"),
    )
    academic_year_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("academic_years.id", ondelete="CASCADE"),
    )
    batch_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("sections.id", ondelete="CASCADE"),
    )
    
    # Contributing COs count
    contributing_cos: Mapped[int] = mapped_column(Integer, default=0)
    
    # Attainment values
    direct_attainment: Mapped[float] = mapped_column(Float, default=0.0)
    indirect_attainment: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    final_attainment: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Target
    target_attainment: Mapped[float] = mapped_column(Float, default=60.0)
    is_target_met: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Trend (compared to previous year)
    previous_attainment: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    trend: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # improved, declined, stable
    
    # Calculation info
    calculated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
