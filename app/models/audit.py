"""
CUSTOS Audit, Notification & Gamification Models
"""

from datetime import datetime
from enum import Enum
from typing import Optional, TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    String, Text, Boolean, Integer, DateTime, Float,
    ForeignKey, Enum as SQLEnum, JSON,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TenantBaseModel, BaseModel

if TYPE_CHECKING:
    from app.models.user import User


class AuditAction(str, Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    EXPORT = "export"
    IMPORT = "import"


class AuditLog(TenantBaseModel):
    """Audit trail for all actions."""
    __tablename__ = "audit_logs"
    
    user_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    action: Mapped[AuditAction] = mapped_column(SQLEnum(AuditAction), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    old_values: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    new_values: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    user: Mapped[Optional["User"]] = relationship("User", lazy="selectin")


class NotificationType(str, Enum):
    GENERAL = "general"
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    ASSIGNMENT = "assignment"
    GRADE = "grade"
    ANNOUNCEMENT = "announcement"
    REMINDER = "reminder"


class NotificationChannel(str, Enum):
    IN_APP = "in_app"
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"


class Notification(TenantBaseModel):
    """User notification."""
    __tablename__ = "notifications"
    
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    type: Mapped[NotificationType] = mapped_column(SQLEnum(NotificationType), default=NotificationType.GENERAL)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    
    data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    action_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    is_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    user: Mapped["User"] = relationship("User", lazy="selectin")


class GamificationPoints(TenantBaseModel):
    """Points for gamification."""
    __tablename__ = "gamification_points"
    
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    points: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    reference_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    reference_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    
    user: Mapped["User"] = relationship("User", lazy="selectin")


class Badge(TenantBaseModel):
    """Achievement badges."""
    __tablename__ = "badges"
    
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    icon: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    color: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    points_required: Mapped[int] = mapped_column(Integer, default=0)
    
    criteria: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class UserBadge(TenantBaseModel):
    """User earned badges."""
    __tablename__ = "user_badges"
    
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    badge_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("badges.id"), nullable=False)
    awarded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    user: Mapped["User"] = relationship("User", lazy="selectin")
    badge: Mapped["Badge"] = relationship("Badge", lazy="selectin")


class FileUpload(TenantBaseModel):
    """Uploaded files."""
    __tablename__ = "file_uploads"
    
    uploaded_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_name: Mapped[str] = mapped_column(String(255), nullable=False)
    path: Mapped[str] = mapped_column(String(500), nullable=False)
    
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # image, document, video
    
    hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)  # SHA-256
    
    uploader: Mapped["User"] = relationship("User", lazy="selectin")
