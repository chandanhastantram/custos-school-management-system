"""
CUSTOS Payment Gateway Models

Payment processing, transactions, and gateway integration.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from uuid import UUID

from sqlalchemy import String, Text, Boolean, Integer, Numeric, DateTime, ForeignKey, Index, JSON
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import TenantBaseModel


class PaymentGateway(str, Enum):
    """Supported payment gateways."""
    RAZORPAY = "razorpay"
    STRIPE = "stripe"
    PAYTM = "paytm"
    PHONEPE = "phonepe"
    MANUAL = "manual"  # Cash, cheque, bank transfer


class PaymentStatus(str, Enum):
    """Payment transaction status."""
    PENDING = "pending"
    INITIATED = "initiated"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class PaymentMethod(str, Enum):
    """Payment method types."""
    CARD = "card"
    UPI = "upi"
    NETBANKING = "netbanking"
    WALLET = "wallet"
    CASH = "cash"
    CHEQUE = "cheque"
    BANK_TRANSFER = "bank_transfer"
    EMI = "emi"


class RefundStatus(str, Enum):
    """Refund status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class GatewayConfig(TenantBaseModel):
    """
    Payment gateway configuration per tenant.
    
    Each school can configure their own payment gateway credentials.
    """
    __tablename__ = "gateway_configs"
    
    __table_args__ = (
        Index("ix_gateway_config_tenant", "tenant_id", "is_active"),
        Index("ix_gateway_config_gateway", "tenant_id", "gateway"),
    )
    
    gateway: Mapped[PaymentGateway] = mapped_column(
        SQLEnum(PaymentGateway),
        nullable=False,
    )
    
    # Gateway credentials (encrypted)
    api_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    api_secret: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    merchant_id: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # Additional config
    webhook_secret: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    config_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Environment
    is_sandbox: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Supported methods
    supported_methods: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)


class PaymentOrder(TenantBaseModel):
    """
    Payment order - Created before initiating payment.
    
    Links fee invoices to payment transactions.
    """
    __tablename__ = "payment_orders"
    
    __table_args__ = (
        Index("ix_payment_order_tenant", "tenant_id", "status"),
        Index("ix_payment_order_student", "tenant_id", "student_id"),
        Index("ix_payment_order_invoice", "tenant_id", "invoice_id"),
    )
    
    # Order reference
    order_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    
    # Linked invoice
    invoice_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("fee_invoices.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Student/Payer
    student_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    parent_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Amount
    amount: Mapped[int] = mapped_column(Integer, nullable=False)  # In smallest currency unit (paise)
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    
    # Gateway details
    gateway: Mapped[PaymentGateway] = mapped_column(
        SQLEnum(PaymentGateway),
        nullable=False,
    )
    gateway_order_id: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # Status
    status: Mapped[PaymentStatus] = mapped_column(
        SQLEnum(PaymentStatus),
        default=PaymentStatus.PENDING,
    )
    
    # Expiry
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Metadata
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Relationships
    transactions: Mapped[List["PaymentTransaction"]] = relationship(
        "PaymentTransaction",
        back_populates="order",
        lazy="selectin",
    )


class PaymentTransaction(TenantBaseModel):
    """
    Individual payment transaction.
    
    Tracks each payment attempt and its status.
    """
    __tablename__ = "payment_transactions"
    
    __table_args__ = (
        Index("ix_payment_txn_tenant", "tenant_id", "status"),
        Index("ix_payment_txn_order", "order_id", "status"),
        Index("ix_payment_txn_gateway", "gateway", "gateway_payment_id"),
    )
    
    # Transaction reference
    transaction_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    
    # Linked order
    order_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("payment_orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Amount
    amount: Mapped[int] = mapped_column(Integer, nullable=False)  # In paise
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    
    # Gateway details
    gateway: Mapped[PaymentGateway] = mapped_column(
        SQLEnum(PaymentGateway),
        nullable=False,
    )
    gateway_payment_id: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    gateway_signature: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Payment method
    method: Mapped[Optional[PaymentMethod]] = mapped_column(
        SQLEnum(PaymentMethod),
        nullable=True,
    )
    method_details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    # e.g., {"bank": "HDFC", "last4": "1234", "upi_id": "xxx@upi"}
    
    # Status
    status: Mapped[PaymentStatus] = mapped_column(
        SQLEnum(PaymentStatus),
        default=PaymentStatus.PENDING,
    )
    
    # Timestamps
    initiated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Error handling
    error_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Raw gateway response
    gateway_response: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Relationships
    order: Mapped["PaymentOrder"] = relationship(
        "PaymentOrder", back_populates="transactions"
    )
    refunds: Mapped[List["PaymentRefund"]] = relationship(
        "PaymentRefund",
        back_populates="transaction",
        lazy="selectin",
    )


class PaymentRefund(TenantBaseModel):
    """
    Refund for a payment transaction.
    """
    __tablename__ = "payment_refunds"
    
    __table_args__ = (
        Index("ix_refund_tenant", "tenant_id", "status"),
        Index("ix_refund_transaction", "transaction_id", "status"),
    )
    
    # Refund reference
    refund_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    
    # Linked transaction
    transaction_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("payment_transactions.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Amount
    amount: Mapped[int] = mapped_column(Integer, nullable=False)  # In paise
    
    # Gateway details
    gateway_refund_id: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # Status
    status: Mapped[RefundStatus] = mapped_column(
        SQLEnum(RefundStatus),
        default=RefundStatus.PENDING,
    )
    
    # Reason
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Admin who initiated
    initiated_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Timestamps
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Gateway response
    gateway_response: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Relationships
    transaction: Mapped["PaymentTransaction"] = relationship(
        "PaymentTransaction", back_populates="refunds"
    )


class WebhookEvent(TenantBaseModel):
    """
    Webhook events from payment gateways.
    
    Used for tracking and debugging.
    """
    __tablename__ = "webhook_events"
    
    __table_args__ = (
        Index("ix_webhook_tenant", "tenant_id", "gateway"),
        Index("ix_webhook_event", "gateway", "event_type"),
    )
    
    # Event reference
    event_id: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Gateway
    gateway: Mapped[PaymentGateway] = mapped_column(
        SQLEnum(PaymentGateway),
        nullable=False,
    )
    
    # Event details
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    # Processing
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False)
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Error
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
