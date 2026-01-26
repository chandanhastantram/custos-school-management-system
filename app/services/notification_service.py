"""
CUSTOS Notification Service

Notifications and alerts management.
"""

from datetime import datetime, timezone
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import Notification, NotificationType
from app.schemas.notification import NotificationCreate


class NotificationService:
    """Notification management service."""
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
    
    async def create_notification(
        self,
        user_id: UUID,
        data: NotificationCreate,
    ) -> Notification:
        """Create notification for user."""
        notification = Notification(
            tenant_id=self.tenant_id,
            user_id=user_id,
            type=data.type,
            title=data.title,
            message=data.message,
            data=data.data,
            action_url=data.action_url,
        )
        self.session.add(notification)
        await self.session.commit()
        await self.session.refresh(notification)
        return notification
    
    async def create_bulk_notifications(
        self,
        user_ids: List[UUID],
        data: NotificationCreate,
    ) -> int:
        """Create notifications for multiple users."""
        count = 0
        for user_id in user_ids:
            notification = Notification(
                tenant_id=self.tenant_id,
                user_id=user_id,
                type=data.type,
                title=data.title,
                message=data.message,
                data=data.data,
                action_url=data.action_url,
            )
            self.session.add(notification)
            count += 1
        
        await self.session.commit()
        return count
    
    async def get_user_notifications(
        self,
        user_id: UUID,
        unread_only: bool = False,
        page: int = 1,
        size: int = 20,
    ) -> tuple[List[Notification], int]:
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
        
        query = query.order_by(Notification.created_at.desc())
        skip = (page - 1) * size
        query = query.offset(skip).limit(size)
        
        result = await self.session.execute(query)
        return list(result.scalars().all()), total
    
    async def get_unread_count(self, user_id: UUID) -> int:
        """Get unread notification count."""
        query = select(func.count()).select_from(Notification).where(
            Notification.tenant_id == self.tenant_id,
            Notification.user_id == user_id,
            Notification.is_read == False,
        )
        result = await self.session.execute(query)
        return result.scalar() or 0
    
    async def mark_as_read(self, notification_id: UUID, user_id: UUID) -> bool:
        """Mark notification as read."""
        query = select(Notification).where(
            Notification.tenant_id == self.tenant_id,
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
        result = await self.session.execute(query)
        notification = result.scalar_one_or_none()
        
        if notification:
            notification.is_read = True
            notification.read_at = datetime.now(timezone.utc)
            await self.session.commit()
            return True
        return False
    
    async def mark_all_as_read(self, user_id: UUID) -> int:
        """Mark all notifications as read."""
        stmt = update(Notification).where(
            Notification.tenant_id == self.tenant_id,
            Notification.user_id == user_id,
            Notification.is_read == False,
        ).values(
            is_read=True,
            read_at=datetime.now(timezone.utc),
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount
    
    async def delete_notification(self, notification_id: UUID, user_id: UUID) -> bool:
        """Delete notification."""
        query = select(Notification).where(
            Notification.tenant_id == self.tenant_id,
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
        result = await self.session.execute(query)
        notification = result.scalar_one_or_none()
        
        if notification:
            await self.session.delete(notification)
            await self.session.commit()
            return True
        return False
    
    # ==================== Notification Triggers ====================
    
    async def notify_assignment_created(
        self,
        section_id: UUID,
        assignment_title: str,
        assignment_id: UUID,
    ) -> int:
        """Notify students about new assignment."""
        from app.models.user import User, StudentProfile
        
        # Get students in section
        students = await self.session.execute(
            select(User.id).join(StudentProfile).where(
                User.tenant_id == self.tenant_id,
                StudentProfile.section_id == section_id,
            )
        )
        student_ids = [s[0] for s in students.all()]
        
        return await self.create_bulk_notifications(
            user_ids=student_ids,
            data=NotificationCreate(
                type=NotificationType.ASSIGNMENT,
                title="New Assignment",
                message=f"New assignment: {assignment_title}",
                action_url=f"/assignments/{assignment_id}",
            ),
        )
    
    async def notify_submission_graded(
        self,
        student_id: UUID,
        assignment_title: str,
        submission_id: UUID,
        marks: float,
    ) -> Notification:
        """Notify student about graded submission."""
        return await self.create_notification(
            user_id=student_id,
            data=NotificationCreate(
                type=NotificationType.GRADE,
                title="Assignment Graded",
                message=f"Your submission for '{assignment_title}' has been graded. Marks: {marks}",
                action_url=f"/submissions/{submission_id}",
            ),
        )
