"""
CUSTOS Examinations Router

API endpoints for exam registration, hall tickets, and results.
"""

from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_tenant_id
from app.auth.dependencies import get_current_user, require_roles
from app.auth.schemas import UserResponse

from app.examinations.service import ExaminationService
from app.examinations.schemas import (
    # Exam schemas
    ExamCreate, ExamUpdate, ExamResponse, ExamListResponse,
    ExamSubjectCreate, ExamSubjectResponse,
    # Registration schemas
    ExamRegistrationCreate, ExamRegistrationResponse, RegistrationEligibilityCheck,
    # Hall ticket schemas
    HallTicketGenerateRequest, HallTicketResponse, HallTicketDownloadResponse,
    # Revaluation schemas
    RevaluationApplyRequest, RevaluationResponse, RevaluationUpdateRequest,
    # Makeup/Backlog schemas
    MakeupBacklogRegisterRequest, MakeupBacklogResponse,
    # Result schemas
    ExamResultCreate, ExamResultBulkCreate, ExamResultResponse,
    ExamResultPublishRequest, StudentExamResultSummary,
    SemesterResultResponse, StudentAcademicSummary,
    # Answer booklet schemas
    AnswerBookletGenerateRequest, AnswerBookletResponse, AnswerBookletAssignRequest,
)


router = APIRouter(tags=["Examinations"])


def get_examination_service(
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
) -> ExaminationService:
    """Get examination service instance."""
    return ExaminationService(db, tenant_id)


# ============================================
# Exam Endpoints
# ============================================

@router.get("/exams", response_model=ExamListResponse)
async def list_exams(
    exam_type: Optional[str] = Query(None, description="Filter by exam type"),
    exam_status: Optional[str] = Query(None, alias="status", description="Filter by status"),
    academic_year_id: Optional[UUID] = Query(None, description="Filter by academic year"),
    semester: Optional[int] = Query(None, description="Filter by semester"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: ExaminationService = Depends(get_examination_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """List exams with filters and pagination."""
    exams, total = await service.list_exams(
        exam_type=exam_type,
        status=exam_status,
        academic_year_id=academic_year_id,
        semester=semester,
        page=page,
        page_size=page_size,
    )
    
    return ExamListResponse(
        items=[ExamResponse.model_validate(e) for e in exams],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.post("/exams", response_model=ExamResponse, status_code=status.HTTP_201_CREATED)
async def create_exam(
    data: ExamCreate,
    service: ExaminationService = Depends(get_examination_service),
    current_user: UserResponse = Depends(require_roles(["admin", "principal", "sub_admin"])),
):
    """Create a new exam (admin only)."""
    exam = await service.create_exam(data, current_user.id)
    return ExamResponse.model_validate(exam)


@router.get("/exams/{exam_id}", response_model=ExamResponse)
async def get_exam(
    exam_id: UUID,
    service: ExaminationService = Depends(get_examination_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """Get exam details."""
    exam = await service.get_exam(exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    return ExamResponse.model_validate(exam)


@router.put("/exams/{exam_id}", response_model=ExamResponse)
async def update_exam(
    exam_id: UUID,
    data: ExamUpdate,
    service: ExaminationService = Depends(get_examination_service),
    current_user: UserResponse = Depends(require_roles(["admin", "principal", "sub_admin"])),
):
    """Update an exam (admin only)."""
    exam = await service.update_exam(exam_id, data)
    return ExamResponse.model_validate(exam)


@router.delete("/exams/{exam_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_exam(
    exam_id: UUID,
    service: ExaminationService = Depends(get_examination_service),
    current_user: UserResponse = Depends(require_roles(["admin", "principal"])),
):
    """Delete an exam (admin only)."""
    await service.delete_exam(exam_id)


# ============================================
# Registration Endpoints
# ============================================

@router.get("/exams/{exam_id}/eligibility", response_model=RegistrationEligibilityCheck)
async def check_eligibility(
    exam_id: UUID,
    service: ExaminationService = Depends(get_examination_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """Check student's eligibility for exam registration."""
    return await service.check_eligibility(current_user.id, exam_id)


@router.post("/exams/{exam_id}/register", response_model=ExamRegistrationResponse, status_code=status.HTTP_201_CREATED)
async def register_for_exam(
    exam_id: UUID,
    data: ExamRegistrationCreate,
    service: ExaminationService = Depends(get_examination_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """Register for an exam."""
    if data.exam_id != exam_id:
        raise HTTPException(status_code=400, detail="Exam ID mismatch")
    
    registration = await service.register_for_exam(current_user.id, data)
    return ExamRegistrationResponse.model_validate(registration)


@router.get("/registrations", response_model=List[ExamRegistrationResponse])
async def get_my_registrations(
    exam_id: Optional[UUID] = Query(None),
    service: ExaminationService = Depends(get_examination_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """Get current user's exam registrations."""
    registrations = await service.get_student_registrations(current_user.id, exam_id)
    return [ExamRegistrationResponse.model_validate(r) for r in registrations]


@router.get("/exams/{exam_id}/registrations", response_model=List[ExamRegistrationResponse])
async def list_exam_registrations(
    exam_id: UUID,
    status_filter: Optional[str] = Query(None, alias="status"),
    service: ExaminationService = Depends(get_examination_service),
    current_user: UserResponse = Depends(require_roles(["admin", "principal", "sub_admin", "teacher"])),
):
    """List all registrations for an exam (admin/teacher only)."""
    registrations = await service.get_student_registrations(
        student_id=None,  # Get all
        exam_id=exam_id
    )
    # TODO: Implement proper filtering in service
    return [ExamRegistrationResponse.model_validate(r) for r in registrations]


@router.post("/registrations/{registration_id}/confirm", response_model=ExamRegistrationResponse)
async def confirm_registration(
    registration_id: UUID,
    payment_id: UUID,
    service: ExaminationService = Depends(get_examination_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """Confirm registration after fee payment."""
    registration = await service.confirm_registration(registration_id, payment_id)
    return ExamRegistrationResponse.model_validate(registration)


# ============================================
# Hall Ticket Endpoints
# ============================================

@router.post("/hall-tickets/generate", response_model=List[HallTicketResponse])
async def generate_hall_tickets(
    data: HallTicketGenerateRequest,
    service: ExaminationService = Depends(get_examination_service),
    current_user: UserResponse = Depends(require_roles(["admin", "principal", "sub_admin"])),
):
    """Generate hall tickets for confirmed registrations (admin only)."""
    hall_tickets = await service.generate_hall_tickets(data, current_user.id)
    return [HallTicketResponse.model_validate(ht) for ht in hall_tickets]


@router.get("/hall-tickets", response_model=List[HallTicketResponse])
async def get_my_hall_tickets(
    exam_id: Optional[UUID] = Query(None),
    service: ExaminationService = Depends(get_examination_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """Get current user's hall tickets."""
    hall_tickets = await service.get_student_hall_tickets(current_user.id, exam_id)
    return [HallTicketResponse.model_validate(ht) for ht in hall_tickets]


@router.post("/hall-tickets/{hall_ticket_id}/download", response_model=HallTicketResponse)
async def download_hall_ticket(
    hall_ticket_id: UUID,
    service: ExaminationService = Depends(get_examination_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """Download hall ticket (records download)."""
    hall_ticket = await service.download_hall_ticket(hall_ticket_id, current_user.id)
    return HallTicketResponse.model_validate(hall_ticket)


# ============================================
# Revaluation Endpoints
# ============================================

@router.post("/revaluation/apply", response_model=RevaluationResponse, status_code=status.HTTP_201_CREATED)
async def apply_for_revaluation(
    data: RevaluationApplyRequest,
    service: ExaminationService = Depends(get_examination_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """Apply for revaluation/retotaling."""
    application = await service.apply_for_revaluation(current_user.id, data)
    return RevaluationResponse.model_validate(application)


@router.get("/revaluation/applications", response_model=List[RevaluationResponse])
async def get_revaluation_applications(
    exam_id: Optional[UUID] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    service: ExaminationService = Depends(get_examination_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """Get revaluation applications (students see their own, admins see all)."""
    # Check if admin
    is_admin = current_user.role in ["admin", "principal", "sub_admin"]
    student_id = None if is_admin else current_user.id
    
    applications = await service.get_revaluation_applications(
        student_id=student_id,
        exam_id=exam_id,
        status=status_filter,
    )
    return [RevaluationResponse.model_validate(a) for a in applications]


# ============================================
# Result Endpoints
# ============================================

@router.post("/results", response_model=ExamResultResponse, status_code=status.HTTP_201_CREATED)
async def publish_result(
    data: ExamResultCreate,
    service: ExaminationService = Depends(get_examination_service),
    current_user: UserResponse = Depends(require_roles(["admin", "principal", "sub_admin", "teacher"])),
):
    """Publish exam result (admin/teacher only)."""
    result = await service.publish_result(data, current_user.id)
    return ExamResultResponse.model_validate(result)


@router.post("/results/bulk", response_model=List[ExamResultResponse])
async def publish_results_bulk(
    data: ExamResultBulkCreate,
    service: ExaminationService = Depends(get_examination_service),
    current_user: UserResponse = Depends(require_roles(["admin", "principal", "sub_admin"])),
):
    """Bulk publish exam results (admin only)."""
    results = []
    for result_data in data.results:
        result = await service.publish_result(result_data, current_user.id)
        results.append(ExamResultResponse.model_validate(result))
    return results


@router.get("/results", response_model=List[ExamResultResponse])
async def get_my_results(
    exam_id: Optional[UUID] = Query(None),
    service: ExaminationService = Depends(get_examination_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """Get current user's exam results."""
    results = await service.get_student_results(current_user.id, exam_id)
    return [ExamResultResponse.model_validate(r) for r in results]


@router.get("/results/student/{student_id}", response_model=List[ExamResultResponse])
async def get_student_results(
    student_id: UUID,
    exam_id: Optional[UUID] = Query(None),
    service: ExaminationService = Depends(get_examination_service),
    current_user: UserResponse = Depends(require_roles(["admin", "principal", "sub_admin", "teacher", "parent"])),
):
    """Get specific student's results (admin/teacher/parent only)."""
    results = await service.get_student_results(student_id, exam_id)
    return [ExamResultResponse.model_validate(r) for r in results]


# ============================================
# Answer Booklet Endpoints
# ============================================

@router.post("/answer-booklets/generate", response_model=List[AnswerBookletResponse])
async def generate_answer_booklets(
    data: AnswerBookletGenerateRequest,
    service: ExaminationService = Depends(get_examination_service),
    current_user: UserResponse = Depends(require_roles(["admin", "principal", "sub_admin"])),
):
    """Generate answer booklet numbers (admin only)."""
    booklets = await service.generate_answer_booklets(data)
    return [AnswerBookletResponse.model_validate(b) for b in booklets]
