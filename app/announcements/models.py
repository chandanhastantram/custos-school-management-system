"""
CUSTOS Announcements Models

Announcements, posts, and school communication.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from uuid import UUID

from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, Index, JSON
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import TenantBaseModel


class PostType(str, Enum):
    """Types of posts/announcements."""
    ANNOUNCEMENT = "announcement"
    NEWS = "news"
    EVENT = "event"
    NOTICE = "notice"
    CIRCULAR = "circular"
    ALERT = "alert"


class PostPriority(str, Enum):
    """Priority levels for posts."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class TargetAudience(str, Enum):
    """Target audience for posts."""
    ALL = "all"
    STUDENTS = "students"
    TEACHERS = "teachers"
    PARENTS = "parents"
    STAFF = "staff"
    SPECIFIC_CLASS = "specific_class"
    SPECIFIC_SECTION = "specific_section"


class Post(TenantBaseModel):
    """
    School Posts / Announcements.
    
    Used for school-wide communication to students, parents, and staff.
    """
    __tablename__ = "posts"
    
    __table_args__ = (
        Index("ix_posts_tenant", "tenant_id", "is_published"),
        Index("ix_posts_type", "tenant_id", "post_type"),
        Index("ix_posts_published", "tenant_id", "published_at"),
    )
    
    # Content
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Type and priority
    post_type: Mapped[PostType] = mapped_column(
        SQLEnum(PostType),
        default=PostType.ANNOUNCEMENT,
    )
    priority: Mapped[PostPriority] = mapped_column(
        SQLEnum(PostPriority),
        default=PostPriority.NORMAL,
    )
    
    # Target audience
    audience: Mapped[TargetAudience] = mapped_column(
        SQLEnum(TargetAudience),
        default=TargetAudience.ALL,
    )
    target_class_ids: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    target_section_ids: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    
    # Attachments
    attachments: Mapped[Optional[List[dict]]] = mapped_column(JSON, nullable=True)
    # [{"name": "Notice.pdf", "url": "...", "size": 1234}]
    
    # Publishing
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Author
    author_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Metadata
    views_count: Mapped[int] = mapped_column(default=0)
    
    # Soft delete
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)


class PostRead(TenantBaseModel):
    """
    Tracks which users have read a post.
    """
    __tablename__ = "post_reads"
    
    __table_args__ = (
        Index("ix_post_reads_post", "post_id", "user_id"),
    )
    
    post_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    read_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
    )
