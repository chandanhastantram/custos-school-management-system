"""
CUSTOS Finance Schemas

Pydantic schemas for Fees & Finance API.
"""

from datetime import datetime, date
from typing import Optional, List
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


class InvoiceStatus(str, Enum):
    """Fee invoice status."""
    PENDING = "pending"
    PARTIAL = "partial"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class PaymentMethod(str, Enum):
    """Payment method."""
    CASH = "cash"
    UPI = "upi"
    CARD = "card"
    BANK_TRANSFER = "bank_transfer"
    CHEQUE = "cheque"
    DD = "dd"
    ONLINE = "online"
    OTHER = "other"


# ============================================
# Fee Component Schemas
# ============================================

class FeeComponentCreate(BaseModel):
    """Create a fee component."""
    code: str = Field(..., max_length=20)
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    is_mandatory: bool = True
    is_refundable: bool = False
    allow_partial: bool = True
    category: Optional[str] = None
    is_taxable: bool = False
    tax_percentage: float = 0.0
    display_order: int = 0


class FeeComponentUpdate(BaseModel):
    """Update a fee component."""
    name: Optional[str] = None
    description: Optional[str] = None
    is_mandatory: Optional[bool] = None
    is_refundable: Optional[bool] = None
    allow_partial: Optional[bool] = None
    category: Optional[str] = None
    is_taxable: Optional[bool] = None
    tax_percentage: Optional[float] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None


class FeeComponentResponse(BaseModel):
    """Fee component response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    code: str
    name: str
    description: Optional[str]
    is_mandatory: bool
    is_refundable: bool
    allow_partial: bool
    category: Optional[str]
    is_taxable: bool
    tax_percentage: float
    display_order: int
    is_active: bool
    created_at: datetime


# ============================================
# Fee Structure Schemas
# ============================================

class FeeStructureItemCreate(BaseModel):
    """Fee structure item for creation."""
    fee_component_id: UUID
    amount: float = Field(..., ge=0)
    discount_percentage: float = Field(default=0.0, ge=0, le=100)


class FeeStructureCreate(BaseModel):
    """Create a fee structure."""
    class_id: UUID
    academic_year_id: UUID
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    installment_count: int = Field(default=1, ge=1, le=12)
    installment_schedule: Optional[List[dict]] = None
    items: List[FeeStructureItemCreate] = []


class FeeStructureUpdate(BaseModel):
    """Update a fee structure."""
    name: Optional[str] = None
    description: Optional[str] = None
    installment_count: Optional[int] = None
    installment_schedule: Optional[List[dict]] = None
    is_published: Optional[bool] = None
    is_active: Optional[bool] = None


class FeeStructureItemResponse(BaseModel):
    """Fee structure item response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    fee_component_id: UUID
    component_name: Optional[str] = None
    component_code: Optional[str] = None
    amount: float
    discount_percentage: float
    discounted_amount: float
    display_order: int


class FeeStructureResponse(BaseModel):
    """Fee structure response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    class_id: UUID
    academic_year_id: UUID
    name: str
    description: Optional[str]
    total_amount: float
    installment_count: int
    installment_schedule: Optional[List[dict]]
    is_published: bool
    is_active: bool
    created_at: datetime
    items: List[FeeStructureItemResponse] = []


# ============================================
# Student Fee Account Schemas
# ============================================

class StudentFeeAccountResponse(BaseModel):
    """Student fee account response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    student_id: UUID
    student_name: Optional[str] = None
    academic_year_id: UUID
    fee_structure_id: Optional[UUID]
    total_due: float
    total_paid: float
    total_discount: float
    total_fine: float
    balance: float
    is_cleared: bool
    has_overdue: bool
    notes: Optional[str]
    created_at: datetime


class StudentFeeAccountSummary(BaseModel):
    """Summary of student fee account."""
    student_id: UUID
    student_name: str
    class_name: str
    total_due: float
    total_paid: float
    balance: float
    is_cleared: bool
    pending_invoices: int
    overdue_invoices: int


# ============================================
# Fee Invoice Schemas
# ============================================

class InvoiceLineItem(BaseModel):
    """Line item in an invoice."""
    component_id: UUID
    component_name: str
    amount: float
    discount: float = 0.0
    net_amount: float


class FeeInvoiceResponse(BaseModel):
    """Fee invoice response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    invoice_number: str
    student_id: UUID
    student_name: Optional[str] = None
    account_id: UUID
    structure_id: UUID
    installment_no: int
    total_installments: int
    invoice_date: date
    due_date: date
    subtotal: float
    discount_amount: float
    fine_amount: float
    tax_amount: float
    total_amount: float
    amount_paid: float
    balance_due: float
    status: InvoiceStatus
    line_items: Optional[List[dict]] = None
    notes: Optional[str]
    created_at: datetime


class GenerateInvoicesRequest(BaseModel):
    """Request to generate invoices."""
    academic_year_id: UUID
    class_id: Optional[UUID] = None  # If None, generate for all classes
    student_ids: Optional[List[UUID]] = None  # If None, generate for all students
    installment_no: int = Field(default=1, ge=1, le=12)
    due_date: date


class GenerateInvoicesResponse(BaseModel):
    """Response from invoice generation."""
    total_generated: int
    total_skipped: int
    invoices: List[UUID] = []
    errors: List[str] = []


# ============================================
# Fee Payment Schemas
# ============================================

class RecordPaymentRequest(BaseModel):
    """Request to record a payment."""
    amount: float = Field(..., gt=0)
    payment_date: date
    method: PaymentMethod = PaymentMethod.CASH
    reference_no: Optional[str] = None
    transaction_id: Optional[str] = None
    bank_name: Optional[str] = None
    cheque_number: Optional[str] = None
    cheque_date: Optional[date] = None
    notes: Optional[str] = None


class FeePaymentResponse(BaseModel):
    """Fee payment response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    invoice_id: UUID
    invoice_number: Optional[str] = None
    amount_paid: float
    payment_date: date
    method: PaymentMethod
    reference_no: Optional[str]
    transaction_id: Optional[str]
    bank_name: Optional[str]
    cheque_number: Optional[str]
    is_verified: bool
    is_reversed: bool
    recorded_by: Optional[UUID]
    notes: Optional[str]
    created_at: datetime
    receipt_number: Optional[str] = None


# ============================================
# Fee Receipt Schemas
# ============================================

class FeeReceiptResponse(BaseModel):
    """Fee receipt response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    payment_id: UUID
    receipt_number: str
    generated_at: datetime
    generated_by: Optional[UUID]
    print_count: int
    student_name: Optional[str] = None
    amount_paid: float = 0.0
    payment_date: Optional[date] = None
    payment_method: Optional[str] = None


# ============================================
# Discount Schemas
# ============================================

class FeeDiscountCreate(BaseModel):
    """Create a fee discount."""
    student_id: UUID
    academic_year_id: UUID
    discount_type: str
    name: str
    is_percentage: bool = False
    discount_value: float = Field(..., ge=0)
    applies_to_components: Optional[List[UUID]] = None
    reason: Optional[str] = None


class FeeDiscountResponse(BaseModel):
    """Fee discount response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    student_id: UUID
    student_name: Optional[str] = None
    academic_year_id: UUID
    discount_type: str
    name: str
    is_percentage: bool
    discount_value: float
    applies_to_components: Optional[List[UUID]]
    is_approved: bool
    approved_by: Optional[UUID]
    approved_at: Optional[datetime]
    reason: Optional[str]
    created_at: datetime


# ============================================
# Report Schemas
# ============================================

class CollectionReport(BaseModel):
    """Fee collection report."""
    period_start: date
    period_end: date
    total_collected: float
    by_method: dict = {}  # {cash: amount, upi: amount, ...}
    by_class: List[dict] = []  # [{class_id, class_name, amount}]
    by_component: List[dict] = []  # [{component_id, name, amount}]
    payment_count: int


class DuesReport(BaseModel):
    """Outstanding dues report."""
    total_due: float
    total_overdue: float
    by_class: List[dict] = []  # [{class_id, class_name, due, overdue}]
    overdue_students: List[StudentFeeAccountSummary] = []
    student_count: int
    overdue_count: int


class ClassFeesSummary(BaseModel):
    """Fee summary for a class."""
    class_id: UUID
    class_name: str
    total_students: int
    total_due: float
    total_collected: float
    total_pending: float
    collection_percentage: float
    cleared_count: int
    overdue_count: int
