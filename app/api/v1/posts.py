"""
CUSTOS Post API Endpoints

Posts and announcements routes.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth import AuthUser, TenantCtx, require_permissions, Permission
from app.services.post_service import PostService
from app.schemas.post import PostCreate, PostUpdate, PostResponse
from app.schemas.common import SuccessResponse
from app.models.post import PostType


router = APIRouter(prefix="/posts", tags=["Posts"])


@router.get("", response_model=dict)
async def list_posts(
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    post_type: Optional[PostType] = None,
    pinned_only: bool = False,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    """List posts/announcements."""
    service = PostService(db, ctx.tenant_id)
    posts, total = await service.get_posts(
        post_type=post_type,
        pinned_only=pinned_only,
        page=page,
        size=size,
    )
    
    return {
        "items": [PostResponse.model_validate(p) for p in posts],
        "total": total,
        "page": page,
        "size": size,
    }


@router.post("", response_model=PostResponse)
async def create_post(
    data: PostCreate,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    _: AuthUser = Depends(require_permissions(Permission.POST_CREATE)),
):
    """Create post/announcement."""
    service = PostService(db, ctx.tenant_id)
    post = await service.create_post(data, ctx.user.user_id)
    return PostResponse.model_validate(post)


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: UUID,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
):
    """Get post by ID."""
    service = PostService(db, ctx.tenant_id)
    post = await service.get_post(post_id)
    
    # Increment view count
    await service.increment_view_count(post_id)
    
    return PostResponse.model_validate(post)


@router.put("/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: UUID,
    data: PostUpdate,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    _: AuthUser = Depends(require_permissions(Permission.POST_UPDATE)),
):
    """Update post."""
    service = PostService(db, ctx.tenant_id)
    post = await service.update_post(post_id, data)
    return PostResponse.model_validate(post)


@router.delete("/{post_id}", response_model=SuccessResponse)
async def delete_post(
    post_id: UUID,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    _: AuthUser = Depends(require_permissions(Permission.POST_DELETE)),
):
    """Delete post."""
    service = PostService(db, ctx.tenant_id)
    await service.delete_post(post_id)
    return SuccessResponse(message="Post deleted")


@router.post("/{post_id}/publish", response_model=PostResponse)
async def publish_post(
    post_id: UUID,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    _: AuthUser = Depends(require_permissions(Permission.POST_CREATE)),
):
    """Publish post."""
    service = PostService(db, ctx.tenant_id)
    post = await service.publish_post(post_id)
    return PostResponse.model_validate(post)


@router.post("/{post_id}/pin", response_model=PostResponse)
async def pin_post(
    post_id: UUID,
    pinned: bool = True,
    ctx: TenantCtx = None,
    db: AsyncSession = Depends(get_db),
    _: AuthUser = Depends(require_permissions(Permission.POST_UPDATE)),
):
    """Pin or unpin post."""
    service = PostService(db, ctx.tenant_id)
    post = await service.pin_post(post_id, pinned)
    return PostResponse.model_validate(post)
