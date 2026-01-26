"""
CUSTOS Post Schemas

Post and announcement request/response schemas.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.post import PostType, Priority


class PostCreate(BaseModel):
    """Create post/announcement."""
    title: str = Field(..., min_length=1, max_length=200)
    content: str
    content_html: Optional[str] = None
    post_type: PostType = PostType.ANNOUNCEMENT
    priority: Optional[Priority] = Priority.NORMAL
    target_roles: Optional[List[str]] = None
    target_sections: Optional[List[UUID]] = None
    publish_at: Optional[datetime] = None
    expire_at: Optional[datetime] = None
    attachments: Optional[List[str]] = None
    is_pinned: bool = False
    allow_comments: bool = True


class PostUpdate(BaseModel):
    """Update post."""
    title: Optional[str] = None
    content: Optional[str] = None
    content_html: Optional[str] = None
    priority: Optional[Priority] = None
    expire_at: Optional[datetime] = None
    is_pinned: Optional[bool] = None


class PostResponse(BaseModel):
    """Post response."""
    id: UUID
    title: str
    content: str
    content_html: Optional[str]
    post_type: str
    priority: str
    is_published: bool
    published_at: Optional[datetime]
    is_pinned: bool
    view_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True
