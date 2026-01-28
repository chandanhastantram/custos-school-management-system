"""
CUSTOS Notification Service
"""

from datetime import datetime, timezone
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.platform.notifications.models import Notification, NotificationType


class NotificationService:
    """Notification management."""
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
    
    async def create(
        self,
        user_id: UUID,
        title: str,
        message: str,
        type: NotificationType = NotificationType.INFO,
        data: Optional[dict] = None,
        action_url: Optional[str] = None,
    ) -> Notification:
        """Create notification."""
        notification = Notification(
            tenant_id=self.tenant_id,
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            data=data,
            action_url=action_url,
        )
        self.session.add(notification)
        await self.session.commit()
        await self.session.refresh(notification)
        return notification
    
    async def get_for_user(
        self,
        user_id: UUID,
        unread_only: bool = False,
        page: int = 1,
        size: int = 20,
    ) -> Tuple[List[Notification], int]:
        """Get notifications for user."""
        query = select(Notification).where(
            Notification.tenant_id == self.tenant_id,
            Notification.user_id == user_id,
        )
        
        if unread_only:
            query = query.where(Notification.is_read == False)
        
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0
        
        skip = (page - 1) * size
        query = query.order_by(Notification.created_at.desc()).offset(skip).limit(size)
        result = await self.session.execute(query)
        
        return list(result.scalars().all()), total
    
    async def get_unread_count(self, user_id: UUID) -> int:
        """Get unread count."""
        query = select(func.count()).where(
            Notification.tenant_id == self.tenant_id,
            Notification.user_id == user_id,
            Notification.is_read == False,
        )
        result = await self.session.execute(query)
        return result.scalar() or 0
    
    async def mark_read(self, notification_id: UUID) -> None:
        """Mark notification as read."""
        query = update(Notification).where(
            Notification.tenant_id == self.tenant_id,
            Notification.id == notification_id,
        ).values(is_read=True, read_at=datetime.now(timezone.utc))
        await self.session.execute(query)
        await self.session.commit()
    
    async def mark_all_read(self, user_id: UUID) -> None:
        """Mark all notifications as read."""
        query = update(Notification).where(
            Notification.tenant_id == self.tenant_id,
            Notification.user_id == user_id,
            Notification.is_read == False,
        ).values(is_read=True, read_at=datetime.now(timezone.utc))
        await self.session.execute(query)
        await self.session.commit()
    
    async def delete(self, notification_id: UUID) -> None:
        """Delete notification."""
        notification = await self.session.get(Notification, notification_id)
        if notification:
            await self.session.delete(notification)
            await self.session.commit()
    
    # Bulk notify
    async def notify_section(
        self,
        section_id: UUID,
        title: str,
        message: str,
        type: NotificationType = NotificationType.INFO,
    ) -> int:
        """Notify all students in section."""
        from app.users.models import User, StudentProfile
        
        query = select(User.id).join(StudentProfile).where(
            User.tenant_id == self.tenant_id,
            StudentProfile.section_id == section_id,
        )
        result = await self.session.execute(query)
        user_ids = [row[0] for row in result.all()]
        
        count = 0
        for user_id in user_ids:
            await self.create(user_id, title, message, type)
            count += 1
        
        return count
