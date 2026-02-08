"""
CUSTOS Assignments Router
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth.dependencies import CurrentUser, require_permission
from app.users.rbac import Permission
from app.academics.services.assignment_service import AssignmentService
from app.academics.models.assignments import AssignmentStatus


router = APIRouter(tags=["Assignments"])


@router.get("")
async def list_assignments(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    section_id: Optional[UUID] = None,
    subject_id: Optional[UUID] = None,
    status: Optional[AssignmentStatus] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    """List assignments."""
    service = AssignmentService(db, user.tenant_id)
    assignments, total = await service.get_assignments(
        section_id, subject_id, status, page, size
    )
    return {"items": assignments, "total": total, "page": page, "size": size}


@router.post("")
async def create_assignment(
    section_id: UUID,
    subject_id: UUID,
    title: str,
    due_date: datetime,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    description: Optional[str] = None,
    total_marks: float = 100,
    time_limit_minutes: Optional[int] = None,
    _=Depends(require_permission(Permission.ASSIGNMENT_CREATE)),
):
    """Create assignment."""
    service = AssignmentService(db, user.tenant_id)
    return await service.create_assignment(
        section_id=section_id,
        subject_id=subject_id,
        created_by=user.user_id,
        title=title,
        due_date=due_date,
        description=description,
        total_marks=total_marks,
        time_limit_minutes=time_limit_minutes,
    )


@router.get("/{assignment_id}")
async def get_assignment(
    assignment_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Get assignment by ID."""
    service = AssignmentService(db, user.tenant_id)
    return await service.get_assignment(assignment_id)


@router.post("/{assignment_id}/questions")
async def add_questions(
    assignment_id: UUID,
    questions: list,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.ASSIGNMENT_UPDATE)),
):
    """Add questions to assignment."""
    service = AssignmentService(db, user.tenant_id)
    return await service.add_questions(assignment_id, questions)


@router.post("/{assignment_id}/publish")
async def publish_assignment(
    assignment_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.ASSIGNMENT_CREATE)),
):
    """Publish assignment."""
    service = AssignmentService(db, user.tenant_id)
    return await service.publish_assignment(assignment_id)


# Student Submissions
@router.post("/{assignment_id}/start")
async def start_assignment(
    assignment_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Start assignment attempt."""
    service = AssignmentService(db, user.tenant_id)
    return await service.start_submission(assignment_id, user.user_id)


@router.post("/submissions/{submission_id}/answer")
async def submit_answer(
    submission_id: UUID,
    question_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    answer_text: Optional[str] = None,
    answer_data: Optional[dict] = None,
):
    """Submit answer."""
    service = AssignmentService(db, user.tenant_id)
    return await service.submit_answer(submission_id, question_id, answer_text, answer_data)


@router.post("/submissions/{submission_id}/complete")
async def complete_submission(
    submission_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Complete and submit."""
    service = AssignmentService(db, user.tenant_id)
    return await service.complete_submission(submission_id)


@router.post("/submissions/{submission_id}/grade")
async def grade_submission(
    submission_id: UUID,
    marks_obtained: float,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    feedback: Optional[str] = None,
    _=Depends(require_permission(Permission.ASSIGNMENT_GRADE)),
):
    """Grade submission."""
    service = AssignmentService(db, user.tenant_id)
    return await service.grade_submission(
        submission_id, user.user_id, marks_obtained, feedback
    )


# File Upload for Submissions
@router.post("/submissions/{submission_id}/upload")
async def upload_submission_file(
    submission_id: UUID,
    file_url: str,
    file_name: str,
    file_type: str,
    file_size_bytes: int,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """
    Upload file attachment for submission.
    
    The file should already be uploaded to storage (S3/local).
    This endpoint records the file metadata with the submission.
    """
    service = AssignmentService(db, user.tenant_id)
    return await service.attach_file_to_submission(
        submission_id=submission_id,
        student_id=user.user_id,
        file_url=file_url,
        file_name=file_name,
        file_type=file_type,
        file_size_bytes=file_size_bytes,
    )


# Student-specific endpoints
@router.get("/my-assignments")
async def get_my_assignments(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    """Get assignments for current student with submission status."""
    service = AssignmentService(db, user.tenant_id)
    return await service.get_student_assignments(
        student_id=user.user_id, status=status, page=page, size=size
    )


@router.get("/submissions/{submission_id}")
async def get_submission_details(
    submission_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Get submission details including file and grade."""
    service = AssignmentService(db, user.tenant_id)
    return await service.get_submission(submission_id, user.user_id)


# Teacher: List all submissions for an assignment
@router.get("/{assignment_id}/submissions")
async def list_assignment_submissions(
    assignment_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    _=Depends(require_permission(Permission.ASSIGNMENT_VIEW)),
):
    """List all submissions for an assignment (Teacher view)."""
    service = AssignmentService(db, user.tenant_id)
    return await service.get_assignment_submissions(
        assignment_id=assignment_id, status=status, page=page, size=size
    )

