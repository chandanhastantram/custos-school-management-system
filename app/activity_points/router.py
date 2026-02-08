"""
CUSTOS Activity Points Router

API endpoints for activity submissions and points tracking.
"""

from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_tenant_id
from app.auth.dependencies import get_current_user, require_roles
from app.auth.schemas import UserResponse

from app.activity_points.service import ActivityPointsService
from app.activity_points.schemas import (
    ActivitySubmissionCreate, ActivitySubmissionUpdate, ActivitySubmissionResponse,
    ActivitySubmissionListResponse, ActivityReviewRequest,
    StudentActivitySummaryResponse, CertificateGenerateRequest, CertificateResponse,
    ActivityPointConfigCreate, ActivityPointConfigResponse, ActivityCategory,
)


router = APIRouter(tags=["Activity Points"])


def get_activity_service(
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
) -> ActivityPointsService:
    """Get activity points service instance."""
    return ActivityPointsService(db, tenant_id)


# ============================================
# Category Endpoints
# ============================================

@router.get("/categories", response_model=List[str])
async def get_categories():
    """Get list of activity categories."""
    return [c.value for c in ActivityCategory]


# ============================================
# Submission Endpoints
# ============================================

@router.post("/submissions", response_model=ActivitySubmissionResponse, status_code=status.HTTP_201_CREATED)
async def create_submission(
    data: ActivitySubmissionCreate,
    academic_year_id: UUID = Query(..., description="Current academic year ID"),
    semester: int = Query(..., ge=1, le=10, description="Current semester"),
    service: ActivityPointsService = Depends(get_activity_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """Submit an activity for points."""
    submission = await service.create_submission(
        data, current_user.id, academic_year_id, semester
    )
    return ActivitySubmissionResponse.model_validate(submission)


@router.get("/submissions", response_model=ActivitySubmissionListResponse)
async def list_submissions(
    submission_status: Optional[str] = Query(None, alias="status"),
    category: Optional[str] = Query(None),
    academic_year_id: Optional[UUID] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: ActivityPointsService = Depends(get_activity_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """List activity submissions. Students see their own, staff sees all."""
    is_staff = current_user.role in ["admin", "principal", "sub_admin", "teacher"]
    student_id = None if is_staff else current_user.id
    
    submissions, total = await service.list_submissions(
        student_id=student_id,
        status=submission_status,
        category=category,
        academic_year_id=academic_year_id,
        page=page,
        page_size=page_size,
    )
    
    return ActivitySubmissionListResponse(
        items=[ActivitySubmissionResponse.model_validate(s) for s in submissions],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.get("/submissions/{submission_id}", response_model=ActivitySubmissionResponse)
async def get_submission(
    submission_id: UUID,
    service: ActivityPointsService = Depends(get_activity_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """Get submission details."""
    submission = await service.get_submission(submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    # Check access
    is_staff = current_user.role in ["admin", "principal", "sub_admin", "teacher"]
    if not is_staff and submission.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return ActivitySubmissionResponse.model_validate(submission)


@router.put("/submissions/{submission_id}", response_model=ActivitySubmissionResponse)
async def update_submission(
    submission_id: UUID,
    data: ActivitySubmissionUpdate,
    service: ActivityPointsService = Depends(get_activity_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """Update a submission (before approval)."""
    submission = await service.update_submission(submission_id, data, current_user.id)
    return ActivitySubmissionResponse.model_validate(submission)


@router.post("/submissions/{submission_id}/review", response_model=ActivitySubmissionResponse)
async def review_submission(
    submission_id: UUID,
    data: ActivityReviewRequest,
    service: ActivityPointsService = Depends(get_activity_service),
    current_user: UserResponse = Depends(require_roles(["admin", "principal", "sub_admin", "teacher"])),
):
    """Review and approve/reject a submission."""
    submission = await service.review_submission(submission_id, data, current_user.id)
    return ActivitySubmissionResponse.model_validate(submission)


# ============================================
# Summary Endpoints
# ============================================

@router.get("/summary", response_model=StudentActivitySummaryResponse)
async def get_my_summary(
    academic_year_id: UUID = Query(..., description="Academic year ID"),
    service: ActivityPointsService = Depends(get_activity_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """Get current user's activity summary."""
    summary = await service.get_student_summary(current_user.id, academic_year_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")
    return StudentActivitySummaryResponse.model_validate(summary)


@router.get("/summary/{student_id}", response_model=StudentActivitySummaryResponse)
async def get_student_summary(
    student_id: UUID,
    academic_year_id: UUID = Query(...),
    service: ActivityPointsService = Depends(get_activity_service),
    current_user: UserResponse = Depends(require_roles(["admin", "principal", "sub_admin", "teacher", "parent"])),
):
    """Get specific student's activity summary."""
    summary = await service.get_student_summary(student_id, academic_year_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")
    return StudentActivitySummaryResponse.model_validate(summary)


# ============================================
# Certificate Endpoints
# ============================================

@router.post("/certificates", response_model=CertificateResponse, status_code=status.HTTP_201_CREATED)
async def generate_certificate(
    data: CertificateGenerateRequest,
    service: ActivityPointsService = Depends(get_activity_service),
    current_user: UserResponse = Depends(require_roles(["admin", "principal", "sub_admin"])),
):
    """Generate activity points certificate."""
    certificate = await service.generate_certificate(data, current_user.id)
    return CertificateResponse.model_validate(certificate)
