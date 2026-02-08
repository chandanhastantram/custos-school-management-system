"""
CUSTOS Core Dependencies

Shared FastAPI dependencies.
"""

from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_db


# Type aliases for dependency injection
DBSession = Annotated[AsyncSession, Depends(get_db)]
AppSettings = Annotated[Settings, Depends(get_settings)]


async def get_tenant_id(
    x_tenant_id: Annotated[str, Header(description="Tenant ID")],
) -> str:
    """Extract tenant ID from header."""
    return x_tenant_id


# Alias for backward compatibility
get_current_tenant_id = get_tenant_id

