"""
CUSTOS Fee Extension Schemas

Schemas for challans, fines, and late payments.
"""

from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


# ============================================
# Enums
# ============================================

class ChallanStatus(str, Enum):
    GENERATED = "generated"
    DOWNLOADED = "downloaded"
    USED = "used"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class FineType(str, Enum):
    LATE_FEE = "late_fee"
    LIBRARY = "library"
    ID_CARD = "id_card"
    LAB_DAMAGE = "lab_damage"
    HOSTEL = "hostel"
    EXAMINATION = "examination"
    DISCIPLINARY = "disciplinary"
    OTHER = "other"


class FineStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    WAIVED = "waived"
    PARTIAL = "partial"


# ============================================
# Fee Component Schema
# ============================================

class FeeComponentBreakdown(BaseModel):
    """Schema for fee component in challan."""
    name: str
    code: str
    amount: Decimal


# ============================================
# Challan Schemas
# ============================================

class ChallanGenerateRequest(BaseModel):
    """Schema for generating a challan."""
    student_id: UUID
    invoice_id: Optional[UUID] = None
    fee_components: Optional[List[FeeComponentBreakdown]] = None
    valid_days: int = Field(15, ge=1, le=90)
    include_fines: bool = True


class ChallanResponse(BaseModel):
    """Schema for challan response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    challan_number: str
    barcode: Optional[str] = None
    student_id: UUID
    student_name: str
    enrollment_number: str
    class_name: Optional[str] = None
    invoice_id: Optional[UUID] = None
    fee_components: Optional[List[dict]] = None
    subtotal: Decimal
    fine_amount: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    issue_date: date
    valid_from: date
    valid_until: date
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    bank_ifsc: Optional[str] = None
    status: ChallanStatus
    download_count: int
    pdf_url: Optional[str] = None
    created_at: datetime


class ChallanListResponse(BaseModel):
    """Schema for paginated challan list."""
    items: List[ChallanResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ============================================
# Late Fee Rule Schemas
# ============================================

class LateFeeRuleCreate(BaseModel):
    """Schema for creating late fee rule."""
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    fee_component_id: Optional[UUID] = None
    class_id: Optional[UUID] = None
    is_percentage: bool = True
    rate: Decimal = Field(..., ge=0)
    rate_period: str = "day"
    max_amount: Optional[Decimal] = None
    max_percentage: Optional[float] = None
    grace_days: int = Field(0, ge=0)
    cap_at_original: bool = False
    effective_from: date
    effective_until: Optional[date] = None


class LateFeeRuleResponse(BaseModel):
    """Schema for late fee rule response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str
    description: Optional[str] = None
    fee_component_id: Optional[UUID] = None
    class_id: Optional[UUID] = None
    is_percentage: bool
    rate: Decimal
    rate_period: str
    max_amount: Optional[Decimal] = None
    max_percentage: Optional[float] = None
    grace_days: int
    cap_at_original: bool
    is_active: bool
    effective_from: date
    effective_until: Optional[date] = None


class LateFeeCalculation(BaseModel):
    """Schema for calculated late fee."""
    original_amount: Decimal
    due_date: date
    calculation_date: date
    days_overdue: int
    applicable_rate: Decimal
    calculated_fee: Decimal
    capped_fee: Decimal
    final_fee: Decimal


# ============================================
# Fine Schemas
# ============================================

class FineCreate(BaseModel):
    """Schema for creating a fine."""
    student_id: UUID
    fine_type: FineType
    description: str
    amount: Decimal = Field(..., gt=0)
    due_date: Optional[date] = None
    reference_type: Optional[str] = None
    reference_id: Optional[UUID] = None


class FineUpdate(BaseModel):
    """Schema for updating a fine."""
    description: Optional[str] = None
    amount: Optional[Decimal] = Field(None, gt=0)
    due_date: Optional[date] = None


class FineResponse(BaseModel):
    """Schema for fine response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    student_id: UUID
    fine_type: FineType
    description: str
    amount: Decimal
    paid_amount: Decimal
    waived_amount: Decimal
    balance: Decimal
    status: FineStatus
    imposed_on: date
    due_date: Optional[date] = None
    reference_type: Optional[str] = None
    reference_id: Optional[UUID] = None
    imposed_by: UUID
    waived_by: Optional[UUID] = None
    waiver_reason: Optional[str] = None
    created_at: datetime


class FineListResponse(BaseModel):
    """Schema for paginated fine list."""
    items: List[FineResponse]
    total: int
    total_pending: Decimal
    page: int
    page_size: int
    pages: int


class FineWaiverRequest(BaseModel):
    """Schema for waiving a fine."""
    amount: Decimal = Field(..., gt=0)
    reason: str


class FinePaymentRequest(BaseModel):
    """Schema for paying a fine."""
    fine_id: UUID
    amount: Decimal = Field(..., gt=0)
    payment_method: str
    transaction_id: Optional[str] = None
    remarks: Optional[str] = None


class FinePaymentResponse(BaseModel):
    """Schema for fine payment response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    fine_id: UUID
    amount: Decimal
    payment_method: str
    transaction_id: Optional[str] = None
    payment_date: datetime
    remarks: Optional[str] = None
    collected_by: UUID


# ============================================
# Summary Schemas
# ============================================

class StudentFinesSummary(BaseModel):
    """Schema for student's fines summary."""
    student_id: UUID
    total_fines: Decimal
    total_paid: Decimal
    total_waived: Decimal
    total_pending: Decimal
    fine_count: int
    pending_count: int


class DueFeesSummary(BaseModel):
    """Schema for due fees summary."""
    student_id: UUID
    student_name: str
    enrollment_number: str
    class_name: str
    
    total_fee: Decimal
    total_paid: Decimal
    total_pending: Decimal
    late_fee: Decimal
    fines: Decimal
    grand_total: Decimal
    
    due_date: Optional[date] = None
    days_overdue: int = 0
