"""
CUSTOS Messages Models

Internal messaging, circulars, and inbox system.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from uuid import UUID

from sqlalchemy import (
    String, Text, Integer, Boolean, DateTime,
    ForeignKey, UniqueConstraint, Index, JSON
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import TenantBaseModel


# ============================================
# Enums
# ============================================

class MessageType(str, Enum):
    """Types of messages."""
    PERSONAL = "personal"           # One-to-one message
    BROADCAST = "broadcast"         # To all users
    CIRCULAR = "circular"           # Official circular
    ANNOUNCEMENT = "announcement"   # Public announcement
    NOTIFICATION = "notification"   # System notification
    REMINDER = "reminder"           # Reminder message
    ALERT = "alert"                 # Important alert


class MessagePriority(str, Enum):
    """Message priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class RecipientType(str, Enum):
    """Types of recipients."""
    USER = "user"                   # Specific user
    CLASS = "class"                 # All students in a class
    SECTION = "section"             # All students in a section
    DEPARTMENT = "department"       # All users in a department
    ROLE = "role"                   # All users with a role
    ALL_STUDENTS = "all_students"   # All students
    ALL_TEACHERS = "all_teachers"   # All teachers
    ALL_PARENTS = "all_parents"     # All parents
    ALL = "all"                     # Everyone


class DeliveryChannel(str, Enum):
    """Delivery channels for messages."""
    IN_APP = "in_app"
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WHATSAPP = "whatsapp"


# ============================================
# Message
# ============================================

class Message(TenantBaseModel):
    """
    Message/Circular/Notification.
    
    Core message entity with support for various types and recipients.
    """
    __tablename__ = "messages"
    __table_args__ = (
        Index("ix_message_tenant_type", "tenant_id", "message_type"),
        Index("ix_message_sender", "tenant_id", "sender_id"),
        Index("ix_message_scheduled", "tenant_id", "scheduled_at"),
        {"extend_existing": True},
    )
    
    # Message identification
    message_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Content
    subject: Mapped[str] = mapped_column(String(500))
    body: Mapped[str] = mapped_column(Text)
    body_html: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Type and priority
    message_type: Mapped[MessageType] = mapped_column(
        SQLEnum(MessageType, name="message_type_enum"),
        default=MessageType.NOTIFICATION
    )
    priority: Mapped[MessagePriority] = mapped_column(
        SQLEnum(MessagePriority, name="message_priority_enum"),
        default=MessagePriority.NORMAL
    )
    
    # Sender
    sender_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
    )
    sender_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # Recipient targeting
    recipient_type: Mapped[RecipientType] = mapped_column(
        SQLEnum(RecipientType, name="recipient_type_enum"),
        default=RecipientType.USER
    )
    target_class_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )
    target_section_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )
    target_department_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )
    target_role: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Delivery channels
    delivery_channels: Mapped[List[str]] = mapped_column(
        JSON, default=["in_app"]
    )
    
    # Scheduling
    is_scheduled: Mapped[bool] = mapped_column(Boolean, default=False)
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Status
    is_draft: Mapped[bool] = mapped_column(Boolean, default=False)
    is_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Expiry
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Attachments
    attachments: Mapped[Optional[List[dict]]] = mapped_column(JSON, nullable=True)
    
    # Reply
    is_reply_allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    reply_to_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("messages.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Tracking
    total_recipients: Mapped[int] = mapped_column(Integer, default=0)
    read_count: Mapped[int] = mapped_column(Integer, default=0)
    delivery_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    recipients: Mapped[List["MessageRecipient"]] = relationship(
        "MessageRecipient",
        back_populates="message",
        cascade="all, delete-orphan",
        lazy="selectin",
        foreign_keys="MessageRecipient.message_id"
    )


# ============================================
# Message Recipient
# ============================================

class MessageRecipient(TenantBaseModel):
    """
    Message recipient with read status.
    
    Tracks delivery and read status per recipient.
    """
    __tablename__ = "message_recipients"
    __table_args__ = (
        UniqueConstraint(
            "message_id", "user_id",
            name="uq_message_recipient"
        ),
        Index("ix_recipient_user", "tenant_id", "user_id"),
        Index("ix_recipient_message", "message_id"),
        Index("ix_recipient_unread", "tenant_id", "user_id", "is_read"),
        {"extend_existing": True},
    )
    
    message_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("messages.id", ondelete="CASCADE"),
    )
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    
    # Status
    is_delivered: Mapped[bool] = mapped_column(Boolean, default=False)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    read_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # User actions
    is_starred: Mapped[bool] = mapped_column(Boolean, default=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    is_deleted_by_user: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Delivery channel used
    delivery_channel: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Folder (for organizing)
    folder: Mapped[str] = mapped_column(String(50), default="inbox")
    
    # Relationship
    message: Mapped["Message"] = relationship(
        "Message", back_populates="recipients",
        foreign_keys=[message_id]
    )


# ============================================
# Message Thread
# ============================================

class MessageThread(TenantBaseModel):
    """
    Message thread for conversations.
    
    Groups related messages together.
    """
    __tablename__ = "message_threads"
    __table_args__ = (
        Index("ix_thread_participants", "tenant_id"),
        {"extend_existing": True},
    )
    
    # Thread info
    subject: Mapped[str] = mapped_column(String(500))
    
    # Participants (JSON array of user IDs)
    participant_ids: Mapped[List[str]] = mapped_column(JSON)
    
    # Last message
    last_message_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    last_message_preview: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # Message count
    message_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Status
    is_closed: Mapped[bool] = mapped_column(Boolean, default=False)


# ============================================
# Message Template
# ============================================

class MessageTemplate(TenantBaseModel):
    """
    Message template for quick messaging.
    
    Pre-defined templates for common messages.
    """
    __tablename__ = "message_templates"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "code",
            name="uq_template_code"
        ),
        Index("ix_template_category", "tenant_id", "category"),
        {"extend_existing": True},
    )
    
    code: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(50))  # fee_reminder, attendance, exam, etc.
    
    subject_template: Mapped[str] = mapped_column(String(500))
    body_template: Mapped[str] = mapped_column(Text)
    
    # Variables (JSON array of variable names)
    variables: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    
    # Default settings
    default_priority: Mapped[MessagePriority] = mapped_column(
        SQLEnum(MessagePriority, name="message_priority_enum"),
        default=MessagePriority.NORMAL
    )
    default_channels: Mapped[List[str]] = mapped_column(
        JSON, default=["in_app"]
    )
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Created by
    created_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )


# ============================================
# User Inbox Settings
# ============================================

class UserInboxSettings(TenantBaseModel):
    """
    User-specific inbox settings and preferences.
    """
    __tablename__ = "user_inbox_settings"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "user_id",
            name="uq_inbox_settings"
        ),
        {"extend_existing": True},
    )
    
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    
    # Notification preferences
    email_notifications: Mapped[bool] = mapped_column(Boolean, default=True)
    sms_notifications: Mapped[bool] = mapped_column(Boolean, default=False)
    push_notifications: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Quiet hours
    quiet_hours_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    quiet_hours_start: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # HH:MM
    quiet_hours_end: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    
    # Auto-archive after days
    auto_archive_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Signature
    email_signature: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
