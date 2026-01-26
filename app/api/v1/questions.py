"""
CUSTOS Questions API Endpoints

Question bank routes.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth import AuthUser, TenantCtx, require_permissions, Permission
from app.services.question_service import QuestionService
from app.schemas.question import (
    QuestionCreate, QuestionUpdate, QuestionResponse,
    QuestionListResponse, QuestionFilter, QuestionAttemptCreate,
    QuestionAttemptResponse,
)
from app.schemas.common import SuccessResponse
from app.models.question import QuestionType, BloomLevel, Difficulty


router = APIRouter(prefix="/questions", tags=["Questions"])


@router.get("", response_model=QuestionListResponse)
async def list_questions(
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    topic_id: Optional[UUID] = None,
    question_type: Optional[QuestionType] = None,
    difficulty: Optional[Difficulty] = None,
    bloom_level: Optional[BloomLevel] = None,
    is_reviewed: Optional[bool] = None,
    search: Optional[str] = None,
):
    """List questions with filters."""
    service = QuestionService(db, ctx.tenant_id)
    
    filters = QuestionFilter(
        topic_id=topic_id,
        question_type=question_type,
        difficulty=difficulty,
        bloom_level=bloom_level,
        is_reviewed=is_reviewed,
        search=search,
    )
    
    questions, total = await service.list_questions(filters, page, size)
    
    return QuestionListResponse(
        items=[QuestionResponse.model_validate(q) for q in questions],
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size,
    )


@router.post("", response_model=QuestionResponse)
async def create_question(
    data: QuestionCreate,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    _: AuthUser = Depends(require_permissions(Permission.QUESTION_CREATE)),
):
    """Create new question."""
    service = QuestionService(db, ctx.tenant_id)
    question = await service.create_question(data, ctx.user.user_id)
    return QuestionResponse.model_validate(question)


@router.get("/{question_id}", response_model=QuestionResponse)
async def get_question(
    question_id: UUID,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
):
    """Get question by ID."""
    service = QuestionService(db, ctx.tenant_id)
    question = await service.get_question(question_id)
    return QuestionResponse.model_validate(question)


@router.put("/{question_id}", response_model=QuestionResponse)
async def update_question(
    question_id: UUID,
    data: QuestionUpdate,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    _: AuthUser = Depends(require_permissions(Permission.QUESTION_UPDATE)),
):
    """Update question."""
    service = QuestionService(db, ctx.tenant_id)
    question = await service.update_question(question_id, data)
    return QuestionResponse.model_validate(question)


@router.delete("/{question_id}", response_model=SuccessResponse)
async def delete_question(
    question_id: UUID,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    _: AuthUser = Depends(require_permissions(Permission.QUESTION_DELETE)),
):
    """Delete question."""
    service = QuestionService(db, ctx.tenant_id)
    await service.delete_question(question_id, ctx.user.user_id)
    return SuccessResponse(message="Question deleted")


@router.post("/{question_id}/review", response_model=QuestionResponse)
async def review_question(
    question_id: UUID,
    approved: bool,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    _: AuthUser = Depends(require_permissions(Permission.QUESTION_APPROVE)),
):
    """Review and approve/reject question."""
    service = QuestionService(db, ctx.tenant_id)
    question = await service.review_question(question_id, ctx.user.user_id, approved)
    return QuestionResponse.model_validate(question)


@router.post("/bulk", response_model=list[QuestionResponse])
async def bulk_create_questions(
    data: list[QuestionCreate],
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    _: AuthUser = Depends(require_permissions(Permission.QUESTION_CREATE)),
):
    """Bulk create questions."""
    service = QuestionService(db, ctx.tenant_id)
    questions = await service.bulk_create_questions(data, ctx.user.user_id)
    return [QuestionResponse.model_validate(q) for q in questions]


@router.post("/{question_id}/attempt", response_model=QuestionAttemptResponse)
async def submit_attempt(
    question_id: UUID,
    data: QuestionAttemptCreate,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
):
    """Submit answer attempt for a question."""
    service = QuestionService(db, ctx.tenant_id)
    attempt = await service.record_attempt(
        question_id=question_id,
        student_id=ctx.user.user_id,
        answer=data.answer,
        selected_options=data.selected_options,
        assignment_id=data.assignment_id,
        time_taken=data.time_taken_seconds,
    )
    return QuestionAttemptResponse.model_validate(attempt)
