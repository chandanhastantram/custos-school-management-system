"""
CUSTOS Payment Gateway Schemas

Pydantic schemas for payment operations.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from app.payments.models import (
    PaymentGateway, PaymentStatus, PaymentMethod, RefundStatus
)


# ============================================
# Gateway Config Schemas
# ============================================

class GatewayConfigBase(BaseModel):
    """Base schema for gateway config."""
    gateway: PaymentGateway
    is_sandbox: bool = True
    is_active: bool = True
    is_primary: bool = False
    supported_methods: Optional[List[str]] = None


class GatewayConfigCreate(GatewayConfigBase):
    """Schema for creating gateway config."""
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    merchant_id: Optional[str] = None
    webhook_secret: Optional[str] = None
    config_json: Optional[Dict[str, Any]] = None


class GatewayConfigUpdate(BaseModel):
    """Schema for updating gateway config."""
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    merchant_id: Optional[str] = None
    webhook_secret: Optional[str] = None
    config_json: Optional[Dict[str, Any]] = None
    is_sandbox: Optional[bool] = None
    is_active: Optional[bool] = None
    is_primary: Optional[bool] = None
    supported_methods: Optional[List[str]] = None


class GatewayConfigResponse(GatewayConfigBase):
    """Schema for gateway config response (credentials hidden)."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    has_api_key: bool = False
    has_api_secret: bool = False
    has_webhook_secret: bool = False
    created_at: datetime


# ============================================
# Payment Order Schemas
# ============================================

class PaymentOrderCreate(BaseModel):
    """Schema for creating a payment order."""
    invoice_id: UUID
    student_id: UUID
    parent_id: Optional[UUID] = None
    gateway: PaymentGateway = PaymentGateway.RAZORPAY
    description: Optional[str] = None
    notes: Optional[Dict[str, Any]] = None


class PaymentOrderResponse(BaseModel):
    """Schema for payment order response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    order_number: str
    invoice_id: UUID
    student_id: UUID
    parent_id: Optional[UUID]
    amount: int
    amount_display: str  # "₹1,500.00"
    currency: str
    gateway: PaymentGateway
    gateway_order_id: Optional[str]
    status: PaymentStatus
    expires_at: Optional[datetime]
    description: Optional[str]
    created_at: datetime


class PaymentOrderWithCheckout(PaymentOrderResponse):
    """Payment order with checkout details."""
    checkout_url: Optional[str] = None
    checkout_data: Optional[Dict[str, Any]] = None
    # For client-side SDK integration


# ============================================
# Payment Transaction Schemas
# ============================================

class PaymentVerifyRequest(BaseModel):
    """Request to verify payment completion."""
    order_id: UUID
    gateway_payment_id: str
    gateway_signature: Optional[str] = None
    method: Optional[PaymentMethod] = None
    method_details: Optional[Dict[str, Any]] = None


class PaymentTransactionResponse(BaseModel):
    """Schema for transaction response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    transaction_id: str
    order_id: UUID
    amount: int
    amount_display: str
    currency: str
    gateway: PaymentGateway
    gateway_payment_id: Optional[str]
    method: Optional[PaymentMethod]
    method_details: Optional[Dict[str, Any]]
    status: PaymentStatus
    initiated_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_code: Optional[str]
    error_message: Optional[str]
    created_at: datetime


# ============================================
# Refund Schemas
# ============================================

class RefundCreate(BaseModel):
    """Schema for creating a refund."""
    transaction_id: UUID
    amount: int  # In paise
    reason: Optional[str] = None


class RefundResponse(BaseModel):
    """Schema for refund response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    refund_id: str
    transaction_id: UUID
    amount: int
    amount_display: str
    status: RefundStatus
    reason: Optional[str]
    gateway_refund_id: Optional[str]
    initiated_by: Optional[UUID]
    processed_at: Optional[datetime]
    created_at: datetime


# ============================================
# Webhook Schemas
# ============================================

class WebhookPayload(BaseModel):
    """Generic webhook payload."""
    event_id: str
    event_type: str
    payload: Dict[str, Any]


class WebhookResponse(BaseModel):
    """Webhook acknowledgment response."""
    success: bool
    message: str


# ============================================
# Payment Link Schemas (for sharing)
# ============================================

class PaymentLinkCreate(BaseModel):
    """Create a shareable payment link."""
    invoice_id: UUID
    expires_in_hours: int = Field(24, ge=1, le=720)
    notify_parent: bool = True


class PaymentLinkResponse(BaseModel):
    """Payment link response."""
    link_id: str
    payment_url: str
    amount: int
    amount_display: str
    expires_at: datetime
    invoice_id: UUID
    student_name: str
    class_name: str


# ============================================
# Payment History Schemas
# ============================================

class PaymentHistoryItem(BaseModel):
    """Single payment history item."""
    transaction_id: str
    order_number: str
    amount: int
    amount_display: str
    status: PaymentStatus
    method: Optional[PaymentMethod]
    gateway: PaymentGateway
    invoice_number: Optional[str]
    fee_type: Optional[str]
    completed_at: Optional[datetime]
    created_at: datetime


class PaymentHistoryResponse(BaseModel):
    """Payment history response."""
    items: List[PaymentHistoryItem]
    total: int
    total_paid: int
    total_paid_display: str


# ============================================
# Receipt Schemas
# ============================================

class PaymentReceiptResponse(BaseModel):
    """Payment receipt data for PDF generation."""
    receipt_number: str
    transaction_id: str
    order_number: str
    
    # School details
    school_name: str
    school_address: Optional[str]
    school_phone: Optional[str]
    school_email: Optional[str]
    
    # Student details
    student_name: str
    student_id: str
    class_section: str
    
    # Payment details
    amount: int
    amount_display: str
    currency: str
    method: Optional[PaymentMethod]
    gateway: PaymentGateway
    gateway_payment_id: Optional[str]
    
    # Invoice details
    invoice_number: str
    fee_type: str
    fee_period: Optional[str]
    
    # Timestamps
    payment_date: datetime
    receipt_date: datetime
    
    # Verification
    qr_code_data: Optional[str] = None


# ============================================
# Stats Schemas
# ============================================

class PaymentStats(BaseModel):
    """Payment statistics for dashboard."""
    total_transactions: int
    successful_transactions: int
    failed_transactions: int
    pending_transactions: int
    
    total_amount_collected: int
    total_amount_collected_display: str
    
    total_refunds: int
    total_refund_amount: int
    total_refund_amount_display: str
    
    # By gateway
    by_gateway: Dict[str, int]
    
    # By method
    by_method: Dict[str, int]
    
    # Recent trend (last 7 days)
    daily_collections: List[Dict[str, Any]]
