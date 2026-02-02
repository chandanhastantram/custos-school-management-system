"""
CUSTOS Announcements Service

Business logic for announcements and posts.
"""

from datetime import datetime, timezone
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundError, ValidationError
from app.announcements.models import Post, PostRead, PostType, PostPriority, TargetAudience
from app.announcements.schemas import PostCreate, PostUpdate


class AnnouncementsService:
    """Service for managing announcements and posts."""
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
    
    async def create_post(
        self, 
        data: PostCreate, 
        author_id: UUID,
    ) -> Post:
        """Create a new post/announcement."""
        post = Post(
            tenant_id=self.tenant_id,
            title=data.title,
            content=data.content,
            summary=data.summary,
            post_type=data.post_type,
            priority=data.priority,
            audience=data.audience,
            target_class_ids=[str(c) for c in data.target_class_ids] if data.target_class_ids else None,
            target_section_ids=[str(s) for s in data.target_section_ids] if data.target_section_ids else None,
            attachments=data.attachments,
            is_pinned=data.is_pinned,
            is_published=data.publish_now,
            published_at=datetime.now(timezone.utc) if data.publish_now else None,
            expires_at=data.expires_at,
            author_id=author_id,
        )
        
        self.session.add(post)
        await self.session.commit()
        await self.session.refresh(post)
        return post
    
    async def update_post(
        self, 
        post_id: UUID, 
        data: PostUpdate,
    ) -> Post:
        """Update an existing post."""
        post = await self.get_post(post_id)
        
        update_data = data.model_dump(exclude_unset=True)
        
        # Handle special fields
        if "target_class_ids" in update_data and update_data["target_class_ids"]:
            update_data["target_class_ids"] = [str(c) for c in update_data["target_class_ids"]]
        if "target_section_ids" in update_data and update_data["target_section_ids"]:
            update_data["target_section_ids"] = [str(s) for s in update_data["target_section_ids"]]
        
        for key, value in update_data.items():
            if value is not None:
                setattr(post, key, value)
        
        await self.session.commit()
        await self.session.refresh(post)
        return post
    
    async def get_post(self, post_id: UUID) -> Post:
        """Get a post by ID."""
        query = select(Post).where(
            Post.tenant_id == self.tenant_id,
            Post.id == post_id,
            Post.is_deleted == False,
        )
        result = await self.session.execute(query)
        post = result.scalar_one_or_none()
        
        if not post:
            raise ResourceNotFoundError("Post", str(post_id))
        
        return post
    
    async def list_posts(
        self,
        post_type: Optional[PostType] = None,
        audience: Optional[TargetAudience] = None,
        published_only: bool = True,
        include_expired: bool = False,
        page: int = 1,
        size: int = 20,
    ) -> Tuple[List[Post], int]:
        """List posts with filters."""
        query = select(Post).where(
            Post.tenant_id == self.tenant_id,
            Post.is_deleted == False,
        )
        
        if published_only:
            query = query.where(Post.is_published == True)
        
        if not include_expired:
            query = query.where(
                or_(
                    Post.expires_at.is_(None),
                    Post.expires_at > datetime.now(timezone.utc),
                )
            )
        
        if post_type:
            query = query.where(Post.post_type == post_type)
        
        if audience:
            query = query.where(
                or_(
                    Post.audience == TargetAudience.ALL,
                    Post.audience == audience,
                )
            )
        
        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.session.execute(count_query)).scalar() or 0
        
        # Order and paginate
        query = query.order_by(
            Post.is_pinned.desc(),
            Post.published_at.desc(),
        )
        
        skip = (page - 1) * size
        query = query.offset(skip).limit(size)
        
        result = await self.session.execute(query)
        return list(result.scalars().all()), total
    
    async def publish_post(self, post_id: UUID, publish: bool = True) -> Post:
        """Publish or unpublish a post."""
        post = await self.get_post(post_id)
        
        post.is_published = publish
        if publish and not post.published_at:
            post.published_at = datetime.now(timezone.utc)
        
        await self.session.commit()
        await self.session.refresh(post)
        return post
    
    async def delete_post(self, post_id: UUID) -> None:
        """Soft delete a post."""
        post = await self.get_post(post_id)
        post.is_deleted = True
        await self.session.commit()
    
    async def mark_as_read(self, post_id: UUID, user_id: UUID) -> None:
        """Mark a post as read by a user."""
        # Check if already read
        query = select(PostRead).where(
            PostRead.post_id == post_id,
            PostRead.user_id == user_id,
        )
        result = await self.session.execute(query)
        existing = result.scalar_one_or_none()
        
        if not existing:
            read_record = PostRead(
                tenant_id=self.tenant_id,
                post_id=post_id,
                user_id=user_id,
            )
            self.session.add(read_record)
            
            # Increment views
            post = await self.get_post(post_id)
            post.views_count += 1
            
            await self.session.commit()
    
    async def get_unread_count(self, user_id: UUID) -> int:
        """Get count of unread posts for a user."""
        # Get all published post IDs
        posts_query = select(Post.id).where(
            Post.tenant_id == self.tenant_id,
            Post.is_published == True,
            Post.is_deleted == False,
            or_(
                Post.expires_at.is_(None),
                Post.expires_at > datetime.now(timezone.utc),
            ),
        )
        
        # Get read post IDs
        read_query = select(PostRead.post_id).where(
            PostRead.user_id == user_id,
        )
        
        # Count unread
        unread_query = select(func.count()).where(
            Post.tenant_id == self.tenant_id,
            Post.is_published == True,
            Post.is_deleted == False,
            ~Post.id.in_(read_query),
        )
        
        result = await self.session.execute(unread_query)
        return result.scalar() or 0
    
    async def get_latest_for_audience(
        self,
        audience: TargetAudience,
        class_id: Optional[UUID] = None,
        section_id: Optional[UUID] = None,
        limit: int = 10,
    ) -> List[Post]:
        """Get latest posts for a specific audience."""
        query = select(Post).where(
            Post.tenant_id == self.tenant_id,
            Post.is_published == True,
            Post.is_deleted == False,
            or_(
                Post.expires_at.is_(None),
                Post.expires_at > datetime.now(timezone.utc),
            ),
        )
        
        # Filter by audience
        audience_conditions = [Post.audience == TargetAudience.ALL]
        
        if audience:
            audience_conditions.append(Post.audience == audience)
        
        query = query.where(or_(*audience_conditions))
        
        # Order by priority and date
        query = query.order_by(
            Post.is_pinned.desc(),
            Post.priority.desc(),
            Post.published_at.desc(),
        ).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
