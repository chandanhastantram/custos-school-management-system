"""
CUSTOS Announcements Router

API endpoints for announcements and posts.
"""

from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth.dependencies import CurrentUser, require_permission
from app.users.rbac import Permission
from app.announcements.service import AnnouncementsService
from app.announcements.models import PostType, TargetAudience
from app.announcements.schemas import (
    PostCreate,
    PostUpdate,
    PostResponse,
    PostListResponse,
    PublishPostRequest,
)


router = APIRouter(tags=["Announcements"])


# ============================================
# Posts / Announcements
# ============================================

@router.post("/", response_model=PostResponse, status_code=201)
async def create_post(
    data: PostCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.ANNOUNCEMENT_MANAGE)),
):
    """
    Create a new post/announcement.
    
    Only users with announcement management permission can create posts.
    """
    service = AnnouncementsService(db, user.tenant_id)
    post = await service.create_post(data, user.user_id)
    return PostResponse.model_validate(post)


@router.get("/", response_model=List[PostListResponse])
async def list_posts(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    post_type: Optional[PostType] = None,
    published_only: bool = True,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=50),
):
    """List all posts/announcements."""
    service = AnnouncementsService(db, user.tenant_id)
    posts, _ = await service.list_posts(
        post_type=post_type,
        published_only=published_only,
        page=page,
        size=size,
    )
    
    return [
        PostListResponse(
            id=post.id,
            title=post.title,
            summary=post.summary,
            post_type=post.post_type,
            priority=post.priority,
            is_pinned=post.is_pinned,
            published_at=post.published_at,
            views_count=post.views_count,
            has_attachments=bool(post.attachments),
        )
        for post in posts
    ]


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Get a single post by ID."""
    service = AnnouncementsService(db, user.tenant_id)
    post = await service.get_post(post_id)
    
    # Mark as read
    await service.mark_as_read(post_id, user.user_id)
    
    return PostResponse.model_validate(post)


@router.patch("/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: UUID,
    data: PostUpdate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.ANNOUNCEMENT_MANAGE)),
):
    """Update an existing post."""
    service = AnnouncementsService(db, user.tenant_id)
    post = await service.update_post(post_id, data)
    return PostResponse.model_validate(post)


@router.post("/{post_id}/publish", response_model=PostResponse)
async def publish_post(
    post_id: UUID,
    request: PublishPostRequest,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.ANNOUNCEMENT_MANAGE)),
):
    """Publish or unpublish a post."""
    service = AnnouncementsService(db, user.tenant_id)
    post = await service.publish_post(post_id, request.publish)
    return PostResponse.model_validate(post)


@router.delete("/{post_id}")
async def delete_post(
    post_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.ANNOUNCEMENT_MANAGE)),
):
    """Delete a post (soft delete)."""
    service = AnnouncementsService(db, user.tenant_id)
    await service.delete_post(post_id)
    return {"success": True, "message": "Post deleted"}


# ============================================
# For Specific Audiences
# ============================================

@router.get("/audience/{audience_type}", response_model=List[PostListResponse])
async def get_posts_for_audience(
    audience_type: TargetAudience,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    limit: int = Query(10, ge=1, le=50),
):
    """Get latest posts for a specific audience type."""
    service = AnnouncementsService(db, user.tenant_id)
    posts = await service.get_latest_for_audience(audience_type, limit=limit)
    
    return [
        PostListResponse(
            id=post.id,
            title=post.title,
            summary=post.summary,
            post_type=post.post_type,
            priority=post.priority,
            is_pinned=post.is_pinned,
            published_at=post.published_at,
            views_count=post.views_count,
            has_attachments=bool(post.attachments),
        )
        for post in posts
    ]


@router.get("/unread/count")
async def get_unread_count(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Get count of unread announcements for current user."""
    service = AnnouncementsService(db, user.tenant_id)
    count = await service.get_unread_count(user.user_id)
    return {"unread_count": count}
