"""
CUSTOS Gamification Service
"""

from datetime import datetime, timezone
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.platform.gamification.models import Points, Badge, UserBadge


POINT_VALUES = {
    "assignment_submit": 10,
    "assignment_pass": 20,
    "assignment_perfect": 50,
    "question_correct": 5,
    "streak_7_days": 100,
    "first_submission": 25,
}


class GamificationService:
    """Gamification management."""
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
    
    async def award_points(
        self,
        user_id: UUID,
        action: str,
        points: int,
        description: Optional[str] = None,
        reference_type: Optional[str] = None,
        reference_id: Optional[UUID] = None,
    ) -> Points:
        """Award points to user."""
        record = Points(
            tenant_id=self.tenant_id,
            user_id=user_id,
            action=action,
            points=points,
            description=description,
            reference_type=reference_type,
            reference_id=reference_id,
        )
        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)
        
        # Check for badge eligibility
        await self._check_badges(user_id)
        
        return record
    
    async def get_user_points(self, user_id: UUID) -> int:
        """Get total points for user."""
        query = select(func.sum(Points.points)).where(
            Points.tenant_id == self.tenant_id,
            Points.user_id == user_id,
        )
        result = await self.session.execute(query)
        return result.scalar() or 0
    
    async def get_leaderboard(self, limit: int = 10) -> List[dict]:
        """Get points leaderboard."""
        from app.users.models import User
        
        query = select(
            Points.user_id,
            func.sum(Points.points).label("total_points")
        ).where(
            Points.tenant_id == self.tenant_id
        ).group_by(
            Points.user_id
        ).order_by(
            func.sum(Points.points).desc()
        ).limit(limit)
        
        result = await self.session.execute(query)
        rows = result.all()
        
        leaderboard = []
        rank = 1
        for user_id, points in rows:
            user = await self.session.get(User, user_id)
            if user:
                leaderboard.append({
                    "rank": rank,
                    "user_id": str(user_id),
                    "name": user.full_name,
                    "points": points or 0,
                })
                rank += 1
        
        return leaderboard
    
    async def get_user_rank(self, user_id: UUID) -> int:
        """Get user's rank."""
        user_points = await self.get_user_points(user_id)
        
        query = select(func.count()).select_from(
            select(func.sum(Points.points)).where(
                Points.tenant_id == self.tenant_id
            ).group_by(
                Points.user_id
            ).having(
                func.sum(Points.points) > user_points
            ).subquery()
        )
        result = await self.session.execute(query)
        higher_count = result.scalar() or 0
        
        return higher_count + 1
    
    async def create_badge(
        self,
        name: str,
        code: str,
        description: str,
        points_required: int = 0,
        icon: Optional[str] = None,
        color: Optional[str] = None,
    ) -> Badge:
        """Create badge."""
        badge = Badge(
            tenant_id=self.tenant_id,
            name=name,
            code=code,
            description=description,
            points_required=points_required,
            icon=icon,
            color=color,
        )
        self.session.add(badge)
        await self.session.commit()
        await self.session.refresh(badge)
        return badge
    
    async def get_badges(self) -> List[Badge]:
        """Get all badges."""
        query = select(Badge).where(
            Badge.tenant_id == self.tenant_id,
            Badge.is_active == True,
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_user_badges(self, user_id: UUID) -> List[Badge]:
        """Get user's badges."""
        query = select(Badge).join(UserBadge).where(
            UserBadge.tenant_id == self.tenant_id,
            UserBadge.user_id == user_id,
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def award_badge(self, user_id: UUID, badge_id: UUID) -> UserBadge:
        """Award badge to user."""
        # Check if already has
        existing = await self.session.execute(
            select(UserBadge).where(
                UserBadge.tenant_id == self.tenant_id,
                UserBadge.user_id == user_id,
                UserBadge.badge_id == badge_id,
            )
        )
        if existing.scalar_one_or_none():
            return existing.scalar_one()
        
        user_badge = UserBadge(
            tenant_id=self.tenant_id,
            user_id=user_id,
            badge_id=badge_id,
            awarded_at=datetime.now(timezone.utc),
        )
        self.session.add(user_badge)
        await self.session.commit()
        await self.session.refresh(user_badge)
        return user_badge
    
    async def _check_badges(self, user_id: UUID) -> None:
        """Check and award badges based on points."""
        total_points = await self.get_user_points(user_id)
        user_badges = await self.get_user_badges(user_id)
        user_badge_ids = {b.id for b in user_badges}
        
        all_badges = await self.get_badges()
        
        for badge in all_badges:
            if badge.id not in user_badge_ids and badge.points_required <= total_points:
                await self.award_badge(user_id, badge.id)
