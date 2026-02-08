"""
CUSTOS Helpdesk Schemas

Pydantic schemas for tickets, applications, and student services.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


# ============================================
# Enums (mirrored from models)
# ============================================

class HelpdeskCategory(str, Enum):
    HOSTEL = "hostel"
    TRANSPORT = "transport"
    FEE = "fee"
    IT = "it"
    INFRASTRUCTURE = "infrastructure"
    ADMISSION = "admission"
    EXAMINATION = "examination"
    REGISTRAR = "registrar"
    DSA = "dsa"
    ERP = "erp"
    LIBRARY = "library"
    PLACEMENT = "placement"
    SCHOLARSHIP = "scholarship"
    OTHER = "other"


class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    PENDING_INFO = "pending_info"
    RESOLVED = "resolved"
    CLOSED = "closed"
    ESCALATED = "escalated"
    REOPENED = "reopened"


class TicketPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class ApplicationStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ApplicationType(str, Enum):
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
    OFFICIAL = "official"
    UNOFFICIAL = "unofficial"
    CONSOLIDATED = "consolidated"
    SEMESTER_WISE = "semester_wise"


class GraceMarkCategory(str, Enum):
    SPORTS = "sports"
    NCC = "ncc"
    NSS = "nss"
    CULTURAL = "cultural"
    TECHNICAL = "technical"
    SOCIAL_SERVICE = "social_service"
    LEADERSHIP = "leadership"
    OTHER = "other"


# ============================================
# Attachment Schema
# ============================================

class AttachmentSchema(BaseModel):
    """Schema for file attachments."""
    file_name: str
    file_url: str
    file_size: Optional[int] = None
    file_type: Optional[str] = None
    uploaded_at: Optional[datetime] = None


# ============================================
# Ticket Schemas
# ============================================

class TicketCommentCreate(BaseModel):
    """Schema for creating a ticket comment."""
    content: str = Field(..., min_length=1)
    is_internal: bool = False
    attachments: Optional[List[AttachmentSchema]] = None


class TicketCommentResponse(BaseModel):
    """Schema for ticket comment response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    ticket_id: UUID
    content: str
    author_id: UUID
    is_internal: bool
    is_system: bool
    attachments: Optional[List[dict]] = None
    created_at: datetime


class TicketCreate(BaseModel):
    """Schema for creating a helpdesk ticket."""
    category: HelpdeskCategory
    priority: TicketPriority = TicketPriority.MEDIUM
    subject: str = Field(..., min_length=5, max_length=300)
    description: str = Field(..., min_length=10)
    attachments: Optional[List[AttachmentSchema]] = None


class TicketUpdate(BaseModel):
    """Schema for updating a ticket."""
    category: Optional[HelpdeskCategory] = None
    priority: Optional[TicketPriority] = None
    status: Optional[TicketStatus] = None
    subject: Optional[str] = Field(None, min_length=5, max_length=300)
    description: Optional[str] = None


class TicketAssign(BaseModel):
    """Schema for assigning a ticket."""
    assigned_to: UUID


class TicketResolve(BaseModel):
    """Schema for resolving a ticket."""
    resolution_notes: str = Field(..., min_length=10)


class TicketSatisfaction(BaseModel):
    """Schema for ticket satisfaction feedback."""
    rating: int = Field(..., ge=1, le=5)
    feedback: Optional[str] = None


class TicketResponse(BaseModel):
    """Schema for ticket response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    ticket_number: str
    category: HelpdeskCategory
    priority: TicketPriority
    status: TicketStatus
    subject: str
    description: str
    created_by: UUID
    assigned_to: Optional[UUID] = None
    assigned_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    sla_due_date: Optional[datetime] = None
    sla_breached: bool
    escalation_level: int
    attachments: Optional[List[dict]] = None
    satisfaction_rating: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    comments: Optional[List[TicketCommentResponse]] = None


class TicketListResponse(BaseModel):
    """Schema for paginated ticket list."""
    items: List[TicketResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ============================================
# Application Schemas
# ============================================

class ApplicationCreate(BaseModel):
    """Base schema for creating an application."""
    application_type: ApplicationType
    purpose: Optional[str] = None
    remarks: Optional[str] = None
    supporting_documents: Optional[List[AttachmentSchema]] = None


class ApplicationResponse(BaseModel):
    """Schema for application response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    application_number: str
    application_type: ApplicationType
    status: ApplicationStatus
    student_id: UUID
    purpose: Optional[str] = None
    remarks: Optional[str] = None
    fee_amount: Decimal
    fee_paid: bool
    supporting_documents: Optional[List[dict]] = None
    reviewed_by: Optional[UUID] = None
    reviewed_at: Optional[datetime] = None
    review_remarks: Optional[str] = None
    processed_at: Optional[datetime] = None
    delivery_mode: Optional[str] = None
    delivered_at: Optional[datetime] = None
    created_at: datetime


class ApplicationReview(BaseModel):
    """Schema for reviewing an application."""
    status: ApplicationStatus
    review_remarks: Optional[str] = None


# ============================================
# Transcript Schemas
# ============================================

class TranscriptApplicationCreate(BaseModel):
    """Schema for applying for transcript."""
    transcript_type: TranscriptType = TranscriptType.OFFICIAL
    num_copies: int = Field(1, ge=1, le=10)
    from_semester: Optional[int] = Field(None, ge=1, le=10)
    to_semester: Optional[int] = Field(None, ge=1, le=10)
    purpose: Optional[str] = None
    delivery_mode: str = Field("pickup", pattern="^(pickup|post|email)$")
    delivery_address: Optional[str] = None


class TranscriptApplicationResponse(BaseModel):
    """Schema for transcript application response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    application_id: UUID
    student_id: UUID
    transcript_type: TranscriptType
    num_copies: int
    from_semester: Optional[int] = None
    to_semester: Optional[int] = None
    delivery_address: Optional[str] = None
    document_url: Optional[str] = None
    document_generated_at: Optional[datetime] = None
    created_at: datetime
    # Include base application fields
    status: Optional[ApplicationStatus] = None
    fee_amount: Optional[Decimal] = None
    fee_paid: Optional[bool] = None


# ============================================
# Grace Mark Schemas
# ============================================

class GraceMarkApplicationCreate(BaseModel):
    """Schema for applying for grace marks."""
    exam_id: UUID
    subject_id: Optional[UUID] = None
    category: GraceMarkCategory
    activity_name: str = Field(..., min_length=5, max_length=300)
    activity_date: Optional[datetime] = None
    activity_level: Optional[str] = Field(None, pattern="^(college|university|state|national|international)$")
    achievement: Optional[str] = Field(None, max_length=200)
    requested_marks: int = Field(..., ge=1, le=10)
    supporting_documents: Optional[List[AttachmentSchema]] = None


class GraceMarkApplicationResponse(BaseModel):
    """Schema for grace mark application response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    application_id: UUID
    student_id: UUID
    exam_id: UUID
    subject_id: Optional[UUID] = None
    category: GraceMarkCategory
    activity_name: str
    activity_date: Optional[datetime] = None
    activity_level: Optional[str] = None
    achievement: Optional[str] = None
    requested_marks: int
    approved_marks: Optional[int] = None
    max_applicable_marks: int
    verification_remarks: Optional[str] = None
    created_at: datetime
    # Include base application fields
    status: Optional[ApplicationStatus] = None


class GraceMarkReview(BaseModel):
    """Schema for reviewing grace mark application."""
    approved_marks: int = Field(..., ge=0, le=10)
    verification_remarks: Optional[str] = None
    status: ApplicationStatus


# ============================================
# Grace Mark Redistribution Schemas
# ============================================

class DistributionItem(BaseModel):
    """Schema for redistribution item."""
    subject_id: UUID
    marks: int = Field(..., ge=1, le=5)


class GraceRedistributionCreate(BaseModel):
    """Schema for grace mark redistribution."""
    original_application_id: UUID
    distribution: List[DistributionItem]
    reason: Optional[str] = None


class GraceRedistributionResponse(BaseModel):
    """Schema for redistribution response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    application_id: UUID
    student_id: UUID
    original_application_id: UUID
    distribution: List[dict]
    total_marks: int
    reason: Optional[str] = None
    created_at: datetime


# ============================================
# FAQ Schemas
# ============================================

class FAQCreate(BaseModel):
    """Schema for creating FAQ."""
    category: HelpdeskCategory
    question: str = Field(..., min_length=10)
    answer: str = Field(..., min_length=10)
    display_order: int = 0


class FAQUpdate(BaseModel):
    """Schema for updating FAQ."""
    category: Optional[HelpdeskCategory] = None
    question: Optional[str] = None
    answer: Optional[str] = None
    display_order: Optional[int] = None
    is_published: Optional[bool] = None


class FAQResponse(BaseModel):
    """Schema for FAQ response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    category: HelpdeskCategory
    question: str
    answer: str
    display_order: int
    view_count: int
    helpful_count: int
    not_helpful_count: int
    is_published: bool


class FAQFeedback(BaseModel):
    """Schema for FAQ feedback."""
    helpful: bool


# ============================================
# Statistics Schemas
# ============================================

class TicketStatistics(BaseModel):
    """Schema for ticket statistics."""
    total: int
    open: int
    in_progress: int
    resolved: int
    closed: int
    average_resolution_time_hours: Optional[float] = None
    sla_breach_rate: float


class CategoryStatistics(BaseModel):
    """Schema for category-wise statistics."""
    category: HelpdeskCategory
    count: int
    percentage: float
