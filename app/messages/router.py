"""
CUSTOS Messages Router

API endpoints for messaging and inbox.
"""

from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_tenant_id
from app.auth.dependencies import get_current_user, require_roles
from app.auth.schemas import UserResponse

from app.messages.service import MessagesService
from app.messages.schemas import (
    MessageCreate, MessageUpdate, MessageResponse, MessageListResponse,
    InboxMessage, InboxResponse, UnreadCount,
    TemplateCreate, TemplateResponse,
    InboxSettingsUpdate, InboxSettingsResponse, BulkAction, MessageType,
)


router = APIRouter(tags=["Messages"])


def get_messages_service(
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
) -> MessagesService:
    """Get messages service instance."""
    return MessagesService(db, tenant_id)


# ============================================
# Message Endpoints
# ============================================

@router.get("/types", response_model=List[str])
async def get_message_types():
    """Get list of message types."""
    return [t.value for t in MessageType]


@router.post("/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_message(
    data: MessageCreate,
    service: MessagesService = Depends(get_messages_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """Create a new message or save as draft."""
    message = await service.create_message(
        data, current_user.id, current_user.full_name
    )
    return MessageResponse.model_validate(message)


@router.get("/sent", response_model=MessageListResponse)
async def list_sent_messages(
    message_type: Optional[str] = Query(None, alias="type"),
    is_draft: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: MessagesService = Depends(get_messages_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """List messages sent by current user."""
    messages, total = await service.list_sent_messages(
        sender_id=current_user.id,
        message_type=message_type,
        is_draft=is_draft,
        page=page,
        page_size=page_size,
    )
    
    return MessageListResponse(
        items=[MessageResponse.model_validate(m) for m in messages],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.get("/{message_id}", response_model=MessageResponse)
async def get_message(
    message_id: UUID,
    service: MessagesService = Depends(get_messages_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """Get message details."""
    message = await service.get_message(message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return MessageResponse.model_validate(message)


@router.post("/{message_id}/send", response_model=MessageResponse)
async def send_draft(
    message_id: UUID,
    service: MessagesService = Depends(get_messages_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """Send a draft message."""
    message = await service.send_message(message_id, current_user.id)
    return MessageResponse.model_validate(message)


@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(
    message_id: UUID,
    service: MessagesService = Depends(get_messages_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """Delete a message."""
    await service.delete_message(message_id, current_user.id)


# ============================================
# Inbox Endpoints
# ============================================

@router.get("/inbox", response_model=InboxResponse)
async def get_inbox(
    folder: str = Query("inbox"),
    is_read: Optional[bool] = Query(None),
    is_starred: Optional[bool] = Query(None),
    message_type: Optional[str] = Query(None, alias="type"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: MessagesService = Depends(get_messages_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """Get current user's inbox."""
    recipients, total, unread_count = await service.get_inbox(
        user_id=current_user.id,
        folder=folder,
        is_read=is_read,
        is_starred=is_starred,
        message_type=message_type,
        page=page,
        page_size=page_size,
    )
    
    # Transform to inbox format
    items = []
    for r in recipients:
        msg = await service.get_message(r.message_id)
        if msg:
            items.append(InboxMessage(
                id=r.id,
                message_id=r.message_id,
                subject=msg.subject,
                body_preview=msg.body[:150] if msg.body else "",
                message_type=msg.message_type,
                priority=msg.priority,
                sender_name=msg.sender_name,
                sender_id=msg.sender_id,
                is_read=r.is_read,
                read_at=r.read_at,
                is_starred=r.is_starred,
                is_archived=r.is_archived,
                folder=r.folder,
                has_attachments=bool(msg.attachments),
                sent_at=msg.sent_at,
                created_at=r.created_at,
            ))
    
    return InboxResponse(
        items=items,
        total=total,
        unread_count=unread_count,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.get("/inbox/unread-count", response_model=UnreadCount)
async def get_unread_count(
    service: MessagesService = Depends(get_messages_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """Get unread message count."""
    return await service.get_unread_count(current_user.id)


@router.post("/inbox/mark-read")
async def mark_as_read(
    message_ids: List[UUID],
    service: MessagesService = Depends(get_messages_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """Mark messages as read."""
    count = await service.mark_as_read(current_user.id, message_ids)
    return {"marked_read": count}


@router.post("/inbox/mark-unread")
async def mark_as_unread(
    message_ids: List[UUID],
    service: MessagesService = Depends(get_messages_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """Mark messages as unread."""
    count = await service.mark_as_unread(current_user.id, message_ids)
    return {"marked_unread": count}


@router.post("/inbox/{message_id}/star")
async def toggle_star(
    message_id: UUID,
    service: MessagesService = Depends(get_messages_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """Toggle starred status."""
    is_starred = await service.toggle_starred(current_user.id, message_id)
    return {"is_starred": is_starred}


@router.post("/inbox/archive")
async def archive_messages(
    message_ids: List[UUID],
    service: MessagesService = Depends(get_messages_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """Archive messages."""
    count = await service.archive_messages(current_user.id, message_ids)
    return {"archived": count}


@router.post("/inbox/delete")
async def delete_from_inbox(
    message_ids: List[UUID],
    service: MessagesService = Depends(get_messages_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """Delete messages from inbox."""
    count = await service.delete_from_inbox(current_user.id, message_ids)
    return {"deleted": count}


# ============================================
# Template Endpoints
# ============================================

@router.post("/templates", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    data: TemplateCreate,
    service: MessagesService = Depends(get_messages_service),
    current_user: UserResponse = Depends(require_roles(["admin", "principal", "sub_admin"])),
):
    """Create a message template (admin only)."""
    template = await service.create_template(data, current_user.id)
    return TemplateResponse.model_validate(template)


@router.get("/templates", response_model=List[TemplateResponse])
async def list_templates(
    category: Optional[str] = Query(None),
    service: MessagesService = Depends(get_messages_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """List message templates."""
    templates = await service.list_templates(category)
    return [TemplateResponse.model_validate(t) for t in templates]


# ============================================
# Settings Endpoints
# ============================================

@router.get("/settings", response_model=InboxSettingsResponse)
async def get_inbox_settings(
    service: MessagesService = Depends(get_messages_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """Get current user's inbox settings."""
    settings = await service.get_inbox_settings(current_user.id)
    if not settings:
        # Return defaults
        return InboxSettingsResponse(
            email_notifications=True,
            sms_notifications=False,
            push_notifications=True,
            quiet_hours_enabled=False,
        )
    return InboxSettingsResponse.model_validate(settings)


@router.put("/settings", response_model=InboxSettingsResponse)
async def update_inbox_settings(
    data: InboxSettingsUpdate,
    service: MessagesService = Depends(get_messages_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """Update current user's inbox settings."""
    settings = await service.update_inbox_settings(current_user.id, data)
    return InboxSettingsResponse.model_validate(settings)
