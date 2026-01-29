"""
CUSTOS Weekly Evaluation Router

API endpoints for weekly offline tests.
"""

from datetime import date
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth.dependencies import CurrentUser, require_permission
from app.users.rbac import Permission, SystemRole
from app.learning.services.weekly_test_service import WeeklyTestService
from app.learning.models.weekly_tests import WeeklyTestStatus
from app.learning.schemas.weekly_tests import (
    WeeklyTestCreate,
    WeeklyTestUpdate,
    WeeklyTestResponse,
    WeeklyTestWithDetails,
    StudentResultSubmit,
    BulkResultSubmit,
    WeeklyTestResultResponse,
    WeeklyTestResultWithDetails,
    WeeklyPerformanceResponse,
    GeneratePaperRequest,
    GeneratePaperResult,
    WeeklyTestPaper,
    WeeklyTestStats,
)


router = APIRouter(tags=["Weekly Evaluation"])


# ============================================
# Weekly Test CRUD Endpoints
# ============================================

@router.post("/tests", response_model=WeeklyTestResponse, status_code=201)
async def create_weekly_test(
    data: WeeklyTestCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.WEEKLY_TEST_CREATE)),
):
    """
    Create a new weekly test.
    
    Specify:
    - Class and subject
    - Topics covered (from daily loops)
    - Date range (which week's daily loop data to use)
    - 40/60 split configuration (default: 40% strong, 60% weak)
    """
    service = WeeklyTestService(db, user.tenant_id)
    test = await service.create_weekly_test(data, created_by=user.id)
    return test


@router.get("/tests", response_model=dict)
async def list_weekly_tests(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    class_id: Optional[UUID] = None,
    subject_id: Optional[UUID] = None,
    status: Optional[WeeklyTestStatus] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    _=Depends(require_permission(Permission.WEEKLY_TEST_VIEW)),
):
    """List weekly tests with filters."""
    service = WeeklyTestService(db, user.tenant_id)
    tests, total = await service.list_tests(
        class_id=class_id,
        subject_id=subject_id,
        status=status,
        start_date=start_date,
        end_date=end_date,
        page=page,
        size=size,
    )
    
    return {
        "items": [WeeklyTestResponse.model_validate(t) for t in tests],
        "total": total,
        "page": page,
        "size": size,
    }


@router.get("/tests/{test_id}", response_model=WeeklyTestResponse)
async def get_weekly_test(
    test_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.WEEKLY_TEST_VIEW)),
):
    """Get a weekly test by ID."""
    service = WeeklyTestService(db, user.tenant_id)
    test = await service.get_test(test_id)
    
    if not test:
        raise HTTPException(status_code=404, detail="Weekly test not found")
    
    return test


@router.patch("/tests/{test_id}", response_model=WeeklyTestResponse)
async def update_weekly_test(
    test_id: UUID,
    data: WeeklyTestUpdate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.WEEKLY_TEST_CREATE)),
):
    """Update a weekly test."""
    service = WeeklyTestService(db, user.tenant_id)
    return await service.update_test(test_id, data)


@router.delete("/tests/{test_id}", status_code=204)
async def delete_weekly_test(
    test_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.WEEKLY_TEST_CREATE)),
):
    """Delete a weekly test."""
    service = WeeklyTestService(db, user.tenant_id)
    await service.delete_test(test_id)


# ============================================
# Paper Generation Endpoints
# ============================================

@router.post("/tests/{test_id}/generate-paper", response_model=GeneratePaperResult)
async def generate_weekly_paper(
    test_id: UUID,
    request: GeneratePaperRequest,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.WEEKLY_TEST_GENERATE)),
):
    """
    Generate weekly test paper using 40/60 rule.
    
    Selects:
    - 40% questions from strong pool (class accuracy >= 70%)
    - 60% questions from weak pool (class accuracy < 40%)
    
    Based on daily loop data from the specified date range.
    """
    service = WeeklyTestService(db, user.tenant_id)
    return await service.generate_weekly_paper(test_id, request)


@router.get("/tests/{test_id}/paper", response_model=WeeklyTestPaper)
async def get_test_paper(
    test_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.WEEKLY_TEST_VIEW)),
):
    """
    Get the test paper (questions without answers).
    
    For printing or display to students.
    """
    service = WeeklyTestService(db, user.tenant_id)
    return await service.get_test_paper(test_id, include_answers=False)


@router.get("/tests/{test_id}/answer-key", response_model=WeeklyTestPaper)
async def get_answer_key(
    test_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.WEEKLY_TEST_GENERATE)),
):
    """
    Get the answer key (paper with correct answers).
    
    Only accessible by teachers/admins.
    """
    service = WeeklyTestService(db, user.tenant_id)
    return await service.get_answer_key(test_id)


# ============================================
# Result Submission Endpoints
# ============================================

@router.post("/tests/{test_id}/results", response_model=WeeklyTestResultResponse, status_code=201)
async def submit_result(
    test_id: UUID,
    data: StudentResultSubmit,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.WEEKLY_TEST_SUBMIT_RESULT)),
):
    """
    Submit a single student's result.
    
    Provide:
    - marks_obtained
    - attempted_questions (list of question numbers)
    - wrong_questions (list of question numbers answered incorrectly)
    
    System automatically:
    - Calculates strong/weak performance breakdown
    - Updates topic mastery
    """
    service = WeeklyTestService(db, user.tenant_id)
    return await service.submit_result(test_id, data, submitted_by=user.id)


@router.post("/tests/{test_id}/results/bulk", response_model=List[WeeklyTestResultResponse], status_code=201)
async def submit_results_bulk(
    test_id: UUID,
    data: BulkResultSubmit,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.WEEKLY_TEST_SUBMIT_RESULT)),
):
    """
    Submit multiple student results at once.
    
    Useful for uploading entire class results after evaluation.
    """
    service = WeeklyTestService(db, user.tenant_id)
    results = await service.submit_results_bulk(test_id, data, submitted_by=user.id)
    return [WeeklyTestResultResponse.model_validate(r) for r in results]


@router.get("/tests/{test_id}/results", response_model=List[WeeklyTestResultResponse])
async def get_test_results(
    test_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.WEEKLY_TEST_VIEW)),
):
    """Get all results for a test."""
    service = WeeklyTestService(db, user.tenant_id)
    results = await service.get_test_results(test_id)
    return [WeeklyTestResultResponse.model_validate(r) for r in results]


@router.get("/tests/{test_id}/results/{student_id}/performance", response_model=WeeklyPerformanceResponse)
async def get_student_test_performance(
    test_id: UUID,
    student_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.WEEKLY_TEST_VIEW)),
):
    """
    Get student's performance breakdown for a test.
    
    Shows:
    - Strong questions: total vs correct
    - Weak questions: total vs correct
    - Mastery delta
    """
    # Students can only view their own
    user_roles = [r.code for r in user.roles] if user.roles else []
    if SystemRole.STUDENT.value in user_roles and student_id != user.id:
        raise HTTPException(status_code=403, detail="You can only view your own performance")
    
    service = WeeklyTestService(db, user.tenant_id)
    perf = await service.get_student_performance(test_id, student_id)
    
    if not perf:
        raise HTTPException(status_code=404, detail="Performance data not found")
    
    return perf


# ============================================
# Student History Endpoint
# ============================================

@router.get("/student/{student_id}", response_model=List[WeeklyTestResultResponse])
async def get_student_weekly_history(
    student_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.WEEKLY_TEST_VIEW)),
):
    """Get all weekly test results for a student."""
    # Students can only view their own
    user_roles = [r.code for r in user.roles] if user.roles else []
    if SystemRole.STUDENT.value in user_roles and student_id != user.id:
        raise HTTPException(status_code=403, detail="You can only view your own results")
    
    service = WeeklyTestService(db, user.tenant_id)
    results = await service.get_student_results(student_id)
    return [WeeklyTestResultResponse.model_validate(r) for r in results]


@router.get("/my-results", response_model=List[WeeklyTestResultResponse])
async def get_my_weekly_results(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """
    Get current user's weekly test results.
    
    No special permission required.
    """
    service = WeeklyTestService(db, user.tenant_id)
    results = await service.get_student_results(user.id)
    return [WeeklyTestResultResponse.model_validate(r) for r in results]


# ============================================
# Stats Endpoint
# ============================================

@router.get("/stats", response_model=WeeklyTestStats)
async def get_weekly_test_stats(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    class_id: Optional[UUID] = None,
    _=Depends(require_permission(Permission.WEEKLY_TEST_VIEW)),
):
    """Get weekly test statistics."""
    service = WeeklyTestService(db, user.tenant_id)
    return await service.get_stats(class_id)
