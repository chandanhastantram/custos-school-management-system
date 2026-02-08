"""
CUSTOS Helpdesk Models

Support tickets, applications, and student services.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List
from uuid import UUID

from sqlalchemy import (
    String, Text, Integer, Boolean, DateTime,
    ForeignKey, UniqueConstraint, Index, JSON, Numeric
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import TenantBaseModel


# ============================================
# Enums
# ============================================

class HelpdeskCategory(str, Enum):
    """Helpdesk ticket categories."""
    HOSTEL = "hostel"
    TRANSPORT = "transport"
    FEE = "fee"
    IT = "it"
    INFRASTRUCTURE = "infrastructure"
    ADMISSION = "admission"
    EXAMINATION = "examination"
    REGISTRAR = "registrar"
    DSA = "dsa"                    # Dean of Student Affairs
    ERP = "erp"
    LIBRARY = "library"
    PLACEMENT = "placement"
    SCHOLARSHIP = "scholarship"
    OTHER = "other"


class TicketStatus(str, Enum):
    """Support ticket status."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    PENDING_INFO = "pending_info"
    RESOLVED = "resolved"
    CLOSED = "closed"
    ESCALATED = "escalated"
    REOPENED = "reopened"


class TicketPriority(str, Enum):
    """Ticket priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class ApplicationStatus(str, Enum):
    """Application status."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ApplicationType(str, Enum):
    """Types of applications."""
    TRANSCRIPT = "transcript"
    GRACE_MARK = "grace_mark"
    GRACE_REDISTRIBUTION = "grace_redistribution"
    BONAFIDE = "bonafide"
    CHARACTER_CERTIFICATE = "character_certificate"
    MIGRATION = "migration"
    NAME_CHANGE = "name_change"
    DUPLICATE_DOCUMENTS = "duplicate_documents"
    LEAVE = "leave"
    OTHER = "other"


class TranscriptType(str, Enum):
    """Types of transcripts."""
    OFFICIAL = "official"
    UNOFFICIAL = "unofficial"
    CONSOLIDATED = "consolidated"
    SEMESTER_WISE = "semester_wise"


class GraceMarkCategory(str, Enum):
    """Grace mark categories."""
    SPORTS = "sports"
    NCC = "ncc"
    NSS = "nss"
    CULTURAL = "cultural"
    TECHNICAL = "technical"
    SOCIAL_SERVICE = "social_service"
    LEADERSHIP = "leadership"
    OTHER = "other"


# ============================================
# Helpdesk Ticket
# ============================================

class HelpdeskTicket(TenantBaseModel):
    """
    Support ticket for student/staff queries.
    
    Supports multiple categories, priorities, and escalation.
    """
    __tablename__ = "helpdesk_tickets"
    __table_args__ = (
        Index("ix_ticket_tenant_status", "tenant_id", "status"),
        Index("ix_ticket_category", "tenant_id", "category"),
        Index("ix_ticket_created_by", "tenant_id", "created_by"),
        {"extend_existing": True},
    )
    
    # Ticket identification
    ticket_number: Mapped[str] = mapped_column(String(50), unique=True)
    
    # Category and priority
    category: Mapped[HelpdeskCategory] = mapped_column(
        SQLEnum(HelpdeskCategory, name="helpdesk_category_enum"),
        default=HelpdeskCategory.OTHER
    )
    priority: Mapped[TicketPriority] = mapped_column(
        SQLEnum(TicketPriority, name="ticket_priority_enum"),
        default=TicketPriority.MEDIUM
    )
    status: Mapped[TicketStatus] = mapped_column(
        SQLEnum(TicketStatus, name="ticket_status_enum"),
        default=TicketStatus.OPEN
    )
    
    # Ticket content
    subject: Mapped[str] = mapped_column(String(300))
    description: Mapped[str] = mapped_column(Text)
    
    # Submitter
    created_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    
    # Assignment
    assigned_to: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    assigned_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Resolution
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolved_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # SLA tracking
    sla_due_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    sla_breached: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Escalation
    escalation_level: Mapped[int] = mapped_column(Integer, default=0)
    escalated_to: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Attachments (JSON array of file URLs)
    attachments: Mapped[Optional[List[dict]]] = mapped_column(JSON, nullable=True)
    
    # Satisfaction
    satisfaction_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-5
    satisfaction_feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    comments: Mapped[List["TicketComment"]] = relationship(
        "TicketComment",
        back_populates="ticket",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


# ============================================
# Ticket Comment
# ============================================

class TicketComment(TenantBaseModel):
    """
    Comment on a helpdesk ticket.
    
    Used for updates, responses, and communication.
    """
    __tablename__ = "ticket_comments"
    __table_args__ = (
        Index("ix_comment_ticket", "ticket_id"),
        {"extend_existing": True},
    )
    
    ticket_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("helpdesk_tickets.id", ondelete="CASCADE"),
    )
    
    # Comment content
    content: Mapped[str] = mapped_column(Text)
    
    # Author
    author_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    
    # Type
    is_internal: Mapped[bool] = mapped_column(Boolean, default=False)  # Internal notes
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)    # System-generated
    
    # Attachments
    attachments: Mapped[Optional[List[dict]]] = mapped_column(JSON, nullable=True)
    
    # Relationship
    ticket: Mapped["HelpdeskTicket"] = relationship(
        "HelpdeskTicket", back_populates="comments"
    )


# ============================================
# Student Application (Base)
# ============================================

class StudentApplication(TenantBaseModel):
    """
    Base model for student applications.
    
    Handles transcript, grace mark, bonafide, etc. applications.
    """
    __tablename__ = "student_applications"
    __table_args__ = (
        Index("ix_application_student", "tenant_id", "student_id"),
        Index("ix_application_type", "tenant_id", "application_type"),
        Index("ix_application_status", "tenant_id", "status"),
        {"extend_existing": True},
    )
    
    # Identification
    application_number: Mapped[str] = mapped_column(String(50), unique=True)
    
    # Type and status
    application_type: Mapped[ApplicationType] = mapped_column(
        SQLEnum(ApplicationType, name="application_type_enum"),
    )
    status: Mapped[ApplicationStatus] = mapped_column(
        SQLEnum(ApplicationStatus, name="application_status_enum"),
        default=ApplicationStatus.DRAFT
    )
    
    # Applicant
    student_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    
    # Application details
    purpose: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Fee
    fee_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.00")
    )
    fee_paid: Mapped[bool] = mapped_column(Boolean, default=False)
    payment_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )
    
    # Documents (JSON array)
    supporting_documents: Mapped[Optional[List[dict]]] = mapped_column(JSON, nullable=True)
    
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
    
    # Processing
    processed_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Delivery
    delivery_mode: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # pickup, post, email
    delivered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Extra data (for type-specific fields)
    extra_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)


# ============================================
# Transcript Application
# ============================================

class TranscriptApplication(TenantBaseModel):
    """
    Application for academic transcript.
    
    Extends StudentApplication with transcript-specific fields.
    """
    __tablename__ = "transcript_applications"
    __table_args__ = (
        Index("ix_transcript_student", "tenant_id", "student_id"),
        {"extend_existing": True},
    )
    
    # Link to base application
    application_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("student_applications.id", ondelete="CASCADE"),
    )
    
    student_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    
    # Transcript details
    transcript_type: Mapped[TranscriptType] = mapped_column(
        SQLEnum(TranscriptType, name="transcript_type_enum"),
        default=TranscriptType.OFFICIAL
    )
    
    # Copies
    num_copies: Mapped[int] = mapped_column(Integer, default=1)
    
    # Semesters (for semester-wise)
    from_semester: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    to_semester: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Delivery address (if postal)
    delivery_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Generated document
    document_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    document_generated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


# ============================================
# Grace Mark Application
# ============================================

class GraceMarkApplication(TenantBaseModel):
    """
    Application for grace marks.
    
    Students can apply for grace marks based on extracurricular activities.
    """
    __tablename__ = "grace_mark_applications"
    __table_args__ = (
        Index("ix_grace_student", "tenant_id", "student_id"),
        Index("ix_grace_exam", "tenant_id", "exam_id"),
        {"extend_existing": True},
    )
    
    # Link to base application
    application_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("student_applications.id", ondelete="CASCADE"),
    )
    
    student_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    
    # Exam context
    exam_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("exams.id", ondelete="CASCADE"),
    )
    subject_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Grace mark details
    category: Mapped[GraceMarkCategory] = mapped_column(
        SQLEnum(GraceMarkCategory, name="grace_mark_category_enum"),
    )
    
    # Activity details
    activity_name: Mapped[str] = mapped_column(String(300))
    activity_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    activity_level: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # college, university, state, national, international
    achievement: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)   # participation, winner, runner-up, etc.
    
    # Marks
    requested_marks: Mapped[int] = mapped_column(Integer, default=0)
    approved_marks: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_applicable_marks: Mapped[int] = mapped_column(Integer, default=5)
    
    # Verification
    verified_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    verification_remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


# ============================================
# Grace Mark Redistribution
# ============================================

class GraceMarkRedistribution(TenantBaseModel):
    """
    Application for grace mark redistribution.
    
    Allows students to redistribute approved grace marks across subjects.
    """
    __tablename__ = "grace_mark_redistributions"
    __table_args__ = (
        Index("ix_redistribution_student", "tenant_id", "student_id"),
        {"extend_existing": True},
    )
    
    # Link to base application
    application_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("student_applications.id", ondelete="CASCADE"),
    )
    
    student_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    
    # Original grace mark application
    original_application_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("grace_mark_applications.id", ondelete="CASCADE"),
    )
    
    # Redistribution details (JSON: [{subject_id, marks}, ...])
    distribution: Mapped[List[dict]] = mapped_column(JSON)
    
    # Total marks being redistributed
    total_marks: Mapped[int] = mapped_column(Integer)
    
    # Reason
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


# ============================================
# FAQ (Knowledge Base)
# ============================================

class HelpdeskFAQ(TenantBaseModel):
    """
    Frequently Asked Questions for helpdesk.
    
    Self-service knowledge base to reduce ticket volume.
    """
    __tablename__ = "helpdesk_faqs"
    __table_args__ = (
        Index("ix_faq_category", "tenant_id", "category"),
        {"extend_existing": True},
    )
    
    category: Mapped[HelpdeskCategory] = mapped_column(
        SQLEnum(HelpdeskCategory, name="helpdesk_category_enum"),
    )
    
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    
    # Ordering
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    
    # Analytics
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    helpful_count: Mapped[int] = mapped_column(Integer, default=0)
    not_helpful_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Status
    is_published: Mapped[bool] = mapped_column(Boolean, default=True)
