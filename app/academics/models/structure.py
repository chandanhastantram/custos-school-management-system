"""
CUSTOS Academic Structure Models

AcademicYear, Class, Section.
"""

from datetime import date, datetime
from typing import Optional, List, TYPE_CHECKING
from uuid import UUID

from sqlalchemy import String, Text, Boolean, Integer, Date, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import TenantBaseModel


class AcademicYear(TenantBaseModel):
    """Academic year."""
    __tablename__ = "academic_years"
    
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Relationships
    classes: Mapped[List["Class"]] = relationship("Class", back_populates="academic_year")


class Class(TenantBaseModel):
    """Class/Grade."""
    __tablename__ = "classes"
    
    academic_year_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("academic_years.id"),
        nullable=False,
    )
    
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    grade_level: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    academic_year: Mapped["AcademicYear"] = relationship("AcademicYear", back_populates="classes")
    sections: Mapped[List["Section"]] = relationship("Section", back_populates="class_")


class Section(TenantBaseModel):
    """Section within a class."""
    __tablename__ = "sections"
    
    class_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("classes.id"),
        nullable=False,
    )
    
    name: Mapped[str] = mapped_column(String(20), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, default=40)
    room_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    class_teacher_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )
    
    # Relationships
    class_: Mapped["Class"] = relationship("Class", back_populates="sections")
