"""
CUSTOS Notification Router
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth.dependencies import CurrentUser, require_permission
from app.users.rbac import Permission
from app.platform.notifications.service import NotificationService
from app.platform.notifications.models import NotificationType


router = APIRouter(tags=["Notifications"])


@router.get("")
async def list_notifications(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    unread_only: bool = False,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    """List notifications."""
    service = NotificationService(db, user.tenant_id)
    notifications, total = await service.get_for_user(
        user.user_id, unread_only, page, size
    )
    return {"items": notifications, "total": total, "page": page, "size": size}


@router.get("/unread-count")
async def get_unread_count(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Get unread count."""
    service = NotificationService(db, user.tenant_id)
    count = await service.get_unread_count(user.user_id)
    return {"unread_count": count}


@router.post("/{notification_id}/read")
async def mark_read(
    notification_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Mark notification as read."""
    service = NotificationService(db, user.tenant_id)
    await service.mark_read(notification_id)
    return {"success": True}


@router.post("/read-all")
async def mark_all_read(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Mark all as read."""
    service = NotificationService(db, user.tenant_id)
    await service.mark_all_read(user.user_id)
    return {"success": True}


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Delete notification."""
    service = NotificationService(db, user.tenant_id)
    await service.delete(notification_id)
    return {"success": True}


@router.post("/send")
async def send_notification(
    user_id: UUID,
    title: str,
    message: str,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    type: NotificationType = NotificationType.INFO,
    _=Depends(require_permission(Permission.NOTIFICATION_SEND)),
):
    """Send notification to user."""
    service = NotificationService(db, user.tenant_id)
    notification = await service.create(user_id, title, message, type)
    return {"notification": notification}


@router.post("/send-section/{section_id}")
async def send_to_section(
    section_id: UUID,
    title: str,
    message: str,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.NOTIFICATION_SEND)),
):
    """Send notification to section."""
    service = NotificationService(db, user.tenant_id)
    count = await service.notify_section(section_id, title, message)
    return {"sent_count": count}
