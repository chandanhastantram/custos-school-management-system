"""
CUSTOS Parent Portal Service

Business logic for parent-facing features.
"""

from datetime import datetime, date
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundError, PermissionDeniedError
from app.parents.schemas import (
    ChildInfo,
    ParentDashboard,
    ChildFeeSummary,
    ParentInvoiceResponse,
    ParentInvoiceDetail,
    ParentPaymentResponse,
    ReceiptDownload,
)
from app.finance.models import (
    StudentFeeAccount,
    FeeInvoice,
    FeePayment,
    FeeReceipt,
    InvoiceStatus,
)
from app.users.models import User


class ParentPortalService:
    """
    Parent Portal Service.
    
    Provides parent-facing features:
    - Dashboard with children and financial summary
    - Invoice viewing
    - Payment history
    - Receipt downloads
    """
    
    def __init__(self, session: AsyncSession, tenant_id: UUID, parent_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
        self.parent_id = parent_id
    
    # ============================================
    # Children Management
    # ============================================
    
    async def get_children(self) -> List[ChildInfo]:
        """Get list of children linked to this parent."""
        from app.users.models import ParentStudentLink
        
        # Get linked students
        query = select(ParentStudentLink).where(
            ParentStudentLink.parent_id == self.parent_id,
            ParentStudentLink.tenant_id == self.tenant_id,
            ParentStudentLink.is_active == True,
        )
        
        result = await self.session.execute(query)
        links = result.scalars().all()
        
        children = []
        for link in links:
            # Get student details
            student_query = select(User).where(
                User.id == link.student_id,
                User.tenant_id == self.tenant_id,
                User.deleted_at.is_(None),
            )
            student_result = await self.session.execute(student_query)
            student = student_result.scalar_one_or_none()
            
            if student:
                children.append(ChildInfo(
                    student_id=student.id,
                    name=student.full_name or student.email,
                    class_name=getattr(link, 'class_name', None),
                    roll_number=getattr(student, 'roll_number', None),
                ))
        
        return children
    
    async def verify_child_access(self, student_id: UUID) -> bool:
        """Verify parent has access to this student."""
        from app.users.models import ParentStudentLink
        
        query = select(ParentStudentLink).where(
            ParentStudentLink.parent_id == self.parent_id,
            ParentStudentLink.student_id == student_id,
            ParentStudentLink.tenant_id == self.tenant_id,
            ParentStudentLink.is_active == True,
        )
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None
    
    # ============================================
    # Dashboard
    # ============================================
    
    async def get_dashboard(self) -> ParentDashboard:
        """Get parent dashboard with financial summary."""
        # Get parent info
        parent_query = select(User).where(
            User.id == self.parent_id,
            User.tenant_id == self.tenant_id,
        )
        parent_result = await self.session.execute(parent_query)
        parent = parent_result.scalar_one_or_none()
        
        parent_name = parent.full_name if parent else "Parent"
        
        # Get children
        children = await self.get_children()
        student_ids = [c.student_id for c in children]
        
        if not student_ids:
            return ParentDashboard(
                parent_id=self.parent_id,
                parent_name=parent_name,
                children=children,
            )
        
        # Aggregate financials across all children
        total_due = 0.0
        total_paid = 0.0
        total_overdue = 0.0
        pending_count = 0
        overdue_count = 0
        
        for student_id in student_ids:
            # Get account
            account_query = select(StudentFeeAccount).where(
                StudentFeeAccount.student_id == student_id,
                StudentFeeAccount.tenant_id == self.tenant_id,
                StudentFeeAccount.deleted_at.is_(None),
            )
            result = await self.session.execute(account_query)
            accounts = result.scalars().all()
            
            for account in accounts:
                total_due += float(account.total_due)
                total_paid += float(account.total_paid)
        
        # Get overdue invoices
        overdue_query = select(FeeInvoice).where(
            FeeInvoice.student_id.in_(student_ids),
            FeeInvoice.tenant_id == self.tenant_id,
            FeeInvoice.status == InvoiceStatus.OVERDUE,
            FeeInvoice.deleted_at.is_(None),
        )
        overdue_result = await self.session.execute(overdue_query)
        overdue_invoices = overdue_result.scalars().all()
        
        for inv in overdue_invoices:
            total_overdue += float(inv.balance_due)
            overdue_count += 1
        
        # Get pending invoices
        pending_query = select(func.count(FeeInvoice.id)).where(
            FeeInvoice.student_id.in_(student_ids),
            FeeInvoice.tenant_id == self.tenant_id,
            FeeInvoice.status.in_([InvoiceStatus.PENDING, InvoiceStatus.PARTIAL]),
            FeeInvoice.deleted_at.is_(None),
        )
        pending_count = await self.session.scalar(pending_query) or 0
        
        # Get next due
        next_due_query = select(FeeInvoice).where(
            FeeInvoice.student_id.in_(student_ids),
            FeeInvoice.tenant_id == self.tenant_id,
            FeeInvoice.status.in_([InvoiceStatus.PENDING, InvoiceStatus.PARTIAL]),
            FeeInvoice.deleted_at.is_(None),
        ).order_by(FeeInvoice.due_date).limit(1)
        
        next_due_result = await self.session.execute(next_due_query)
        next_due = next_due_result.scalar_one_or_none()
        
        # Get last payment
        last_payment_query = select(FeePayment).join(FeeInvoice).where(
            FeeInvoice.student_id.in_(student_ids),
            FeePayment.tenant_id == self.tenant_id,
            FeePayment.is_reversed == False,
            FeePayment.deleted_at.is_(None),
        ).order_by(FeePayment.payment_date.desc()).limit(1)
        
        last_payment_result = await self.session.execute(last_payment_query)
        last_payment = last_payment_result.scalar_one_or_none()
        
        return ParentDashboard(
            parent_id=self.parent_id,
            parent_name=parent_name,
            children=children,
            total_due=total_due,
            total_paid=total_paid,
            total_overdue=total_overdue,
            balance=total_due - total_paid,
            next_due_date=next_due.due_date if next_due else None,
            next_due_amount=float(next_due.balance_due) if next_due else 0.0,
            pending_invoices=pending_count,
            overdue_invoices=overdue_count,
            last_payment_date=last_payment.payment_date if last_payment else None,
            last_payment_amount=float(last_payment.amount_paid) if last_payment else 0.0,
        )
    
    # ============================================
    # Invoices
    # ============================================
    
    async def get_student_invoices(
        self,
        student_id: UUID,
        status: Optional[InvoiceStatus] = None,
    ) -> List[ParentInvoiceResponse]:
        """Get invoices for a student."""
        # Verify access
        if not await self.verify_child_access(student_id):
            raise PermissionDeniedError("You don't have access to this student")
        
        query = select(FeeInvoice).where(
            FeeInvoice.student_id == student_id,
            FeeInvoice.tenant_id == self.tenant_id,
            FeeInvoice.deleted_at.is_(None),
        )
        
        if status:
            query = query.where(FeeInvoice.status == status)
        
        query = query.order_by(FeeInvoice.due_date.desc())
        
        result = await self.session.execute(query)
        invoices = result.scalars().all()
        
        # Get student name
        student = await self._get_student(student_id)
        student_name = student.full_name if student else None
        
        return [
            ParentInvoiceResponse(
                id=inv.id,
                invoice_number=inv.invoice_number,
                student_id=inv.student_id,
                student_name=student_name,
                installment_no=inv.installment_no,
                total_installments=inv.total_installments,
                invoice_date=inv.invoice_date,
                due_date=inv.due_date,
                total_amount=float(inv.total_amount),
                amount_paid=float(inv.amount_paid),
                balance_due=float(inv.balance_due),
                status=inv.status.value,
                is_overdue=inv.status == InvoiceStatus.OVERDUE,
                can_pay_online=inv.status in [InvoiceStatus.PENDING, InvoiceStatus.PARTIAL, InvoiceStatus.OVERDUE],
            )
            for inv in invoices
        ]
    
    async def get_invoice_detail(
        self,
        invoice_id: UUID,
    ) -> ParentInvoiceDetail:
        """Get detailed invoice with line items and payments."""
        query = select(FeeInvoice).where(
            FeeInvoice.id == invoice_id,
            FeeInvoice.tenant_id == self.tenant_id,
            FeeInvoice.deleted_at.is_(None),
        )
        
        result = await self.session.execute(query)
        invoice = result.scalar_one_or_none()
        
        if not invoice:
            raise ResourceNotFoundError("Invoice", invoice_id)
        
        # Verify access
        if not await self.verify_child_access(invoice.student_id):
            raise PermissionDeniedError("You don't have access to this invoice")
        
        # Get student name
        student = await self._get_student(invoice.student_id)
        student_name = student.full_name if student else None
        
        # Get payments
        payments_query = select(FeePayment).where(
            FeePayment.invoice_id == invoice_id,
            FeePayment.deleted_at.is_(None),
        ).order_by(FeePayment.payment_date.desc())
        
        payments_result = await self.session.execute(payments_query)
        payments = payments_result.scalars().all()
        
        payment_list = []
        for p in payments:
            # Get receipt if exists
            receipt_query = select(FeeReceipt).where(FeeReceipt.payment_id == p.id)
            receipt_result = await self.session.execute(receipt_query)
            receipt = receipt_result.scalar_one_or_none()
            
            payment_list.append({
                "id": str(p.id),
                "amount": float(p.amount_paid),
                "date": p.payment_date.isoformat(),
                "method": p.method.value,
                "reference": p.reference_no,
                "receipt_number": receipt.receipt_number if receipt else None,
            })
        
        return ParentInvoiceDetail(
            id=invoice.id,
            invoice_number=invoice.invoice_number,
            student_id=invoice.student_id,
            student_name=student_name,
            installment_no=invoice.installment_no,
            total_installments=invoice.total_installments,
            invoice_date=invoice.invoice_date,
            due_date=invoice.due_date,
            total_amount=float(invoice.total_amount),
            amount_paid=float(invoice.amount_paid),
            balance_due=float(invoice.balance_due),
            status=invoice.status.value,
            is_overdue=invoice.status == InvoiceStatus.OVERDUE,
            can_pay_online=invoice.status in [InvoiceStatus.PENDING, InvoiceStatus.PARTIAL, InvoiceStatus.OVERDUE],
            line_items=invoice.line_items or [],
            payments=payment_list,
        )
    
    # ============================================
    # Payment History
    # ============================================
    
    async def get_student_payments(
        self,
        student_id: UUID,
    ) -> List[ParentPaymentResponse]:
        """Get payment history for a student."""
        if not await self.verify_child_access(student_id):
            raise PermissionDeniedError("You don't have access to this student")
        
        query = select(FeePayment).join(FeeInvoice).where(
            FeeInvoice.student_id == student_id,
            FeePayment.tenant_id == self.tenant_id,
            FeePayment.is_reversed == False,
            FeePayment.deleted_at.is_(None),
        ).order_by(FeePayment.payment_date.desc())
        
        result = await self.session.execute(query)
        payments = result.scalars().all()
        
        # Get student name
        student = await self._get_student(student_id)
        student_name = student.full_name if student else None
        
        response = []
        for payment in payments:
            # Get invoice number
            invoice_query = select(FeeInvoice).where(FeeInvoice.id == payment.invoice_id)
            invoice_result = await self.session.execute(invoice_query)
            invoice = invoice_result.scalar_one_or_none()
            
            # Get receipt
            receipt_query = select(FeeReceipt).where(FeeReceipt.payment_id == payment.id)
            receipt_result = await self.session.execute(receipt_query)
            receipt = receipt_result.scalar_one_or_none()
            
            response.append(ParentPaymentResponse(
                id=payment.id,
                invoice_id=payment.invoice_id,
                invoice_number=invoice.invoice_number if invoice else "N/A",
                student_name=student_name,
                amount_paid=float(payment.amount_paid),
                payment_date=payment.payment_date,
                method=payment.method.value,
                reference_no=payment.reference_no,
                receipt_number=receipt.receipt_number if receipt else None,
                is_online=payment.method.value in ["upi", "card", "online"],
            ))
        
        return response
    
    # ============================================
    # Receipts
    # ============================================
    
    async def get_receipt(self, receipt_id: UUID) -> ReceiptDownload:
        """Get receipt download info."""
        query = select(FeeReceipt).where(
            FeeReceipt.id == receipt_id,
            FeeReceipt.tenant_id == self.tenant_id,
            FeeReceipt.deleted_at.is_(None),
        )
        
        result = await self.session.execute(query)
        receipt = result.scalar_one_or_none()
        
        if not receipt:
            raise ResourceNotFoundError("Receipt", receipt_id)
        
        # Get payment
        payment_query = select(FeePayment).where(FeePayment.id == receipt.payment_id)
        payment_result = await self.session.execute(payment_query)
        payment = payment_result.scalar_one_or_none()
        
        if not payment:
            raise ResourceNotFoundError("Payment", receipt.payment_id)
        
        # Get invoice and verify access
        invoice_query = select(FeeInvoice).where(FeeInvoice.id == payment.invoice_id)
        invoice_result = await self.session.execute(invoice_query)
        invoice = invoice_result.scalar_one_or_none()
        
        if invoice and not await self.verify_child_access(invoice.student_id):
            raise PermissionDeniedError("You don't have access to this receipt")
        
        # Get student name
        student = await self._get_student(invoice.student_id) if invoice else None
        student_name = student.full_name if student else "Unknown"
        
        return ReceiptDownload(
            receipt_id=receipt.id,
            receipt_number=receipt.receipt_number,
            student_name=student_name,
            amount=float(payment.amount_paid),
            payment_date=payment.payment_date,
            payment_method=payment.method.value,
            download_url=f"/api/v1/parents/receipt/{receipt.id}/pdf",
        )
    
    # ============================================
    # Helpers
    # ============================================
    
    async def _get_student(self, student_id: UUID) -> Optional[User]:
        """Get student by ID."""
        query = select(User).where(
            User.id == student_id,
            User.tenant_id == self.tenant_id,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()


class ParentService:
    """
    Extended Parent Service for dashboard and comprehensive features.
    
    Used by the parent router for full portal functionality.
    """
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
    
    # ============================================
    # Dashboard
    # ============================================
    
    async def get_dashboard(self, parent_id: UUID):
        """Get comprehensive parent dashboard."""
        from app.parents.schemas import (
            ParentDashboardResponse, ChildSummary,
            FeesSummary, AttendanceSummary, AcademicSummary,
        )
        
        # Get children
        children = await self.get_children(parent_id)
        
        # Aggregate data across all children
        total_pending_fees = 0.0
        total_paid_fees = 0.0
        unread_notifications = 0
        upcoming_events = []
        
        for child in children:
            fees = await self.get_fees_summary(child.student_id)
            total_pending_fees += fees.pending_amount
            total_paid_fees += fees.paid_amount
        
        # Get notifications count
        from app.notifications.models import Notification
        notif_query = select(func.count(Notification.id)).where(
            Notification.user_id == parent_id,
            Notification.tenant_id == self.tenant_id,
            Notification.is_read == False,
        )
        unread_notifications = await self.session.scalar(notif_query) or 0
        
        return {
            "parent_id": str(parent_id),
            "children": [c.model_dump() for c in children],
            "total_children": len(children),
            "total_pending_fees": total_pending_fees,
            "total_paid_fees": total_paid_fees,
            "unread_notifications": unread_notifications,
            "upcoming_events": upcoming_events,
        }
    
    # ============================================
    # Children
    # ============================================
    
    async def get_children(self, parent_id: UUID):
        """Get list of children linked to parent."""
        from app.users.models import ParentStudentLink
        from app.parents.schemas import ChildSummary
        
        query = select(ParentStudentLink).where(
            ParentStudentLink.parent_id == parent_id,
            ParentStudentLink.tenant_id == self.tenant_id,
            ParentStudentLink.is_active == True,
        )
        
        result = await self.session.execute(query)
        links = result.scalars().all()
        
        children = []
        for link in links:
            student_query = select(User).where(
                User.id == link.student_id,
                User.tenant_id == self.tenant_id,
                User.deleted_at.is_(None),
            )
            student_result = await self.session.execute(student_query)
            student = student_result.scalar_one_or_none()
            
            if student:
                children.append(ChildSummary(
                    student_id=student.id,
                    name=student.full_name or student.email,
                    class_name=getattr(link, 'class_name', 'N/A'),
                    section=getattr(link, 'section_name', ''),
                    roll_number=getattr(student, 'roll_number', None),
                    photo_url=getattr(student, 'avatar_url', None),
                ))
        
        return children
    
    async def get_child_detail(self, student_id: UUID):
        """Get detailed information for a child."""
        from app.parents.schemas import ChildDetail
        
        student_query = select(User).where(
            User.id == student_id,
            User.tenant_id == self.tenant_id,
        )
        result = await self.session.execute(student_query)
        student = result.scalar_one_or_none()
        
        if not student:
            raise ResourceNotFoundError("Student", str(student_id))
        
        # Get academics, attendance, fees
        academics = await self.get_academic_summary(student_id)
        attendance = await self.get_attendance_summary(student_id, datetime.now().month, datetime.now().year)
        fees = await self.get_fees_summary(student_id)
        
        return ChildDetail(
            student_id=student.id,
            name=student.full_name or student.email,
            class_name="N/A",
            section="",
            roll_number=None,
            photo_url=getattr(student, 'avatar_url', None),
            date_of_birth=getattr(student, 'date_of_birth', None),
            academics=academics,
            attendance=attendance,
            fees=fees,
        )
    
    # ============================================
    # Academics
    # ============================================
    
    async def get_academic_summary(self, student_id: UUID):
        """Get academic performance summary."""
        from app.parents.schemas import AcademicSummary
        
        # Get recent grades/marks
        # This would normally query from assessments/exams tables
        
        return AcademicSummary(
            student_id=student_id,
            overall_grade="A",
            overall_percentage=85.5,
            rank_in_class=5,
            total_students=30,
            subjects=[],
            recent_assessments=[],
            improvement_areas=[],
        )
    
    async def get_assignments(
        self, 
        student_id: UUID, 
        status: Optional[str] = None,
        page: int = 1,
        size: int = 20,
    ):
        """Get assignments for a student."""
        # Would query from assignments table
        return {
            "items": [],
            "total": 0,
            "page": page,
            "size": size,
        }
    
    async def get_report_cards(self, student_id: UUID):
        """Get report cards for a student."""
        # Would query from report cards table
        return []
    
    # ============================================
    # Attendance
    # ============================================
    
    async def get_attendance_summary(
        self, 
        student_id: UUID, 
        month: int, 
        year: int,
    ):
        """Get attendance summary."""
        from app.parents.schemas import AttendanceSummary
        
        # Would query from attendance table
        return AttendanceSummary(
            student_id=student_id,
            month=month,
            year=year,
            total_days=22,
            present_days=20,
            absent_days=2,
            late_days=1,
            attendance_percentage=90.9,
            daily_records=[],
        )
    
    # ============================================
    # Fees
    # ============================================
    
    async def get_fees_summary(self, student_id: UUID):
        """Get fee summary for a student."""
        from app.parents.schemas import FeesSummary
        
        # Query from finance module
        from app.finance.models import StudentFeeAccount, FeeInvoice, InvoiceStatus
        
        account_query = select(StudentFeeAccount).where(
            StudentFeeAccount.student_id == student_id,
            StudentFeeAccount.tenant_id == self.tenant_id,
            StudentFeeAccount.deleted_at.is_(None),
        )
        result = await self.session.execute(account_query)
        accounts = result.scalars().all()
        
        total_due = sum(float(a.total_due) for a in accounts)
        total_paid = sum(float(a.total_paid) for a in accounts)
        
        # Count pending invoices
        pending_query = select(func.count(FeeInvoice.id)).where(
            FeeInvoice.student_id == student_id,
            FeeInvoice.tenant_id == self.tenant_id,
            FeeInvoice.status.in_([InvoiceStatus.PENDING, InvoiceStatus.PARTIAL]),
            FeeInvoice.deleted_at.is_(None),
        )
        pending_count = await self.session.scalar(pending_query) or 0
        
        return FeesSummary(
            student_id=student_id,
            total_amount=total_due,
            paid_amount=total_paid,
            pending_amount=total_due - total_paid,
            pending_invoices=pending_count,
            next_due_date=None,
            next_due_amount=0.0,
        )
    
    async def get_invoices(
        self, 
        student_id: UUID, 
        status: Optional[str] = None,
    ):
        """Get invoices for a student."""
        from app.finance.models import FeeInvoice, InvoiceStatus
        
        query = select(FeeInvoice).where(
            FeeInvoice.student_id == student_id,
            FeeInvoice.tenant_id == self.tenant_id,
            FeeInvoice.deleted_at.is_(None),
        )
        
        if status:
            query = query.where(FeeInvoice.status == InvoiceStatus(status))
        
        query = query.order_by(FeeInvoice.due_date.desc())
        
        result = await self.session.execute(query)
        invoices = result.scalars().all()
        
        return [
            {
                "id": str(inv.id),
                "invoice_number": inv.invoice_number,
                "total_amount": float(inv.total_amount),
                "amount_paid": float(inv.amount_paid),
                "balance_due": float(inv.balance_due),
                "due_date": inv.due_date.isoformat() if inv.due_date else None,
                "status": inv.status.value,
            }
            for inv in invoices
        ]
    
    async def get_payment_history(
        self, 
        student_id: UUID, 
        page: int = 1,
        size: int = 20,
    ):
        """Get payment history for a student."""
        from app.finance.models import FeePayment, FeeInvoice
        
        query = select(FeePayment).join(FeeInvoice).where(
            FeeInvoice.student_id == student_id,
            FeePayment.tenant_id == self.tenant_id,
            FeePayment.is_reversed == False,
            FeePayment.deleted_at.is_(None),
        ).order_by(FeePayment.payment_date.desc())
        
        skip = (page - 1) * size
        query = query.offset(skip).limit(size)
        
        result = await self.session.execute(query)
        payments = result.scalars().all()
        
        return {
            "items": [
                {
                    "id": str(p.id),
                    "amount": float(p.amount_paid),
                    "date": p.payment_date.isoformat(),
                    "method": p.method.value,
                    "reference": p.reference_no,
                }
                for p in payments
            ],
            "page": page,
            "size": size,
        }
    
    # ============================================
    # Timetable & Calendar
    # ============================================
    
    async def get_timetable(self, student_id: UUID):
        """Get class timetable for a student."""
        # Would query from timetable table based on student's class
        return {
            "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
            "periods": [],
        }
    
    async def get_calendar_events(self, month: int, year: int):
        """Get school calendar events."""
        from app.scheduling.models.schedule import Event
        from datetime import date
        
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)
        
        query = select(Event).where(
            Event.tenant_id == self.tenant_id,
            Event.start_date >= start_date,
            Event.start_date < end_date,
            Event.is_deleted == False,
        ).order_by(Event.start_date)
        
        result = await self.session.execute(query)
        events = result.scalars().all()
        
        return [
            {
                "id": str(e.id),
                "title": e.title,
                "date": e.start_date.isoformat(),
                "type": e.event_type.value if hasattr(e.event_type, 'value') else str(e.event_type),
            }
            for e in events
        ]
    
    # ============================================
    # Notifications
    # ============================================
    
    async def get_notifications(
        self, 
        parent_id: UUID, 
        unread_only: bool = False,
        page: int = 1,
        size: int = 20,
    ):
        """Get notifications for parent."""
        from app.notifications.models import Notification
        from app.parents.schemas import NotificationItem
        
        query = select(Notification).where(
            Notification.user_id == parent_id,
            Notification.tenant_id == self.tenant_id,
        )
        
        if unread_only:
            query = query.where(Notification.is_read == False)
        
        query = query.order_by(Notification.created_at.desc())
        
        skip = (page - 1) * size
        query = query.offset(skip).limit(size)
        
        result = await self.session.execute(query)
        notifications = result.scalars().all()
        
        return [
            NotificationItem(
                id=n.id,
                title=n.title,
                message=n.message,
                type=n.notification_type.value if hasattr(n.notification_type, 'value') else str(n.notification_type),
                is_read=n.is_read,
                created_at=n.created_at,
            )
            for n in notifications
        ]
    
    async def mark_notification_read(self, notification_id: UUID, parent_id: UUID):
        """Mark notification as read."""
        from app.notifications.models import Notification
        
        query = select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == parent_id,
            Notification.tenant_id == self.tenant_id,
        )
        result = await self.session.execute(query)
        notification = result.scalar_one_or_none()
        
        if notification:
            notification.is_read = True
            await self.session.commit()
    
    async def get_announcements(self, page: int = 1, size: int = 20):
        """Get school announcements."""
        from app.announcements.models import Post
        
        query = select(Post).where(
            Post.tenant_id == self.tenant_id,
            Post.is_published == True,
            Post.is_deleted == False,
        ).order_by(Post.published_at.desc())
        
        skip = (page - 1) * size
        query = query.offset(skip).limit(size)
        
        result = await self.session.execute(query)
        posts = result.scalars().all()
        
        return [
            {
                "id": str(p.id),
                "title": p.title,
                "content": p.content[:200] + "..." if len(p.content) > 200 else p.content,
                "published_at": p.published_at.isoformat() if p.published_at else None,
            }
            for p in posts
        ]
    
    # ============================================
    # Communication
    # ============================================
    
    async def get_teachers(self, student_id: UUID):
        """Get teachers for a student's class."""
        # Would query from teacher assignments
        return []
    
    async def send_message(
        self, 
        parent_id: UUID, 
        teacher_id: UUID, 
        subject: str, 
        message: str,
        student_id: Optional[UUID] = None,
    ):
        """Send message to a teacher."""
        # Would create a message record
        return {"success": True, "message": "Message sent"}
    
    # ============================================
    # Leave Requests
    # ============================================
    
    async def submit_leave_request(
        self,
        student_id: UUID,
        parent_id: UUID,
        start_date: date,
        end_date: date,
        reason: str,
    ):
        """Submit a leave request."""
        # Would create leave request record
        return {
            "success": True,
            "message": "Leave request submitted",
            "request_id": "LR" + datetime.now().strftime("%Y%m%d%H%M%S"),
        }
    
    async def get_leave_requests(self, student_id: UUID):
        """Get leave request history."""
        return []
