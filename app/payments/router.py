"""
CUSTOS Payment Gateway Router

API endpoints for payment operations.
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth.dependencies import CurrentUser, require_permission
from app.users.rbac import Permission, SystemRole
from app.payments.service import PaymentService, format_amount
from app.payments.models import PaymentGateway, PaymentStatus
from app.payments.schemas import (
    GatewayConfigCreate, GatewayConfigUpdate, GatewayConfigResponse,
    PaymentOrderCreate, PaymentOrderResponse, PaymentOrderWithCheckout,
    PaymentVerifyRequest, PaymentTransactionResponse,
    RefundCreate, RefundResponse,
    PaymentHistoryResponse, PaymentHistoryItem,
    PaymentReceiptResponse, PaymentStats,
    WebhookPayload, WebhookResponse,
)


router = APIRouter(tags=["Payments"])


# ============================================
# Gateway Configuration (Admin Only)
# ============================================

@router.get("/gateways", response_model=List[GatewayConfigResponse])
async def list_gateway_configs(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.BILLING_MANAGE)),
):
    """List all configured payment gateways (Admin only)."""
    service = PaymentService(db, user.tenant_id)
    configs = await service.list_gateway_configs()
    
    # Hide credentials
    result = []
    for config in configs:
        response = GatewayConfigResponse(
            id=config.id,
            tenant_id=config.tenant_id,
            gateway=config.gateway,
            is_sandbox=config.is_sandbox,
            is_active=config.is_active,
            is_primary=config.is_primary,
            supported_methods=config.supported_methods,
            has_api_key=bool(config.api_key),
            has_api_secret=bool(config.api_secret),
            has_webhook_secret=bool(config.webhook_secret),
            created_at=config.created_at,
        )
        result.append(response)
    
    return result


@router.post("/gateways", response_model=GatewayConfigResponse, status_code=201)
async def configure_gateway(
    data: GatewayConfigCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.BILLING_MANAGE)),
):
    """Configure a payment gateway (Admin only)."""
    service = PaymentService(db, user.tenant_id)
    config = await service.configure_gateway(data)
    
    return GatewayConfigResponse(
        id=config.id,
        tenant_id=config.tenant_id,
        gateway=config.gateway,
        is_sandbox=config.is_sandbox,
        is_active=config.is_active,
        is_primary=config.is_primary,
        supported_methods=config.supported_methods,
        has_api_key=bool(config.api_key),
        has_api_secret=bool(config.api_secret),
        has_webhook_secret=bool(config.webhook_secret),
        created_at=config.created_at,
    )


@router.patch("/gateways/{gateway}", response_model=GatewayConfigResponse)
async def update_gateway_config(
    gateway: PaymentGateway,
    data: GatewayConfigUpdate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.BILLING_MANAGE)),
):
    """Update gateway configuration (Admin only)."""
    service = PaymentService(db, user.tenant_id)
    config = await service.update_gateway_config(gateway, data)
    
    return GatewayConfigResponse(
        id=config.id,
        tenant_id=config.tenant_id,
        gateway=config.gateway,
        is_sandbox=config.is_sandbox,
        is_active=config.is_active,
        is_primary=config.is_primary,
        supported_methods=config.supported_methods,
        has_api_key=bool(config.api_key),
        has_api_secret=bool(config.api_secret),
        has_webhook_secret=bool(config.webhook_secret),
        created_at=config.created_at,
    )


# ============================================
# Payment Orders
# ============================================

@router.post("/orders", response_model=PaymentOrderWithCheckout, status_code=201)
async def create_payment_order(
    data: PaymentOrderCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a payment order for an invoice.
    
    Returns order details and checkout data for client-side integration.
    """
    service = PaymentService(db, user.tenant_id)
    
    # Get invoice amount (simplified - would normally fetch from finance service)
    from sqlalchemy import select
    from app.finance.models import FeeInvoice
    
    invoice_query = select(FeeInvoice).where(
        FeeInvoice.tenant_id == user.tenant_id,
        FeeInvoice.id == data.invoice_id,
    )
    result = await db.execute(invoice_query)
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Calculate amount due (in paise)
    amount_due = int((invoice.total_amount - invoice.amount_paid) * 100)
    
    if amount_due <= 0:
        raise HTTPException(status_code=400, detail="Invoice already paid")
    
    # Get customer info
    from app.users.models import User
    student_query = select(User).where(User.id == data.student_id)
    student_result = await db.execute(student_query)
    student = student_result.scalar_one_or_none()
    
    customer_info = {
        "name": f"{student.first_name} {student.last_name}" if student else "",
        "email": student.email if student else "",
        "phone": student.phone if student else "",
    }
    
    order, checkout_data = await service.create_order(data, amount_due, customer_info)
    
    return PaymentOrderWithCheckout(
        id=order.id,
        tenant_id=order.tenant_id,
        order_number=order.order_number,
        invoice_id=order.invoice_id,
        student_id=order.student_id,
        parent_id=order.parent_id,
        amount=order.amount,
        amount_display=format_amount(order.amount),
        currency=order.currency,
        gateway=order.gateway,
        gateway_order_id=order.gateway_order_id,
        status=order.status,
        expires_at=order.expires_at,
        description=order.description,
        created_at=order.created_at,
        checkout_data=checkout_data,
    )


@router.get("/orders/{order_id}", response_model=PaymentOrderResponse)
async def get_payment_order(
    order_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Get payment order details."""
    service = PaymentService(db, user.tenant_id)
    order = await service.get_order(order_id)
    
    return PaymentOrderResponse(
        id=order.id,
        tenant_id=order.tenant_id,
        order_number=order.order_number,
        invoice_id=order.invoice_id,
        student_id=order.student_id,
        parent_id=order.parent_id,
        amount=order.amount,
        amount_display=format_amount(order.amount),
        currency=order.currency,
        gateway=order.gateway,
        gateway_order_id=order.gateway_order_id,
        status=order.status,
        expires_at=order.expires_at,
        description=order.description,
        created_at=order.created_at,
    )


# ============================================
# Payment Verification
# ============================================

@router.post("/verify", response_model=PaymentTransactionResponse)
async def verify_payment(
    data: PaymentVerifyRequest,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """
    Verify a payment completion.
    
    Called after successful payment on client-side to verify and record the transaction.
    """
    service = PaymentService(db, user.tenant_id)
    transaction = await service.verify_payment(data)
    
    # Update invoice payment status
    from app.finance.models import FeeInvoice, InvoiceStatus
    from sqlalchemy import select
    
    order = await service.get_order(data.order_id)
    invoice_query = select(FeeInvoice).where(FeeInvoice.id == order.invoice_id)
    result = await db.execute(invoice_query)
    invoice = result.scalar_one_or_none()
    
    if invoice:
        invoice.amount_paid += order.amount / 100  # Convert from paise
        if invoice.amount_paid >= invoice.total_amount:
            invoice.status = InvoiceStatus.PAID
            invoice.paid_at = datetime.now(timezone.utc)
        else:
            invoice.status = InvoiceStatus.PARTIAL
        await db.commit()
    
    return PaymentTransactionResponse(
        id=transaction.id,
        transaction_id=transaction.transaction_id,
        order_id=transaction.order_id,
        amount=transaction.amount,
        amount_display=format_amount(transaction.amount),
        currency=transaction.currency,
        gateway=transaction.gateway,
        gateway_payment_id=transaction.gateway_payment_id,
        method=transaction.method,
        method_details=transaction.method_details,
        status=transaction.status,
        initiated_at=transaction.initiated_at,
        completed_at=transaction.completed_at,
        error_code=transaction.error_code,
        error_message=transaction.error_message,
        created_at=transaction.created_at,
    )


@router.post("/failed")
async def record_failed_payment(
    order_id: UUID,
    error_code: str,
    error_message: str,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Record a failed payment attempt."""
    service = PaymentService(db, user.tenant_id)
    transaction = await service.record_failed_payment(order_id, error_code, error_message)
    
    return PaymentTransactionResponse(
        id=transaction.id,
        transaction_id=transaction.transaction_id,
        order_id=transaction.order_id,
        amount=transaction.amount,
        amount_display=format_amount(transaction.amount),
        currency=transaction.currency,
        gateway=transaction.gateway,
        gateway_payment_id=transaction.gateway_payment_id,
        method=transaction.method,
        method_details=transaction.method_details,
        status=transaction.status,
        initiated_at=transaction.initiated_at,
        completed_at=transaction.completed_at,
        error_code=transaction.error_code,
        error_message=transaction.error_message,
        created_at=transaction.created_at,
    )


# ============================================
# Refunds (Admin Only)
# ============================================

@router.post("/refunds", response_model=RefundResponse, status_code=201)
async def create_refund(
    data: RefundCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.BILLING_MANAGE)),
):
    """Create a refund for a transaction (Admin only)."""
    service = PaymentService(db, user.tenant_id)
    refund = await service.create_refund(data, user.id)
    
    return RefundResponse(
        id=refund.id,
        refund_id=refund.refund_id,
        transaction_id=refund.transaction_id,
        amount=refund.amount,
        amount_display=format_amount(refund.amount),
        status=refund.status,
        reason=refund.reason,
        gateway_refund_id=refund.gateway_refund_id,
        initiated_by=refund.initiated_by,
        processed_at=refund.processed_at,
        created_at=refund.created_at,
    )


# ============================================
# Payment History
# ============================================

@router.get("/history", response_model=PaymentHistoryResponse)
async def get_payment_history(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    student_id: Optional[UUID] = None,
    status: Optional[PaymentStatus] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    """
    Get payment transaction history.
    
    Parents/students see their own payments.
    Admins can filter by student.
    """
    service = PaymentService(db, user.tenant_id)
    
    # Check if user is admin
    user_roles = [r.code for r in user.roles] if user.roles else []
    admin_roles = {SystemRole.SUPER_ADMIN.value, SystemRole.PRINCIPAL.value, SystemRole.SUB_ADMIN.value}
    
    if not any(r in admin_roles for r in user_roles):
        # Non-admins see their own or their children's payments
        student_id = user.id
    
    transactions, total = await service.get_payment_history(
        student_id=student_id,
        status=status,
        page=page,
        size=size,
    )
    
    items = []
    total_paid = 0
    
    for txn in transactions:
        items.append(PaymentHistoryItem(
            transaction_id=txn.transaction_id,
            order_number=txn.order.order_number if txn.order else "",
            amount=txn.amount,
            amount_display=format_amount(txn.amount),
            status=txn.status,
            method=txn.method,
            gateway=txn.gateway,
            invoice_number=None,  # Would be populated from invoice
            fee_type=None,
            completed_at=txn.completed_at,
            created_at=txn.created_at,
        ))
        
        if txn.status == PaymentStatus.SUCCESS:
            total_paid += txn.amount
    
    return PaymentHistoryResponse(
        items=items,
        total=total,
        total_paid=total_paid,
        total_paid_display=format_amount(total_paid),
    )


# ============================================
# Stats (Admin)
# ============================================

@router.get("/stats", response_model=PaymentStats)
async def get_payment_stats(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.BILLING_VIEW)),
):
    """Get payment statistics."""
    service = PaymentService(db, user.tenant_id)
    return await service.get_stats()


# ============================================
# Webhooks
# ============================================

@router.post("/webhooks/razorpay", response_model=WebhookResponse)
async def razorpay_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Razorpay webhook endpoint.
    
    Note: This should validate webhook signature in production.
    """
    payload = await request.json()
    
    event_id = payload.get("event_id", "")
    event_type = payload.get("event", "")
    
    # Get tenant from order (simplified)
    # In production, would verify signature and extract tenant from order data
    
    # For now, just store the webhook
    return WebhookResponse(success=True, message="Webhook received")


# ============================================
# Receipt
# ============================================

@router.get("/receipt/{transaction_id}", response_model=PaymentReceiptResponse)
async def get_payment_receipt(
    transaction_id: str,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Get payment receipt data for a transaction."""
    from sqlalchemy import select
    from app.payments.models import PaymentTransaction, PaymentOrder
    from app.users.models import User
    from app.tenants.models import Tenant
    
    # Get transaction
    query = select(PaymentTransaction).where(
        PaymentTransaction.tenant_id == user.tenant_id,
        PaymentTransaction.transaction_id == transaction_id,
    )
    result = await db.execute(query)
    transaction = result.scalar_one_or_none()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Get order
    order_query = select(PaymentOrder).where(PaymentOrder.id == transaction.order_id)
    order_result = await db.execute(order_query)
    order = order_result.scalar_one_or_none()
    
    # Get student
    student_query = select(User).where(User.id == order.student_id)
    student_result = await db.execute(student_query)
    student = student_result.scalar_one_or_none()
    
    # Get tenant
    tenant_query = select(Tenant).where(Tenant.id == user.tenant_id)
    tenant_result = await db.execute(tenant_query)
    tenant = tenant_result.scalar_one_or_none()
    
    return PaymentReceiptResponse(
        receipt_number=f"RCP{transaction.transaction_id[3:]}",
        transaction_id=transaction.transaction_id,
        order_number=order.order_number,
        school_name=tenant.name if tenant else "",
        school_address=tenant.address if tenant else None,
        school_phone=tenant.phone if tenant else None,
        school_email=tenant.email if tenant else None,
        student_name=f"{student.first_name} {student.last_name}" if student else "",
        student_id=str(student.id) if student else "",
        class_section="",  # Would be populated from student profile
        amount=transaction.amount,
        amount_display=format_amount(transaction.amount),
        currency=transaction.currency,
        method=transaction.method,
        gateway=transaction.gateway,
        gateway_payment_id=transaction.gateway_payment_id,
        invoice_number=order.order_number,
        fee_type="Fee Payment",
        fee_period=None,
        payment_date=transaction.completed_at or transaction.created_at,
        receipt_date=datetime.now(timezone.utc),
    )
