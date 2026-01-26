"""
CUSTOS Gamification Service

Points, badges, and leaderboards.
"""

from datetime import datetime, timezone
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import GamificationPoints, Badge, UserBadge


class GamificationService:
    """Gamification service."""
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
    
    # ==================== Points ====================
    
    async def award_points(
        self,
        user_id: UUID,
        action: str,
        points: int,
        description: Optional[str] = None,
        reference_type: Optional[str] = None,
        reference_id: Optional[UUID] = None,
    ) -> GamificationPoints:
        """Award points to user."""
        record = GamificationPoints(
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
        query = select(func.sum(GamificationPoints.points)).where(
            GamificationPoints.tenant_id == self.tenant_id,
            GamificationPoints.user_id == user_id,
        )
        result = await self.session.execute(query)
        return result.scalar() or 0
    
    async def get_points_history(
        self,
        user_id: UUID,
        page: int = 1,
        size: int = 20,
    ) -> tuple[List[GamificationPoints], int]:
        """Get points history for user."""
        query = select(GamificationPoints).where(
            GamificationPoints.tenant_id == self.tenant_id,
            GamificationPoints.user_id == user_id,
        )
        
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0
        
        query = query.order_by(GamificationPoints.created_at.desc())
        skip = (page - 1) * size
        query = query.offset(skip).limit(size)
        
        result = await self.session.execute(query)
        return list(result.scalars().all()), total
    
    # ==================== Leaderboard ====================
    
    async def get_leaderboard(
        self,
        section_id: Optional[UUID] = None,
        limit: int = 10,
    ) -> List[dict]:
        """Get points leaderboard."""
        from app.models.user import User, StudentProfile
        
        # Aggregate points per user
        query = select(
            GamificationPoints.user_id,
            func.sum(GamificationPoints.points).label("total_points")
        ).where(
            GamificationPoints.tenant_id == self.tenant_id
        ).group_by(
            GamificationPoints.user_id
        ).order_by(
            func.sum(GamificationPoints.points).desc()
        ).limit(limit)
        
        result = await self.session.execute(query)
        rows = result.all()
        
        # Get user details
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
        """Get user's rank in leaderboard."""
        user_points = await self.get_user_points(user_id)
        
        # Count users with more points
        query = select(func.count()).select_from(
            select(func.sum(GamificationPoints.points)).where(
                GamificationPoints.tenant_id == self.tenant_id
            ).group_by(
                GamificationPoints.user_id
            ).having(
                func.sum(GamificationPoints.points) > user_points
            ).subquery()
        )
        result = await self.session.execute(query)
        higher_count = result.scalar() or 0
        
        return higher_count + 1
    
    # ==================== Badges ====================
    
    async def create_badge(
        self,
        name: str,
        code: str,
        description: str,
        icon: str,
        points_required: int = 0,
        color: str = None,
    ) -> Badge:
        """Create badge."""
        badge = Badge(
            tenant_id=self.tenant_id,
            name=name,
            code=code,
            description=description,
            icon=icon,
            points_required=points_required,
            color=color,
        )
        self.session.add(badge)
        await self.session.commit()
        await self.session.refresh(badge)
        return badge
    
    async def get_badges(self) -> List[Badge]:
        """Get all badges."""
        query = select(Badge).where(Badge.tenant_id == self.tenant_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def award_badge(
        self,
        user_id: UUID,
        badge_id: UUID,
    ) -> UserBadge:
        """Award badge to user."""
        # Check if already has badge
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
    
    async def get_user_badges(self, user_id: UUID) -> List[Badge]:
        """Get badges for user."""
        query = select(Badge).join(UserBadge).where(
            UserBadge.tenant_id == self.tenant_id,
            UserBadge.user_id == user_id,
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def _check_badges(self, user_id: UUID) -> None:
        """Check and award badges based on points."""
        total_points = await self.get_user_points(user_id)
        
        # Get badges user doesn't have
        user_badges = await self.get_user_badges(user_id)
        user_badge_ids = {b.id for b in user_badges}
        
        all_badges = await self.get_badges()
        
        for badge in all_badges:
            if badge.id not in user_badge_ids and badge.points_required <= total_points:
                await self.award_badge(user_id, badge.id)
    
    # ==================== Point Actions ====================
    
    POINT_VALUES = {
        "assignment_submit": 10,
        "assignment_pass": 20,
        "assignment_perfect": 50,
        "question_correct": 5,
        "streak_7_days": 100,
        "first_submission": 25,
    }
    
    async def points_for_submission(
        self,
        user_id: UUID,
        submission_id: UUID,
        is_passed: bool,
        is_perfect: bool,
    ) -> int:
        """Award points for assignment submission."""
        total = 0
        
        # Submit points
        await self.award_points(
            user_id=user_id,
            action="assignment_submit",
            points=self.POINT_VALUES["assignment_submit"],
            reference_type="submission",
            reference_id=submission_id,
        )
        total += self.POINT_VALUES["assignment_submit"]
        
        if is_perfect:
            await self.award_points(
                user_id=user_id,
                action="assignment_perfect",
                points=self.POINT_VALUES["assignment_perfect"],
                reference_type="submission",
                reference_id=submission_id,
            )
            total += self.POINT_VALUES["assignment_perfect"]
        elif is_passed:
            await self.award_points(
                user_id=user_id,
                action="assignment_pass",
                points=self.POINT_VALUES["assignment_pass"],
                reference_type="submission",
                reference_id=submission_id,
            )
            total += self.POINT_VALUES["assignment_pass"]
        
        return total
