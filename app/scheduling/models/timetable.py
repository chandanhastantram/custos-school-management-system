"""
CUSTOS Timetable Models

Timetable and TimetableEntry for weekly schedule structure.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy import String, Boolean, Integer, ForeignKey, UniqueConstraint, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import TenantBaseModel


class Timetable(TenantBaseModel):
    """
    Timetable - Weekly schedule template for a class.
    
    A timetable defines the weekly period structure for a class.
    It contains entries that map periods to subjects and teachers.
    """
    __tablename__ = "timetables"
    
    __table_args__ = (
        # Indexes for common queries
        Index("ix_timetable_tenant", "tenant_id", "is_active"),
        Index("ix_timetable_year", "tenant_id", "academic_year_id", "is_active"),
    )
    
    # Academic year binding
    academic_year_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("academic_years.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Timetable name (e.g., "Class 8A Timetable - 2025-26")
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    
    # Description (optional)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Configuration (optional - for future use)
    # periods_per_day: Mapped[int] = mapped_column(Integer, default=8)
    # days_per_week: Mapped[int] = mapped_column(Integer, default=6)  # Mon-Sat
    
    # Relationships
    entries: Mapped[List["TimetableEntry"]] = relationship(
        "TimetableEntry",
        back_populates="timetable",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class TimetableEntry(TenantBaseModel):
    """
    TimetableEntry - A single slot in the timetable.
    
    Maps: Day + Period → Class + Subject + Teacher
    
    Example: Monday, Period 2 → Class 8A, Maths, Mr. Smith
    """
    __tablename__ = "timetable_entries"
    
    __table_args__ = (
        # A class can only have one subject in a given day+period slot
        UniqueConstraint(
            "timetable_id",
            "class_id",
            "day_of_week",
            "period_number",
            name="uq_timetable_class_slot",
        ),
        # Check constraint for day_of_week (0=Monday to 6=Sunday)
        CheckConstraint(
            "day_of_week >= 0 AND day_of_week <= 6",
            name="ck_timetable_day_of_week",
        ),
        # Check constraint for period_number (1-based, max 12 periods)
        CheckConstraint(
            "period_number >= 1 AND period_number <= 12",
            name="ck_timetable_period_number",
        ),
        # Indexes for common queries
        Index("ix_timetable_entry_timetable", "timetable_id"),
        Index("ix_timetable_entry_class", "class_id", "day_of_week", "period_number"),
        Index("ix_timetable_entry_teacher", "teacher_id", "day_of_week", "period_number"),
        Index("ix_timetable_entry_subject", "subject_id"),
    )
    
    # Parent timetable
    timetable_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("timetables.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Class (the class this entry is for)
    class_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("classes.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Optional: specific section
    section_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("sections.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Subject taught in this slot
    subject_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Teacher assigned to this slot
    teacher_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Day of week (0 = Monday, 1 = Tuesday, ..., 6 = Sunday)
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Period number (1-based: Period 1, Period 2, etc.)
    period_number: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Optional: Room/Location
    room: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Optional: Notes
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Relationships
    timetable: Mapped["Timetable"] = relationship(
        "Timetable",
        back_populates="entries",
    )


# Day of week mapping for display
DAY_OF_WEEK_NAMES = {
    0: "Monday",
    1: "Tuesday",
    2: "Wednesday",
    3: "Thursday",
    4: "Friday",
    5: "Saturday",
    6: "Sunday",
}
