"""
CUSTOS OCR Engine Router

API endpoints for offline exam OCR processing.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, UploadFile, File, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth.dependencies import CurrentUser, require_permission
from app.users.rbac import Permission
from app.ai.ocr_service import OCRService
from app.ai.ocr_models import ExamType, OCRJobStatus
from app.ai.ocr_schemas import (
    OCRJobResponse,
    OCRJobWithDetails,
    OCRJobUploadResponse,
    OCRJobResultsResponse,
    ImportOCRResultsRequest,
    ImportOCRResultsResponse,
    OCRStats,
)


router = APIRouter(tags=["AI OCR Engine"])


# ============================================
# Upload Endpoint
# ============================================

@router.post("/upload", response_model=OCRJobUploadResponse)
async def upload_ocr_image(
    file: UploadFile = File(..., description="Exam answer sheet or marks register image"),
    exam_type: ExamType = Form(..., description="Type of exam: weekly or lesson"),
    exam_id: UUID = Form(..., description="ID of the weekly test or lesson evaluation"),
    user: CurrentUser = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.AI_OCR_PROCESS)),
):
    """
    Upload exam answer sheet for OCR processing.
    
    Accepts:
    - JPEG, PNG, WebP, GIF images
    - Max size: 10MB
    
    Process:
    1. Validates file and exam
    2. Saves image
    3. Processes with AI OCR
    4. Extracts student results
    
    Returns job ID for tracking.
    """
    service = OCRService(db, user.tenant_id)
    return await service.upload_and_create_job(
        file=file,
        exam_type=exam_type,
        exam_id=exam_id,
        uploaded_by=user.id,
    )


# ============================================
# Job Management Endpoints
# ============================================

@router.get("/jobs", response_model=dict)
async def list_ocr_jobs(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    exam_type: Optional[ExamType] = None,
    status: Optional[OCRJobStatus] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    _=Depends(require_permission(Permission.AI_OCR_PROCESS)),
):
    """List OCR jobs with filters."""
    service = OCRService(db, user.tenant_id)
    jobs, total = await service.list_jobs(
        uploaded_by=user.id,  # Teachers see their own jobs
        exam_type=exam_type,
        status=status,
        page=page,
        size=size,
    )
    
    return {
        "items": [OCRJobResponse.model_validate(j) for j in jobs],
        "total": total,
        "page": page,
        "size": size,
    }


@router.get("/jobs/{job_id}", response_model=OCRJobWithDetails)
async def get_ocr_job(
    job_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.AI_OCR_PROCESS)),
):
    """Get details of an OCR job."""
    service = OCRService(db, user.tenant_id)
    job = await service.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="OCR job not found")
    
    return OCRJobWithDetails(
        id=job.id,
        tenant_id=job.tenant_id,
        uploaded_by=job.uploaded_by,
        exam_type=job.exam_type,
        exam_id=job.exam_id,
        status=job.status,
        image_path=job.image_path,
        original_filename=job.original_filename,
        ai_provider=job.ai_provider,
        error_message=job.error_message,
        tokens_used=job.tokens_used,
        results_extracted=job.results_extracted,
        results_imported=job.results_imported,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        input_snapshot=job.input_snapshot,
        output_snapshot=job.output_snapshot,
    )


# ============================================
# Results Endpoints
# ============================================

@router.get("/jobs/{job_id}/results", response_model=OCRJobResultsResponse)
async def get_ocr_job_results(
    job_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.AI_OCR_PROCESS)),
):
    """
    Get all parsed results for an OCR job.
    
    Shows:
    - Student identifiers extracted
    - Marks obtained
    - Wrong questions
    - Import status
    """
    service = OCRService(db, user.tenant_id)
    return await service.get_job_results(job_id)


@router.post("/jobs/{job_id}/import", response_model=ImportOCRResultsResponse)
async def import_ocr_results(
    job_id: UUID,
    request: ImportOCRResultsRequest,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.AI_OCR_PROCESS)),
):
    """
    Import parsed OCR results into exam system.
    
    Creates:
    - WeeklyTestResult (for weekly exams)
    - LessonEvaluationResult (for lesson evaluations)
    
    Options:
    - result_ids: Import only specific results (default: all)
    - override_existing: Re-import already imported results
    """
    service = OCRService(db, user.tenant_id)
    return await service.import_results(
        job_id=job_id,
        request=request,
        imported_by=user.id,
    )


@router.post("/jobs/{job_id}/reprocess", response_model=OCRJobResponse)
async def reprocess_ocr_job(
    job_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.AI_OCR_PROCESS)),
):
    """
    Reprocess a failed OCR job.
    
    Useful if OCR failed due to transient errors.
    """
    service = OCRService(db, user.tenant_id)
    job = await service.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="OCR job not found")
    
    if job.status not in [OCRJobStatus.FAILED, OCRJobStatus.PENDING]:
        raise HTTPException(
            status_code=400,
            detail="Only failed or pending jobs can be reprocessed"
        )
    
    job = await service.process_job(job_id)
    return OCRJobResponse.model_validate(job)


# ============================================
# Stats Endpoint
# ============================================

@router.get("/stats", response_model=OCRStats)
async def get_ocr_stats(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.AI_OCR_PROCESS)),
):
    """Get OCR processing statistics."""
    service = OCRService(db, user.tenant_id)
    return await service.get_stats()
