"""
CUSTOS AI Router
"""

from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth.dependencies import CurrentUser, require_permission
from app.users.rbac import Permission
from app.ai.service import AIService


router = APIRouter(tags=["AI"])


@router.post("/lesson-plan")
async def generate_lesson_plan(
    subject: str,
    topic: str,
    grade_level: int,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    duration_minutes: int = 45,
    _=Depends(require_permission(Permission.AI_LESSON_PLAN)),
):
    """Generate AI lesson plan."""
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


@router.get("/usage")
async def get_ai_usage(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Get AI usage statistics."""
    service = AIService(db, user.tenant_id)
    return await service.get_usage()
