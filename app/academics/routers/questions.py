"""
CUSTOS Questions Router
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth.dependencies import CurrentUser, require_permission
from app.users.rbac import Permission
from app.academics.services.question_service import QuestionService
from app.academics.models.questions import QuestionType, DifficultyLevel, QuestionStatus


router = APIRouter(tags=["Questions"])


@router.get("")
async def list_questions(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    subject_id: Optional[UUID] = None,
    topic_id: Optional[UUID] = None,
    question_type: Optional[QuestionType] = None,
    difficulty: Optional[DifficultyLevel] = None,
    status: Optional[QuestionStatus] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    """List questions."""
    service = QuestionService(db, user.tenant_id)
    questions, total = await service.get_questions(
        subject_id, topic_id, question_type, difficulty, status, page, size
    )
    return {
        "items": questions,
        "total": total,
        "page": page,
        "size": size,
    }


@router.post("")
async def create_question(
    subject_id: UUID,
    question_type: QuestionType,
    question_text: str,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    topic_id: Optional[UUID] = None,
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM,
    options: Optional[list] = None,
    correct_answer: Optional[str] = None,
    marks: float = 1.0,
    _=Depends(require_permission(Permission.QUESTION_CREATE)),
):
    """Create question."""
    service = QuestionService(db, user.tenant_id)
    return await service.create_question(
        subject_id=subject_id,
        question_type=question_type,
        question_text=question_text,
        created_by=user.user_id,
        topic_id=topic_id,
        difficulty=difficulty,
        options=options,
        correct_answer=correct_answer,
        marks=marks,
    )


@router.get("/{question_id}")
async def get_question(
    question_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Get question by ID."""
    service = QuestionService(db, user.tenant_id)
    return await service.get_question(question_id)


@router.post("/{question_id}/approve")
async def approve_question(
    question_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.QUESTION_APPROVE)),
):
    """Approve question."""
    service = QuestionService(db, user.tenant_id)
    return await service.approve_question(question_id, user.user_id)


@router.post("/{question_id}/reject")
async def reject_question(
    question_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    reason: Optional[str] = None,
    _=Depends(require_permission(Permission.QUESTION_APPROVE)),
):
    """Reject question."""
    service = QuestionService(db, user.tenant_id)
    return await service.reject_question(question_id, user.user_id, reason)
