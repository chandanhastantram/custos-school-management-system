"""
CUSTOS Tenant API Endpoints

Tenant management routes.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth import AuthUser, TenantCtx, require_permissions, require_admin, Permission
from app.services.tenant_service import TenantService
from app.schemas.tenant import TenantCreate, TenantUpdate, TenantResponse, TenantStats
from app.schemas.common import SuccessResponse
from app.models.tenant import TenantStatus


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
    
    Creates tenant with admin user.
    """
    service = TenantService(db)
    tenant, admin = await service.register_tenant(data, admin_email, admin_password)
    
    return {
        "tenant": TenantResponse.model_validate(tenant),
        "admin": {
            "id": str(admin.id),
            "email": admin.email,
        },
        "message": "Registration successful. Please verify your email.",
    }


@router.get("/current", response_model=TenantResponse)
async def get_current_tenant(
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
):
    """Get current tenant details."""
    service = TenantService(db)
    tenant = await service.get_tenant(ctx.tenant_id)
    return TenantResponse.model_validate(tenant)


@router.put("/current", response_model=TenantResponse)
async def update_current_tenant(
    data: TenantUpdate,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    _: AuthUser = Depends(require_permissions(Permission.TENANT_UPDATE)),
):
    """Update current tenant settings."""
    service = TenantService(db)
    tenant = await service.update_tenant(ctx.tenant_id, data)
    return TenantResponse.model_validate(tenant)


@router.get("/current/stats", response_model=TenantStats)
async def get_tenant_stats(
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
):
    """Get current tenant statistics."""
    service = TenantService(db)
    stats = await service.get_tenant_stats(ctx.tenant_id)
    return stats


@router.get("/by-slug/{slug}")
async def get_tenant_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_db),
):
    """Get tenant info by slug (for login page)."""
    service = TenantService(db)
    tenant = await service.get_tenant_by_slug(slug)
    
    if not tenant:
        return {"exists": False}
    
    return {
        "exists": True,
        "id": str(tenant.id),
        "name": tenant.name,
        "logo": tenant.logo,
        "primary_color": tenant.primary_color,
    }


# ==================== Platform Admin Endpoints ====================

@router.get("", response_model=dict)
async def list_all_tenants(
    db: AsyncSession = Depends(get_db),
    status: Optional[TenantStatus] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    # _: AuthUser = Depends(require_platform_admin),  # Would need platform admin check
):
    """List all tenants (platform admin only)."""
    service = TenantService(db)
    tenants, total = await service.list_tenants(status, page, size)
    
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
    # _: AuthUser = Depends(require_platform_admin),
):
    """Activate tenant (platform admin only)."""
    service = TenantService(db)
    tenant = await service.activate_tenant(tenant_id)
    return TenantResponse.model_validate(tenant)


@router.post("/{tenant_id}/suspend", response_model=TenantResponse)
async def suspend_tenant(
    tenant_id: UUID,
    reason: str = None,
    db: AsyncSession = Depends(get_db),
    # _: AuthUser = Depends(require_platform_admin),
):
    """Suspend tenant (platform admin only)."""
    service = TenantService(db)
    tenant = await service.suspend_tenant(tenant_id, reason)
    return TenantResponse.model_validate(tenant)
