"""
CUSTOS Finance Router

API endpoints for Fees & Finance management.
"""

from datetime import date
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth.dependencies import CurrentUser, require_permission
from app.users.rbac import Permission
from app.finance.service import FeeService
from app.finance.models import InvoiceStatus, PaymentMethod
from app.finance.schemas import (
    FeeComponentCreate,
    FeeComponentUpdate,
    FeeComponentResponse,
    FeeStructureCreate,
    FeeStructureUpdate,
    FeeStructureResponse,
    FeeStructureItemResponse,
    StudentFeeAccountResponse,
    FeeInvoiceResponse,
    GenerateInvoicesRequest,
    GenerateInvoicesResponse,
    RecordPaymentRequest,
    FeePaymentResponse,
    FeeReceiptResponse,
    FeeDiscountCreate,
    FeeDiscountResponse,
    CollectionReport,
    DuesReport,
)


router = APIRouter(tags=["Fees & Finance"])


# ============================================
# Fee Components
# ============================================

@router.post("/components", response_model=FeeComponentResponse)
async def create_fee_component(
    data: FeeComponentCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.FEE_COMPONENT_MANAGE)),
):
    """
    Create a fee component (fee head).
    
    Examples: Tuition Fee, Building Fee, Lab Fee, Sports Fee, etc.
    """
    service = FeeService(db, user.tenant_id)
    component = await service.create_component(data)
    return FeeComponentResponse.model_validate(component)


@router.get("/components", response_model=List[FeeComponentResponse])
async def list_fee_components(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    is_active: Optional[bool] = None,
    category: Optional[str] = None,
    _=Depends(require_permission(Permission.FEE_VIEW)),
):
    """List all fee components."""
    service = FeeService(db, user.tenant_id)
    components = await service.list_components(is_active=is_active, category=category)
    return [FeeComponentResponse.model_validate(c) for c in components]


@router.get("/components/{component_id}", response_model=FeeComponentResponse)
async def get_fee_component(
    component_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.FEE_VIEW)),
):
    """Get a fee component by ID."""
    service = FeeService(db, user.tenant_id)
    component = await service.get_component(component_id)
    if not component:
        raise HTTPException(status_code=404, detail="Fee component not found")
    return FeeComponentResponse.model_validate(component)


@router.patch("/components/{component_id}", response_model=FeeComponentResponse)
async def update_fee_component(
    component_id: UUID,
    data: FeeComponentUpdate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.FEE_COMPONENT_MANAGE)),
):
    """Update a fee component."""
    service = FeeService(db, user.tenant_id)
    component = await service.update_component(component_id, data)
    return FeeComponentResponse.model_validate(component)


@router.delete("/components/{component_id}")
async def delete_fee_component(
    component_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.FEE_COMPONENT_MANAGE)),
):
    """Delete a fee component (soft delete)."""
    service = FeeService(db, user.tenant_id)
    await service.delete_component(component_id)
    return {"message": "Component deleted"}


# ============================================
# Fee Structures
# ============================================

@router.post("/structures", response_model=FeeStructureResponse)
async def create_fee_structure(
    data: FeeStructureCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.FEE_STRUCTURE_MANAGE)),
):
    """
    Create a fee structure for a class.
    
    Defines fees for a class per academic year with optional installments.
    """
    service = FeeService(db, user.tenant_id)
    structure = await service.create_structure(data)
    
    items = [
        FeeStructureItemResponse(
            id=item.id,
            fee_component_id=item.fee_component_id,
            amount=float(item.amount),
            discount_percentage=item.discount_percentage,
            discounted_amount=float(item.discounted_amount),
            display_order=item.display_order,
        )
        for item in structure.items
    ]
    
    return FeeStructureResponse(
        id=structure.id,
        tenant_id=structure.tenant_id,
        class_id=structure.class_id,
        academic_year_id=structure.academic_year_id,
        name=structure.name,
        description=structure.description,
        total_amount=float(structure.total_amount),
        installment_count=structure.installment_count,
        installment_schedule=structure.installment_schedule,
        is_published=structure.is_published,
        is_active=structure.is_active,
        created_at=structure.created_at,
        items=items,
    )


@router.get("/structures", response_model=List[FeeStructureResponse])
async def list_fee_structures(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    academic_year_id: Optional[UUID] = None,
    class_id: Optional[UUID] = None,
    is_published: Optional[bool] = None,
    _=Depends(require_permission(Permission.FEE_VIEW)),
):
    """List fee structures with filters."""
    service = FeeService(db, user.tenant_id)
    structures = await service.list_structures(
        academic_year_id=academic_year_id,
        class_id=class_id,
        is_published=is_published,
    )
    
    result = []
    for structure in structures:
        items = [
            FeeStructureItemResponse(
                id=item.id,
                fee_component_id=item.fee_component_id,
                amount=float(item.amount),
                discount_percentage=item.discount_percentage,
                discounted_amount=float(item.discounted_amount),
                display_order=item.display_order,
            )
            for item in structure.items
        ]
        
        result.append(FeeStructureResponse(
            id=structure.id,
            tenant_id=structure.tenant_id,
            class_id=structure.class_id,
            academic_year_id=structure.academic_year_id,
            name=structure.name,
            description=structure.description,
            total_amount=float(structure.total_amount),
            installment_count=structure.installment_count,
            installment_schedule=structure.installment_schedule,
            is_published=structure.is_published,
            is_active=structure.is_active,
            created_at=structure.created_at,
            items=items,
        ))
    
    return result


@router.get("/structures/{structure_id}", response_model=FeeStructureResponse)
async def get_fee_structure(
    structure_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.FEE_VIEW)),
):
    """Get a fee structure by ID."""
    service = FeeService(db, user.tenant_id)
    structure = await service.get_structure(structure_id)
    if not structure:
        raise HTTPException(status_code=404, detail="Fee structure not found")
    
    items = [
        FeeStructureItemResponse(
            id=item.id,
            fee_component_id=item.fee_component_id,
            amount=float(item.amount),
            discount_percentage=item.discount_percentage,
            discounted_amount=float(item.discounted_amount),
            display_order=item.display_order,
        )
        for item in structure.items
    ]
    
    return FeeStructureResponse(
        id=structure.id,
        tenant_id=structure.tenant_id,
        class_id=structure.class_id,
        academic_year_id=structure.academic_year_id,
        name=structure.name,
        description=structure.description,
        total_amount=float(structure.total_amount),
        installment_count=structure.installment_count,
        installment_schedule=structure.installment_schedule,
        is_published=structure.is_published,
        is_active=structure.is_active,
        created_at=structure.created_at,
        items=items,
    )


@router.patch("/structures/{structure_id}", response_model=FeeStructureResponse)
async def update_fee_structure(
    structure_id: UUID,
    data: FeeStructureUpdate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.FEE_STRUCTURE_MANAGE)),
):
    """Update a fee structure."""
    service = FeeService(db, user.tenant_id)
    structure = await service.update_structure(structure_id, data)
    
    items = [
        FeeStructureItemResponse(
            id=item.id,
            fee_component_id=item.fee_component_id,
            amount=float(item.amount),
            discount_percentage=item.discount_percentage,
            discounted_amount=float(item.discounted_amount),
            display_order=item.display_order,
        )
        for item in structure.items
    ]
    
    return FeeStructureResponse(
        id=structure.id,
        tenant_id=structure.tenant_id,
        class_id=structure.class_id,
        academic_year_id=structure.academic_year_id,
        name=structure.name,
        description=structure.description,
        total_amount=float(structure.total_amount),
        installment_count=structure.installment_count,
        installment_schedule=structure.installment_schedule,
        is_published=structure.is_published,
        is_active=structure.is_active,
        created_at=structure.created_at,
        items=items,
    )


# ============================================
# Student Fee Accounts
# ============================================

@router.post("/generate/{academic_year_id}")
async def generate_student_accounts(
    academic_year_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    class_id: Optional[UUID] = None,
    _=Depends(require_permission(Permission.FEE_INVOICE_GENERATE)),
):
    """
    Generate fee accounts for students.
    
    Creates StudentFeeAccount records for all students in the academic year.
    """
    service = FeeService(db, user.tenant_id)
    count = await service.generate_student_accounts(academic_year_id, class_id)
    return {"accounts_created": count}


@router.get("/student/{student_id}/account", response_model=StudentFeeAccountResponse)
async def get_student_fee_account(
    student_id: UUID,
    academic_year_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.FEE_VIEW)),
):
    """Get student's fee account."""
    service = FeeService(db, user.tenant_id)
    account = await service.get_student_account(student_id, academic_year_id)
    if not account:
        raise HTTPException(status_code=404, detail="Fee account not found")
    return StudentFeeAccountResponse.model_validate(account)


# ============================================
# Invoices
# ============================================

@router.post("/invoices/generate", response_model=GenerateInvoicesResponse)
async def generate_invoices(
    request: GenerateInvoicesRequest,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.FEE_INVOICE_GENERATE)),
):
    """
    Generate fee invoices for students.
    
    Creates invoices for the specified installment.
    """
    service = FeeService(db, user.tenant_id)
    count, invoice_ids, errors = await service.generate_invoices(request)
    
    return GenerateInvoicesResponse(
        total_generated=count,
        total_skipped=len(errors),
        invoices=invoice_ids,
        errors=errors,
    )


@router.get("/student/{student_id}/invoices", response_model=List[FeeInvoiceResponse])
async def get_student_invoices(
    student_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    academic_year_id: Optional[UUID] = None,
    status: Optional[InvoiceStatus] = None,
    _=Depends(require_permission(Permission.FEE_VIEW)),
):
    """Get invoices for a student."""
    service = FeeService(db, user.tenant_id)
    invoices = await service.get_student_invoices(
        student_id, academic_year_id, status
    )
    return [FeeInvoiceResponse.model_validate(i) for i in invoices]


@router.get("/invoices/{invoice_id}", response_model=FeeInvoiceResponse)
async def get_invoice(
    invoice_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.FEE_VIEW)),
):
    """Get invoice by ID."""
    service = FeeService(db, user.tenant_id)
    invoice = await service.get_invoice(invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return FeeInvoiceResponse.model_validate(invoice)


# ============================================
# Payments
# ============================================

@router.post("/invoices/{invoice_id}/pay", response_model=FeePaymentResponse)
async def record_payment(
    invoice_id: UUID,
    data: RecordPaymentRequest,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.FEE_PAYMENT_RECORD)),
):
    """
    Record a payment against an invoice.
    
    Supports partial payments. Automatically generates receipt.
    """
    service = FeeService(db, user.tenant_id)
    payment, receipt = await service.record_payment(
        invoice_id, data, user.id
    )
    
    return FeePaymentResponse(
        id=payment.id,
        tenant_id=payment.tenant_id,
        invoice_id=payment.invoice_id,
        amount_paid=float(payment.amount_paid),
        payment_date=payment.payment_date,
        method=payment.method,
        reference_no=payment.reference_no,
        transaction_id=payment.transaction_id,
        bank_name=payment.bank_name,
        cheque_number=payment.cheque_number,
        is_verified=payment.is_verified,
        is_reversed=payment.is_reversed,
        recorded_by=payment.recorded_by,
        notes=payment.notes,
        created_at=payment.created_at,
        receipt_number=receipt.receipt_number,
    )


@router.post("/payments/{payment_id}/reverse")
async def reverse_payment(
    payment_id: UUID,
    reason: str,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.FEE_PAYMENT_RECORD)),
):
    """Reverse a payment."""
    service = FeeService(db, user.tenant_id)
    payment = await service.reverse_payment(payment_id, reason)
    return {"message": "Payment reversed", "payment_id": str(payment.id)}


# ============================================
# Reports
# ============================================

@router.get("/reports/collection", response_model=CollectionReport)
async def get_collection_report(
    start_date: date,
    end_date: date,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.FEE_VIEW)),
):
    """
    Get fee collection report.
    
    Shows total collected, by payment method, by class, etc.
    """
    service = FeeService(db, user.tenant_id)
    return await service.get_collection_report(start_date, end_date)


@router.get("/reports/dues", response_model=DuesReport)
async def get_dues_report(
    academic_year_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.FEE_VIEW)),
):
    """
    Get outstanding dues report.
    
    Shows total pending, overdue, by class, top defaulters.
    """
    service = FeeService(db, user.tenant_id)
    return await service.get_dues_report(academic_year_id)


@router.post("/update-overdue")
async def update_overdue_invoices(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.FEE_INVOICE_GENERATE)),
):
    """Mark overdue invoices (run daily)."""
    service = FeeService(db, user.tenant_id)
    count = await service.update_overdue_invoices()
    return {"invoices_updated": count}


# ============================================
# Discounts
# ============================================

@router.post("/discounts", response_model=FeeDiscountResponse)
async def create_discount(
    data: FeeDiscountCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.FEE_STRUCTURE_MANAGE)),
):
    """Create a fee discount for a student."""
    service = FeeService(db, user.tenant_id)
    discount = await service.create_discount(data)
    return FeeDiscountResponse.model_validate(discount)


@router.post("/discounts/{discount_id}/approve", response_model=FeeDiscountResponse)
async def approve_discount(
    discount_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.FEE_STRUCTURE_MANAGE)),
):
    """Approve a fee discount."""
    service = FeeService(db, user.tenant_id)
    discount = await service.approve_discount(discount_id, user.id)
    return FeeDiscountResponse.model_validate(discount)
