"""
CUSTOS Attendance Models

Student and teacher attendance tracking.
"""

from datetime import datetime, date, time
from enum import Enum
from typing import Optional, List
from uuid import UUID

from sqlalchemy import String, Text, Boolean, Date, Time, DateTime, ForeignKey, Index, JSON, UniqueConstraint
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import TenantBaseModel


class AttendanceStatus(str, Enum):
    """Attendance status options."""
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    HALF_DAY = "half_day"
    EXCUSED = "excused"
    HOLIDAY = "holiday"
    NOT_MARKED = "not_marked"


class LeaveRequestStatus(str, Enum):
    """Leave request status."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class LeaveType(str, Enum):
    """Types of leave."""
    SICK = "sick"
    CASUAL = "casual"
    PERSONAL = "personal"
    FAMILY = "family"
    OTHER = "other"


class StudentAttendance(TenantBaseModel):
    """
    Daily student attendance record.
    
    One record per student per day.
    """
    __tablename__ = "student_attendance"
    
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "student_id", "attendance_date",
            name="uq_student_attendance_date",
        ),
        Index("ix_student_attendance_date", "tenant_id", "attendance_date"),
        Index("ix_student_attendance_student", "tenant_id", "student_id"),
        Index("ix_student_attendance_class", "tenant_id", "class_id", "attendance_date"),
    )
    
    # Student
    student_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Class & Section
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
    
    # Date
    attendance_date: Mapped[date] = mapped_column(Date, nullable=False)
    
    # Status
    status: Mapped[AttendanceStatus] = mapped_column(
        SQLEnum(AttendanceStatus),
        default=AttendanceStatus.NOT_MARKED,
    )
    
    # Time tracking (optional)
    check_in_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    check_out_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    
    # Late details
    late_minutes: Mapped[int] = mapped_column(default=0)
    
    # Notes
    remarks: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Who marked it
    marked_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    marked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Academic year reference
    academic_year_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("academic_years.id", ondelete="SET NULL"),
        nullable=True,
    )


class AttendanceSummary(TenantBaseModel):
    """
    Monthly attendance summary per student.
    
    Aggregated for reporting and parent view.
    """
    __tablename__ = "attendance_summaries"
    
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "student_id", "year", "month",
            name="uq_attendance_summary_month",
        ),
        Index("ix_attendance_summary_student", "tenant_id", "student_id"),
    )
    
    student_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    year: Mapped[int] = mapped_column(nullable=False)
    month: Mapped[int] = mapped_column(nullable=False)
    
    # Counts
    total_days: Mapped[int] = mapped_column(default=0)
    present_days: Mapped[int] = mapped_column(default=0)
    absent_days: Mapped[int] = mapped_column(default=0)
    late_days: Mapped[int] = mapped_column(default=0)
    half_days: Mapped[int] = mapped_column(default=0)
    excused_days: Mapped[int] = mapped_column(default=0)
    
    # Percentage
    attendance_percentage: Mapped[float] = mapped_column(default=0.0)
    
    # Last calculated
    calculated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class LeaveRequest(TenantBaseModel):
    """
    Leave request from parent/student.
    """
    __tablename__ = "leave_requests"
    
    __table_args__ = (
        Index("ix_leave_request_student", "tenant_id", "student_id"),
        Index("ix_leave_request_status", "tenant_id", "status"),
    )
    
    # Student
    student_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Requested by (parent or student)
    requested_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Leave details
    leave_type: Mapped[LeaveType] = mapped_column(
        SQLEnum(LeaveType),
        default=LeaveType.CASUAL,
    )
    
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Supporting documents
    attachments: Mapped[Optional[List[dict]]] = mapped_column(JSON, nullable=True)
    
    # Status
    status: Mapped[LeaveRequestStatus] = mapped_column(
        SQLEnum(LeaveRequestStatus),
        default=LeaveRequestStatus.PENDING,
    )
    
    # Approval
    reviewed_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    review_notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)


class TeacherAttendance(TenantBaseModel):
    """
    Daily teacher attendance record.
    """
    __tablename__ = "teacher_attendance"
    
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "teacher_id", "attendance_date",
            name="uq_teacher_attendance_date",
        ),
        Index("ix_teacher_attendance_date", "tenant_id", "attendance_date"),
        Index("ix_teacher_attendance_teacher", "tenant_id", "teacher_id"),
    )
    
    teacher_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    attendance_date: Mapped[date] = mapped_column(Date, nullable=False)
    
    status: Mapped[AttendanceStatus] = mapped_column(
        SQLEnum(AttendanceStatus),
        default=AttendanceStatus.NOT_MARKED,
    )
    
    check_in_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    check_out_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    
    remarks: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    marked_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
