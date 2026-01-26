"""
CUSTOS Corrections API Endpoints

Manual correction workflow routes.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth import AuthUser, TenantCtx, require_permissions, Permission
from app.services.correction_service import CorrectionService
from app.schemas.assignment import (
    CorrectionData, BulkCorrectionRequest, SubmissionResponse,
)
from app.schemas.common import SuccessResponse, BulkActionResponse


router = APIRouter(prefix="/corrections", tags=["Corrections"])


@router.get("/pending")
async def get_pending_corrections(
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    assignment_id: Optional[UUID] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    _: AuthUser = Depends(require_permissions(Permission.ASSIGNMENT_GRADE)),
):
    """Get submissions pending manual correction."""
    service = CorrectionService(db, ctx.tenant_id)
    submissions, total = await service.get_pending_corrections(
        teacher_id=ctx.user.user_id,
        assignment_id=assignment_id,
        page=page,
        size=size,
    )
    
    return {
        "items": [SubmissionResponse.model_validate(s) for s in submissions],
        "total": total,
        "page": page,
        "size": size,
    }


@router.get("/spreadsheet/{assignment_id}")
async def get_spreadsheet_data(
    assignment_id: UUID,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    _: AuthUser = Depends(require_permissions(Permission.ASSIGNMENT_GRADE)),
):
    """
    Get correction data in spreadsheet format.
    
    Returns data optimized for displaying in a correction spreadsheet:
    - Rows: Students
    - Columns: Questions
    - Cells: Marks/Answers
    """
    service = CorrectionService(db, ctx.tenant_id)
    return await service.get_spreadsheet_data(assignment_id)


@router.post("/apply/{submission_id}", response_model=SubmissionResponse)
async def apply_correction(
    submission_id: UUID,
    data: CorrectionData,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    _: AuthUser = Depends(require_permissions(Permission.ASSIGNMENT_GRADE)),
):
    """Apply correction to a single submission."""
    service = CorrectionService(db, ctx.tenant_id)
    submission = await service.apply_correction(
        submission_id=submission_id,
        corrections=data.corrections,
        teacher_id=ctx.user.user_id,
    )
    return SubmissionResponse.model_validate(submission)


@router.post("/bulk", response_model=BulkActionResponse)
async def bulk_correct(
    request: BulkCorrectionRequest,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    _: AuthUser = Depends(require_permissions(Permission.ASSIGNMENT_GRADE)),
):
    """Apply corrections to multiple submissions at once."""
    service = CorrectionService(db, ctx.tenant_id)
    result = await service.bulk_correct(
        corrections=request.corrections,
        teacher_id=ctx.user.user_id,
    )
    
    return BulkActionResponse(
        success_count=result["success_count"],
        failure_count=result["failure_count"],
        failures=result["failures"],
    )


@router.post("/auto-grade/{submission_id}", response_model=SubmissionResponse)
async def auto_grade_mcq(
    submission_id: UUID,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    _: AuthUser = Depends(require_permissions(Permission.ASSIGNMENT_GRADE)),
):
    """Auto-grade MCQ questions in submission."""
    service = CorrectionService(db, ctx.tenant_id)
    submission = await service.auto_grade_mcq(submission_id)
    return SubmissionResponse.model_validate(submission)
