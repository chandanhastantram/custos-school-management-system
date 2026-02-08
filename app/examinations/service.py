"""
CUSTOS Examinations Service

Business logic for exam registration, hall tickets, and results.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Tuple
from uuid import UUID, uuid4

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.examinations.models import (
    Exam, ExamSubject, ExamRegistration, HallTicket,
    AnswerBooklet, RevaluationApplication, MakeupBacklogRegistration,
    ExamResult, SemesterResult, ExamStatus, RegistrationStatus,
    HallTicketStatus, RevaluationStatus, ResultStatus
)
from app.examinations.schemas import (
    ExamCreate, ExamUpdate, ExamRegistrationCreate,
    HallTicketGenerateRequest, RevaluationApplyRequest,
    MakeupBacklogRegisterRequest, ExamResultCreate,
    RegistrationEligibilityCheck, AnswerBookletGenerateRequest
)
from app.core.exceptions import (
    NotFoundError, ValidationError, ForbiddenError, ConflictError
)

logger = logging.getLogger(__name__)


class ExaminationService:
    """Service for examination management."""
    
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
    
    # ============================================
    # Exam CRUD
    # ============================================
    
    async def create_exam(self, data: ExamCreate, created_by: UUID) -> Exam:
        """Create a new exam."""
        exam = Exam(
            tenant_id=self.tenant_id,
            name=data.name,
            code=data.code,
            description=data.description,
            exam_type=data.exam_type,
            academic_year_id=data.academic_year_id,
            semester=data.semester,
            registration_start=data.registration_start,
            registration_end=data.registration_end,
            late_registration_end=data.late_registration_end,
            late_fee=data.late_fee,
            exam_start_date=data.exam_start_date,
            exam_end_date=data.exam_end_date,
            min_attendance_percentage=data.min_attendance_percentage,
            require_fee_clearance=data.require_fee_clearance,
            exam_fee_per_subject=data.exam_fee_per_subject,
            status=ExamStatus.DRAFT,
        )
        self.db.add(exam)
        await self.db.flush()
        
        # Add subjects if provided
        if data.subjects:
            for subj_data in data.subjects:
                exam_subject = ExamSubject(
                    tenant_id=self.tenant_id,
                    exam_id=exam.id,
                    subject_id=subj_data.subject_id,
                    exam_date=subj_data.exam_date,
                    start_time=subj_data.start_time,
                    end_time=subj_data.end_time,
                    duration_minutes=subj_data.duration_minutes,
                    venue=subj_data.venue,
                    room_number=subj_data.room_number,
                    max_marks=subj_data.max_marks,
                    passing_marks=subj_data.passing_marks,
                )
                self.db.add(exam_subject)
        
        await self.db.commit()
        await self.db.refresh(exam)
        
        logger.info(f"Created exam {exam.code} for tenant {self.tenant_id}")
        return exam
    
    async def get_exam(self, exam_id: UUID) -> Optional[Exam]:
        """Get exam by ID."""
        result = await self.db.execute(
            select(Exam)
            .options(selectinload(Exam.subjects))
            .where(
                Exam.id == exam_id,
                Exam.tenant_id == self.tenant_id,
                Exam.is_deleted == False
            )
        )
        return result.scalar_one_or_none()
    
    async def list_exams(
        self,
        exam_type: Optional[str] = None,
        status: Optional[str] = None,
        academic_year_id: Optional[UUID] = None,
        semester: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Exam], int]:
        """List exams with filters."""
        query = select(Exam).where(
            Exam.tenant_id == self.tenant_id,
            Exam.is_deleted == False
        )
        
        if exam_type:
            query = query.where(Exam.exam_type == exam_type)
        if status:
            query = query.where(Exam.status == status)
        if academic_year_id:
            query = query.where(Exam.academic_year_id == academic_year_id)
        if semester:
            query = query.where(Exam.semester == semester)
        
        # Count total
        count_result = await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar()
        
        # Paginate
        query = query.order_by(Exam.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.db.execute(query)
        return result.scalars().all(), total
    
    async def update_exam(self, exam_id: UUID, data: ExamUpdate) -> Exam:
        """Update an exam."""
        exam = await self.get_exam(exam_id)
        if not exam:
            raise NotFoundError("Exam not found")
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(exam, key, value)
        
        await self.db.commit()
        await self.db.refresh(exam)
        return exam
    
    async def delete_exam(self, exam_id: UUID) -> bool:
        """Soft delete an exam."""
        exam = await self.get_exam(exam_id)
        if not exam:
            raise NotFoundError("Exam not found")
        
        if exam.status not in [ExamStatus.DRAFT, ExamStatus.CANCELLED]:
            raise ValidationError("Can only delete draft or cancelled exams")
        
        exam.is_deleted = True
        await self.db.commit()
        return True
    
    # ============================================
    # Exam Registration
    # ============================================
    
    async def check_eligibility(
        self,
        student_id: UUID,
        exam_id: UUID
    ) -> RegistrationEligibilityCheck:
        """Check student eligibility for exam registration."""
        exam = await self.get_exam(exam_id)
        if not exam:
            raise NotFoundError("Exam not found")
        
        remarks = []
        is_eligible = True
        
        # Check registration window
        now = datetime.utcnow()
        if exam.registration_start and now < exam.registration_start:
            remarks.append("Registration has not started yet")
            is_eligible = False
        
        if exam.registration_end and now > exam.registration_end:
            if exam.late_registration_end and now <= exam.late_registration_end:
                remarks.append("Late registration period - additional fee applies")
            else:
                remarks.append("Registration period has ended")
                is_eligible = False
        
        # TODO: Check attendance percentage from attendance module
        attendance_percentage = 80.0  # Placeholder
        
        if attendance_percentage < exam.min_attendance_percentage:
            remarks.append(
                f"Attendance {attendance_percentage}% is below minimum {exam.min_attendance_percentage}%"
            )
            is_eligible = False
        
        # TODO: Check fee clearance from finance module
        fee_status_clear = True  # Placeholder
        
        if exam.require_fee_clearance and not fee_status_clear:
            remarks.append("Fee dues pending - clear fees before registration")
            is_eligible = False
        
        return RegistrationEligibilityCheck(
            is_eligible=is_eligible,
            attendance_percentage=attendance_percentage,
            fee_status_clear=fee_status_clear,
            remarks=remarks,
            subjects_eligible=[s.subject_id for s in exam.subjects] if is_eligible else [],
            subjects_not_eligible=[] if is_eligible else [s.subject_id for s in exam.subjects],
        )
    
    async def register_for_exam(
        self,
        student_id: UUID,
        data: ExamRegistrationCreate
    ) -> ExamRegistration:
        """Register student for an exam."""
        exam = await self.get_exam(data.exam_id)
        if not exam:
            raise NotFoundError("Exam not found")
        
        # Check if already registered
        existing = await self.db.execute(
            select(ExamRegistration).where(
                ExamRegistration.exam_id == data.exam_id,
                ExamRegistration.student_id == student_id,
                ExamRegistration.tenant_id == self.tenant_id,
            )
        )
        if existing.scalar_one_or_none():
            raise ConflictError("Already registered for this exam")
        
        # Check eligibility
        eligibility = await self.check_eligibility(student_id, data.exam_id)
        
        # Calculate fee
        num_subjects = len(data.subject_ids)
        total_fee = exam.exam_fee_per_subject * num_subjects
        
        # Check if late registration
        now = datetime.utcnow()
        if exam.registration_end and now > exam.registration_end:
            if exam.late_registration_end and now <= exam.late_registration_end:
                total_fee += exam.late_fee
        
        # Create registration
        registration = ExamRegistration(
            tenant_id=self.tenant_id,
            exam_id=data.exam_id,
            student_id=student_id,
            registration_number=self._generate_registration_number(exam.code),
            status=RegistrationStatus.PENDING if eligibility.is_eligible else RegistrationStatus.DEBARRED,
            registered_subject_ids=[str(sid) for sid in data.subject_ids],
            total_fee=total_fee,
            fee_paid=Decimal("0.00"),
            is_eligible=eligibility.is_eligible,
            eligibility_remarks="; ".join(eligibility.remarks) if eligibility.remarks else None,
            attendance_percentage=eligibility.attendance_percentage,
            registered_at=datetime.utcnow(),
        )
        
        self.db.add(registration)
        await self.db.commit()
        await self.db.refresh(registration)
        
        logger.info(f"Student {student_id} registered for exam {exam.code}")
        return registration
    
    async def get_student_registrations(
        self,
        student_id: UUID,
        exam_id: Optional[UUID] = None
    ) -> List[ExamRegistration]:
        """Get student's exam registrations."""
        query = select(ExamRegistration).where(
            ExamRegistration.tenant_id == self.tenant_id,
            ExamRegistration.student_id == student_id,
        )
        
        if exam_id:
            query = query.where(ExamRegistration.exam_id == exam_id)
        
        result = await self.db.execute(query.order_by(ExamRegistration.created_at.desc()))
        return result.scalars().all()
    
    async def confirm_registration(
        self,
        registration_id: UUID,
        payment_id: UUID
    ) -> ExamRegistration:
        """Confirm registration after fee payment."""
        result = await self.db.execute(
            select(ExamRegistration).where(
                ExamRegistration.id == registration_id,
                ExamRegistration.tenant_id == self.tenant_id,
            )
        )
        registration = result.scalar_one_or_none()
        
        if not registration:
            raise NotFoundError("Registration not found")
        
        registration.status = RegistrationStatus.CONFIRMED
        registration.fee_paid = registration.total_fee
        registration.fee_payment_id = payment_id
        registration.confirmed_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(registration)
        return registration
    
    # ============================================
    # Hall Tickets
    # ============================================
    
    async def generate_hall_tickets(
        self,
        data: HallTicketGenerateRequest,
        generated_by: UUID
    ) -> List[HallTicket]:
        """Generate hall tickets for confirmed registrations."""
        query = select(ExamRegistration).where(
            ExamRegistration.exam_id == data.exam_id,
            ExamRegistration.tenant_id == self.tenant_id,
            ExamRegistration.status == RegistrationStatus.CONFIRMED,
        )
        
        if data.registration_ids:
            query = query.where(ExamRegistration.id.in_(data.registration_ids))
        
        result = await self.db.execute(query)
        registrations = result.scalars().all()
        
        hall_tickets = []
        for reg in registrations:
            # Check if hall ticket already exists
            existing = await self.db.execute(
                select(HallTicket).where(
                    HallTicket.registration_id == reg.id,
                    HallTicket.tenant_id == self.tenant_id,
                )
            )
            if existing.scalar_one_or_none():
                continue
            
            hall_ticket = HallTicket(
                tenant_id=self.tenant_id,
                registration_id=reg.id,
                student_id=reg.student_id,
                exam_id=data.exam_id,
                hall_ticket_number=self._generate_hall_ticket_number(data.exam_id),
                status=HallTicketStatus.GENERATED,
                generated_at=datetime.utcnow(),
                generated_by=generated_by,
            )
            self.db.add(hall_ticket)
            hall_tickets.append(hall_ticket)
        
        await self.db.commit()
        
        for ht in hall_tickets:
            await self.db.refresh(ht)
        
        logger.info(f"Generated {len(hall_tickets)} hall tickets for exam {data.exam_id}")
        return hall_tickets
    
    async def get_student_hall_tickets(
        self,
        student_id: UUID,
        exam_id: Optional[UUID] = None
    ) -> List[HallTicket]:
        """Get student's hall tickets."""
        query = select(HallTicket).where(
            HallTicket.tenant_id == self.tenant_id,
            HallTicket.student_id == student_id,
        )
        
        if exam_id:
            query = query.where(HallTicket.exam_id == exam_id)
        
        result = await self.db.execute(query.order_by(HallTicket.created_at.desc()))
        return result.scalars().all()
    
    async def download_hall_ticket(self, hall_ticket_id: UUID, student_id: UUID) -> HallTicket:
        """Record hall ticket download."""
        result = await self.db.execute(
            select(HallTicket).where(
                HallTicket.id == hall_ticket_id,
                HallTicket.student_id == student_id,
                HallTicket.tenant_id == self.tenant_id,
            )
        )
        hall_ticket = result.scalar_one_or_none()
        
        if not hall_ticket:
            raise NotFoundError("Hall ticket not found")
        
        hall_ticket.download_count += 1
        hall_ticket.last_downloaded_at = datetime.utcnow()
        hall_ticket.status = HallTicketStatus.DOWNLOADED
        
        await self.db.commit()
        await self.db.refresh(hall_ticket)
        return hall_ticket
    
    # ============================================
    # Revaluation
    # ============================================
    
    async def apply_for_revaluation(
        self,
        student_id: UUID,
        data: RevaluationApplyRequest
    ) -> RevaluationApplication:
        """Apply for revaluation/retotaling."""
        # Check if result exists
        result_check = await self.db.execute(
            select(ExamResult).where(
                ExamResult.exam_id == data.exam_id,
                ExamResult.student_id == student_id,
                ExamResult.subject_id == data.subject_id,
                ExamResult.tenant_id == self.tenant_id,
            )
        )
        exam_result = result_check.scalar_one_or_none()
        
        if not exam_result:
            raise NotFoundError("Result not found for this subject")
        
        if exam_result.status != ResultStatus.PUBLISHED:
            raise ValidationError("Results not yet published")
        
        # Check if already applied
        existing = await self.db.execute(
            select(RevaluationApplication).where(
                RevaluationApplication.exam_id == data.exam_id,
                RevaluationApplication.student_id == student_id,
                RevaluationApplication.subject_id == data.subject_id,
                RevaluationApplication.tenant_id == self.tenant_id,
                RevaluationApplication.status.not_in([
                    RevaluationStatus.COMPLETED,
                    RevaluationStatus.REJECTED
                ])
            )
        )
        if existing.scalar_one_or_none():
            raise ConflictError("Already applied for revaluation")
        
        # Determine fee based on type
        fee_map = {
            "revaluation": Decimal("500.00"),
            "retotaling": Decimal("200.00"),
            "photocopy": Decimal("300.00"),
        }
        fee_amount = fee_map.get(data.revaluation_type.value, Decimal("500.00"))
        
        application = RevaluationApplication(
            tenant_id=self.tenant_id,
            student_id=student_id,
            exam_id=data.exam_id,
            subject_id=data.subject_id,
            application_number=self._generate_application_number("RV"),
            revaluation_type=data.revaluation_type,
            status=RevaluationStatus.PENDING,
            original_marks=exam_result.total_marks,
            fee_amount=fee_amount,
            reason=data.reason,
            applied_at=datetime.utcnow(),
        )
        
        self.db.add(application)
        await self.db.commit()
        await self.db.refresh(application)
        
        logger.info(f"Revaluation application created: {application.application_number}")
        return application
    
    async def get_revaluation_applications(
        self,
        student_id: Optional[UUID] = None,
        exam_id: Optional[UUID] = None,
        status: Optional[str] = None
    ) -> List[RevaluationApplication]:
        """Get revaluation applications."""
        query = select(RevaluationApplication).where(
            RevaluationApplication.tenant_id == self.tenant_id,
        )
        
        if student_id:
            query = query.where(RevaluationApplication.student_id == student_id)
        if exam_id:
            query = query.where(RevaluationApplication.exam_id == exam_id)
        if status:
            query = query.where(RevaluationApplication.status == status)
        
        result = await self.db.execute(
            query.order_by(RevaluationApplication.applied_at.desc())
        )
        return result.scalars().all()
    
    # ============================================
    # Results
    # ============================================
    
    async def publish_result(
        self,
        result_data: ExamResultCreate,
        published_by: UUID
    ) -> ExamResult:
        """Create or update exam result."""
        # Check if result exists
        existing = await self.db.execute(
            select(ExamResult).where(
                ExamResult.exam_id == result_data.exam_id,
                ExamResult.student_id == result_data.student_id,
                ExamResult.subject_id == result_data.subject_id,
                ExamResult.tenant_id == self.tenant_id,
            )
        )
        result = existing.scalar_one_or_none()
        
        if result:
            # Update existing
            result.internal_marks = result_data.internal_marks
            result.external_marks = result_data.external_marks
            result.practical_marks = result_data.practical_marks
            result.total_marks = result_data.total_marks
            result.max_marks = result_data.max_marks
            result.grade = result_data.grade
            result.grade_points = result_data.grade_points
            result.is_pass = result_data.is_pass
            result.grace_marks = result_data.grace_marks
            result.grace_reason = result_data.grace_reason
            result.status = ResultStatus.PUBLISHED
            result.published_at = datetime.utcnow()
            result.published_by = published_by
        else:
            # Create new
            result = ExamResult(
                tenant_id=self.tenant_id,
                exam_id=result_data.exam_id,
                student_id=result_data.student_id,
                subject_id=result_data.subject_id,
                internal_marks=result_data.internal_marks,
                external_marks=result_data.external_marks,
                practical_marks=result_data.practical_marks,
                total_marks=result_data.total_marks,
                max_marks=result_data.max_marks,
                grade=result_data.grade,
                grade_points=result_data.grade_points,
                is_pass=result_data.is_pass,
                grace_marks=result_data.grace_marks,
                grace_reason=result_data.grace_reason,
                status=ResultStatus.PUBLISHED,
                published_at=datetime.utcnow(),
                published_by=published_by,
            )
            self.db.add(result)
        
        await self.db.commit()
        await self.db.refresh(result)
        return result
    
    async def get_student_results(
        self,
        student_id: UUID,
        exam_id: Optional[UUID] = None,
        academic_year_id: Optional[UUID] = None
    ) -> List[ExamResult]:
        """Get student's exam results."""
        query = select(ExamResult).where(
            ExamResult.tenant_id == self.tenant_id,
            ExamResult.student_id == student_id,
            ExamResult.status == ResultStatus.PUBLISHED,
        )
        
        if exam_id:
            query = query.where(ExamResult.exam_id == exam_id)
        
        result = await self.db.execute(query.order_by(ExamResult.created_at.desc()))
        return result.scalars().all()
    
    # ============================================
    # Answer Booklets
    # ============================================
    
    async def generate_answer_booklets(
        self,
        data: AnswerBookletGenerateRequest
    ) -> List[AnswerBooklet]:
        """Generate answer booklet numbers."""
        booklets = []
        
        for i in range(data.quantity):
            booklet = AnswerBooklet(
                tenant_id=self.tenant_id,
                exam_id=data.exam_id,
                subject_id=data.subject_id,
                booklet_number=self._generate_booklet_number(data.prefix or "AB"),
                barcode=self._generate_barcode(),
            )
            self.db.add(booklet)
            booklets.append(booklet)
        
        await self.db.commit()
        
        for b in booklets:
            await self.db.refresh(b)
        
        return booklets
    
    # ============================================
    # Helper Methods
    # ============================================
    
    def _generate_registration_number(self, exam_code: str) -> str:
        """Generate unique registration number."""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        random_part = str(uuid4())[:6].upper()
        return f"REG-{exam_code}-{timestamp}-{random_part}"
    
    def _generate_hall_ticket_number(self, exam_id: UUID) -> str:
        """Generate unique hall ticket number."""
        timestamp = datetime.utcnow().strftime("%Y%m")
        random_part = str(uuid4())[:8].upper()
        return f"HT-{timestamp}-{random_part}"
    
    def _generate_application_number(self, prefix: str) -> str:
        """Generate application number."""
        timestamp = datetime.utcnow().strftime("%Y%m%d")
        random_part = str(uuid4())[:6].upper()
        return f"{prefix}-{timestamp}-{random_part}"
    
    def _generate_booklet_number(self, prefix: str) -> str:
        """Generate answer booklet number."""
        timestamp = datetime.utcnow().strftime("%Y%m")
        random_part = str(uuid4())[:10].upper()
        return f"{prefix}-{timestamp}-{random_part}"
    
    def _generate_barcode(self) -> str:
        """Generate barcode string."""
        return str(uuid4()).replace("-", "")[:16].upper()
