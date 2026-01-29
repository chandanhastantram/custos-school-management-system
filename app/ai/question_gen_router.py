"""
CUSTOS AI Question Generator Router

API endpoints for AI-powered question generation from syllabus topics.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth.dependencies import CurrentUser, require_permission
from app.users.rbac import Permission
from app.ai.question_gen_service import AIQuestionGenService
from app.ai.models import AIJobStatus
from app.ai.question_gen_schemas import (
    GenerateQuestionsRequest,
    GenerateQuestionsResponse,
    AIQuestionGenJobResponse,
    AIQuestionGenJobWithDetails,
    QuestionGenUsageResponse,
    QuestionGenJobListResponse,
    AIQuestionGenJobStatus,
)


router = APIRouter(tags=["AI Question Generator"])


# ============================================
# Question Generation
# ============================================

@router.post("/questions/generate", response_model=GenerateQuestionsResponse)
async def generate_questions(
    request: GenerateQuestionsRequest,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.AI_QUESTION_GEN)),
):
    """
    Generate AI questions from a syllabus topic.
    
    This endpoint:
    1. Checks AI quota for the tenant's subscription tier
    2. Loads topic context (description, keywords, learning objectives)
    3. Calls AI to generate questions based on topic
    4. Validates and saves questions to QuestionBank
    5. Creates job record for tracking
    
    **Quota**: Each request counts as 1 question_gen usage.
    Generated questions are saved with status PENDING_REVIEW.
    
    **Limits by tier**:
    - FREE: 10 requests/month, max 20 questions/request
    - STARTER: 50 requests/month, max 50 questions/request
    - PROFESSIONAL: 200 requests/month, max 100 questions/request
    - ENTERPRISE: 1000 requests/month, max 200 questions/request
    """
    service = AIQuestionGenService(db, user.tenant_id)
    
    result = await service.generate_questions(
        request=request.model_dump(),
        teacher_id=user.id,
    )
    
    return GenerateQuestionsResponse(
        job_id=UUID(result["job_id"]),
        status=AIQuestionGenJobStatus(result["status"]),
        questions_created=result["questions_created"],
        question_ids=result.get("question_ids", []),
        tokens_used=result.get("tokens_used", 0),
    )


# ============================================
# Job Management
# ============================================

@router.get("/questions/jobs", response_model=QuestionGenJobListResponse)
async def list_question_gen_jobs(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    status: Optional[AIJobStatus] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    _=Depends(require_permission(Permission.AI_QUESTION_GEN)),
):
    """
    List AI question generation jobs.
    
    Teachers see only their own jobs.
    """
    service = AIQuestionGenService(db, user.tenant_id)
    
    jobs, total = await service.list_jobs(
        teacher_id=user.id,  # Teachers only see their own
        status=status,
        page=page,
        size=size,
    )
    
    return QuestionGenJobListResponse(
        items=[AIQuestionGenJobResponse.model_validate(j) for j in jobs],
        total=total,
        page=page,
        size=size,
    )


@router.get("/questions/jobs/{job_id}", response_model=AIQuestionGenJobWithDetails)
async def get_question_gen_job(
    job_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.AI_QUESTION_GEN)),
):
    """
    Get details of a question generation job.
    
    Includes input/output snapshots and created question IDs.
    """
    service = AIQuestionGenService(db, user.tenant_id)
    job = await service.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Teachers can only view their own jobs
    if job.requested_by != user.id:
        # Check if user has admin role
        from app.users.rbac import SystemRole
        user_roles = [r.code for r in getattr(user, 'roles', [])]
        if SystemRole.PRINCIPAL.value not in user_roles and SystemRole.SUPER_ADMIN.value not in user_roles:
            raise HTTPException(status_code=403, detail="Access denied")
    
    return AIQuestionGenJobWithDetails(
        id=job.id,
        tenant_id=job.tenant_id,
        requested_by=job.requested_by,
        topic_id=job.topic_id,
        subject_id=job.subject_id,
        class_id=job.class_id,
        difficulty=job.difficulty,
        question_type=job.question_type,
        count=job.count,
        status=job.status,
        ai_provider=job.ai_provider,
        questions_created=job.questions_created,
        tokens_used=job.tokens_used,
        error_message=job.error_message,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        input_snapshot=job.input_snapshot,
        output_snapshot=job.output_snapshot,
        created_question_ids=job.created_question_ids,
    )


# ============================================
# Usage Endpoint
# ============================================

@router.get("/questions/usage", response_model=QuestionGenUsageResponse)
async def get_question_gen_usage(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """
    Get AI question generation usage for current month.
    
    Shows:
    - Current tier
    - Questions generated vs limit
    - Max questions per request
    """
    service = AIQuestionGenService(db, user.tenant_id)
    usage = await service.get_usage()
    
    return QuestionGenUsageResponse(**usage)
