"""
CUSTOS Assignment API Endpoints

Assignment and worksheet routes.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth import AuthUser, TenantCtx, require_permissions, Permission
from app.services.assignment_service import AssignmentService
from app.schemas.assignment import (
    AssignmentCreate, AssignmentUpdate, AssignmentResponse,
    SubmissionCreate, SubmissionResponse, AnswerSubmit,
    WorksheetCreate, WorksheetResponse,
)
from app.schemas.common import SuccessResponse
from app.models.assignment import AssignmentStatus, SubmissionStatus


router = APIRouter(prefix="/assignments", tags=["Assignments"])


# ==================== Assignments ====================

@router.get("", response_model=dict)
async def list_assignments(
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    section_id: Optional[UUID] = None,
    subject_id: Optional[UUID] = None,
    status: Optional[AssignmentStatus] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    """List assignments with filters."""
    service = AssignmentService(db, ctx.tenant_id)
    assignments, total = await service.get_assignments(
        section_id=section_id,
        subject_id=subject_id,
        status=status,
        page=page,
        size=size,
    )
    return {
        "items": [AssignmentResponse.model_validate(a) for a in assignments],
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size,
    }


@router.post("", response_model=AssignmentResponse)
async def create_assignment(
    data: AssignmentCreate,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    _: AuthUser = Depends(require_permissions(Permission.ASSIGNMENT_CREATE)),
):
    """Create assignment."""
    service = AssignmentService(db, ctx.tenant_id)
    assignment = await service.create_assignment(data, ctx.user.user_id)
    return AssignmentResponse.model_validate(assignment)


@router.get("/{assignment_id}", response_model=AssignmentResponse)
async def get_assignment(
    assignment_id: UUID,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
):
    """Get assignment by ID."""
    service = AssignmentService(db, ctx.tenant_id)
    assignment = await service.get_assignment(assignment_id)
    return AssignmentResponse.model_validate(assignment)


@router.put("/{assignment_id}", response_model=AssignmentResponse)
async def update_assignment(
    assignment_id: UUID,
    data: AssignmentUpdate,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    _: AuthUser = Depends(require_permissions(Permission.ASSIGNMENT_UPDATE)),
):
    """Update assignment."""
    service = AssignmentService(db, ctx.tenant_id)
    assignment = await service.update_assignment(assignment_id, data)
    return AssignmentResponse.model_validate(assignment)


@router.delete("/{assignment_id}", response_model=SuccessResponse)
async def delete_assignment(
    assignment_id: UUID,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    _: AuthUser = Depends(require_permissions(Permission.ASSIGNMENT_DELETE)),
):
    """Delete assignment."""
    service = AssignmentService(db, ctx.tenant_id)
    await service.delete_assignment(assignment_id)
    return SuccessResponse(message="Assignment deleted")


@router.post("/{assignment_id}/publish", response_model=AssignmentResponse)
async def publish_assignment(
    assignment_id: UUID,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    _: AuthUser = Depends(require_permissions(Permission.ASSIGNMENT_CREATE)),
):
    """Publish assignment."""
    service = AssignmentService(db, ctx.tenant_id)
    assignment = await service.publish_assignment(assignment_id)
    return AssignmentResponse.model_validate(assignment)


@router.get("/{assignment_id}/questions")
async def get_assignment_questions(
    assignment_id: UUID,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
):
    """Get questions for assignment."""
    service = AssignmentService(db, ctx.tenant_id)
    questions = await service.get_assignment_questions(assignment_id)
    return {"questions": questions}


# ==================== Submissions ====================

@router.post("/{assignment_id}/start", response_model=SubmissionResponse)
async def start_assignment(
    assignment_id: UUID,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
):
    """Start assignment attempt."""
    service = AssignmentService(db, ctx.tenant_id)
    submission = await service.start_submission(assignment_id, ctx.user.user_id)
    return SubmissionResponse.model_validate(submission)


@router.post("/submissions/{submission_id}/submit", response_model=SubmissionResponse)
async def submit_assignment(
    submission_id: UUID,
    answers: list[AnswerSubmit],
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
):
    """Submit answers for assignment."""
    service = AssignmentService(db, ctx.tenant_id)
    submission = await service.submit_answers(submission_id, answers)
    return SubmissionResponse.model_validate(submission)


@router.get("/{assignment_id}/submissions", response_model=list[SubmissionResponse])
async def get_submissions(
    assignment_id: UUID,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    status: Optional[SubmissionStatus] = None,
    _: AuthUser = Depends(require_permissions(Permission.ASSIGNMENT_VIEW_SUBMISSIONS)),
):
    """Get all submissions for assignment."""
    service = AssignmentService(db, ctx.tenant_id)
    submissions = await service.get_submissions(assignment_id, status)
    return [SubmissionResponse.model_validate(s) for s in submissions]


@router.get("/my-submissions")
async def get_my_submissions(
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    """Get current user's submissions."""
    service = AssignmentService(db, ctx.tenant_id)
    submissions, total = await service.get_student_submissions(
        ctx.user.user_id, page, size
    )
    return {
        "items": [SubmissionResponse.model_validate(s) for s in submissions],
        "total": total,
        "page": page,
        "size": size,
    }


# ==================== Worksheets ====================

@router.get("/worksheets", response_model=list[WorksheetResponse])
async def list_worksheets(
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    section_id: Optional[UUID] = None,
    subject_id: Optional[UUID] = None,
):
    """List worksheets."""
    service = AssignmentService(db, ctx.tenant_id)
    worksheets = await service.get_worksheets(section_id, subject_id)
    return [WorksheetResponse.model_validate(w) for w in worksheets]


@router.post("/worksheets", response_model=WorksheetResponse)
async def create_worksheet(
    data: WorksheetCreate,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    _: AuthUser = Depends(require_permissions(Permission.WORKSHEET_CREATE)),
):
    """Create worksheet."""
    service = AssignmentService(db, ctx.tenant_id)
    worksheet = await service.create_worksheet(data, ctx.user.user_id)
    return WorksheetResponse.model_validate(worksheet)


@router.get("/worksheets/{worksheet_id}", response_model=WorksheetResponse)
async def get_worksheet(
    worksheet_id: UUID,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
):
    """Get worksheet by ID."""
    service = AssignmentService(db, ctx.tenant_id)
    worksheet = await service.get_worksheet(worksheet_id)
    return WorksheetResponse.model_validate(worksheet)
