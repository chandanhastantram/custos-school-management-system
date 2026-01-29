"""
CUSTOS AI Router

AI-powered features with cost control.
"""

from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth.dependencies import CurrentUser, require_permission
from app.users.rbac import Permission
from app.ai.service import AIService
from app.ai.lesson_plan_generator import AILessonPlanService
from app.ai.models import AIJobStatus
from app.ai.schemas import (
    GenerateAILessonPlanRequest,
    GenerateAILessonPlanResponse,
    AILessonPlanJobResponse,
    AILessonPlanJobWithDetails,
    AIUsageResponse,
)


router = APIRouter(tags=["AI Teaching Assistant"])


# ============================================
# AI Lesson Plan Generation (New)
# ============================================

@router.post("/lesson-plan/generate", response_model=GenerateAILessonPlanResponse)
async def generate_ai_lesson_plan(
    request: GenerateAILessonPlanRequest,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.AI_LESSON_PLAN_GENERATE)),
):
    """
    Generate AI-assisted lesson plan from syllabus.
    
    This endpoint:
    1. Reads syllabus topics in order
    2. Reads academic calendar constraints
    3. Reads timetable (periods/week)
    4. Uses AI to allocate periods optimally
    5. Creates LessonPlan and LessonPlanUnits
    
    Preferences:
    - pace: slow/normal/fast
    - focus: concepts/problems/revision/balanced
    
    Cost: Deducts from monthly AI quota.
    """
    service = AILessonPlanService(db, user.tenant_id)
    return await service.generate_lesson_plan(
        teacher_id=user.id,
        request=request,
    )


@router.get("/lesson-plan/jobs", response_model=dict)
async def list_lesson_plan_jobs(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    status: Optional[AIJobStatus] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    _=Depends(require_permission(Permission.AI_LESSON_PLAN_GENERATE)),
):
    """List AI lesson plan generation jobs."""
    service = AILessonPlanService(db, user.tenant_id)
    jobs, total = await service.list_jobs(
        teacher_id=user.id,  # Teachers only see their own
        status=status,
        page=page,
        size=size,
    )
    
    return {
        "items": [AILessonPlanJobResponse.model_validate(j) for j in jobs],
        "total": total,
        "page": page,
        "size": size,
    }


@router.get("/lesson-plan/jobs/{job_id}", response_model=AILessonPlanJobWithDetails)
async def get_lesson_plan_job(
    job_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.AI_LESSON_PLAN_GENERATE)),
):
    """Get details of a lesson plan generation job."""
    service = AILessonPlanService(db, user.tenant_id)
    job = await service.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return AILessonPlanJobWithDetails(
        id=job.id,
        tenant_id=job.tenant_id,
        teacher_id=job.teacher_id,
        class_id=job.class_id,
        subject_id=job.subject_id,
        syllabus_subject_id=job.syllabus_subject_id,
        status=job.status,
        ai_provider=job.ai_provider,
        lesson_plan_id=job.lesson_plan_id,
        error_message=job.error_message,
        tokens_used=job.tokens_used,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        input_snapshot=job.input_snapshot,
        output_snapshot=job.output_snapshot,
    )


# ============================================
# Legacy AI Endpoints (Simple)
# ============================================

@router.post("/lesson-plan")
async def generate_lesson_plan_simple(
    subject: str,
    topic: str,
    grade_level: int,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    duration_minutes: int = 45,
    _=Depends(require_permission(Permission.AI_LESSON_PLAN)),
):
    """Generate simple AI lesson plan (legacy)."""
    service = AIService(db, user.tenant_id)
    return await service.generate_lesson_plan(
        subject=subject,
        topic=topic,
        grade_level=grade_level,
        duration_minutes=duration_minutes,
    )


@router.post("/generate-questions")
async def generate_questions(
    subject: str,
    topic: str,
    question_type: str,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    count: int = 5,
    difficulty: str = "medium",
    _=Depends(require_permission(Permission.AI_QUESTION_GEN)),
):
    """Generate AI questions."""
    service = AIService(db, user.tenant_id)
    questions = await service.generate_questions(
        subject=subject,
        topic=topic,
        question_type=question_type,
        count=count,
        difficulty=difficulty,
    )
    return {"questions": questions}


@router.post("/doubt-solver")
async def solve_doubt(
    question: str,
    subject: str,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    context: Optional[str] = None,
    _=Depends(require_permission(Permission.AI_DOUBT_SOLVER)),
):
    """AI doubt solver."""
    service = AIService(db, user.tenant_id)
    return await service.solve_doubt(
        question=question,
        subject=subject,
        context=context,
    )


# ============================================
# Usage Endpoints
# ============================================

@router.get("/usage", response_model=AIUsageResponse)
async def get_ai_usage(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """
    Get AI usage statistics for current month.
    
    Shows:
    - Requests used
    - Requests limit
    - Remaining quota
    - Percent used
    """
    service = AILessonPlanService(db, user.tenant_id)
    usage = await service.get_usage()
    return AIUsageResponse(**usage)

