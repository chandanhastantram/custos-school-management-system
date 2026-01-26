"""
CUSTOS AI API Endpoints

AI-powered features routes.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth import AuthUser, TenantCtx, require_permissions, Permission
from app.ai import LessonGenerator, QuestionGenerator, DoubtSolver
from app.services.subscription_service import SubscriptionService
from app.schemas.ai import (
    LessonPlanRequest, LessonPlanResponse,
    QuestionGenerationRequest, QuestionGenerationResponse,
    DoubtSolverRequest, DoubtSolverResponse,
    AIUsageResponse,
)


router = APIRouter(prefix="/ai", tags=["AI Features"])


@router.post("/lesson-plan", response_model=LessonPlanResponse)
async def generate_lesson_plan(
    request: LessonPlanRequest,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    _: AuthUser = Depends(require_permissions(Permission.AI_LESSON_PLAN)),
):
    """
    Generate AI-powered lesson plan.
    
    Creates a comprehensive lesson plan based on the topic,
    including objectives, activities, and assessments.
    """
    # Check AI token limit
    sub_service = SubscriptionService(db, ctx.tenant_id)
    await sub_service.check_limit("ai_tokens", 2000)  # Estimated tokens
    
    generator = LessonGenerator(db, ctx.tenant_id, ctx.user.user_id)
    result = await generator.generate(request)
    
    # Track usage
    await sub_service.increment_usage("ai_tokens", result.tokens_used)
    
    return result


@router.post("/generate-questions", response_model=QuestionGenerationResponse)
async def generate_questions(
    request: QuestionGenerationRequest,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    _: AuthUser = Depends(require_permissions(Permission.AI_QUESTION_GEN)),
):
    """
    Generate AI-powered questions.
    
    Creates questions based on topic, difficulty, and type.
    Questions are saved to the question bank for review.
    """
    sub_service = SubscriptionService(db, ctx.tenant_id)
    await sub_service.check_limit("ai_tokens", request.count * 500)
    
    generator = QuestionGenerator(db, ctx.tenant_id, ctx.user.user_id)
    result = await generator.generate(request)
    
    await sub_service.increment_usage("ai_tokens", result.tokens_used)
    
    return result


@router.post("/doubt-solver", response_model=DoubtSolverResponse)
async def solve_doubt(
    request: DoubtSolverRequest,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    _: AuthUser = Depends(require_permissions(Permission.AI_DOUBT_SOLVER)),
):
    """
    AI-powered doubt solving for students.
    
    Provides explanations and related concepts for student questions.
    """
    sub_service = SubscriptionService(db, ctx.tenant_id)
    await sub_service.check_limit("ai_tokens", 1000)
    
    solver = DoubtSolver(db, ctx.tenant_id, ctx.user.user_id)
    result = await solver.solve(request)
    
    await sub_service.increment_usage("ai_tokens", result.tokens_used)
    
    return result


@router.get("/usage", response_model=AIUsageResponse)
async def get_ai_usage(
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
):
    """Get current AI usage statistics."""
    from datetime import datetime, timezone
    
    sub_service = SubscriptionService(db, ctx.tenant_id)
    usage = await sub_service.get_usage_limits()
    subscription = await sub_service.get_current_subscription()
    
    limit = subscription.plan.ai_tokens_monthly if subscription else 0
    
    now = datetime.now(timezone.utc)
    
    return AIUsageResponse(
        tenant_id=ctx.tenant_id,
        year=now.year,
        month=now.month,
        total_tokens=usage.current_ai_tokens,
        limit_tokens=limit,
        remaining_tokens=max(0, limit - usage.current_ai_tokens),
        total_cost=0,  # Would need to track
        request_count=0,  # Would need to track
        usage_by_feature={},  # Would need to track
        is_limit_reached=usage.current_ai_tokens >= limit,
    )
