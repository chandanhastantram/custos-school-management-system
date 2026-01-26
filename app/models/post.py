"""
CUSTOS Post & Announcement Models
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    String, Text, Boolean, Integer, DateTime,
    ForeignKey, Enum as SQLEnum, JSON,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TenantSoftDeleteModel, TenantBaseModel

if TYPE_CHECKING:
    from app.models.user import User


class PostType(str, Enum):
    ANNOUNCEMENT = "announcement"
    NEWS = "news"
    CIRCULAR = "circular"
    NOTICE = "notice"
    EVENT = "event"


class PostPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class Post(TenantSoftDeleteModel):
    """Announcement/Post model."""
    __tablename__ = "posts"
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_html: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    post_type: Mapped[PostType] = mapped_column(SQLEnum(PostType), nullable=False)
    priority: Mapped[PostPriority] = mapped_column(SQLEnum(PostPriority), default=PostPriority.NORMAL)
    
    author_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    pin_order: Mapped[int] = mapped_column(Integer, default=0)
    
    target_roles: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    target_sections: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    
    attachments: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    
    views_count: Mapped[int] = mapped_column(Integer, default=0)
    
    author: Mapped["User"] = relationship("User", lazy="selectin")


class PostView(TenantBaseModel):
    """Track post views."""
    __tablename__ = "post_views"
    
    post_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("posts.id"), nullable=False, index=True)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    viewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
