"""
CUSTOS Post Service

Announcements and posts management.
"""

from datetime import datetime, timezone
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundError
from app.models.post import Post, PostType, Priority
from app.schemas.post import PostCreate, PostUpdate


class PostService:
    """Post management service."""
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
    
    async def create_post(
        self,
        data: PostCreate,
        created_by: UUID,
    ) -> Post:
        """Create post/announcement."""
        post = Post(
            tenant_id=self.tenant_id,
            created_by=created_by,
            title=data.title,
            content=data.content,
            content_html=data.content_html,
            post_type=data.post_type,
            priority=data.priority or Priority.NORMAL,
            target_roles=data.target_roles,
            target_sections=[str(s) for s in data.target_sections] if data.target_sections else None,
            publish_at=data.publish_at,
            expire_at=data.expire_at,
            attachments=data.attachments,
            is_pinned=data.is_pinned or False,
            allow_comments=data.allow_comments or True,
        )
        
        if not data.publish_at or data.publish_at <= datetime.now(timezone.utc):
            post.is_published = True
            post.published_at = datetime.now(timezone.utc)
        
        self.session.add(post)
        await self.session.commit()
        await self.session.refresh(post)
        return post
    
    async def get_posts(
        self,
        post_type: Optional[PostType] = None,
        role: Optional[str] = None,
        section_id: Optional[UUID] = None,
        pinned_only: bool = False,
        page: int = 1,
        size: int = 20,
    ) -> tuple[List[Post], int]:
        """Get posts with filters."""
        now = datetime.now(timezone.utc)
        
        query = select(Post).where(
            Post.tenant_id == self.tenant_id,
            Post.is_published == True,
            (Post.expire_at.is_(None)) | (Post.expire_at > now),
        )
        
        if post_type:
            query = query.where(Post.post_type == post_type)
        
        if pinned_only:
            query = query.where(Post.is_pinned == True)
        
        # Count
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0
        
        # Order: pinned first, then by date
        query = query.order_by(Post.is_pinned.desc(), Post.published_at.desc())
        
        skip = (page - 1) * size
        query = query.offset(skip).limit(size)
        result = await self.session.execute(query)
        
        return list(result.scalars().all()), total
    
    async def get_post(self, post_id: UUID) -> Post:
        """Get post by ID."""
        query = select(Post).where(
            Post.tenant_id == self.tenant_id,
            Post.id == post_id
        )
        result = await self.session.execute(query)
        post = result.scalar_one_or_none()
        if not post:
            raise ResourceNotFoundError("Post", str(post_id))
        return post
    
    async def update_post(self, post_id: UUID, data: PostUpdate) -> Post:
        """Update post."""
        post = await self.get_post(post_id)
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(post, key, value)
        
        await self.session.commit()
        await self.session.refresh(post)
        return post
    
    async def delete_post(self, post_id: UUID) -> bool:
        """Delete post."""
        post = await self.get_post(post_id)
        await self.session.delete(post)
        await self.session.commit()
        return True
    
    async def publish_post(self, post_id: UUID) -> Post:
        """Publish post."""
        post = await self.get_post(post_id)
        post.is_published = True
        post.published_at = datetime.now(timezone.utc)
        await self.session.commit()
        return post
    
    async def pin_post(self, post_id: UUID, pinned: bool = True) -> Post:
        """Pin or unpin post."""
        post = await self.get_post(post_id)
        post.is_pinned = pinned
        await self.session.commit()
        return post
    
    async def increment_view_count(self, post_id: UUID) -> None:
        """Increment view count."""
        post = await self.get_post(post_id)
        post.view_count += 1
        await self.session.commit()
