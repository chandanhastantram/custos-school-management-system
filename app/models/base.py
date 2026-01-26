"""
CUSTOS Base Model Module

Base model class with common fields for all entities.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, Boolean, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, declared_attr

from app.core.database import Base


class TimestampMixin:
    """Mixin for timestamp fields."""
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class SoftDeleteMixin:
    """Mixin for soft delete functionality."""
    
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
    )
    
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    deleted_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
    )
    
    def soft_delete(self, deleted_by_id: Optional[UUID] = None) -> None:
        """Mark entity as deleted."""
        self.is_deleted = True
        self.deleted_at = datetime.now(timezone.utc)
        if deleted_by_id:
            self.deleted_by = deleted_by_id
    
    def restore(self) -> None:
        """Restore soft-deleted entity."""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None


class TenantMixin:
    """Mixin for tenant isolation."""
    
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
    )


class BaseModel(Base, TimestampMixin):
    """
    Abstract base model for all entities.
    
    Provides:
    - UUID primary key
    - Created/updated timestamps
    - Table naming convention
    """
    
    __abstract__ = True
    
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    
    @declared_attr.directive
    def __tablename__(cls) -> str:
        """Generate table name from class name."""
        # Convert CamelCase to snake_case
        name = cls.__name__
        return ''.join(
            ['_' + c.lower() if c.isupper() else c for c in name]
        ).lstrip('_') + 's'


class TenantBaseModel(BaseModel, TenantMixin):
    """
    Base model for tenant-scoped entities.
    
    All tenant-specific data should extend this.
    """
    
    __abstract__ = True


class SoftDeleteBaseModel(BaseModel, SoftDeleteMixin):
    """
    Base model with soft delete support.
    """
    
    __abstract__ = True


class TenantSoftDeleteModel(TenantBaseModel, SoftDeleteMixin):
    """
    Base model for tenant-scoped entities with soft delete.
    """
    
    __abstract__ = True
