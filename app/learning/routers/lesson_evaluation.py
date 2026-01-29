"""
CUSTOS Lesson Evaluation & Adaptive Router

API endpoints for lesson evaluations and adaptive recommendations.
"""

from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth.dependencies import CurrentUser, require_permission
from app.users.rbac import Permission, SystemRole
from app.learning.services.lesson_eval_service import LessonEvaluationService
from app.learning.models.lesson_evaluation import LessonEvaluationStatus
from app.learning.schemas.lesson_evaluation import (
    LessonEvaluationCreate,
    LessonEvaluationUpdate,
    LessonEvaluationResponse,
    LessonEvaluationWithDetails,
    LessonResultSubmit,
    BulkLessonResultSubmit,
    LessonEvaluationResultResponse,
    LessonResultWithDetails,
    LessonMasterySnapshotResponse,
    MasterySnapshotWithDetails,
    AdaptiveRecommendationResponse,
    AdaptiveRecommendationsForStudent,
    ActionRecommendation,
    GenerateLessonPaperRequest,
    GenerateLessonPaperResult,
    LessonEvaluationPaper,
    CalculateMasteryResult,
    LessonEvaluationStats,
)


router = APIRouter(tags=["Lesson Evaluation & Adaptive Learning"])


# ============================================
# Lesson Evaluation CRUD Endpoints
# ============================================

@router.post("/tests", response_model=LessonEvaluationResponse, status_code=201)
async def create_lesson_evaluation(
    data: LessonEvaluationCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.LESSON_TEST_CREATE)),
):
    """
    Create a lesson evaluation for a completed lesson plan.
    
    Evaluates student mastery at the end of a chapter/lesson.
    """
    service = LessonEvaluationService(db, user.tenant_id)
    evaluation = await service.create_lesson_evaluation(data, created_by=user.id)
    return evaluation


@router.get("/tests", response_model=dict)
async def list_lesson_evaluations(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    class_id: Optional[UUID] = None,
    lesson_plan_id: Optional[UUID] = None,
    status: Optional[LessonEvaluationStatus] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    _=Depends(require_permission(Permission.LESSON_TEST_VIEW)),
):
    """List lesson evaluations with filters."""
    service = LessonEvaluationService(db, user.tenant_id)
    evaluations, total = await service.list_evaluations(
        class_id=class_id,
        lesson_plan_id=lesson_plan_id,
        status=status,
        page=page,
        size=size,
    )
    
    return {
        "items": [LessonEvaluationResponse.model_validate(e) for e in evaluations],
        "total": total,
        "page": page,
        "size": size,
    }


@router.get("/tests/{test_id}", response_model=LessonEvaluationResponse)
async def get_lesson_evaluation(
    test_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.LESSON_TEST_VIEW)),
):
    """Get a lesson evaluation by ID."""
    service = LessonEvaluationService(db, user.tenant_id)
    evaluation = await service.get_evaluation(test_id)
    
    if not evaluation:
        raise HTTPException(status_code=404, detail="Lesson evaluation not found")
    
    return evaluation


@router.patch("/tests/{test_id}", response_model=LessonEvaluationResponse)
async def update_lesson_evaluation(
    test_id: UUID,
    data: LessonEvaluationUpdate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.LESSON_TEST_CREATE)),
):
    """Update a lesson evaluation."""
    service = LessonEvaluationService(db, user.tenant_id)
    return await service.update_evaluation(test_id, data)


@router.delete("/tests/{test_id}", status_code=204)
async def delete_lesson_evaluation(
    test_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.LESSON_TEST_CREATE)),
):
    """Delete a lesson evaluation."""
    service = LessonEvaluationService(db, user.tenant_id)
    await service.delete_evaluation(test_id)


# ============================================
# Paper Generation Endpoints
# ============================================

@router.post("/tests/{test_id}/generate-paper", response_model=GenerateLessonPaperResult)
async def generate_lesson_paper(
    test_id: UUID,
    request: GenerateLessonPaperRequest,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.LESSON_TEST_GENERATE)),
):
    """
    Generate lesson evaluation paper.
    
    Selects questions from all topics covered in the lesson plan.
    """
    service = LessonEvaluationService(db, user.tenant_id)
    return await service.generate_lesson_paper(test_id, request)


@router.get("/tests/{test_id}/paper", response_model=LessonEvaluationPaper)
async def get_evaluation_paper(
    test_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.LESSON_TEST_VIEW)),
):
    """
    Get the evaluation paper (questions without answers).
    
    For printing or display to students.
    """
    service = LessonEvaluationService(db, user.tenant_id)
    return await service.get_evaluation_paper(test_id, include_answers=False)


@router.get("/tests/{test_id}/answer-key", response_model=LessonEvaluationPaper)
async def get_answer_key(
    test_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.LESSON_TEST_GENERATE)),
):
    """
    Get the answer key (paper with correct answers).
    
    Only accessible by teachers/admins.
    """
    service = LessonEvaluationService(db, user.tenant_id)
    return await service.get_answer_key(test_id)


# ============================================
# Result Submission Endpoints
# ============================================

@router.post("/tests/{test_id}/results", response_model=LessonEvaluationResultResponse, status_code=201)
async def submit_result(
    test_id: UUID,
    data: LessonResultSubmit,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.LESSON_TEST_SUBMIT_RESULT)),
):
    """
    Submit a single student's result.
    
    Automatically:
    - Calculates combined mastery (daily + weekly + lesson)
    - Generates adaptive recommendations based on thresholds
    """
    service = LessonEvaluationService(db, user.tenant_id)
    return await service.submit_result(test_id, data, submitted_by=user.id)


@router.post("/tests/{test_id}/results/bulk", response_model=List[LessonEvaluationResultResponse], status_code=201)
async def submit_results_bulk(
    test_id: UUID,
    data: BulkLessonResultSubmit,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.LESSON_TEST_SUBMIT_RESULT)),
):
    """Submit multiple student results at once."""
    service = LessonEvaluationService(db, user.tenant_id)
    results = await service.submit_results_bulk(test_id, data, submitted_by=user.id)
    return [LessonEvaluationResultResponse.model_validate(r) for r in results]


@router.get("/tests/{test_id}/results", response_model=List[LessonEvaluationResultResponse])
async def get_evaluation_results(
    test_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.LESSON_TEST_VIEW)),
):
    """Get all results for an evaluation."""
    service = LessonEvaluationService(db, user.tenant_id)
    results = await service.get_evaluation_results(test_id)
    return [LessonEvaluationResultResponse.model_validate(r) for r in results]


# ============================================
# Student History Endpoint
# ============================================

@router.get("/student/{student_id}", response_model=List[LessonEvaluationResultResponse])
async def get_student_lesson_history(
    student_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.LESSON_TEST_VIEW)),
):
    """Get all lesson evaluation results for a student."""
    user_roles = [r.code for r in user.roles] if user.roles else []
    if SystemRole.STUDENT.value in user_roles and student_id != user.id:
        raise HTTPException(status_code=403, detail="You can only view your own results")
    
    service = LessonEvaluationService(db, user.tenant_id)
    results = await service.get_student_results(student_id)
    return [LessonEvaluationResultResponse.model_validate(r) for r in results]


@router.get("/my-results", response_model=List[LessonEvaluationResultResponse])
async def get_my_lesson_results(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Get current user's lesson evaluation results."""
    service = LessonEvaluationService(db, user.tenant_id)
    results = await service.get_student_results(user.id)
    return [LessonEvaluationResultResponse.model_validate(r) for r in results]


# ============================================
# Adaptive Recommendations Endpoints
# ============================================

@router.get("/adaptive/{student_id}", response_model=AdaptiveRecommendationsForStudent)
async def get_student_recommendations(
    student_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    include_actioned: bool = False,
    _=Depends(require_permission(Permission.ADAPTIVE_VIEW)),
):
    """
    Get adaptive recommendations for a student.
    
    Recommendations are generated based on mastery thresholds:
    - mastery < 40%  → REMEDIAL_CLASS (HIGH priority)
    - mastery 40-60% → EXTRA_DAILY_LOOP (MEDIUM priority)
    - mastery 60-75% → REVISION (LOW priority)
    """
    user_roles = [r.code for r in user.roles] if user.roles else []
    if SystemRole.STUDENT.value in user_roles and student_id != user.id:
        raise HTTPException(status_code=403, detail="You can only view your own recommendations")
    
    service = LessonEvaluationService(db, user.tenant_id)
    return await service.get_student_recommendations(student_id, include_actioned)


@router.get("/my-recommendations", response_model=AdaptiveRecommendationsForStudent)
async def get_my_recommendations(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    include_actioned: bool = False,
):
    """
    Get current user's adaptive recommendations.
    
    No special permission required.
    """
    service = LessonEvaluationService(db, user.tenant_id)
    return await service.get_student_recommendations(user.id, include_actioned)


@router.post("/adaptive/{recommendation_id}/action", response_model=AdaptiveRecommendationResponse)
async def action_recommendation(
    recommendation_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.LESSON_TEST_CREATE)),
):
    """
    Mark a recommendation as actioned.
    
    Teachers mark when they've addressed a recommendation
    (e.g., scheduled a remedial class).
    """
    service = LessonEvaluationService(db, user.tenant_id)
    rec = await service.action_recommendation(recommendation_id, actioned_by=user.id)
    return rec


# ============================================
# Mastery Calculation Endpoint
# ============================================

@router.post("/student/{student_id}/chapter/{chapter_id}/calculate-mastery", response_model=CalculateMasteryResult)
async def calculate_student_mastery(
    student_id: UUID,
    chapter_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.LESSON_TEST_VIEW)),
):
    """
    Calculate combined mastery for a student on a chapter.
    
    Combines:
    - Daily mastery (30%)
    - Weekly mastery (30%)
    - Lesson mastery (40%)
    
    Also generates adaptive recommendations.
    """
    service = LessonEvaluationService(db, user.tenant_id)
    return await service.calculate_lesson_mastery(student_id, chapter_id)


# ============================================
# Stats Endpoint
# ============================================

@router.get("/stats", response_model=LessonEvaluationStats)
async def get_lesson_evaluation_stats(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    class_id: Optional[UUID] = None,
    _=Depends(require_permission(Permission.LESSON_TEST_VIEW)),
):
    """Get lesson evaluation statistics."""
    service = LessonEvaluationService(db, user.tenant_id)
    return await service.get_stats(class_id)
