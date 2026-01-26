"""
CUSTOS Users API Endpoints

User management routes.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth import AuthUser, TenantCtx, require_permissions, Permission
from app.services.user_service import UserService
from app.schemas.user import (
    UserCreate, UserUpdate, UserResponse, UserListResponse,
    StudentProfileCreate, TeacherProfileCreate,
)
from app.schemas.common import SuccessResponse


router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=UserListResponse)
async def list_users(
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    role: Optional[str] = None,
    search: Optional[str] = None,
):
    """List users with pagination and filters."""
    service = UserService(db, ctx.tenant_id)
    users, total = await service.list_users(
        role_code=role,
        search=search,
        page=page,
        size=size,
    )
    
    return UserListResponse(
        items=[UserResponse.model_validate(u) for u in users],
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size,
    )


@router.post("", response_model=UserResponse)
async def create_user(
    data: UserCreate,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    _: AuthUser = Depends(require_permissions(Permission.USER_CREATE)),
):
    """Create new user."""
    service = UserService(db, ctx.tenant_id)
    user = await service.create_user(data, ctx.user.user_id)
    return UserResponse.model_validate(user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
):
    """Get user by ID."""
    service = UserService(db, ctx.tenant_id)
    user = await service.get_user(user_id)
    return UserResponse.model_validate(user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    data: UserUpdate,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    _: AuthUser = Depends(require_permissions(Permission.USER_UPDATE)),
):
    """Update user."""
    service = UserService(db, ctx.tenant_id)
    user = await service.update_user(user_id, data)
    return UserResponse.model_validate(user)


@router.delete("/{user_id}", response_model=SuccessResponse)
async def delete_user(
    user_id: UUID,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    _: AuthUser = Depends(require_permissions(Permission.USER_DELETE)),
):
    """Delete user (soft delete)."""
    service = UserService(db, ctx.tenant_id)
    await service.delete_user(user_id, ctx.user.user_id)
    return SuccessResponse(message="User deleted")


@router.post("/{user_id}/roles", response_model=UserResponse)
async def assign_roles(
    user_id: UUID,
    role_codes: list[str],
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    _: AuthUser = Depends(require_permissions(Permission.USER_MANAGE_ROLES)),
):
    """Assign roles to user."""
    service = UserService(db, ctx.tenant_id)
    user = await service.assign_roles(user_id, role_codes)
    return UserResponse.model_validate(user)


@router.post("/{user_id}/activate", response_model=UserResponse)
async def activate_user(
    user_id: UUID,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    _: AuthUser = Depends(require_permissions(Permission.USER_UPDATE)),
):
    """Activate user account."""
    service = UserService(db, ctx.tenant_id)
    user = await service.activate_user(user_id)
    return UserResponse.model_validate(user)


@router.post("/{user_id}/suspend", response_model=UserResponse)
async def suspend_user(
    user_id: UUID,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    _: AuthUser = Depends(require_permissions(Permission.USER_UPDATE)),
):
    """Suspend user account."""
    service = UserService(db, ctx.tenant_id)
    user = await service.suspend_user(user_id)
    return UserResponse.model_validate(user)


# Student-specific endpoints
@router.post("/students", response_model=dict)
async def create_student(
    user_data: UserCreate,
    profile_data: StudentProfileCreate,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    _: AuthUser = Depends(require_permissions(Permission.STUDENT_CREATE)),
):
    """Create student with profile."""
    service = UserService(db, ctx.tenant_id)
    user, profile = await service.create_student(user_data, profile_data)
    return {
        "user": UserResponse.model_validate(user),
        "profile": profile,
    }


@router.get("/students/section/{section_id}")
async def get_students_by_section(
    section_id: UUID,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
):
    """Get all students in a section."""
    service = UserService(db, ctx.tenant_id)
    students = await service.get_students_by_section(section_id, page, size)
    return {"items": [UserResponse.model_validate(s) for s in students]}


# Teacher-specific endpoints
@router.post("/teachers", response_model=dict)
async def create_teacher(
    user_data: UserCreate,
    profile_data: TeacherProfileCreate,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    _: AuthUser = Depends(require_permissions(Permission.TEACHER_CREATE)),
):
    """Create teacher with profile."""
    service = UserService(db, ctx.tenant_id)
    user, profile = await service.create_teacher(user_data, profile_data)
    return {
        "user": UserResponse.model_validate(user),
        "profile": profile,
    }
