"""
CUSTOS Notification API Endpoints

Notifications routes.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth import AuthUser, TenantCtx, require_permissions, Permission
from app.services.notification_service import NotificationService
from app.schemas.notification import NotificationCreate, NotificationResponse
from app.schemas.common import SuccessResponse


router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("")
async def list_notifications(
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    unread_only: bool = False,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    """Get current user's notifications."""
    service = NotificationService(db, ctx.tenant_id)
    notifications, total = await service.get_user_notifications(
        ctx.user.user_id,
        unread_only=unread_only,
        page=page,
        size=size,
    )
    
    return {
        "items": [NotificationResponse.model_validate(n) for n in notifications],
        "total": total,
        "page": page,
        "size": size,
    }


@router.get("/unread-count")
async def get_unread_count(
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
):
    """Get unread notification count."""
    service = NotificationService(db, ctx.tenant_id)
    count = await service.get_unread_count(ctx.user.user_id)
    return {"unread_count": count}


@router.post("/{notification_id}/read", response_model=SuccessResponse)
async def mark_as_read(
    notification_id: UUID,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
):
    """Mark notification as read."""
    service = NotificationService(db, ctx.tenant_id)
    success = await service.mark_as_read(notification_id, ctx.user.user_id)
    return SuccessResponse(success=success, message="Marked as read" if success else "Not found")


@router.post("/read-all", response_model=SuccessResponse)
async def mark_all_as_read(
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
):
    """Mark all notifications as read."""
    service = NotificationService(db, ctx.tenant_id)
    count = await service.mark_all_as_read(ctx.user.user_id)
    return SuccessResponse(message=f"Marked {count} as read")


@router.delete("/{notification_id}", response_model=SuccessResponse)
async def delete_notification(
    notification_id: UUID,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
):
    """Delete notification."""
    service = NotificationService(db, ctx.tenant_id)
    success = await service.delete_notification(notification_id, ctx.user.user_id)
    return SuccessResponse(success=success, message="Deleted" if success else "Not found")


# ==================== Admin Endpoints ====================

@router.post("/send")
async def send_notification(
    user_id: UUID,
    data: NotificationCreate,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    _: AuthUser = Depends(require_permissions(Permission.NOTIFICATION_SEND)),
):
    """Send notification to user."""
    service = NotificationService(db, ctx.tenant_id)
    notification = await service.create_notification(user_id, data)
    return NotificationResponse.model_validate(notification)


@router.post("/send-bulk")
async def send_bulk_notifications(
    user_ids: list[UUID],
    data: NotificationCreate,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    _: AuthUser = Depends(require_permissions(Permission.NOTIFICATION_SEND)),
):
    """Send notification to multiple users."""
    service = NotificationService(db, ctx.tenant_id)
    count = await service.create_bulk_notifications(user_ids, data)
    return {"sent_count": count}
