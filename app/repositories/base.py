"""
CUSTOS Base Repository

Generic repository pattern implementation.
"""

from typing import TypeVar, Generic, Optional, List, Type, Any
from uuid import UUID

from sqlalchemy import select, func, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import TenantBaseModel


ModelType = TypeVar("ModelType", bound=TenantBaseModel)


class BaseRepository(Generic[ModelType]):
    """
    Generic repository for CRUD operations with tenant isolation.
    """
    
    def __init__(self, model: Type[ModelType], session: AsyncSession, tenant_id: UUID):
        self.model = model
        self.session = session
        self.tenant_id = tenant_id
    
    def _base_query(self):
        """Base query with tenant filter."""
        return select(self.model).where(self.model.tenant_id == self.tenant_id)
    
    async def get_by_id(self, id: UUID) -> Optional[ModelType]:
        """Get entity by ID."""
        query = self._base_query().where(self.model.id == id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None,
        order_desc: bool = False,
    ) -> List[ModelType]:
        """Get all entities with pagination."""
        query = self._base_query()
        
        if order_by and hasattr(self.model, order_by):
            col = getattr(self.model, order_by)
            query = query.order_by(col.desc() if order_desc else col)
        
        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def count(self) -> int:
        """Count all entities."""
        query = select(func.count()).select_from(self.model).where(
            self.model.tenant_id == self.tenant_id
        )
        result = await self.session.execute(query)
        return result.scalar() or 0
    
    async def create(self, **kwargs) -> ModelType:
        """Create new entity."""
        kwargs["tenant_id"] = self.tenant_id
        entity = self.model(**kwargs)
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity
    
    async def update(self, id: UUID, **kwargs) -> Optional[ModelType]:
        """Update entity by ID."""
        entity = await self.get_by_id(id)
        if not entity:
            return None
        
        for key, value in kwargs.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)
        
        await self.session.flush()
        await self.session.refresh(entity)
        return entity
    
    async def delete(self, id: UUID) -> bool:
        """Delete entity by ID."""
        entity = await self.get_by_id(id)
        if not entity:
            return False
        
        await self.session.delete(entity)
        await self.session.flush()
        return True
    
    async def soft_delete(self, id: UUID, deleted_by: Optional[UUID] = None) -> bool:
        """Soft delete entity."""
        entity = await self.get_by_id(id)
        if not entity:
            return False
        
        if hasattr(entity, "soft_delete"):
            entity.soft_delete(deleted_by)
            await self.session.flush()
            return True
        return False
    
    async def exists(self, id: UUID) -> bool:
        """Check if entity exists."""
        query = select(func.count()).select_from(self.model).where(
            self.model.tenant_id == self.tenant_id,
            self.model.id == id
        )
        result = await self.session.execute(query)
        return (result.scalar() or 0) > 0
    
    async def get_by_ids(self, ids: List[UUID]) -> List[ModelType]:
        """Get entities by list of IDs."""
        query = self._base_query().where(self.model.id.in_(ids))
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def bulk_create(self, items: List[dict]) -> List[ModelType]:
        """Bulk create entities."""
        entities = []
        for item in items:
            item["tenant_id"] = self.tenant_id
            entity = self.model(**item)
            self.session.add(entity)
            entities.append(entity)
        
        await self.session.flush()
        for entity in entities:
            await self.session.refresh(entity)
        return entities
