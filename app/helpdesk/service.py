"""
CUSTOS Helpdesk Service

Business logic for tickets, applications, and student services.
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, List, Tuple
from uuid import UUID, uuid4

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.helpdesk.models import (
    HelpdeskTicket, TicketComment, StudentApplication,
    TranscriptApplication, GraceMarkApplication, GraceMarkRedistribution,
    HelpdeskFAQ, HelpdeskCategory, TicketStatus, TicketPriority,
    ApplicationStatus, ApplicationType, TranscriptType
)
from app.helpdesk.schemas import (
    TicketCreate, TicketUpdate, TicketCommentCreate,
    TranscriptApplicationCreate, GraceMarkApplicationCreate,
    GraceRedistributionCreate, FAQCreate, FAQUpdate
)
from app.core.exceptions import NotFoundError, ValidationError, ForbiddenError

logger = logging.getLogger(__name__)


# SLA hours by priority
SLA_HOURS = {
    TicketPriority.LOW: 72,
    TicketPriority.MEDIUM: 48,
    TicketPriority.HIGH: 24,
    TicketPriority.URGENT: 4,
}

# Fee amounts by application type
APPLICATION_FEES = {
    ApplicationType.TRANSCRIPT: Decimal("200.00"),
    ApplicationType.GRACE_MARK: Decimal("0.00"),
    ApplicationType.GRACE_REDISTRIBUTION: Decimal("100.00"),
    ApplicationType.BONAFIDE: Decimal("50.00"),
    ApplicationType.CHARACTER_CERTIFICATE: Decimal("100.00"),
    ApplicationType.MIGRATION: Decimal("500.00"),
    ApplicationType.DUPLICATE_DOCUMENTS: Decimal("300.00"),
}


class HelpdeskService:
    """Service for helpdesk operations."""
    
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
    
    # ============================================
    # Ticket Operations
    # ============================================
    
    async def create_ticket(self, data: TicketCreate, created_by: UUID) -> HelpdeskTicket:
        """Create a new support ticket."""
        # Calculate SLA due date
        sla_hours = SLA_HOURS.get(data.priority, 48)
        sla_due_date = datetime.utcnow() + timedelta(hours=sla_hours)
        
        ticket = HelpdeskTicket(
            tenant_id=self.tenant_id,
            ticket_number=self._generate_ticket_number(),
            category=data.category,
            priority=data.priority,
            status=TicketStatus.OPEN,
            subject=data.subject,
            description=data.description,
            created_by=created_by,
            sla_due_date=sla_due_date,
            attachments=[a.model_dump() for a in data.attachments] if data.attachments else None,
        )
        
        self.db.add(ticket)
        await self.db.commit()
        await self.db.refresh(ticket)
        
        logger.info(f"Created ticket {ticket.ticket_number} for tenant {self.tenant_id}")
        return ticket
    
    async def get_ticket(self, ticket_id: UUID) -> Optional[HelpdeskTicket]:
        """Get ticket by ID."""
        result = await self.db.execute(
            select(HelpdeskTicket)
            .options(selectinload(HelpdeskTicket.comments))
            .where(
                HelpdeskTicket.id == ticket_id,
                HelpdeskTicket.tenant_id == self.tenant_id,
                HelpdeskTicket.is_deleted == False
            )
        )
        return result.scalar_one_or_none()
    
    async def list_tickets(
        self,
        user_id: Optional[UUID] = None,
        category: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        assigned_to: Optional[UUID] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[HelpdeskTicket], int]:
        """List tickets with filters."""
        query = select(HelpdeskTicket).where(
            HelpdeskTicket.tenant_id == self.tenant_id,
            HelpdeskTicket.is_deleted == False
        )
        
        if user_id:
            query = query.where(HelpdeskTicket.created_by == user_id)
        if category:
            query = query.where(HelpdeskTicket.category == category)
        if status:
            query = query.where(HelpdeskTicket.status == status)
        if priority:
            query = query.where(HelpdeskTicket.priority == priority)
        if assigned_to:
            query = query.where(HelpdeskTicket.assigned_to == assigned_to)
        
        # Count
        count_result = await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar()
        
        # Paginate
        query = query.order_by(HelpdeskTicket.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.db.execute(query)
        return result.scalars().all(), total
    
    async def update_ticket(
        self,
        ticket_id: UUID,
        data: TicketUpdate,
        updated_by: UUID
    ) -> HelpdeskTicket:
        """Update a ticket."""
        ticket = await self.get_ticket(ticket_id)
        if not ticket:
            raise NotFoundError("Ticket not found")
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(ticket, key, value)
        
        await self.db.commit()
        await self.db.refresh(ticket)
        return ticket
    
    async def assign_ticket(
        self,
        ticket_id: UUID,
        assigned_to: UUID,
        assigned_by: UUID
    ) -> HelpdeskTicket:
        """Assign ticket to a user."""
        ticket = await self.get_ticket(ticket_id)
        if not ticket:
            raise NotFoundError("Ticket not found")
        
        ticket.assigned_to = assigned_to
        ticket.assigned_at = datetime.utcnow()
        ticket.status = TicketStatus.IN_PROGRESS
        
        # Add system comment
        comment = TicketComment(
            tenant_id=self.tenant_id,
            ticket_id=ticket_id,
            content=f"Ticket assigned to staff member",
            author_id=assigned_by,
            is_system=True,
        )
        self.db.add(comment)
        
        await self.db.commit()
        await self.db.refresh(ticket)
        return ticket
    
    async def resolve_ticket(
        self,
        ticket_id: UUID,
        resolution_notes: str,
        resolved_by: UUID
    ) -> HelpdeskTicket:
        """Resolve a ticket."""
        ticket = await self.get_ticket(ticket_id)
        if not ticket:
            raise NotFoundError("Ticket not found")
        
        ticket.status = TicketStatus.RESOLVED
        ticket.resolution_notes = resolution_notes
        ticket.resolved_by = resolved_by
        ticket.resolved_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(ticket)
        return ticket
    
    async def add_comment(
        self,
        ticket_id: UUID,
        data: TicketCommentCreate,
        author_id: UUID
    ) -> TicketComment:
        """Add comment to ticket."""
        ticket = await self.get_ticket(ticket_id)
        if not ticket:
            raise NotFoundError("Ticket not found")
        
        comment = TicketComment(
            tenant_id=self.tenant_id,
            ticket_id=ticket_id,
            content=data.content,
            author_id=author_id,
            is_internal=data.is_internal,
            attachments=[a.model_dump() for a in data.attachments] if data.attachments else None,
        )
        
        self.db.add(comment)
        await self.db.commit()
        await self.db.refresh(comment)
        return comment
    
    # ============================================
    # Transcript Applications
    # ============================================
    
    async def apply_for_transcript(
        self,
        data: TranscriptApplicationCreate,
        student_id: UUID
    ) -> TranscriptApplication:
        """Apply for academic transcript."""
        # Calculate fee
        base_fee = APPLICATION_FEES.get(ApplicationType.TRANSCRIPT, Decimal("200.00"))
        total_fee = base_fee * data.num_copies
        
        if data.delivery_mode == "post":
            total_fee += Decimal("50.00")  # Postal charges
        
        # Create base application
        application = StudentApplication(
            tenant_id=self.tenant_id,
            application_number=self._generate_application_number("TR"),
            application_type=ApplicationType.TRANSCRIPT,
            status=ApplicationStatus.SUBMITTED,
            student_id=student_id,
            purpose=data.purpose,
            fee_amount=total_fee,
            delivery_mode=data.delivery_mode,
        )
        self.db.add(application)
        await self.db.flush()
        
        # Create transcript-specific record
        transcript = TranscriptApplication(
            tenant_id=self.tenant_id,
            application_id=application.id,
            student_id=student_id,
            transcript_type=data.transcript_type,
            num_copies=data.num_copies,
            from_semester=data.from_semester,
            to_semester=data.to_semester,
            delivery_address=data.delivery_address,
        )
        self.db.add(transcript)
        
        await self.db.commit()
        await self.db.refresh(transcript)
        
        logger.info(f"Created transcript application {application.application_number}")
        return transcript
    
    async def get_transcript_applications(
        self,
        student_id: Optional[UUID] = None,
        status: Optional[str] = None
    ) -> List[TranscriptApplication]:
        """Get transcript applications."""
        query = select(TranscriptApplication).where(
            TranscriptApplication.tenant_id == self.tenant_id,
        )
        
        if student_id:
            query = query.where(TranscriptApplication.student_id == student_id)
        
        result = await self.db.execute(
            query.order_by(TranscriptApplication.created_at.desc())
        )
        return result.scalars().all()
    
    # ============================================
    # Grace Mark Applications
    # ============================================
    
    async def apply_for_grace_marks(
        self,
        data: GraceMarkApplicationCreate,
        student_id: UUID
    ) -> GraceMarkApplication:
        """Apply for grace marks."""
        # Create base application
        application = StudentApplication(
            tenant_id=self.tenant_id,
            application_number=self._generate_application_number("GM"),
            application_type=ApplicationType.GRACE_MARK,
            status=ApplicationStatus.SUBMITTED,
            student_id=student_id,
            fee_amount=Decimal("0.00"),
            supporting_documents=[d.model_dump() for d in data.supporting_documents] if data.supporting_documents else None,
        )
        self.db.add(application)
        await self.db.flush()
        
        # Create grace mark specific record
        grace_app = GraceMarkApplication(
            tenant_id=self.tenant_id,
            application_id=application.id,
            student_id=student_id,
            exam_id=data.exam_id,
            subject_id=data.subject_id,
            category=data.category,
            activity_name=data.activity_name,
            activity_date=data.activity_date,
            activity_level=data.activity_level,
            achievement=data.achievement,
            requested_marks=data.requested_marks,
        )
        self.db.add(grace_app)
        
        await self.db.commit()
        await self.db.refresh(grace_app)
        
        logger.info(f"Created grace mark application {application.application_number}")
        return grace_app
    
    async def get_grace_mark_applications(
        self,
        student_id: Optional[UUID] = None,
        exam_id: Optional[UUID] = None,
        status: Optional[str] = None
    ) -> List[GraceMarkApplication]:
        """Get grace mark applications."""
        query = select(GraceMarkApplication).where(
            GraceMarkApplication.tenant_id == self.tenant_id,
        )
        
        if student_id:
            query = query.where(GraceMarkApplication.student_id == student_id)
        if exam_id:
            query = query.where(GraceMarkApplication.exam_id == exam_id)
        
        result = await self.db.execute(
            query.order_by(GraceMarkApplication.created_at.desc())
        )
        return result.scalars().all()
    
    async def review_grace_mark(
        self,
        application_id: UUID,
        approved_marks: int,
        status: ApplicationStatus,
        remarks: Optional[str],
        reviewed_by: UUID
    ) -> GraceMarkApplication:
        """Review grace mark application."""
        result = await self.db.execute(
            select(GraceMarkApplication).where(
                GraceMarkApplication.id == application_id,
                GraceMarkApplication.tenant_id == self.tenant_id,
            )
        )
        app = result.scalar_one_or_none()
        
        if not app:
            raise NotFoundError("Application not found")
        
        app.approved_marks = approved_marks
        app.verified_by = reviewed_by
        app.verification_remarks = remarks
        
        # Update base application
        base_app_result = await self.db.execute(
            select(StudentApplication).where(
                StudentApplication.id == app.application_id,
            )
        )
        base_app = base_app_result.scalar_one_or_none()
        if base_app:
            base_app.status = status
            base_app.reviewed_by = reviewed_by
            base_app.reviewed_at = datetime.utcnow()
            base_app.review_remarks = remarks
        
        await self.db.commit()
        await self.db.refresh(app)
        return app
    
    # ============================================
    # Grace Mark Redistribution
    # ============================================
    
    async def apply_for_redistribution(
        self,
        data: GraceRedistributionCreate,
        student_id: UUID
    ) -> GraceMarkRedistribution:
        """Apply for grace mark redistribution."""
        # Validate original application
        original = await self.db.execute(
            select(GraceMarkApplication).where(
                GraceMarkApplication.id == data.original_application_id,
                GraceMarkApplication.student_id == student_id,
                GraceMarkApplication.tenant_id == self.tenant_id,
            )
        )
        original_app = original.scalar_one_or_none()
        
        if not original_app:
            raise NotFoundError("Original grace mark application not found")
        
        if not original_app.approved_marks:
            raise ValidationError("No approved marks to redistribute")
        
        # Validate total marks
        total_marks = sum(item.marks for item in data.distribution)
        if total_marks > original_app.approved_marks:
            raise ValidationError(
                f"Total redistribution marks ({total_marks}) exceed approved marks ({original_app.approved_marks})"
            )
        
        # Create base application
        application = StudentApplication(
            tenant_id=self.tenant_id,
            application_number=self._generate_application_number("GR"),
            application_type=ApplicationType.GRACE_REDISTRIBUTION,
            status=ApplicationStatus.SUBMITTED,
            student_id=student_id,
            fee_amount=APPLICATION_FEES.get(ApplicationType.GRACE_REDISTRIBUTION, Decimal("100.00")),
        )
        self.db.add(application)
        await self.db.flush()
        
        # Create redistribution record
        redistribution = GraceMarkRedistribution(
            tenant_id=self.tenant_id,
            application_id=application.id,
            student_id=student_id,
            original_application_id=data.original_application_id,
            distribution=[item.model_dump() for item in data.distribution],
            total_marks=total_marks,
            reason=data.reason,
        )
        self.db.add(redistribution)
        
        await self.db.commit()
        await self.db.refresh(redistribution)
        return redistribution
    
    # ============================================
    # FAQ Operations
    # ============================================
    
    async def create_faq(self, data: FAQCreate) -> HelpdeskFAQ:
        """Create a new FAQ."""
        faq = HelpdeskFAQ(
            tenant_id=self.tenant_id,
            category=data.category,
            question=data.question,
            answer=data.answer,
            display_order=data.display_order,
        )
        self.db.add(faq)
        await self.db.commit()
        await self.db.refresh(faq)
        return faq
    
    async def list_faqs(
        self,
        category: Optional[str] = None,
        published_only: bool = True
    ) -> List[HelpdeskFAQ]:
        """List FAQs."""
        query = select(HelpdeskFAQ).where(
            HelpdeskFAQ.tenant_id == self.tenant_id,
            HelpdeskFAQ.is_deleted == False,
        )
        
        if published_only:
            query = query.where(HelpdeskFAQ.is_published == True)
        if category:
            query = query.where(HelpdeskFAQ.category == category)
        
        result = await self.db.execute(
            query.order_by(HelpdeskFAQ.display_order, HelpdeskFAQ.created_at)
        )
        return result.scalars().all()
    
    async def record_faq_feedback(
        self,
        faq_id: UUID,
        helpful: bool
    ) -> HelpdeskFAQ:
        """Record FAQ feedback."""
        result = await self.db.execute(
            select(HelpdeskFAQ).where(
                HelpdeskFAQ.id == faq_id,
                HelpdeskFAQ.tenant_id == self.tenant_id,
            )
        )
        faq = result.scalar_one_or_none()
        
        if not faq:
            raise NotFoundError("FAQ not found")
        
        if helpful:
            faq.helpful_count += 1
        else:
            faq.not_helpful_count += 1
        
        await self.db.commit()
        await self.db.refresh(faq)
        return faq
    
    # ============================================
    # Helpers
    # ============================================
    
    def _generate_ticket_number(self) -> str:
        """Generate unique ticket number."""
        timestamp = datetime.utcnow().strftime("%Y%m%d")
        random_part = str(uuid4())[:6].upper()
        return f"TKT-{timestamp}-{random_part}"
    
    def _generate_application_number(self, prefix: str) -> str:
        """Generate application number."""
        timestamp = datetime.utcnow().strftime("%Y%m%d")
        random_part = str(uuid4())[:6].upper()
        return f"{prefix}-{timestamp}-{random_part}"
