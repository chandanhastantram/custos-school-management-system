"""
CUSTOS Examinations Models

Exam registration, hall tickets, results, and revaluation tracking.
"""

from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional, List
from uuid import UUID

from sqlalchemy import (
    String, Text, Integer, Float, Boolean, Date, DateTime,
    ForeignKey, UniqueConstraint, Index, JSON, Numeric
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import TenantBaseModel


# ============================================
# Enums
# ============================================

class ExamType(str, Enum):
    """Types of examinations."""
    REGULAR = "regular"
    SUPPLEMENTARY = "supplementary"
    BACKLOG = "backlog"
    REEXAM = "reexam"
    INTERNAL = "internal"
    MIDTERM = "midterm"
    ENDTERM = "endterm"
    PRACTICAL = "practical"
    VIVA = "viva"


class ExamStatus(str, Enum):
    """Exam status."""
    DRAFT = "draft"
    REGISTRATION_OPEN = "registration_open"
    REGISTRATION_CLOSED = "registration_closed"
    ONGOING = "ongoing"
    COMPLETED = "completed"
    RESULTS_PUBLISHED = "results_published"
    CANCELLED = "cancelled"


class RegistrationStatus(str, Enum):
    """Student exam registration status."""
    PENDING = "pending"
    REGISTERED = "registered"
    FEE_PENDING = "fee_pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    DEBARRED = "debarred"


class HallTicketStatus(str, Enum):
    """Hall ticket status."""
    NOT_GENERATED = "not_generated"
    GENERATED = "generated"
    DOWNLOADED = "downloaded"
    PRINTED = "printed"


class RevaluationStatus(str, Enum):
    """Revaluation application status."""
    PENDING = "pending"
    FEE_PENDING = "fee_pending"
    UNDER_REVIEW = "under_review"
    COMPLETED = "completed"
    NO_CHANGE = "no_change"
    MARKS_UPDATED = "marks_updated"
    REJECTED = "rejected"


class RevaluationType(str, Enum):
    """Type of revaluation."""
    REVALUATION = "revaluation"  # RV - Full paper re-evaluation
    RETOTALING = "retotaling"    # RT - Only marks re-totaling
    PHOTOCOPY = "photocopy"       # Request answer sheet photocopy


class ResultStatus(str, Enum):
    """Result status."""
    NOT_PUBLISHED = "not_published"
    PUBLISHED = "published"
    WITHHELD = "withheld"
    UNDER_REVIEW = "under_review"


class GradeType(str, Enum):
    """Grading system type."""
    PERCENTAGE = "percentage"
    CGPA = "cgpa"
    LETTER = "letter"


# ============================================
# Exam Definition
# ============================================

class Exam(TenantBaseModel):
    """
    Exam definition.
    
    Represents an examination event with registration period and schedule.
    """
    __tablename__ = "exams"
    __table_args__ = (
        Index("ix_exam_tenant_type", "tenant_id", "exam_type"),
        Index("ix_exam_tenant_status", "tenant_id", "status"),
        Index("ix_exam_academic_year", "tenant_id", "academic_year_id"),
        {"extend_existing": True},
    )
    
    # Basic info
    name: Mapped[str] = mapped_column(String(200))
    code: Mapped[str] = mapped_column(String(50))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Exam type and status
    exam_type: Mapped[ExamType] = mapped_column(
        SQLEnum(ExamType, name="exam_type_enum"),
        default=ExamType.REGULAR
    )
    status: Mapped[ExamStatus] = mapped_column(
        SQLEnum(ExamStatus, name="exam_status_enum"),
        default=ExamStatus.DRAFT
    )
    
    # Academic context
    academic_year_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("academic_years.id", ondelete="CASCADE"),
    )
    semester: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Registration period
    registration_start: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    registration_end: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    late_registration_end: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    late_fee: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.00")
    )
    
    # Exam dates
    exam_start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    exam_end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Eligibility criteria
    min_attendance_percentage: Mapped[float] = mapped_column(Float, default=75.0)
    require_fee_clearance: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Fee per subject
    exam_fee_per_subject: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.00")
    )
    
    # Relationships
    registrations: Mapped[List["ExamRegistration"]] = relationship(
        "ExamRegistration",
        back_populates="exam",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    subjects: Mapped[List["ExamSubject"]] = relationship(
        "ExamSubject",
        back_populates="exam",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


# ============================================
# Exam Subject Schedule
# ============================================

class ExamSubject(TenantBaseModel):
    """
    Subject schedule within an exam.
    
    Defines when and where a subject exam takes place.
    """
    __tablename__ = "exam_subjects"
    __table_args__ = (
        UniqueConstraint(
            "exam_id", "subject_id",
            name="uq_exam_subject"
        ),
        Index("ix_exam_subject_date", "exam_date"),
        {"extend_existing": True},
    )
    
    exam_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("exams.id", ondelete="CASCADE"),
    )
    subject_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="CASCADE"),
    )
    
    # Schedule
    exam_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    start_time: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # "09:00"
    end_time: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)    # "12:00"
    duration_minutes: Mapped[int] = mapped_column(Integer, default=180)
    
    # Venue
    venue: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    room_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Marks
    max_marks: Mapped[int] = mapped_column(Integer, default=100)
    passing_marks: Mapped[int] = mapped_column(Integer, default=40)
    
    # Relationships
    exam: Mapped["Exam"] = relationship("Exam", back_populates="subjects")


# ============================================
# Exam Registration
# ============================================

class ExamRegistration(TenantBaseModel):
    """
    Student exam registration.
    
    Tracks a student's registration for an exam including fee payment.
    """
    __tablename__ = "exam_registrations"
    __table_args__ = (
        UniqueConstraint(
            "exam_id", "student_id",
            name="uq_exam_student_registration"
        ),
        Index("ix_exam_reg_student", "tenant_id", "student_id"),
        Index("ix_exam_reg_status", "tenant_id", "status"),
        {"extend_existing": True},
    )
    
    exam_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("exams.id", ondelete="CASCADE"),
    )
    student_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    
    # Registration details
    registration_number: Mapped[str] = mapped_column(String(50))
    status: Mapped[RegistrationStatus] = mapped_column(
        SQLEnum(RegistrationStatus, name="registration_status_enum"),
        default=RegistrationStatus.PENDING
    )
    
    # Registered subjects (JSON array of subject IDs)
    registered_subject_ids: Mapped[Optional[List[str]]] = mapped_column(
        JSON, nullable=True
    )
    
    # Fee
    total_fee: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.00")
    )
    fee_paid: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.00")
    )
    fee_payment_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )
    
    # Eligibility
    is_eligible: Mapped[bool] = mapped_column(Boolean, default=True)
    eligibility_remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    attendance_percentage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Timestamps
    registered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Relationships
    exam: Mapped["Exam"] = relationship("Exam", back_populates="registrations")
    hall_ticket: Mapped[Optional["HallTicket"]] = relationship(
        "HallTicket",
        back_populates="registration",
        uselist=False,
    )


# ============================================
# Hall Ticket
# ============================================

class HallTicket(TenantBaseModel):
    """
    Exam hall ticket / admit card.
    
    Generated after successful registration and fee payment.
    """
    __tablename__ = "hall_tickets"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "hall_ticket_number",
            name="uq_hall_ticket_number"
        ),
        Index("ix_hall_ticket_student", "tenant_id", "student_id"),
        {"extend_existing": True},
    )
    
    registration_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("exam_registrations.id", ondelete="CASCADE"),
    )
    student_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    exam_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("exams.id", ondelete="CASCADE"),
    )
    
    # Hall ticket details
    hall_ticket_number: Mapped[str] = mapped_column(String(50))
    status: Mapped[HallTicketStatus] = mapped_column(
        SQLEnum(HallTicketStatus, name="hall_ticket_status_enum"),
        default=HallTicketStatus.NOT_GENERATED
    )
    
    # Seating arrangement
    seat_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    room_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    block: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Student photo for hall ticket
    photo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Generation info
    generated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    generated_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    download_count: Mapped[int] = mapped_column(Integer, default=0)
    last_downloaded_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # PDF storage
    pdf_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Relationships
    registration: Mapped["ExamRegistration"] = relationship(
        "ExamRegistration", back_populates="hall_ticket"
    )


# ============================================
# Answer Booklet
# ============================================

class AnswerBooklet(TenantBaseModel):
    """
    Answer booklet tracking.
    
    Tracks answer booklets generated and assigned for exams.
    """
    __tablename__ = "answer_booklets"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "booklet_number",
            name="uq_answer_booklet_number"
        ),
        Index("ix_booklet_exam", "exam_id"),
        {"extend_existing": True},
    )
    
    exam_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("exams.id", ondelete="CASCADE"),
    )
    student_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    subject_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Booklet details
    booklet_number: Mapped[str] = mapped_column(String(50))
    barcode: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    qr_code: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Assignment
    assigned_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Page count
    main_pages: Mapped[int] = mapped_column(Integer, default=16)
    supplement_pages: Mapped[int] = mapped_column(Integer, default=0)
    
    # Evaluation tracking
    is_evaluated: Mapped[bool] = mapped_column(Boolean, default=False)
    evaluated_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )
    evaluated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


# ============================================
# Revaluation Application
# ============================================

class RevaluationApplication(TenantBaseModel):
    """
    Application for revaluation or retotaling.
    
    Students can apply for RV (revaluation) or RT (retotaling) of answer sheets.
    """
    __tablename__ = "revaluation_applications"
    __table_args__ = (
        Index("ix_revaluation_student", "tenant_id", "student_id"),
        Index("ix_revaluation_status", "tenant_id", "status"),
        {"extend_existing": True},
    )
    
    student_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    exam_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("exams.id", ondelete="CASCADE"),
    )
    subject_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="CASCADE"),
    )
    
    # Application details
    application_number: Mapped[str] = mapped_column(String(50))
    revaluation_type: Mapped[RevaluationType] = mapped_column(
        SQLEnum(RevaluationType, name="revaluation_type_enum"),
        default=RevaluationType.REVALUATION
    )
    status: Mapped[RevaluationStatus] = mapped_column(
        SQLEnum(RevaluationStatus, name="revaluation_status_enum"),
        default=RevaluationStatus.PENDING
    )
    
    # Marks
    original_marks: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    revised_marks: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Fee
    fee_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.00")
    )
    fee_paid: Mapped[bool] = mapped_column(Boolean, default=False)
    payment_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )
    
    # Reason
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Review
    reviewed_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    review_remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
    applied_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


# ============================================
# Makeup / Backlog Registration
# ============================================

class MakeupBacklogRegistration(TenantBaseModel):
    """
    Registration for makeup or backlog exams.
    
    Students who failed or missed exams can register for re-attempts.
    """
    __tablename__ = "makeup_backlog_registrations"
    __table_args__ = (
        Index("ix_makeup_student", "tenant_id", "student_id"),
        Index("ix_makeup_exam", "makeup_exam_id"),
        {"extend_existing": True},
    )
    
    student_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    
    # Original exam where student failed/missed
    original_exam_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("exams.id", ondelete="CASCADE"),
    )
    subject_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="CASCADE"),
    )
    
    # Makeup/Backlog exam
    makeup_exam_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("exams.id", ondelete="CASCADE"),
    )
    
    # Registration details
    registration_number: Mapped[str] = mapped_column(String(50))
    status: Mapped[RegistrationStatus] = mapped_column(
        SQLEnum(RegistrationStatus, name="registration_status_enum"),
        default=RegistrationStatus.PENDING
    )
    
    # Original result
    original_marks: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    original_grade: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    
    # Reason
    is_backlog: Mapped[bool] = mapped_column(Boolean, default=True)  # True=backlog, False=makeup
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Fee
    fee_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.00")
    )
    fee_paid: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Approval
    approved_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


# ============================================
# Exam Result
# ============================================

class ExamResult(TenantBaseModel):
    """
    Student exam result.
    
    Stores marks and grades for each subject in an exam.
    """
    __tablename__ = "exam_results"
    __table_args__ = (
        UniqueConstraint(
            "exam_id", "student_id", "subject_id",
            name="uq_exam_result_student_subject"
        ),
        Index("ix_result_student", "tenant_id", "student_id"),
        Index("ix_result_exam", "exam_id"),
        {"extend_existing": True},
    )
    
    exam_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("exams.id", ondelete="CASCADE"),
    )
    student_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    subject_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="CASCADE"),
    )
    
    # Marks breakdown
    internal_marks: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    external_marks: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    practical_marks: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_marks: Mapped[float] = mapped_column(Float, default=0.0)
    max_marks: Mapped[float] = mapped_column(Float, default=100.0)
    
    # Grade
    grade: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    grade_points: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Result
    is_pass: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[ResultStatus] = mapped_column(
        SQLEnum(ResultStatus, name="result_status_enum"),
        default=ResultStatus.NOT_PUBLISHED
    )
    
    # Attendance
    attendance_percentage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Grace marks (if applied)
    grace_marks: Mapped[float] = mapped_column(Float, default=0.0)
    grace_reason: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # Publishing
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    published_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Withheld reason
    withheld_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


# ============================================
# Semester Result Summary
# ============================================

class SemesterResult(TenantBaseModel):
    """
    Semester-wise result summary.
    
    Aggregated SGPA/CGPA for a student per semester.
    """
    __tablename__ = "semester_results"
    __table_args__ = (
        UniqueConstraint(
            "student_id", "academic_year_id", "semester",
            name="uq_semester_result"
        ),
        Index("ix_semester_result_student", "tenant_id", "student_id"),
        {"extend_existing": True},
    )
    
    student_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    academic_year_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("academic_years.id", ondelete="CASCADE"),
    )
    semester: Mapped[int] = mapped_column(Integer)
    
    # Credits
    total_credits: Mapped[float] = mapped_column(Float, default=0.0)
    earned_credits: Mapped[float] = mapped_column(Float, default=0.0)
    
    # GPA
    sgpa: Mapped[float] = mapped_column(Float, default=0.0)  # Semester GPA
    cgpa: Mapped[float] = mapped_column(Float, default=0.0)  # Cumulative GPA
    
    # Percentage
    percentage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Subjects
    total_subjects: Mapped[int] = mapped_column(Integer, default=0)
    passed_subjects: Mapped[int] = mapped_column(Integer, default=0)
    failed_subjects: Mapped[int] = mapped_column(Integer, default=0)
    
    # Backlogs
    active_backlogs: Mapped[int] = mapped_column(Integer, default=0)
    cleared_backlogs: Mapped[int] = mapped_column(Integer, default=0)
    
    # Status
    is_promoted: Mapped[bool] = mapped_column(Boolean, default=False)
    promotion_remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Publishing
    status: Mapped[ResultStatus] = mapped_column(
        SQLEnum(ResultStatus, name="result_status_enum"),
        default=ResultStatus.NOT_PUBLISHED
    )
