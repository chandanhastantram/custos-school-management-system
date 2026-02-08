"""
CUSTOS Finance Models

School Fees & Finance data models.
"""

from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional, List
from uuid import UUID

from sqlalchemy import (
    String, Text, Integer, Float, Boolean, DateTime, Date,
    ForeignKey, Index, JSON, Numeric, UniqueConstraint
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import TenantBaseModel


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
# Fee Component (Fee Heads)
# ============================================

class FeeComponent(TenantBaseModel):
    """
    Fee Component / Fee Head.
    
    Examples: Tuition Fee, Building Fee, Lab Fee, Sports Fee, etc.
    """
    __tablename__ = "fee_components"
    
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_fee_component_code"),
        Index("ix_fee_comp_tenant", "tenant_id"),
    )
    
    # Identification
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Configuration
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True)
    is_refundable: Mapped[bool] = mapped_column(Boolean, default=False)
    allow_partial: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Category
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    # tuition, development, transport, lab, library, sports, etc.
    
    # Tax applicability
    is_taxable: Mapped[bool] = mapped_column(Boolean, default=False)
    tax_percentage: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Display order
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


# ============================================
# Fee Structure (Per Class Per Year)
# ============================================

class FeeStructure(TenantBaseModel):
    """
    Fee Structure - Defines fees for a class per academic year.
    
    Each class has one fee structure per year, containing multiple items.
    """
    __tablename__ = "fee_structures"
    
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "class_id", "academic_year_id",
            name="uq_fee_structure_class_year"
        ),
        Index("ix_fee_struct_tenant", "tenant_id"),
        Index("ix_fee_struct_class", "class_id"),
    )
    
    # Class linkage
    class_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("classes.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Academic year
    academic_year_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("academic_years.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Name & description
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Totals (computed)
    total_amount: Mapped[float] = mapped_column(
        Numeric(12, 2), default=0.0
    )
    
    # Installment config
    installment_count: Mapped[int] = mapped_column(Integer, default=1)
    installment_schedule: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )  # [{month: 1, percentage: 50}, {month: 7, percentage: 50}]
    
    # Status
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    items: Mapped[List["FeeStructureItem"]] = relationship(
        "FeeStructureItem",
        back_populates="structure",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class FeeStructureItem(TenantBaseModel):
    """
    Fee Structure Item - Individual fee component within a structure.
    """
    __tablename__ = "fee_structure_items"
    
    __table_args__ = (
        UniqueConstraint(
            "fee_structure_id", "fee_component_id",
            name="uq_fee_item_structure_component"
        ),
        Index("ix_fee_item_structure", "fee_structure_id"),
    )
    
    # Parent structure
    fee_structure_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("fee_structures.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Fee component
    fee_component_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("fee_components.id", ondelete="RESTRICT"),
        nullable=False,
    )
    
    # Amount
    amount: Mapped[float] = mapped_column(
        Numeric(12, 2), nullable=False
    )
    
    # Optional discount
    discount_percentage: Mapped[float] = mapped_column(Float, default=0.0)
    discounted_amount: Mapped[float] = mapped_column(
        Numeric(12, 2), default=0.0
    )
    
    # Display order
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    structure: Mapped["FeeStructure"] = relationship(
        "FeeStructure", back_populates="items"
    )
    component: Mapped["FeeComponent"] = relationship("FeeComponent")


# ============================================
# Student Fee Account
# ============================================

class StudentFeeAccount(TenantBaseModel):
    """
    Student Fee Account - Tracks student's fee status per year.
    
    One account per student per academic year.
    """
    __tablename__ = "student_fee_accounts"
    
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "student_id", "academic_year_id",
            name="uq_student_fee_account"
        ),
        Index("ix_fee_account_student", "student_id"),
        Index("ix_fee_account_year", "academic_year_id"),
    )
    
    # Student
    student_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Academic year
    academic_year_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("academic_years.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Fee structure applied
    fee_structure_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("fee_structures.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Amounts
    total_due: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0)
    total_paid: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0)
    total_discount: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0)
    total_fine: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0)
    balance: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0)
    
    # Status
    is_cleared: Mapped[bool] = mapped_column(Boolean, default=False)
    has_overdue: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    invoices: Mapped[List["FeeInvoice"]] = relationship(
        "FeeInvoice",
        back_populates="account",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


# ============================================
# Fee Invoice
# ============================================

class FeeInvoice(TenantBaseModel):
    """
    Fee Invoice - Bill generated for a student.
    
    Can be for full amount or installment.
    """
    __tablename__ = "fee_invoices"
    
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "invoice_number",
            name="uq_fee_invoice_number"
        ),
        Index("ix_invoice_account", "account_id"),
        Index("ix_invoice_student", "student_id"),
        Index("ix_invoice_status", "tenant_id", "status"),
        Index("ix_invoice_due_date", "tenant_id", "due_date"),
    )
    
    # Invoice number
    invoice_number: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Student & Account
    student_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("student_fee_accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Fee structure
    structure_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("fee_structures.id", ondelete="RESTRICT"),
        nullable=False,
    )
    
    # Installment info
    installment_no: Mapped[int] = mapped_column(Integer, default=1)
    total_installments: Mapped[int] = mapped_column(Integer, default=1)
    
    # Dates
    invoice_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    
    # Amounts
    subtotal: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0)
    discount_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0)
    fine_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0)
    tax_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0)
    total_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0)
    amount_paid: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0)
    balance_due: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0)
    
    # Status
    status: Mapped[InvoiceStatus] = mapped_column(
        SQLEnum(InvoiceStatus),
        default=InvoiceStatus.PENDING,
    )
    
    # Line items (snapshot)
    line_items: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    # [{component_id, component_name, amount, discount, net}]
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    account: Mapped["StudentFeeAccount"] = relationship(
        "StudentFeeAccount", back_populates="invoices"
    )
    payments: Mapped[List["FeePayment"]] = relationship(
        "FeePayment",
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


# ============================================
# Fee Payment
# ============================================

class FeePayment(TenantBaseModel):
    """
    Fee Payment - Payment against an invoice.
    
    Supports partial payments.
    """
    __tablename__ = "fee_payments"
    
    __table_args__ = (
        Index("ix_payment_invoice", "invoice_id"),
        Index("ix_payment_date", "tenant_id", "payment_date"),
    )
    
    # Invoice
    invoice_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("fee_invoices.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Payment details
    amount_paid: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    payment_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Method
    method: Mapped[PaymentMethod] = mapped_column(
        SQLEnum(PaymentMethod),
        default=PaymentMethod.CASH,
    )
    
    # Reference
    reference_no: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    transaction_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Bank details (for cheque/DD)
    bank_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    cheque_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    cheque_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Status
    is_verified: Mapped[bool] = mapped_column(Boolean, default=True)
    is_reversed: Mapped[bool] = mapped_column(Boolean, default=False)
    reversed_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Recorded by
    recorded_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    invoice: Mapped["FeeInvoice"] = relationship(
        "FeeInvoice", back_populates="payments"
    )
    receipt: Mapped[Optional["FeeReceipt"]] = relationship(
        "FeeReceipt",
        back_populates="payment",
        uselist=False,
    )


# ============================================
# Fee Receipt
# ============================================

class FeeReceipt(TenantBaseModel):
    """
    Fee Receipt - Generated for payments.
    """
    __tablename__ = "fee_receipts"
    
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "receipt_number",
            name="uq_fee_receipt_number"
        ),
        Index("ix_receipt_payment", "payment_id"),
    )
    
    # Payment
    payment_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("fee_payments.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Receipt number
    receipt_number: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Generated
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
    )
    generated_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Print status
    print_count: Mapped[int] = mapped_column(Integer, default=0)
    last_printed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Additional info
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    payment: Mapped["FeePayment"] = relationship(
        "FeePayment", back_populates="receipt"
    )


# ============================================
# Fee Discount
# ============================================

class FeeDiscount(TenantBaseModel):
    """
    Fee Discount - Applied to student accounts.
    
    Types: Scholarship, Sibling, Staff Child, Merit, Financial Aid, etc.
    """
    __tablename__ = "fee_discounts"
    
    __table_args__ = (
        Index("ix_discount_student", "student_id"),
        Index("ix_discount_type", "tenant_id", "discount_type"),
    )
    
    # Student
    student_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Academic year
    academic_year_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("academic_years.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Discount type
    discount_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # scholarship, sibling, staff_child, merit, financial_aid, other
    
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Amount
    is_percentage: Mapped[bool] = mapped_column(Boolean, default=False)
    discount_value: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    # If is_percentage=True, this is percentage. Otherwise, flat amount.
    
    # Applicability
    applies_to_components: Mapped[Optional[list]] = mapped_column(
        JSON, nullable=True
    )  # List of component IDs. Null = all.
    
    # Status
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    approved_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Reason
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


# ============================================
# Fee Challan (Bank Payment Slip)
# ============================================

class ChallanStatus(str, Enum):
    """Challan status."""
    GENERATED = "generated"
    PAID = "paid"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class FeeChallan(TenantBaseModel):
    """
    Fee Challan - Bank payment slip for offline payments.
    
    Used for students to pay fees at banks via pre-printed challans.
    """
    __tablename__ = "fee_challans"
    
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "challan_number",
            name="uq_fee_challan_number"
        ),
        Index("ix_challan_student", "student_id"),
        Index("ix_challan_invoice", "invoice_id"),
        Index("ix_challan_status", "tenant_id", "status"),
    )
    
    # Challan number
    challan_number: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Student & Invoice
    student_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    invoice_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("fee_invoices.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Amount details
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    fine_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0)
    total_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    
    # Bank details
    bank_name: Mapped[str] = mapped_column(String(100), nullable=False)
    bank_account_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    bank_ifsc: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    branch: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Validity
    issue_date: Mapped[date] = mapped_column(Date, nullable=False)
    valid_until: Mapped[date] = mapped_column(Date, nullable=False)
    
    # Purpose
    purpose: Mapped[str] = mapped_column(String(200), nullable=False)
    fee_components: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    # [{component_id, name, amount}]
    
    # Status
    status: Mapped[ChallanStatus] = mapped_column(
        SQLEnum(ChallanStatus, name="challan_status_enum"),
        default=ChallanStatus.GENERATED,
    )
    
    # Payment verification (after bank submits)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verified_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    bank_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    payment_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Generated by
    generated_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Print tracking
    print_count: Mapped[int] = mapped_column(Integer, default=0)
    last_printed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
