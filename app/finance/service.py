"""
CUSTOS Fee Service

Business logic for school fees management.
"""

from datetime import datetime, date
from typing import Optional, List, Tuple
from uuid import UUID, uuid4

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundError, ValidationError
from app.finance.models import (
    FeeComponent,
    FeeStructure,
    FeeStructureItem,
    StudentFeeAccount,
    FeeInvoice,
    FeePayment,
    FeeReceipt,
    FeeDiscount,
    InvoiceStatus,
    PaymentMethod,
)
from app.finance.schemas import (
    FeeComponentCreate,
    FeeComponentUpdate,
    FeeStructureCreate,
    FeeStructureUpdate,
    FeeStructureItemCreate,
    GenerateInvoicesRequest,
    RecordPaymentRequest,
    FeeDiscountCreate,
    CollectionReport,
    DuesReport,
    ClassFeesSummary,
)


class FeeService:
    """
    Fee Management Service.
    
    Handles:
    - Fee component CRUD
    - Fee structure management
    - Student fee account generation
    - Invoice generation
    - Payment recording
    - Receipt generation
    - Financial reports
    """
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
    
    # ============================================
    # Fee Components
    # ============================================
    
    async def create_component(
        self,
        data: FeeComponentCreate,
    ) -> FeeComponent:
        """Create a fee component."""
        component = FeeComponent(
            tenant_id=self.tenant_id,
            **data.model_dump(),
        )
        self.session.add(component)
        await self.session.flush()
        return component
    
    async def update_component(
        self,
        component_id: UUID,
        data: FeeComponentUpdate,
    ) -> FeeComponent:
        """Update a fee component."""
        component = await self.get_component(component_id)
        if not component:
            raise ResourceNotFoundError("FeeComponent", component_id)
        
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(component, key, value)
        
        await self.session.flush()
        return component
    
    async def get_component(self, component_id: UUID) -> Optional[FeeComponent]:
        """Get a fee component by ID."""
        query = select(FeeComponent).where(
            FeeComponent.id == component_id,
            FeeComponent.tenant_id == self.tenant_id,
            FeeComponent.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def list_components(
        self,
        is_active: Optional[bool] = None,
        category: Optional[str] = None,
    ) -> List[FeeComponent]:
        """List fee components."""
        query = select(FeeComponent).where(
            FeeComponent.tenant_id == self.tenant_id,
            FeeComponent.deleted_at.is_(None),
        )
        
        if is_active is not None:
            query = query.where(FeeComponent.is_active == is_active)
        if category:
            query = query.where(FeeComponent.category == category)
        
        query = query.order_by(FeeComponent.display_order, FeeComponent.name)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def delete_component(self, component_id: UUID) -> None:
        """Soft delete a fee component."""
        component = await self.get_component(component_id)
        if component:
            component.deleted_at = datetime.utcnow()
            await self.session.flush()
    
    # ============================================
    # Fee Structures
    # ============================================
    
    async def create_structure(
        self,
        data: FeeStructureCreate,
    ) -> FeeStructure:
        """Create a fee structure with items."""
        # Calculate total
        total = sum(item.amount for item in data.items)
        
        structure = FeeStructure(
            tenant_id=self.tenant_id,
            class_id=data.class_id,
            academic_year_id=data.academic_year_id,
            name=data.name,
            description=data.description,
            total_amount=total,
            installment_count=data.installment_count,
            installment_schedule=data.installment_schedule,
        )
        self.session.add(structure)
        await self.session.flush()
        
        # Add items
        for i, item_data in enumerate(data.items):
            discounted = item_data.amount * (1 - item_data.discount_percentage / 100)
            
            item = FeeStructureItem(
                tenant_id=self.tenant_id,
                fee_structure_id=structure.id,
                fee_component_id=item_data.fee_component_id,
                amount=item_data.amount,
                discount_percentage=item_data.discount_percentage,
                discounted_amount=discounted,
                display_order=i,
            )
            self.session.add(item)
        
        await self.session.flush()
        await self.session.refresh(structure)
        
        return structure
    
    async def update_structure(
        self,
        structure_id: UUID,
        data: FeeStructureUpdate,
    ) -> FeeStructure:
        """Update a fee structure."""
        structure = await self.get_structure(structure_id)
        if not structure:
            raise ResourceNotFoundError("FeeStructure", structure_id)
        
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(structure, key, value)
        
        await self.session.flush()
        return structure
    
    async def get_structure(self, structure_id: UUID) -> Optional[FeeStructure]:
        """Get a fee structure by ID."""
        query = select(FeeStructure).where(
            FeeStructure.id == structure_id,
            FeeStructure.tenant_id == self.tenant_id,
            FeeStructure.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_structure_for_class(
        self,
        class_id: UUID,
        academic_year_id: UUID,
    ) -> Optional[FeeStructure]:
        """Get fee structure for a class in an academic year."""
        query = select(FeeStructure).where(
            FeeStructure.tenant_id == self.tenant_id,
            FeeStructure.class_id == class_id,
            FeeStructure.academic_year_id == academic_year_id,
            FeeStructure.is_active == True,
            FeeStructure.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def list_structures(
        self,
        academic_year_id: Optional[UUID] = None,
        class_id: Optional[UUID] = None,
        is_published: Optional[bool] = None,
    ) -> List[FeeStructure]:
        """List fee structures."""
        query = select(FeeStructure).where(
            FeeStructure.tenant_id == self.tenant_id,
            FeeStructure.deleted_at.is_(None),
        )
        
        if academic_year_id:
            query = query.where(FeeStructure.academic_year_id == academic_year_id)
        if class_id:
            query = query.where(FeeStructure.class_id == class_id)
        if is_published is not None:
            query = query.where(FeeStructure.is_published == is_published)
        
        query = query.order_by(FeeStructure.created_at.desc())
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    # ============================================
    # Student Fee Accounts
    # ============================================
    
    async def generate_student_accounts(
        self,
        academic_year_id: UUID,
        class_id: Optional[UUID] = None,
    ) -> int:
        """Generate fee accounts for students."""
        from app.users.models import User
        from app.academics.models.structure import ClassEnrollment
        
        # Get students (via enrollments)
        query = select(ClassEnrollment).where(
            ClassEnrollment.tenant_id == self.tenant_id,
            ClassEnrollment.academic_year_id == academic_year_id,
            ClassEnrollment.is_active == True,
        )
        
        if class_id:
            query = query.where(ClassEnrollment.class_id == class_id)
        
        result = await self.session.execute(query)
        enrollments = result.scalars().all()
        
        accounts_created = 0
        
        for enrollment in enrollments:
            # Check if account exists
            existing = await self.get_student_account(
                enrollment.student_id, academic_year_id
            )
            if existing:
                continue
            
            # Get fee structure
            structure = await self.get_structure_for_class(
                enrollment.class_id, academic_year_id
            )
            
            total_due = structure.total_amount if structure else 0.0
            
            account = StudentFeeAccount(
                tenant_id=self.tenant_id,
                student_id=enrollment.student_id,
                academic_year_id=academic_year_id,
                fee_structure_id=structure.id if structure else None,
                total_due=total_due,
                balance=total_due,
            )
            self.session.add(account)
            accounts_created += 1
        
        await self.session.flush()
        return accounts_created
    
    async def get_student_account(
        self,
        student_id: UUID,
        academic_year_id: UUID,
    ) -> Optional[StudentFeeAccount]:
        """Get student fee account."""
        query = select(StudentFeeAccount).where(
            StudentFeeAccount.tenant_id == self.tenant_id,
            StudentFeeAccount.student_id == student_id,
            StudentFeeAccount.academic_year_id == academic_year_id,
            StudentFeeAccount.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def recalculate_account(
        self,
        account_id: UUID,
    ) -> StudentFeeAccount:
        """Recalculate account balances from invoices."""
        account = await self._get_account_by_id(account_id)
        if not account:
            raise ResourceNotFoundError("StudentFeeAccount", account_id)
        
        # Sum from invoices
        query = select(
            func.sum(FeeInvoice.total_amount).label("total_due"),
            func.sum(FeeInvoice.amount_paid).label("total_paid"),
        ).where(
            FeeInvoice.account_id == account_id,
            FeeInvoice.status != InvoiceStatus.CANCELLED,
            FeeInvoice.deleted_at.is_(None),
        )
        
        result = await self.session.execute(query)
        row = result.first()
        
        total_due = float(row.total_due or 0)
        total_paid = float(row.total_paid or 0)
        
        account.total_due = total_due
        account.total_paid = total_paid
        account.balance = total_due - total_paid
        account.is_cleared = account.balance <= 0
        
        # Check overdue
        overdue_query = select(func.count(FeeInvoice.id)).where(
            FeeInvoice.account_id == account_id,
            FeeInvoice.status == InvoiceStatus.OVERDUE,
            FeeInvoice.deleted_at.is_(None),
        )
        overdue_count = await self.session.scalar(overdue_query) or 0
        account.has_overdue = overdue_count > 0
        
        await self.session.flush()
        return account
    
    async def _get_account_by_id(
        self,
        account_id: UUID,
    ) -> Optional[StudentFeeAccount]:
        """Get account by ID."""
        query = select(StudentFeeAccount).where(
            StudentFeeAccount.id == account_id,
            StudentFeeAccount.tenant_id == self.tenant_id,
            StudentFeeAccount.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    # ============================================
    # Invoices
    # ============================================
    
    async def generate_invoices(
        self,
        request: GenerateInvoicesRequest,
    ) -> Tuple[int, List[UUID], List[str]]:
        """Generate invoices for students."""
        # Get accounts
        query = select(StudentFeeAccount).where(
            StudentFeeAccount.tenant_id == self.tenant_id,
            StudentFeeAccount.academic_year_id == request.academic_year_id,
            StudentFeeAccount.deleted_at.is_(None),
        )
        
        if request.student_ids:
            query = query.where(
                StudentFeeAccount.student_id.in_(request.student_ids)
            )
        
        result = await self.session.execute(query)
        accounts = result.scalars().all()
        
        generated = 0
        invoice_ids = []
        errors = []
        
        for account in accounts:
            try:
                # Check if invoice already exists for this installment
                existing = await self._get_invoice_for_installment(
                    account.id, request.installment_no
                )
                if existing:
                    continue
                
                # Get structure
                structure = await self.get_structure(account.fee_structure_id)
                if not structure:
                    continue
                
                # Calculate installment amount
                if structure.installment_schedule:
                    schedule = structure.installment_schedule
                    installment = next(
                        (s for s in schedule if s.get("installment") == request.installment_no),
                        None
                    )
                    percentage = installment.get("percentage", 100) if installment else 100
                else:
                    percentage = 100 / structure.installment_count
                
                amount = structure.total_amount * (percentage / 100)
                
                # Generate invoice number
                invoice_number = await self._generate_invoice_number()
                
                # Build line items
                line_items = []
                for item in structure.items:
                    item_amount = float(item.amount) * (percentage / 100)
                    component = await self.get_component(item.fee_component_id)
                    line_items.append({
                        "component_id": str(item.fee_component_id),
                        "component_name": component.name if component else "Unknown",
                        "amount": item_amount,
                        "discount": 0,
                        "net_amount": item_amount,
                    })
                
                invoice = FeeInvoice(
                    tenant_id=self.tenant_id,
                    invoice_number=invoice_number,
                    student_id=account.student_id,
                    account_id=account.id,
                    structure_id=structure.id,
                    installment_no=request.installment_no,
                    total_installments=structure.installment_count,
                    invoice_date=date.today(),
                    due_date=request.due_date,
                    subtotal=amount,
                    total_amount=amount,
                    balance_due=amount,
                    status=InvoiceStatus.PENDING,
                    line_items=line_items,
                )
                self.session.add(invoice)
                await self.session.flush()
                
                invoice_ids.append(invoice.id)
                generated += 1
                
            except Exception as e:
                errors.append(str(e))
        
        await self.session.flush()
        return generated, invoice_ids, errors
    
    async def _get_invoice_for_installment(
        self,
        account_id: UUID,
        installment_no: int,
    ) -> Optional[FeeInvoice]:
        """Check if invoice exists for installment."""
        query = select(FeeInvoice).where(
            FeeInvoice.account_id == account_id,
            FeeInvoice.installment_no == installment_no,
            FeeInvoice.status != InvoiceStatus.CANCELLED,
            FeeInvoice.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def _generate_invoice_number(self) -> str:
        """Generate unique invoice number."""
        prefix = datetime.now().strftime("INV%Y%m")
        
        # Get count for this month
        query = select(func.count(FeeInvoice.id)).where(
            FeeInvoice.tenant_id == self.tenant_id,
            FeeInvoice.invoice_number.like(f"{prefix}%"),
        )
        count = await self.session.scalar(query) or 0
        
        return f"{prefix}{count + 1:05d}"
    
    async def get_invoice(self, invoice_id: UUID) -> Optional[FeeInvoice]:
        """Get invoice by ID."""
        query = select(FeeInvoice).where(
            FeeInvoice.id == invoice_id,
            FeeInvoice.tenant_id == self.tenant_id,
            FeeInvoice.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_student_invoices(
        self,
        student_id: UUID,
        academic_year_id: Optional[UUID] = None,
        status: Optional[InvoiceStatus] = None,
    ) -> List[FeeInvoice]:
        """Get invoices for a student."""
        query = select(FeeInvoice).where(
            FeeInvoice.tenant_id == self.tenant_id,
            FeeInvoice.student_id == student_id,
            FeeInvoice.deleted_at.is_(None),
        )
        
        if academic_year_id:
            query = query.join(StudentFeeAccount).where(
                StudentFeeAccount.academic_year_id == academic_year_id
            )
        if status:
            query = query.where(FeeInvoice.status == status)
        
        query = query.order_by(FeeInvoice.due_date.desc())
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def update_overdue_invoices(self) -> int:
        """Mark overdue invoices."""
        today = date.today()
        
        query = select(FeeInvoice).where(
            FeeInvoice.tenant_id == self.tenant_id,
            FeeInvoice.status == InvoiceStatus.PENDING,
            FeeInvoice.due_date < today,
            FeeInvoice.deleted_at.is_(None),
        )
        
        result = await self.session.execute(query)
        invoices = result.scalars().all()
        
        for invoice in invoices:
            invoice.status = InvoiceStatus.OVERDUE
        
        await self.session.flush()
        return len(invoices)
    
    # ============================================
    # Payments
    # ============================================
    
    async def record_payment(
        self,
        invoice_id: UUID,
        data: RecordPaymentRequest,
        recorded_by: UUID,
    ) -> Tuple[FeePayment, FeeReceipt]:
        """Record a payment against an invoice."""
        invoice = await self.get_invoice(invoice_id)
        if not invoice:
            raise ResourceNotFoundError("FeeInvoice", invoice_id)
        
        if invoice.status == InvoiceStatus.CANCELLED:
            raise ValidationError("Cannot pay cancelled invoice")
        
        if data.amount > invoice.balance_due:
            raise ValidationError(
                f"Payment amount {data.amount} exceeds balance {invoice.balance_due}"
            )
        
        # Create payment
        payment = FeePayment(
            tenant_id=self.tenant_id,
            invoice_id=invoice_id,
            amount_paid=data.amount,
            payment_date=data.payment_date,
            payment_time=datetime.now(),
            method=data.method,
            reference_no=data.reference_no,
            transaction_id=data.transaction_id,
            bank_name=data.bank_name,
            cheque_number=data.cheque_number,
            cheque_date=data.cheque_date,
            recorded_by=recorded_by,
            notes=data.notes,
        )
        self.session.add(payment)
        await self.session.flush()
        
        # Update invoice
        invoice.amount_paid += data.amount
        invoice.balance_due = invoice.total_amount - invoice.amount_paid
        
        if invoice.balance_due <= 0:
            invoice.status = InvoiceStatus.PAID
        elif invoice.amount_paid > 0:
            invoice.status = InvoiceStatus.PARTIAL
        
        # Generate receipt
        receipt = await self._generate_receipt(payment.id, recorded_by)
        
        # Recalculate account
        await self.recalculate_account(invoice.account_id)
        
        await self.session.flush()
        
        return payment, receipt
    
    async def _generate_receipt(
        self,
        payment_id: UUID,
        generated_by: UUID,
    ) -> FeeReceipt:
        """Generate receipt for payment."""
        # Generate receipt number
        prefix = datetime.now().strftime("RCP%Y%m")
        query = select(func.count(FeeReceipt.id)).where(
            FeeReceipt.tenant_id == self.tenant_id,
            FeeReceipt.receipt_number.like(f"{prefix}%"),
        )
        count = await self.session.scalar(query) or 0
        receipt_number = f"{prefix}{count + 1:05d}"
        
        receipt = FeeReceipt(
            tenant_id=self.tenant_id,
            payment_id=payment_id,
            receipt_number=receipt_number,
            generated_at=datetime.now(),
            generated_by=generated_by,
        )
        self.session.add(receipt)
        await self.session.flush()
        
        return receipt
    
    async def get_payment(self, payment_id: UUID) -> Optional[FeePayment]:
        """Get payment by ID."""
        query = select(FeePayment).where(
            FeePayment.id == payment_id,
            FeePayment.tenant_id == self.tenant_id,
            FeePayment.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def reverse_payment(
        self,
        payment_id: UUID,
        reason: str,
    ) -> FeePayment:
        """Reverse a payment."""
        payment = await self.get_payment(payment_id)
        if not payment:
            raise ResourceNotFoundError("FeePayment", payment_id)
        
        if payment.is_reversed:
            raise ValidationError("Payment already reversed")
        
        payment.is_reversed = True
        payment.reversed_reason = reason
        
        # Update invoice
        invoice = await self.get_invoice(payment.invoice_id)
        if invoice:
            invoice.amount_paid -= payment.amount_paid
            invoice.balance_due = invoice.total_amount - invoice.amount_paid
            
            if invoice.balance_due > 0:
                if invoice.amount_paid > 0:
                    invoice.status = InvoiceStatus.PARTIAL
                else:
                    invoice.status = InvoiceStatus.PENDING
            
            await self.recalculate_account(invoice.account_id)
        
        await self.session.flush()
        return payment
    
    # ============================================
    # Reports
    # ============================================
    
    async def get_collection_report(
        self,
        start_date: date,
        end_date: date,
    ) -> CollectionReport:
        """Get fee collection report."""
        # Total collected
        query = select(
            func.sum(FeePayment.amount_paid).label("total"),
            func.count(FeePayment.id).label("count"),
        ).where(
            FeePayment.tenant_id == self.tenant_id,
            FeePayment.payment_date >= start_date,
            FeePayment.payment_date <= end_date,
            FeePayment.is_reversed == False,
            FeePayment.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        row = result.first()
        
        total = float(row.total or 0)
        count = int(row.count or 0)
        
        # By method
        method_query = select(
            FeePayment.method,
            func.sum(FeePayment.amount_paid).label("amount"),
        ).where(
            FeePayment.tenant_id == self.tenant_id,
            FeePayment.payment_date >= start_date,
            FeePayment.payment_date <= end_date,
            FeePayment.is_reversed == False,
            FeePayment.deleted_at.is_(None),
        ).group_by(FeePayment.method)
        
        method_result = await self.session.execute(method_query)
        by_method = {
            str(row.method.value): float(row.amount or 0)
            for row in method_result
        }
        
        return CollectionReport(
            period_start=start_date,
            period_end=end_date,
            total_collected=total,
            by_method=by_method,
            by_class=[],
            by_component=[],
            payment_count=count,
        )
    
    async def get_dues_report(
        self,
        academic_year_id: UUID,
    ) -> DuesReport:
        """Get outstanding dues report."""
        query = select(
            func.sum(StudentFeeAccount.balance).label("total_due"),
            func.count(StudentFeeAccount.id).label("count"),
        ).where(
            StudentFeeAccount.tenant_id == self.tenant_id,
            StudentFeeAccount.academic_year_id == academic_year_id,
            StudentFeeAccount.balance > 0,
            StudentFeeAccount.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        row = result.first()
        
        total_due = float(row.total_due or 0)
        count = int(row.count or 0)
        
        # Overdue
        overdue_query = select(
            func.sum(FeeInvoice.balance_due).label("overdue"),
            func.count(FeeInvoice.id).label("count"),
        ).where(
            FeeInvoice.tenant_id == self.tenant_id,
            FeeInvoice.status == InvoiceStatus.OVERDUE,
            FeeInvoice.deleted_at.is_(None),
        )
        overdue_result = await self.session.execute(overdue_query)
        overdue_row = overdue_result.first()
        
        total_overdue = float(overdue_row.overdue or 0)
        overdue_count = int(overdue_row.count or 0)
        
        return DuesReport(
            total_due=total_due,
            total_overdue=total_overdue,
            by_class=[],
            overdue_students=[],
            student_count=count,
            overdue_count=overdue_count,
        )
    
    # ============================================
    # Discounts
    # ============================================
    
    async def create_discount(
        self,
        data: FeeDiscountCreate,
    ) -> FeeDiscount:
        """Create a fee discount for a student."""
        discount = FeeDiscount(
            tenant_id=self.tenant_id,
            **data.model_dump(),
        )
        self.session.add(discount)
        await self.session.flush()
        return discount
    
    async def approve_discount(
        self,
        discount_id: UUID,
        approved_by: UUID,
    ) -> FeeDiscount:
        """Approve a discount."""
        query = select(FeeDiscount).where(
            FeeDiscount.id == discount_id,
            FeeDiscount.tenant_id == self.tenant_id,
            FeeDiscount.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        discount = result.scalar_one_or_none()
        
        if not discount:
            raise ResourceNotFoundError("FeeDiscount", discount_id)
        
        discount.is_approved = True
        discount.approved_by = approved_by
        discount.approved_at = datetime.now()
        
        # Apply discount to account
        account = await self.get_student_account(
            discount.student_id, discount.academic_year_id
        )
        if account:
            if discount.is_percentage:
                discount_amount = account.total_due * (discount.discount_value / 100)
            else:
                discount_amount = discount.discount_value
            
            account.total_discount += discount_amount
            account.balance = account.total_due - account.total_paid - account.total_discount
            
        await self.session.flush()
        return discount
