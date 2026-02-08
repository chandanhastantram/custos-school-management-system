"""
CUSTOS Examinations Schemas

Pydantic schemas for exam registration, hall tickets, and results.
"""

from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


# ============================================
# Enums (mirrored from models)
# ============================================

class ExamType(str, Enum):
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
    DRAFT = "draft"
    REGISTRATION_OPEN = "registration_open"
    REGISTRATION_CLOSED = "registration_closed"
    ONGOING = "ongoing"
    COMPLETED = "completed"
    RESULTS_PUBLISHED = "results_published"
    CANCELLED = "cancelled"


class RegistrationStatus(str, Enum):
    PENDING = "pending"
    REGISTERED = "registered"
    FEE_PENDING = "fee_pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    DEBARRED = "debarred"


class HallTicketStatus(str, Enum):
    NOT_GENERATED = "not_generated"
    GENERATED = "generated"
    DOWNLOADED = "downloaded"
    PRINTED = "printed"


class RevaluationType(str, Enum):
    REVALUATION = "revaluation"
    RETOTALING = "retotaling"
    PHOTOCOPY = "photocopy"


class RevaluationStatus(str, Enum):
    PENDING = "pending"
    FEE_PENDING = "fee_pending"
    UNDER_REVIEW = "under_review"
    COMPLETED = "completed"
    NO_CHANGE = "no_change"
    MARKS_UPDATED = "marks_updated"
    REJECTED = "rejected"


class ResultStatus(str, Enum):
    NOT_PUBLISHED = "not_published"
    PUBLISHED = "published"
    WITHHELD = "withheld"
    UNDER_REVIEW = "under_review"


# ============================================
# Exam Schemas
# ============================================

class ExamSubjectBase(BaseModel):
    """Base schema for exam subject."""
    subject_id: UUID
    exam_date: Optional[date] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_minutes: int = 180
    venue: Optional[str] = None
    room_number: Optional[str] = None
    max_marks: int = 100
    passing_marks: int = 40


class ExamSubjectCreate(ExamSubjectBase):
    """Schema for creating exam subject schedule."""
    pass


class ExamSubjectResponse(ExamSubjectBase):
    """Schema for exam subject response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    exam_id: UUID
    created_at: datetime


class ExamBase(BaseModel):
    """Base schema for exam."""
    name: str = Field(..., min_length=2, max_length=200)
    code: str = Field(..., min_length=2, max_length=50)
    description: Optional[str] = None
    exam_type: ExamType = ExamType.REGULAR
    semester: Optional[int] = None
    
    registration_start: Optional[datetime] = None
    registration_end: Optional[datetime] = None
    late_registration_end: Optional[datetime] = None
    late_fee: Decimal = Decimal("0.00")
    
    exam_start_date: Optional[date] = None
    exam_end_date: Optional[date] = None
    
    min_attendance_percentage: float = 75.0
    require_fee_clearance: bool = True
    exam_fee_per_subject: Decimal = Decimal("0.00")


class ExamCreate(ExamBase):
    """Schema for creating an exam."""
    academic_year_id: UUID
    subjects: Optional[List[ExamSubjectCreate]] = None


class ExamUpdate(BaseModel):
    """Schema for updating an exam."""
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    code: Optional[str] = Field(None, min_length=2, max_length=50)
    description: Optional[str] = None
    status: Optional[ExamStatus] = None
    
    registration_start: Optional[datetime] = None
    registration_end: Optional[datetime] = None
    late_registration_end: Optional[datetime] = None
    late_fee: Optional[Decimal] = None
    
    exam_start_date: Optional[date] = None
    exam_end_date: Optional[date] = None
    
    min_attendance_percentage: Optional[float] = None
    require_fee_clearance: Optional[bool] = None
    exam_fee_per_subject: Optional[Decimal] = None


class ExamResponse(ExamBase):
    """Schema for exam response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    academic_year_id: UUID
    status: ExamStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    subjects: Optional[List[ExamSubjectResponse]] = None


class ExamListResponse(BaseModel):
    """Schema for paginated exam list."""
    items: List[ExamResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ============================================
# Registration Schemas
# ============================================

class ExamRegistrationCreate(BaseModel):
    """Schema for registering for an exam."""
    exam_id: UUID
    subject_ids: List[UUID] = Field(..., min_length=1)


class ExamRegistrationResponse(BaseModel):
    """Schema for registration response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    exam_id: UUID
    student_id: UUID
    registration_number: str
    status: RegistrationStatus
    registered_subject_ids: Optional[List[str]] = None
    total_fee: Decimal
    fee_paid: Decimal
    is_eligible: bool
    eligibility_remarks: Optional[str] = None
    attendance_percentage: Optional[float] = None
    registered_at: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None
    created_at: datetime


class RegistrationEligibilityCheck(BaseModel):
    """Schema for eligibility check result."""
    is_eligible: bool
    attendance_percentage: float
    fee_status_clear: bool
    remarks: List[str] = []
    subjects_eligible: List[UUID] = []
    subjects_not_eligible: List[UUID] = []


# ============================================
# Hall Ticket Schemas
# ============================================

class HallTicketGenerateRequest(BaseModel):
    """Schema for hall ticket generation request."""
    registration_ids: Optional[List[UUID]] = None  # If None, generate for all confirmed
    exam_id: UUID


class HallTicketResponse(BaseModel):
    """Schema for hall ticket response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    registration_id: UUID
    student_id: UUID
    exam_id: UUID
    hall_ticket_number: str
    status: HallTicketStatus
    seat_number: Optional[str] = None
    room_number: Optional[str] = None
    block: Optional[str] = None
    photo_url: Optional[str] = None
    pdf_url: Optional[str] = None
    generated_at: Optional[datetime] = None
    download_count: int = 0


class HallTicketDownloadResponse(BaseModel):
    """Schema for hall ticket download."""
    hall_ticket_number: str
    pdf_url: str
    student_name: str
    exam_name: str
    subjects: List[dict]


# ============================================
# Revaluation Schemas
# ============================================

class RevaluationApplyRequest(BaseModel):
    """Schema for applying for revaluation."""
    exam_id: UUID
    subject_id: UUID
    revaluation_type: RevaluationType
    reason: Optional[str] = None


class RevaluationResponse(BaseModel):
    """Schema for revaluation application response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    student_id: UUID
    exam_id: UUID
    subject_id: UUID
    application_number: str
    revaluation_type: RevaluationType
    status: RevaluationStatus
    original_marks: Optional[float] = None
    revised_marks: Optional[float] = None
    fee_amount: Decimal
    fee_paid: bool
    reason: Optional[str] = None
    review_remarks: Optional[str] = None
    applied_at: datetime
    completed_at: Optional[datetime] = None


class RevaluationUpdateRequest(BaseModel):
    """Schema for updating revaluation status (admin)."""
    status: RevaluationStatus
    revised_marks: Optional[float] = None
    review_remarks: Optional[str] = None


# ============================================
# Makeup/Backlog Schemas
# ============================================

class MakeupBacklogRegisterRequest(BaseModel):
    """Schema for makeup/backlog registration."""
    original_exam_id: UUID
    subject_id: UUID
    makeup_exam_id: UUID
    reason: Optional[str] = None


class MakeupBacklogResponse(BaseModel):
    """Schema for makeup/backlog registration response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    student_id: UUID
    original_exam_id: UUID
    subject_id: UUID
    makeup_exam_id: UUID
    registration_number: str
    status: RegistrationStatus
    original_marks: Optional[float] = None
    original_grade: Optional[str] = None
    is_backlog: bool
    reason: Optional[str] = None
    fee_amount: Decimal
    fee_paid: bool
    approved_at: Optional[datetime] = None
    created_at: datetime


# ============================================
# Result Schemas
# ============================================

class ExamResultCreate(BaseModel):
    """Schema for publishing exam result."""
    exam_id: UUID
    student_id: UUID
    subject_id: UUID
    internal_marks: Optional[float] = None
    external_marks: Optional[float] = None
    practical_marks: Optional[float] = None
    total_marks: float
    max_marks: float = 100.0
    grade: Optional[str] = None
    grade_points: Optional[float] = None
    is_pass: bool
    grace_marks: float = 0.0
    grace_reason: Optional[str] = None


class ExamResultBulkCreate(BaseModel):
    """Schema for bulk result upload."""
    exam_id: UUID
    results: List[ExamResultCreate]


class ExamResultResponse(BaseModel):
    """Schema for exam result response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    exam_id: UUID
    student_id: UUID
    subject_id: UUID
    internal_marks: Optional[float] = None
    external_marks: Optional[float] = None
    practical_marks: Optional[float] = None
    total_marks: float
    max_marks: float
    grade: Optional[str] = None
    grade_points: Optional[float] = None
    is_pass: bool
    status: ResultStatus
    grace_marks: float = 0.0
    attendance_percentage: Optional[float] = None
    published_at: Optional[datetime] = None


class ExamResultPublishRequest(BaseModel):
    """Schema for publishing results."""
    exam_id: UUID
    subject_ids: Optional[List[UUID]] = None  # If None, publish all


class StudentExamResultSummary(BaseModel):
    """Schema for student's exam result summary."""
    exam_id: UUID
    exam_name: str
    exam_type: ExamType
    semester: Optional[int] = None
    subjects: List[ExamResultResponse]
    total_marks: float
    max_marks: float
    percentage: float
    sgpa: Optional[float] = None
    passed: int
    failed: int
    status: ResultStatus


# ============================================
# Semester Result Schemas
# ============================================

class SemesterResultResponse(BaseModel):
    """Schema for semester result response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    student_id: UUID
    academic_year_id: UUID
    semester: int
    total_credits: float
    earned_credits: float
    sgpa: float
    cgpa: float
    percentage: Optional[float] = None
    total_subjects: int
    passed_subjects: int
    failed_subjects: int
    active_backlogs: int
    cleared_backlogs: int
    is_promoted: bool
    status: ResultStatus


class StudentAcademicSummary(BaseModel):
    """Schema for student's complete academic summary."""
    student_id: UUID
    student_name: str
    enrollment_number: str
    program: str
    current_semester: int
    cgpa: float
    total_credits: float
    earned_credits: float
    total_backlogs: int
    semester_results: List[SemesterResultResponse]


# ============================================
# Answer Booklet Schemas
# ============================================

class AnswerBookletGenerateRequest(BaseModel):
    """Schema for generating answer booklets."""
    exam_id: UUID
    subject_id: Optional[UUID] = None
    quantity: int = Field(..., ge=1, le=1000)
    prefix: Optional[str] = None


class AnswerBookletResponse(BaseModel):
    """Schema for answer booklet response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    exam_id: UUID
    student_id: Optional[UUID] = None
    subject_id: Optional[UUID] = None
    booklet_number: str
    barcode: Optional[str] = None
    assigned_at: Optional[datetime] = None
    main_pages: int
    supplement_pages: int
    is_evaluated: bool
    evaluated_at: Optional[datetime] = None


class AnswerBookletAssignRequest(BaseModel):
    """Schema for assigning answer booklet to student."""
    booklet_id: UUID
    student_id: UUID
    subject_id: UUID
