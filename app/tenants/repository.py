"""
CUSTOS Tenant Repository

Tenant data access layer.
"""

from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.tenants.models import Tenant, TenantStatus


class TenantRepository:
    """Tenant data access."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, tenant: Tenant) -> Tenant:
        """Create tenant."""
        self.session.add(tenant)
        await self.session.flush()
        await self.session.refresh(tenant)
        return tenant
    
    async def get_by_id(self, tenant_id: UUID) -> Optional[Tenant]:
        """Get tenant by ID."""
        return await self.session.get(Tenant, tenant_id)
    
    async def get_by_slug(self, slug: str) -> Optional[Tenant]:
        """Get tenant by slug."""
        query = select(Tenant).where(Tenant.slug == slug)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[Tenant]:
        """Get tenant by email."""
        query = select(Tenant).where(Tenant.email == email.lower())
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_domain(self, domain: str) -> Optional[Tenant]:
        """Get tenant by custom domain."""
        query = select(Tenant).where(Tenant.custom_domain == domain)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def list_all(
        self,
        status: Optional[TenantStatus] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[List[Tenant], int]:
        """List all tenants with pagination."""
        query = select(Tenant).where(Tenant.is_deleted == False)
        
        if status:
            query = query.where(Tenant.status == status)
        
        # Count
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0
        
        # Fetch
        query = query.order_by(Tenant.created_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(query)
        
        return list(result.scalars().all()), total
    
    async def update(self, tenant: Tenant) -> Tenant:
        """Update tenant."""
        await self.session.flush()
        await self.session.refresh(tenant)
        return tenant
    
    async def slug_exists(self, slug: str) -> bool:
        """Check if slug already exists."""
        query = select(func.count()).where(Tenant.slug == slug)
        result = await self.session.execute(query)
        return (result.scalar() or 0) > 0
    
    async def email_exists(self, email: str) -> bool:
        """Check if email already exists."""
        query = select(func.count()).where(Tenant.email == email.lower())
        result = await self.session.execute(query)
        return (result.scalar() or 0) > 0
