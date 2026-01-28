"""
CUSTOS Academic Structure Router
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth.dependencies import CurrentUser, require_permission
from app.users.rbac import Permission
from app.academics.services.structure_service import StructureService
from app.academics.schemas.structure import (
    AcademicYearCreate, AcademicYearResponse,
    ClassCreate, ClassResponse,
    SectionCreate, SectionResponse,
)


router = APIRouter(tags=["Academic Structure"])


# Academic Years
@router.get("/years", response_model=list[AcademicYearResponse])
async def list_academic_years(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """List academic years."""
    service = StructureService(db, user.tenant_id)
    return await service.get_academic_years()


@router.post("/years", response_model=AcademicYearResponse)
async def create_academic_year(
    data: AcademicYearCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.CLASS_CREATE)),
):
    """Create academic year."""
    service = StructureService(db, user.tenant_id)
    return await service.create_academic_year(data)


@router.get("/years/current", response_model=AcademicYearResponse)
async def get_current_year(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Get current academic year."""
    service = StructureService(db, user.tenant_id)
    year = await service.get_current_year()
    return year


# Classes
@router.get("/classes", response_model=list[ClassResponse])
async def list_classes(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    academic_year_id: Optional[UUID] = None,
):
    """List classes."""
    service = StructureService(db, user.tenant_id)
    return await service.get_classes(academic_year_id)


@router.post("/classes", response_model=ClassResponse)
async def create_class(
    data: ClassCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.CLASS_CREATE)),
):
    """Create class."""
    service = StructureService(db, user.tenant_id)
    return await service.create_class(data)


@router.get("/classes/{class_id}", response_model=ClassResponse)
async def get_class(
    class_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Get class by ID."""
    service = StructureService(db, user.tenant_id)
    return await service.get_class(class_id)


# Sections
@router.get("/classes/{class_id}/sections", response_model=list[SectionResponse])
async def list_sections(
    class_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """List sections in class."""
    service = StructureService(db, user.tenant_id)
    return await service.get_sections(class_id)


@router.post("/sections", response_model=SectionResponse)
async def create_section(
    data: SectionCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.CLASS_CREATE)),
):
    """Create section."""
    service = StructureService(db, user.tenant_id)
    return await service.create_section(data)
