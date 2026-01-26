"""
CUSTOS Gamification API Endpoints

Points, badges, leaderboard routes.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth import AuthUser, TenantCtx, require_permissions, Permission
from app.services.gamification_service import GamificationService
from app.schemas.common import SuccessResponse


router = APIRouter(prefix="/gamification", tags=["Gamification"])


# ==================== Points ====================

@router.get("/my-points")
async def get_my_points(
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
):
    """Get current user's total points."""
    service = GamificationService(db, ctx.tenant_id)
    points = await service.get_user_points(ctx.user.user_id)
    rank = await service.get_user_rank(ctx.user.user_id)
    
    return {
        "user_id": str(ctx.user.user_id),
        "total_points": points,
        "rank": rank,
    }


@router.get("/my-points/history")
async def get_my_points_history(
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    """Get current user's points history."""
    service = GamificationService(db, ctx.tenant_id)
    history, total = await service.get_points_history(
        ctx.user.user_id, page, size
    )
    
    return {
        "items": [
            {
                "action": h.action,
                "points": h.points,
                "description": h.description,
                "created_at": str(h.created_at),
            }
            for h in history
        ],
        "total": total,
        "page": page,
        "size": size,
    }


@router.get("/user/{user_id}/points")
async def get_user_points(
    user_id: UUID,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
):
    """Get user's total points."""
    service = GamificationService(db, ctx.tenant_id)
    points = await service.get_user_points(user_id)
    return {"user_id": str(user_id), "total_points": points}


@router.post("/award-points")
async def award_points(
    user_id: UUID,
    action: str,
    points: int,
    description: str = None,
    ctx: TenantCtx = None,
    db: AsyncSession = Depends(get_db),
    _: AuthUser = Depends(require_permissions(Permission.GAMIFICATION_MANAGE)),
):
    """Award points to user (admin)."""
    service = GamificationService(db, ctx.tenant_id)
    record = await service.award_points(
        user_id=user_id,
        action=action,
        points=points,
        description=description,
    )
    
    return {
        "id": str(record.id),
        "points": record.points,
        "action": record.action,
    }


# ==================== Leaderboard ====================

@router.get("/leaderboard")
async def get_leaderboard(
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    section_id: Optional[UUID] = None,
    limit: int = Query(10, ge=1, le=100),
):
    """Get points leaderboard."""
    service = GamificationService(db, ctx.tenant_id)
    leaderboard = await service.get_leaderboard(section_id, limit)
    return {"leaderboard": leaderboard}


@router.get("/my-rank")
async def get_my_rank(
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
):
    """Get current user's rank."""
    service = GamificationService(db, ctx.tenant_id)
    rank = await service.get_user_rank(ctx.user.user_id)
    return {"rank": rank}


# ==================== Badges ====================

@router.get("/badges")
async def list_badges(
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
):
    """List all available badges."""
    service = GamificationService(db, ctx.tenant_id)
    badges = await service.get_badges()
    
    return {
        "badges": [
            {
                "id": str(b.id),
                "name": b.name,
                "code": b.code,
                "description": b.description,
                "icon": b.icon,
                "points_required": b.points_required,
                "color": b.color,
            }
            for b in badges
        ]
    }


@router.post("/badges")
async def create_badge(
    name: str,
    code: str,
    description: str,
    icon: str,
    points_required: int = 0,
    color: str = None,
    ctx: TenantCtx = None,
    db: AsyncSession = Depends(get_db),
    _: AuthUser = Depends(require_permissions(Permission.GAMIFICATION_MANAGE)),
):
    """Create badge (admin)."""
    service = GamificationService(db, ctx.tenant_id)
    badge = await service.create_badge(
        name=name,
        code=code,
        description=description,
        icon=icon,
        points_required=points_required,
        color=color,
    )
    
    return {
        "id": str(badge.id),
        "name": badge.name,
        "code": badge.code,
    }


@router.get("/my-badges")
async def get_my_badges(
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
):
    """Get current user's badges."""
    service = GamificationService(db, ctx.tenant_id)
    badges = await service.get_user_badges(ctx.user.user_id)
    
    return {
        "badges": [
            {
                "id": str(b.id),
                "name": b.name,
                "icon": b.icon,
                "description": b.description,
            }
            for b in badges
        ]
    }


@router.get("/user/{user_id}/badges")
async def get_user_badges(
    user_id: UUID,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
):
    """Get user's badges."""
    service = GamificationService(db, ctx.tenant_id)
    badges = await service.get_user_badges(user_id)
    
    return {
        "badges": [
            {
                "id": str(b.id),
                "name": b.name,
                "icon": b.icon,
            }
            for b in badges
        ]
    }


@router.post("/user/{user_id}/award-badge/{badge_id}")
async def award_badge(
    user_id: UUID,
    badge_id: UUID,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    _: AuthUser = Depends(require_permissions(Permission.GAMIFICATION_MANAGE)),
):
    """Award badge to user (admin)."""
    service = GamificationService(db, ctx.tenant_id)
    user_badge = await service.award_badge(user_id, badge_id)
    
    return {
        "user_id": str(user_id),
        "badge_id": str(badge_id),
        "awarded_at": str(user_badge.awarded_at),
    }
