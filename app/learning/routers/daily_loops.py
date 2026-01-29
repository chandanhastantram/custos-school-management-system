"""
CUSTOS Daily Learning Loop Router

API endpoints for daily loop operations.
"""

from datetime import date
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth.dependencies import CurrentUser, require_permission
from app.users.rbac import Permission, SystemRole
from app.learning.services.daily_loop_service import DailyLoopService
from app.learning.schemas.daily_loops import (
    DailySessionResponse,
    DailySessionWithQuestions,
    AttemptSubmit,
    AttemptBulkSubmit,
    AttemptResponse,
    AttemptWithFeedback,
    StudentMasteryResponse,
    MasteryWithDetails,
    StudentMasterySummary,
    StrongWeakAnalysis,
    TodaySessionInfo,
    DailyLoopStats,
    QuestionForAttempt,
)


router = APIRouter(tags=["Daily Learning Loops"])


# ============================================
# Session Endpoints
# ============================================

@router.post("/daily/start/{schedule_entry_id}", response_model=DailySessionResponse, status_code=201)
async def start_daily_session(
    schedule_entry_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    max_questions: int = Query(10, ge=1, le=50),
    time_limit_minutes: Optional[int] = Query(None, ge=1, le=120),
    _=Depends(require_permission(Permission.DAILY_LOOP_START)),
):
    """
    Start a daily loop session from a schedule entry.
    
    Creates a session linked to the schedule entry's topic.
    Teachers/admins can create sessions.
    """
    service = DailyLoopService(db, user.tenant_id)
    session = await service.create_daily_session(
        schedule_entry_id=schedule_entry_id,
        max_questions=max_questions,
        time_limit_minutes=time_limit_minutes,
    )
    return session


@router.get("/daily/session/{session_id}", response_model=DailySessionResponse)
async def get_daily_session(
    session_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.DAILY_LOOP_VIEW)),
):
    """Get a daily loop session by ID."""
    service = DailyLoopService(db, user.tenant_id)
    session = await service.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return session


@router.get("/daily/session/{session_id}/questions", response_model=List[QuestionForAttempt])
async def get_session_questions(
    session_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.DAILY_LOOP_VIEW)),
):
    """
    Get questions for a session.
    
    Returns MCQ questions for the session's topic.
    Excludes questions the current user has already attempted.
    """
    service = DailyLoopService(db, user.tenant_id)
    session, questions = await service.get_session_with_questions(
        session_id=session_id,
        student_id=user.id,
    )
    return questions


@router.get("/daily/sessions", response_model=dict)
async def list_daily_sessions(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    class_id: Optional[UUID] = None,
    topic_id: Optional[UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    _=Depends(require_permission(Permission.DAILY_LOOP_VIEW)),
):
    """List daily loop sessions with filters."""
    service = DailyLoopService(db, user.tenant_id)
    sessions, total = await service.list_sessions(
        class_id=class_id,
        topic_id=topic_id,
        start_date=start_date,
        end_date=end_date,
        page=page,
        size=size,
    )
    
    return {
        "items": [DailySessionResponse.model_validate(s) for s in sessions],
        "total": total,
        "page": page,
        "size": size,
    }


# ============================================
# Attempt Endpoints
# ============================================

@router.post("/daily/attempt", response_model=AttemptResponse, status_code=201)
async def submit_attempt(
    session_id: UUID,
    attempt: AttemptSubmit,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.DAILY_LOOP_ATTEMPT)),
):
    """
    Submit a single question attempt.
    
    Students can only submit for themselves.
    Returns whether the answer was correct.
    """
    service = DailyLoopService(db, user.tenant_id)
    result = await service.submit_attempt(
        session_id=session_id,
        student_id=user.id,
        attempt=attempt,
    )
    return result


@router.post("/daily/attempts/bulk", response_model=List[AttemptResponse], status_code=201)
async def submit_attempts_bulk(
    data: AttemptBulkSubmit,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.DAILY_LOOP_ATTEMPT)),
):
    """
    Submit multiple attempts at once.
    
    Useful for submitting all answers at end of session.
    """
    service = DailyLoopService(db, user.tenant_id)
    results = await service.submit_attempts_bulk(
        student_id=user.id,
        data=data,
    )
    return [AttemptResponse.model_validate(r) for r in results]


@router.get("/daily/session/{session_id}/my-attempts", response_model=List[AttemptResponse])
async def get_my_session_attempts(
    session_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """
    Get current user's attempts for a session.
    
    No special permission required - users can always view their own attempts.
    """
    service = DailyLoopService(db, user.tenant_id)
    attempts = await service.get_student_attempts_for_session(
        session_id=session_id,
        student_id=user.id,
    )
    return [AttemptResponse.model_validate(a) for a in attempts]


# ============================================
# Today's Sessions Endpoint
# ============================================

@router.get("/daily/student/{student_id}/today", response_model=TodaySessionInfo)
async def get_student_today(
    student_id: UUID,
    class_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.DAILY_LOOP_VIEW)),
):
    """
    Get today's sessions and progress for a student.
    
    Teachers can view any student, students can only view themselves.
    """
    # Students can only view themselves
    user_roles = [r.code for r in user.roles] if user.roles else []
    if SystemRole.STUDENT.value in user_roles and student_id != user.id:
        raise HTTPException(status_code=403, detail="You can only view your own sessions")
    
    service = DailyLoopService(db, user.tenant_id)
    return await service.get_student_today_info(student_id, class_id)


@router.get("/daily/my-today", response_model=TodaySessionInfo)
async def get_my_today(
    class_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """
    Get current user's today sessions and progress.
    
    No special permission required.
    """
    service = DailyLoopService(db, user.tenant_id)
    return await service.get_student_today_info(user.id, class_id)


# ============================================
# Mastery Endpoints
# ============================================

@router.get("/daily/student/{student_id}/topic/{topic_id}/mastery", response_model=StudentMasteryResponse)
async def get_student_topic_mastery(
    student_id: UUID,
    topic_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.DAILY_LOOP_VIEW)),
):
    """
    Get student's mastery for a specific topic.
    
    Returns total attempts, correct attempts, and mastery percentage.
    """
    # Students can only view themselves
    user_roles = [r.code for r in user.roles] if user.roles else []
    if SystemRole.STUDENT.value in user_roles and student_id != user.id:
        raise HTTPException(status_code=403, detail="You can only view your own mastery")
    
    service = DailyLoopService(db, user.tenant_id)
    mastery = await service.get_student_topic_mastery(student_id, topic_id)
    
    if not mastery:
        raise HTTPException(status_code=404, detail="No mastery data found for this student+topic")
    
    return mastery


@router.get("/daily/student/{student_id}/mastery", response_model=StudentMasterySummary)
async def get_student_mastery_summary(
    student_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.DAILY_LOOP_VIEW)),
):
    """
    Get summary of student's mastery across all topics.
    
    Returns strong/moderate/weak topic counts and overall mastery.
    """
    user_roles = [r.code for r in user.roles] if user.roles else []
    if SystemRole.STUDENT.value in user_roles and student_id != user.id:
        raise HTTPException(status_code=403, detail="You can only view your own mastery")
    
    service = DailyLoopService(db, user.tenant_id)
    return await service.get_student_mastery_summary(student_id)


@router.get("/daily/my-mastery", response_model=StudentMasterySummary)
async def get_my_mastery_summary(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """
    Get current user's mastery summary.
    
    No special permission required.
    """
    service = DailyLoopService(db, user.tenant_id)
    return await service.get_student_mastery_summary(user.id)


# ============================================
# Strong/Weak Analysis Endpoint
# ============================================

@router.get("/daily/student/{student_id}/topic/{topic_id}/analysis", response_model=StrongWeakAnalysis)
async def get_strong_weak_analysis(
    student_id: UUID,
    topic_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.DAILY_LOOP_VIEW)),
):
    """
    Get strong/weak question analysis for a student on a topic.
    
    Strong = accuracy >= 70%
    Weak = accuracy < 40%
    
    Useful for adaptive question selection and targeted practice.
    """
    user_roles = [r.code for r in user.roles] if user.roles else []
    if SystemRole.STUDENT.value in user_roles and student_id != user.id:
        raise HTTPException(status_code=403, detail="You can only view your own analysis")
    
    service = DailyLoopService(db, user.tenant_id)
    return await service.get_strong_weak_questions(student_id, topic_id)


# ============================================
# Stats Endpoint
# ============================================

@router.get("/daily/stats", response_model=DailyLoopStats)
async def get_daily_loop_stats(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    _=Depends(require_permission(Permission.DAILY_LOOP_VIEW)),
):
    """Get daily loop statistics."""
    service = DailyLoopService(db, user.tenant_id)
    return await service.get_stats(start_date, end_date)
