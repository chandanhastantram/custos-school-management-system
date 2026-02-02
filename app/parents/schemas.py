"""
CUSTOS Parent Portal Schemas

Pydantic schemas for parent portal API.
"""

from datetime import datetime, date
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


# ============================================
# Child Information
# ============================================

class ChildInfo(BaseModel):
    """Basic child information for parent view."""
    student_id: UUID
    name: str
    class_name: Optional[str] = None
    section: Optional[str] = None
    roll_number: Optional[str] = None
    profile_image: Optional[str] = None


# ============================================
# Dashboard
# ============================================

class ParentDashboard(BaseModel):
    """Parent portal dashboard."""
    parent_id: UUID
    parent_name: str
    children: List[ChildInfo] = []
    
    # Financial summary
    total_due: float = 0.0
    total_paid: float = 0.0
    total_overdue: float = 0.0
    balance: float = 0.0
    
    # Next due
    next_due_date: Optional[date] = None
    next_due_amount: float = 0.0
    
    # Counts
    pending_invoices: int = 0
    overdue_invoices: int = 0
    
    # Recent activity
    last_payment_date: Optional[date] = None
    last_payment_amount: float = 0.0


class ChildFeeSummary(BaseModel):
    """Fee summary for a single child."""
    student_id: UUID
    student_name: str
    class_name: Optional[str] = None
    total_due: float = 0.0
    total_paid: float = 0.0
    balance: float = 0.0
    pending_invoices: int = 0
    overdue_invoices: int = 0


# ============================================
# Invoices for Parent View
# ============================================

class ParentInvoiceResponse(BaseModel):
    """Invoice as seen by parent."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    invoice_number: str
    student_id: UUID
    student_name: Optional[str] = None
    installment_no: int
    total_installments: int
    invoice_date: date
    due_date: date
    total_amount: float
    amount_paid: float
    balance_due: float
    status: str
    is_overdue: bool = False
    can_pay_online: bool = True


class ParentInvoiceDetail(ParentInvoiceResponse):
    """Detailed invoice with line items."""
    line_items: List[dict] = []
    payments: List[dict] = []


# ============================================
# Payments for Parent View
# ============================================

class ParentPaymentResponse(BaseModel):
    """Payment as seen by parent."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    invoice_id: UUID
    invoice_number: str
    student_name: Optional[str] = None
    amount_paid: float
    payment_date: date
    method: str
    reference_no: Optional[str] = None
    receipt_number: Optional[str] = None
    is_online: bool = False


# ============================================
# Receipt Download
# ============================================

class ReceiptDownload(BaseModel):
    """Receipt download info."""
    receipt_id: UUID
    receipt_number: str
    student_name: str
    amount: float
    payment_date: date
    payment_method: str
    download_url: Optional[str] = None


# ============================================
# Notifications
# ============================================

class ParentNotification(BaseModel):
    """Notification for parent."""
    id: UUID
    title: str
    message: str
    notification_type: str
    is_read: bool = False
    created_at: datetime
    related_invoice_id: Optional[UUID] = None


class ParentNotificationList(BaseModel):
    """List of notifications."""
    items: List[ParentNotification] = []
    unread_count: int = 0
    total: int = 0


# ============================================
# Extended Schemas for Parent Router
# ============================================

class ChildSummary(BaseModel):
    """Summary of a child for listing."""
    student_id: UUID
    name: str
    class_name: str = "N/A"
    section: str = ""
    roll_number: Optional[str] = None
    photo_url: Optional[str] = None


class AttendanceSummary(BaseModel):
    """Attendance summary for a month."""
    student_id: UUID
    month: int
    year: int
    total_days: int = 0
    present_days: int = 0
    absent_days: int = 0
    late_days: int = 0
    attendance_percentage: float = 0.0
    daily_records: List[dict] = []


class AcademicSummary(BaseModel):
    """Academic performance summary."""
    student_id: UUID
    overall_grade: str = "N/A"
    overall_percentage: float = 0.0
    rank_in_class: Optional[int] = None
    total_students: int = 0
    subjects: List[dict] = []
    recent_assessments: List[dict] = []
    improvement_areas: List[str] = []


class FeesSummary(BaseModel):
    """Fee summary for a student."""
    student_id: UUID
    total_amount: float = 0.0
    paid_amount: float = 0.0
    pending_amount: float = 0.0
    pending_invoices: int = 0
    next_due_date: Optional[date] = None
    next_due_amount: float = 0.0


class ChildDetail(BaseModel):
    """Detailed information about a child."""
    student_id: UUID
    name: str
    class_name: str = "N/A"
    section: str = ""
    roll_number: Optional[str] = None
    photo_url: Optional[str] = None
    date_of_birth: Optional[date] = None
    academics: Optional[AcademicSummary] = None
    attendance: Optional[AttendanceSummary] = None
    fees: Optional[FeesSummary] = None


class ParentDashboardResponse(BaseModel):
    """Comprehensive parent dashboard response."""
    parent_id: str
    children: List[dict] = []
    total_children: int = 0
    total_pending_fees: float = 0.0
    total_paid_fees: float = 0.0
    unread_notifications: int = 0
    upcoming_events: List[dict] = []


class NotificationItem(BaseModel):
    """Single notification item."""
    id: UUID
    title: str
    message: str
    type: str
    is_read: bool = False
    created_at: datetime
