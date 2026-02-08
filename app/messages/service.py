"""
CUSTOS Messages Service

Business logic for messaging and inbox.
"""

import logging
from datetime import datetime
from typing import Optional, List, Tuple
from uuid import UUID, uuid4

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.messages.models import (
    Message, MessageRecipient, MessageThread, MessageTemplate, UserInboxSettings,
    MessageType, MessagePriority, RecipientType
)
from app.messages.schemas import (
    MessageCreate, MessageUpdate, TemplateCreate, InboxSettingsUpdate, BulkAction
)
from app.core.exceptions import NotFoundError, ValidationError

logger = logging.getLogger(__name__)


class MessagesService:
    """Service for messaging and inbox management."""
    
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
    
    # ============================================
    # Message CRUD
    # ============================================
    
    async def create_message(
        self,
        data: MessageCreate,
        sender_id: UUID,
        sender_name: Optional[str] = None
    ) -> Message:
        """Create a new message."""
        message = Message(
            tenant_id=self.tenant_id,
            message_number=self._generate_message_number() if not data.is_draft else None,
            subject=data.subject,
            body=data.body,
            body_html=data.body_html,
            message_type=data.message_type,
            priority=data.priority,
            sender_id=sender_id,
            sender_name=sender_name,
            recipient_type=data.recipient_type,
            target_class_id=data.target_class_id,
            target_section_id=data.target_section_id,
            target_department_id=data.target_department_id,
            target_role=data.target_role,
            delivery_channels=data.delivery_channels,
            is_scheduled=data.is_scheduled,
            scheduled_at=data.scheduled_at,
            expires_at=data.expires_at,
            is_reply_allowed=data.is_reply_allowed,
            is_draft=data.is_draft,
            attachments=[a.model_dump() for a in data.attachments] if data.attachments else None,
        )
        
        self.db.add(message)
        await self.db.flush()
        
        # Add recipients if specific users provided
        if data.recipient_user_ids and data.recipient_type == RecipientType.USER:
            for user_id in data.recipient_user_ids:
                recipient = MessageRecipient(
                    tenant_id=self.tenant_id,
                    message_id=message.id,
                    user_id=user_id,
                )
                self.db.add(recipient)
            message.total_recipients = len(data.recipient_user_ids)
        
        # If not a draft and not scheduled, mark as sent
        if not data.is_draft and not data.is_scheduled:
            message.is_sent = True
            message.sent_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(message)
        
        logger.info(f"Created message {message.id} by sender {sender_id}")
        return message
    
    async def get_message(self, message_id: UUID) -> Optional[Message]:
        """Get message by ID."""
        result = await self.db.execute(
            select(Message)
            .options(selectinload(Message.recipients))
            .where(
                Message.id == message_id,
                Message.tenant_id == self.tenant_id,
                Message.is_deleted == False
            )
        )
        return result.scalar_one_or_none()
    
    async def list_sent_messages(
        self,
        sender_id: UUID,
        message_type: Optional[str] = None,
        is_draft: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Message], int]:
        """List messages sent by a user."""
        query = select(Message).where(
            Message.tenant_id == self.tenant_id,
            Message.sender_id == sender_id,
            Message.is_deleted == False
        )
        
        if message_type:
            query = query.where(Message.message_type == message_type)
        if is_draft is not None:
            query = query.where(Message.is_draft == is_draft)
        
        # Count
        count_result = await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar()
        
        # Paginate
        query = query.order_by(Message.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.db.execute(query)
        return result.scalars().all(), total
    
    async def send_message(self, message_id: UUID, sender_id: UUID) -> Message:
        """Send a draft message."""
        message = await self.get_message(message_id)
        if not message:
            raise NotFoundError("Message not found")
        
        if message.sender_id != sender_id:
            raise ValidationError("Cannot send another user's message")
        
        if not message.is_draft:
            raise ValidationError("Message is not a draft")
        
        message.is_draft = False
        message.is_sent = True
        message.sent_at = datetime.utcnow()
        message.message_number = self._generate_message_number()
        
        await self.db.commit()
        await self.db.refresh(message)
        return message
    
    async def delete_message(self, message_id: UUID, user_id: UUID) -> bool:
        """Soft delete a message."""
        message = await self.get_message(message_id)
        if not message:
            raise NotFoundError("Message not found")
        
        if message.sender_id != user_id:
            raise ValidationError("Cannot delete another user's message")
        
        message.is_deleted = True
        await self.db.commit()
        return True
    
    # ============================================
    # Inbox
    # ============================================
    
    async def get_inbox(
        self,
        user_id: UUID,
        folder: str = "inbox",
        is_read: Optional[bool] = None,
        is_starred: Optional[bool] = None,
        message_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[MessageRecipient], int, int]:
        """Get user's inbox messages."""
        query = (
            select(MessageRecipient)
            .join(Message)
            .where(
                MessageRecipient.tenant_id == self.tenant_id,
                MessageRecipient.user_id == user_id,
                MessageRecipient.is_deleted_by_user == False,
                MessageRecipient.folder == folder,
                Message.is_deleted == False,
                Message.is_sent == True,
            )
        )
        
        if is_read is not None:
            query = query.where(MessageRecipient.is_read == is_read)
        if is_starred is not None:
            query = query.where(MessageRecipient.is_starred == is_starred)
        if message_type:
            query = query.where(Message.message_type == message_type)
        
        # Count total and unread
        count_result = await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar()
        
        unread_result = await self.db.execute(
            select(func.count()).select_from(
                query.where(MessageRecipient.is_read == False).subquery()
            )
        )
        unread_count = unread_result.scalar()
        
        # Paginate
        query = query.order_by(Message.sent_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.db.execute(query)
        return result.scalars().all(), total, unread_count
    
    async def get_unread_count(self, user_id: UUID) -> dict:
        """Get unread message count for a user."""
        result = await self.db.execute(
            select(
                Message.message_type,
                func.count(MessageRecipient.id)
            )
            .join(Message)
            .where(
                MessageRecipient.tenant_id == self.tenant_id,
                MessageRecipient.user_id == user_id,
                MessageRecipient.is_read == False,
                MessageRecipient.is_deleted_by_user == False,
                Message.is_deleted == False,
                Message.is_sent == True,
            )
            .group_by(Message.message_type)
        )
        
        by_type = {row[0].value: row[1] for row in result.all()}
        total = sum(by_type.values())
        
        return {"total": total, "by_type": by_type}
    
    async def mark_as_read(self, user_id: UUID, message_ids: List[UUID]) -> int:
        """Mark messages as read."""
        result = await self.db.execute(
            select(MessageRecipient).where(
                MessageRecipient.user_id == user_id,
                MessageRecipient.message_id.in_(message_ids),
                MessageRecipient.tenant_id == self.tenant_id,
            )
        )
        recipients = result.scalars().all()
        
        count = 0
        for recipient in recipients:
            if not recipient.is_read:
                recipient.is_read = True
                recipient.read_at = datetime.utcnow()
                count += 1
                
                # Update message read count
                message = await self.get_message(recipient.message_id)
                if message:
                    message.read_count += 1
        
        await self.db.commit()
        return count
    
    async def mark_as_unread(self, user_id: UUID, message_ids: List[UUID]) -> int:
        """Mark messages as unread."""
        result = await self.db.execute(
            select(MessageRecipient).where(
                MessageRecipient.user_id == user_id,
                MessageRecipient.message_id.in_(message_ids),
                MessageRecipient.tenant_id == self.tenant_id,
            )
        )
        recipients = result.scalars().all()
        
        count = 0
        for recipient in recipients:
            if recipient.is_read:
                recipient.is_read = False
                recipient.read_at = None
                count += 1
        
        await self.db.commit()
        return count
    
    async def toggle_starred(self, user_id: UUID, message_id: UUID) -> bool:
        """Toggle starred status."""
        result = await self.db.execute(
            select(MessageRecipient).where(
                MessageRecipient.user_id == user_id,
                MessageRecipient.message_id == message_id,
                MessageRecipient.tenant_id == self.tenant_id,
            )
        )
        recipient = result.scalar_one_or_none()
        
        if not recipient:
            raise NotFoundError("Message not found in inbox")
        
        recipient.is_starred = not recipient.is_starred
        await self.db.commit()
        return recipient.is_starred
    
    async def archive_messages(self, user_id: UUID, message_ids: List[UUID]) -> int:
        """Archive messages."""
        result = await self.db.execute(
            select(MessageRecipient).where(
                MessageRecipient.user_id == user_id,
                MessageRecipient.message_id.in_(message_ids),
                MessageRecipient.tenant_id == self.tenant_id,
            )
        )
        recipients = result.scalars().all()
        
        for recipient in recipients:
            recipient.folder = "archive"
            recipient.is_archived = True
        
        await self.db.commit()
        return len(recipients)
    
    async def delete_from_inbox(self, user_id: UUID, message_ids: List[UUID]) -> int:
        """Delete messages from user's inbox."""
        result = await self.db.execute(
            select(MessageRecipient).where(
                MessageRecipient.user_id == user_id,
                MessageRecipient.message_id.in_(message_ids),
                MessageRecipient.tenant_id == self.tenant_id,
            )
        )
        recipients = result.scalars().all()
        
        for recipient in recipients:
            recipient.is_deleted_by_user = True
            recipient.folder = "trash"
        
        await self.db.commit()
        return len(recipients)
    
    # ============================================
    # Templates
    # ============================================
    
    async def create_template(
        self,
        data: TemplateCreate,
        created_by: UUID
    ) -> MessageTemplate:
        """Create a message template."""
        template = MessageTemplate(
            tenant_id=self.tenant_id,
            code=data.code,
            name=data.name,
            category=data.category,
            subject_template=data.subject_template,
            body_template=data.body_template,
            variables=data.variables,
            default_priority=data.default_priority,
            default_channels=data.default_channels,
            created_by=created_by,
        )
        
        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)
        return template
    
    async def list_templates(
        self,
        category: Optional[str] = None
    ) -> List[MessageTemplate]:
        """List message templates."""
        query = select(MessageTemplate).where(
            MessageTemplate.tenant_id == self.tenant_id,
            MessageTemplate.is_active == True,
            MessageTemplate.is_deleted == False,
        )
        
        if category:
            query = query.where(MessageTemplate.category == category)
        
        result = await self.db.execute(query.order_by(MessageTemplate.name))
        return result.scalars().all()
    
    # ============================================
    # Settings
    # ============================================
    
    async def get_inbox_settings(self, user_id: UUID) -> Optional[UserInboxSettings]:
        """Get user's inbox settings."""
        result = await self.db.execute(
            select(UserInboxSettings).where(
                UserInboxSettings.user_id == user_id,
                UserInboxSettings.tenant_id == self.tenant_id,
            )
        )
        return result.scalar_one_or_none()
    
    async def update_inbox_settings(
        self,
        user_id: UUID,
        data: InboxSettingsUpdate
    ) -> UserInboxSettings:
        """Update user's inbox settings."""
        settings = await self.get_inbox_settings(user_id)
        
        if not settings:
            settings = UserInboxSettings(
                tenant_id=self.tenant_id,
                user_id=user_id,
            )
            self.db.add(settings)
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(settings, key, value)
        
        await self.db.commit()
        await self.db.refresh(settings)
        return settings
    
    # ============================================
    # Helpers
    # ============================================
    
    def _generate_message_number(self) -> str:
        """Generate unique message number."""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M")
        random_part = str(uuid4())[:6].upper()
        return f"MSG-{timestamp}-{random_part}"
