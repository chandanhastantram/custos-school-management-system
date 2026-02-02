"""
CUSTOS Announcements Schemas

Pydantic schemas for announcements API.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from app.announcements.models import PostType, PostPriority, TargetAudience


class PostCreate(BaseModel):
    """Schema for creating a post."""
    title: str = Field(..., max_length=300)
    content: str
    summary: Optional[str] = Field(None, max_length=500)
    post_type: PostType = PostType.ANNOUNCEMENT
    priority: PostPriority = PostPriority.NORMAL
    audience: TargetAudience = TargetAudience.ALL
    target_class_ids: Optional[List[UUID]] = None
    target_section_ids: Optional[List[UUID]] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    is_pinned: bool = False
    publish_now: bool = True
    expires_at: Optional[datetime] = None


class PostUpdate(BaseModel):
    """Schema for updating a post."""
    title: Optional[str] = Field(None, max_length=300)
    content: Optional[str] = None
    summary: Optional[str] = Field(None, max_length=500)
    post_type: Optional[PostType] = None
    priority: Optional[PostPriority] = None
    audience: Optional[TargetAudience] = None
    target_class_ids: Optional[List[UUID]] = None
    target_section_ids: Optional[List[UUID]] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    is_pinned: Optional[bool] = None
    expires_at: Optional[datetime] = None


class PostResponse(BaseModel):
    """Schema for post response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    title: str
    content: str
    summary: Optional[str] = None
    post_type: PostType
    priority: PostPriority
    audience: TargetAudience
    target_class_ids: Optional[List[str]] = None
    target_section_ids: Optional[List[str]] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    is_published: bool
    is_pinned: bool
    published_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    author_id: Optional[UUID] = None
    views_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None


class PostListResponse(BaseModel):
    """Schema for listing posts."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    title: str
    summary: Optional[str] = None
    post_type: PostType
    priority: PostPriority
    is_pinned: bool
    published_at: Optional[datetime] = None
    views_count: int = 0
    has_attachments: bool = False


class PublishPostRequest(BaseModel):
    """Schema for publishing a post."""
    publish: bool = True
