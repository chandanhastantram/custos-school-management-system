"""
CUSTOS Messages Schemas

Pydantic schemas for messaging and inbox.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


# ============================================
# Enums
# ============================================

class MessageType(str, Enum):
    PERSONAL = "personal"
    BROADCAST = "broadcast"
    CIRCULAR = "circular"
    ANNOUNCEMENT = "announcement"
    NOTIFICATION = "notification"
    REMINDER = "reminder"
    ALERT = "alert"


class MessagePriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class RecipientType(str, Enum):
    USER = "user"
    CLASS = "class"
    SECTION = "section"
    DEPARTMENT = "department"
    ROLE = "role"
    ALL_STUDENTS = "all_students"
    ALL_TEACHERS = "all_teachers"
    ALL_PARENTS = "all_parents"
    ALL = "all"


class DeliveryChannel(str, Enum):
    IN_APP = "in_app"
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WHATSAPP = "whatsapp"


# ============================================
# Attachment Schema
# ============================================

class Attachment(BaseModel):
    """Schema for message attachment."""
    file_name: str
    file_url: str
    file_type: Optional[str] = None
    file_size: Optional[int] = None


# ============================================
# Message Schemas
# ============================================

class MessageCreate(BaseModel):
    """Schema for creating a message."""
    subject: str = Field(..., min_length=1, max_length=500)
    body: str = Field(..., min_length=1)
    body_html: Optional[str] = None
    
    message_type: MessageType = MessageType.NOTIFICATION
    priority: MessagePriority = MessagePriority.NORMAL
    
    # Recipients
    recipient_type: RecipientType = RecipientType.USER
    recipient_user_ids: Optional[List[UUID]] = None
    target_class_id: Optional[UUID] = None
    target_section_id: Optional[UUID] = None
    target_department_id: Optional[UUID] = None
    target_role: Optional[str] = None
    
    # Delivery
    delivery_channels: List[str] = ["in_app"]
    
    # Options
    is_scheduled: bool = False
    scheduled_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    is_reply_allowed: bool = False
    is_draft: bool = False
    
    # Attachments
    attachments: Optional[List[Attachment]] = None


class MessageUpdate(BaseModel):
    """Schema for updating a message (draft only)."""
    subject: Optional[str] = Field(None, min_length=1, max_length=500)
    body: Optional[str] = None
    body_html: Optional[str] = None
    priority: Optional[MessagePriority] = None
    scheduled_at: Optional[datetime] = None
    attachments: Optional[List[Attachment]] = None


class MessageResponse(BaseModel):
    """Schema for message response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    message_number: Optional[str] = None
    subject: str
    body: str
    body_html: Optional[str] = None
    message_type: MessageType
    priority: MessagePriority
    sender_id: UUID
    sender_name: Optional[str] = None
    recipient_type: RecipientType
    delivery_channels: List[str]
    is_scheduled: bool
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    is_draft: bool
    is_sent: bool
    is_pinned: bool
    expires_at: Optional[datetime] = None
    is_reply_allowed: bool
    total_recipients: int
    read_count: int
    attachments: Optional[List[dict]] = None
    created_at: datetime


class MessageListResponse(BaseModel):
    """Schema for paginated message list."""
    items: List[MessageResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ============================================
# Inbox Schemas
# ============================================

class InboxMessage(BaseModel):
    """Schema for inbox message (from recipient perspective)."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID  # recipient record id
    message_id: UUID
    subject: str
    body_preview: str
    message_type: MessageType
    priority: MessagePriority
    sender_name: Optional[str] = None
    sender_id: UUID
    is_read: bool
    read_at: Optional[datetime] = None
    is_starred: bool
    is_archived: bool
    folder: str
    has_attachments: bool
    sent_at: Optional[datetime] = None
    created_at: datetime


class InboxResponse(BaseModel):
    """Schema for inbox response."""
    items: List[InboxMessage]
    total: int
    unread_count: int
    page: int
    page_size: int
    pages: int


class UnreadCount(BaseModel):
    """Schema for unread message count."""
    total: int
    by_type: dict


# ============================================
# Recipient Schemas
# ============================================

class RecipientResponse(BaseModel):
    """Schema for recipient response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    user_id: UUID
    is_delivered: bool
    delivered_at: Optional[datetime] = None
    is_read: bool
    read_at: Optional[datetime] = None
    is_starred: bool
    is_archived: bool


# ============================================
# Template Schemas
# ============================================

class TemplateCreate(BaseModel):
    """Schema for creating message template."""
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=200)
    category: str
    subject_template: str = Field(..., max_length=500)
    body_template: str
    variables: Optional[List[str]] = None
    default_priority: MessagePriority = MessagePriority.NORMAL
    default_channels: List[str] = ["in_app"]


class TemplateResponse(BaseModel):
    """Schema for template response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    code: str
    name: str
    category: str
    subject_template: str
    body_template: str
    variables: Optional[List[str]] = None
    default_priority: MessagePriority
    default_channels: List[str]
    is_active: bool
    is_system: bool


# ============================================
# Settings Schemas
# ============================================

class InboxSettingsUpdate(BaseModel):
    """Schema for updating inbox settings."""
    email_notifications: Optional[bool] = None
    sms_notifications: Optional[bool] = None
    push_notifications: Optional[bool] = None
    quiet_hours_enabled: Optional[bool] = None
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
    auto_archive_days: Optional[int] = None
    email_signature: Optional[str] = None


class InboxSettingsResponse(BaseModel):
    """Schema for inbox settings response."""
    model_config = ConfigDict(from_attributes=True)
    
    email_notifications: bool
    sms_notifications: bool
    push_notifications: bool
    quiet_hours_enabled: bool
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
    auto_archive_days: Optional[int] = None
    email_signature: Optional[str] = None


# ============================================
# Action Schemas
# ============================================

class BulkAction(BaseModel):
    """Schema for bulk message actions."""
    message_ids: List[UUID]
    action: str  # mark_read, mark_unread, archive, star, unstar, delete


class SendMessageRequest(BaseModel):
    """Schema for sending a draft."""
    message_id: UUID
