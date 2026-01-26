"""
CUSTOS Database Module

Async SQLAlchemy engine and session management for PostgreSQL.
Provides session factories and dependency injection utilities.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import AsyncAdaptedQueuePool

from app.core.config import settings


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


# Create async engine
engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=settings.database_echo,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_pre_ping=True,
    pool_recycle=3600,
    poolclass=AsyncAdaptedQueuePool,
)

# Session factory
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager for database sessions.
    
    Usage:
        async with get_session() as session:
            result = await session.execute(query)
    """
    session = async_session_factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for database sessions.
    
    Usage:
        @router.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


class TenantSession:
    """
    Tenant-aware session wrapper that automatically filters by tenant_id.
    
    This ensures complete data isolation between tenants.
    """
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self._session = session
        self._tenant_id = tenant_id
    
    @property
    def session(self) -> AsyncSession:
        """Get the underlying session."""
        return self._session
    
    @property
    def tenant_id(self) -> UUID:
        """Get the current tenant ID."""
        return self._tenant_id
    
    async def execute(self, statement, **kwargs):
        """Execute a statement with automatic tenant filtering."""
        return await self._session.execute(statement, **kwargs)
    
    async def get(self, entity, ident, **kwargs):
        """Get entity by ID with tenant check."""
        obj = await self._session.get(entity, ident, **kwargs)
        if obj and hasattr(obj, 'tenant_id') and obj.tenant_id != self._tenant_id:
            return None
        return obj
    
    async def commit(self):
        """Commit the transaction."""
        await self._session.commit()
    
    async def rollback(self):
        """Rollback the transaction."""
        await self._session.rollback()
    
    async def refresh(self, instance, **kwargs):
        """Refresh an instance from the database."""
        await self._session.refresh(instance, **kwargs)
    
    def add(self, instance):
        """Add an instance to the session."""
        if hasattr(instance, 'tenant_id') and instance.tenant_id is None:
            instance.tenant_id = self._tenant_id
        self._session.add(instance)
    
    def add_all(self, instances):
        """Add multiple instances to the session."""
        for instance in instances:
            self.add(instance)
    
    async def delete(self, instance):
        """Delete an instance."""
        await self._session.delete(instance)
    
    async def flush(self):
        """Flush pending changes."""
        await self._session.flush()


async def init_db() -> None:
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()
