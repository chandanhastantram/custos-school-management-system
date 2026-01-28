"""
CUSTOS Gamification Router
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth.dependencies import CurrentUser, require_permission
from app.users.rbac import Permission
from app.platform.gamification.service import GamificationService


router = APIRouter(tags=["Gamification"])


@router.get("/my-points")
async def get_my_points(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Get current user's points."""
    service = GamificationService(db, user.tenant_id)
    points = await service.get_user_points(user.user_id)
    rank = await service.get_user_rank(user.user_id)
    return {"points": points, "rank": rank}


@router.get("/leaderboard")
async def get_leaderboard(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    limit: int = Query(10, ge=1, le=100),
):
    """Get leaderboard."""
    service = GamificationService(db, user.tenant_id)
    return {"leaderboard": await service.get_leaderboard(limit)}


@router.get("/badges")
async def list_badges(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """List all badges."""
    service = GamificationService(db, user.tenant_id)
    return {"badges": await service.get_badges()}


@router.get("/my-badges")
async def get_my_badges(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Get my badges."""
    service = GamificationService(db, user.tenant_id)
    return {"badges": await service.get_user_badges(user.user_id)}


@router.post("/badges")
async def create_badge(
    name: str,
    code: str,
    description: str,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    points_required: int = 0,
    _=Depends(require_permission(Permission.GAMIFICATION_MANAGE)),
):
    """Create badge."""
    service = GamificationService(db, user.tenant_id)
    return await service.create_badge(name, code, description, points_required)


@router.post("/award-points")
async def award_points(
    user_id: UUID,
    action: str,
    points: int,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    description: Optional[str] = None,
    _=Depends(require_permission(Permission.GAMIFICATION_MANAGE)),
):
    """Award points to user."""
    service = GamificationService(db, user.tenant_id)
    return await service.award_points(user_id, action, points, description)


@router.post("/award-badge")
async def award_badge(
    user_id: UUID,
    badge_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.GAMIFICATION_MANAGE)),
):
    """Award badge to user."""
    service = GamificationService(db, user.tenant_id)
    return await service.award_badge(user_id, badge_id)
