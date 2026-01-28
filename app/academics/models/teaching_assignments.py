"""
CUSTOS Teaching Assignment Models

Maps teachers to classes and subjects for an academic year.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import String, Boolean, ForeignKey, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import TenantBaseModel


class TeachingAssignment(TenantBaseModel):
    """
    Teaching Assignment - Teacher ↔ Class ↔ Subject mapping.
    
    Answers: "Who teaches which subject in which class this year?"
    
    Used by:
    - Lesson planning (teacher ownership)
    - Timetable generation
    - Progress analytics
    - Report generation
    """
    __tablename__ = "teaching_assignments"
    
    __table_args__ = (
        # Unique constraint: one teacher per class-subject per year
        UniqueConstraint(
            "tenant_id", 
            "academic_year_id", 
            "teacher_id", 
            "class_id", 
            "subject_id",
            name="uq_teaching_assignment",
        ),
        # Indexes for common queries
        Index("ix_teaching_assignment_tenant", "tenant_id", "is_active"),
        Index("ix_teaching_assignment_teacher", "tenant_id", "teacher_id", "is_active"),
        Index("ix_teaching_assignment_class", "tenant_id", "class_id", "is_active"),
        Index("ix_teaching_assignment_subject", "tenant_id", "subject_id", "is_active"),
        Index("ix_teaching_assignment_year", "tenant_id", "academic_year_id", "is_active"),
    )
    
    # Academic year binding
    academic_year_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("academic_years.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Teacher
    teacher_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Class (may include section)
    class_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("classes.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Optional: specific section (null = all sections)
    section_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("sections.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Subject
    subject_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Additional metadata
    is_primary: Mapped[bool] = mapped_column(Boolean, default=True)
    # is_primary = True means main teacher, False = co-teacher/substitute
    
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Periods per week (for timetable planning)
    periods_per_week: Mapped[int] = mapped_column(default=0)
    
    # Relationships (optional, for eager loading)
    # teacher: Mapped["User"] = relationship("User", foreign_keys=[teacher_id])
    # class_: Mapped["Class"] = relationship("Class", foreign_keys=[class_id])
    # subject: Mapped["Subject"] = relationship("Subject", foreign_keys=[subject_id])
