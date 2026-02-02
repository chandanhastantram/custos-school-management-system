"""
CUSTOS Hostel / Boarding Management Models

Hostels, rooms, beds, wardens, and student assignments.
"""

from datetime import datetime, date
from enum import Enum
from typing import Optional, List
from uuid import UUID

from sqlalchemy import String, Text, Boolean, Date, DateTime, ForeignKey, Index, Integer
from sqlalchemy import Enum as SQLEnum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import TenantBaseModel


class HostelGender(str, Enum):
    """Gender type for hostel."""
    BOYS = "boys"
    GIRLS = "girls"
    MIXED = "mixed"


class Hostel(TenantBaseModel):
    """
    Hostel / Boarding House.
    
    Represents a student residential facility.
    """
    __tablename__ = "hostels"
    
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "name",
            name="uq_hostel_name",
        ),
        Index("ix_hostels_tenant", "tenant_id", "is_active"),
    )
    
    # Basic info
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Gender type
    gender: Mapped[HostelGender] = mapped_column(
        SQLEnum(HostelGender),
        default=HostelGender.MIXED,
    )
    
    # Location
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    building_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # Capacity
    total_capacity: Mapped[int] = mapped_column(Integer, default=0)
    floor_count: Mapped[int] = mapped_column(Integer, default=1)
    
    # Contact
    contact_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    contact_email: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Soft delete
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    rooms: Mapped[List["HostelRoom"]] = relationship(
        "HostelRoom",
        back_populates="hostel",
        lazy="selectin",
    )
    wardens: Mapped[List["Warden"]] = relationship(
        "Warden",
        back_populates="hostel",
        lazy="selectin",
    )


class HostelRoom(TenantBaseModel):
    """
    Hostel Room.
    
    Individual room within a hostel.
    """
    __tablename__ = "hostel_rooms"
    
    __table_args__ = (
        UniqueConstraint(
            "hostel_id", "room_number",
            name="uq_room_number",
        ),
        Index("ix_hostel_rooms_hostel", "hostel_id", "is_active"),
    )
    
    # Hostel reference
    hostel_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("hostels.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Room details
    room_number: Mapped[str] = mapped_column(String(20), nullable=False)
    room_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Single, Double, Dormitory
    floor: Mapped[int] = mapped_column(Integer, default=0)
    
    # Capacity
    capacity: Mapped[int] = mapped_column(Integer, default=1)
    
    # Amenities (optional JSON for future)
    has_attached_bathroom: Mapped[bool] = mapped_column(Boolean, default=False)
    has_ac: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Soft delete
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    hostel: Mapped["Hostel"] = relationship("Hostel", back_populates="rooms")
    beds: Mapped[List["Bed"]] = relationship(
        "Bed",
        back_populates="room",
        lazy="selectin",
    )


class Bed(TenantBaseModel):
    """
    Individual Bed within a Room.
    
    The smallest allocatable unit in a hostel.
    """
    __tablename__ = "hostel_beds"
    
    __table_args__ = (
        UniqueConstraint(
            "room_id", "bed_number",
            name="uq_bed_number",
        ),
        Index("ix_hostel_beds_room", "room_id", "is_active"),
    )
    
    # Room reference
    room_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("hostel_rooms.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Bed details
    bed_number: Mapped[str] = mapped_column(String(20), nullable=False)
    bed_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Single, Bunk-Upper, Bunk-Lower
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_occupied: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Relationship
    room: Mapped["HostelRoom"] = relationship("HostelRoom", back_populates="beds")


class Warden(TenantBaseModel):
    """
    Hostel Warden.
    
    Staff member responsible for hostel management.
    """
    __tablename__ = "hostel_wardens"
    
    __table_args__ = (
        Index("ix_hostel_wardens_tenant", "tenant_id", "is_active"),
        Index("ix_hostel_wardens_hostel", "assigned_hostel_id"),
    )
    
    # Personal details
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    alternate_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Link to user (if warden is also a system user)
    user_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Assigned hostel
    assigned_hostel_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("hostels.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Role
    is_chief_warden: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Date range
    assigned_from: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    assigned_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationship
    hostel: Mapped[Optional["Hostel"]] = relationship("Hostel", back_populates="wardens")


class StudentHostelAssignment(TenantBaseModel):
    """
    Student Hostel Assignment.
    
    Links a student to a hostel room and bed.
    """
    __tablename__ = "student_hostel_assignments"
    
    __table_args__ = (
        Index("ix_student_hostel_tenant", "tenant_id", "is_active"),
        Index("ix_student_hostel_student", "student_id"),
        Index("ix_student_hostel_hostel", "hostel_id"),
        Index("ix_student_hostel_room", "room_id"),
        Index("ix_student_hostel_bed", "bed_id"),
    )
    
    # Student
    student_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Hostel
    hostel_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("hostels.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Room
    room_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("hostel_rooms.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Bed
    bed_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("hostel_beds.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Academic year (optional)
    academic_year_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("academic_years.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Date range
    assigned_from: Mapped[date] = mapped_column(Date, nullable=False)
    assigned_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Check-in / Check-out tracking
    checked_in_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    checked_out_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Guardian contact (emergency)
    guardian_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    guardian_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    guardian_relation: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class HostelFeeLink(TenantBaseModel):
    """
    Hostel Fee Link.
    
    Links student hostel assignment to fee invoices.
    """
    __tablename__ = "hostel_fee_links"
    
    __table_args__ = (
        Index("ix_hostel_fee_links_tenant", "tenant_id"),
        Index("ix_hostel_fee_links_student", "student_id"),
    )
    
    # Student
    student_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Hostel assignment reference
    assignment_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("student_hostel_assignments.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Fee details
    monthly_fee: Mapped[float] = mapped_column(nullable=False)
    
    # Fee period
    fee_month: Mapped[int] = mapped_column(Integer, nullable=False)
    fee_year: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Linked invoice (when generated)
    linked_invoice_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("fee_invoices.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Payment status
    is_paid: Mapped[bool] = mapped_column(Boolean, default=False)
    paid_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
