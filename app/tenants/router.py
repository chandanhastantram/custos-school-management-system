"""
CUSTOS Tenant Router

Tenant API endpoints.
"""

from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth.dependencies import CurrentUser
from app.tenants.service import TenantService
from app.tenants.schemas import (
    TenantCreate, TenantUpdate, TenantResponse,
    TenantStats, TenantPublicInfo,
)
from app.tenants.models import TenantStatus


router = APIRouter(prefix="/tenants", tags=["Tenants"])


@router.post("/register")
async def register_tenant(
    data: TenantCreate,
    admin_email: str,
    admin_password: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Register new school/institution.
    
    Creates tenant with admin user and starts trial period.
    """
    service = TenantService(db)
    tenant, admin = await service.register(data, admin_email, admin_password)
    
    return {
        "tenant": TenantResponse.model_validate(tenant),
        "admin": {
            "id": str(admin.id),
            "email": admin.email,
        },
        "message": "Registration successful. Trial period started.",
    }


@router.get("/by-slug/{slug}", response_model=TenantPublicInfo)
async def get_tenant_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get public tenant info by slug.
    
    Used for login page branding.
    """
    service = TenantService(db)
    tenant = await service.get_by_slug(slug)
    
    if not tenant:
        return TenantPublicInfo(exists=False)
    
    return TenantPublicInfo(
        exists=True,
        id=tenant.id,
        name=tenant.name,
        logo=tenant.logo,
        primary_color=tenant.primary_color,
    )


@router.get("/current", response_model=TenantResponse)
async def get_current_tenant(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Get current tenant details."""
    service = TenantService(db)
    tenant = await service.get_by_id(user.tenant_id)
    return TenantResponse.model_validate(tenant)


@router.put("/current", response_model=TenantResponse)
async def update_current_tenant(
    data: TenantUpdate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Update current tenant settings."""
    service = TenantService(db)
    tenant = await service.update(user.tenant_id, data)
    return TenantResponse.model_validate(tenant)


@router.get("/current/stats", response_model=TenantStats)
async def get_tenant_stats(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Get current tenant statistics."""
    service = TenantService(db)
    stats = await service.get_stats(user.tenant_id)
    return TenantStats(**stats)


# Platform admin endpoints

@router.get("", response_model=dict)
async def list_tenants(
    db: AsyncSession = Depends(get_db),
    status: Optional[TenantStatus] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    """
    List all tenants (platform admin only).
    """
    from app.tenants.repository import TenantRepository
    
    repo = TenantRepository(db)
    skip = (page - 1) * size
    tenants, total = await repo.list_all(status, skip, size)
    
    return {
        "items": [TenantResponse.model_validate(t) for t in tenants],
        "total": total,
        "page": page,
        "size": size,
    }


@router.post("/{tenant_id}/activate", response_model=TenantResponse)
async def activate_tenant(
    tenant_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Activate tenant (platform admin only)."""
    service = TenantService(db)
    tenant = await service.activate(tenant_id)
    return TenantResponse.model_validate(tenant)


@router.post("/{tenant_id}/suspend", response_model=TenantResponse)
async def suspend_tenant(
    tenant_id: UUID,
    reason: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Suspend tenant (platform admin only)."""
    service = TenantService(db)
    tenant = await service.suspend(tenant_id, reason)
    return TenantResponse.model_validate(tenant)
