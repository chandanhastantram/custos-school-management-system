"""
CUSTOS User Router

User API endpoints.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth.dependencies import CurrentUser, require_permission
from app.users.rbac import Permission
from app.users.service import UserService
from app.users.schemas import (
    UserCreate, UserUpdate, UserResponse,
    StudentCreate, TeacherCreate, RoleResponse,
)
from app.users.models import UserStatus


router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=dict)
async def list_users(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    status: Optional[UserStatus] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    """List users with filters."""
    service = UserService(db, user.tenant_id)
    users, total = await service.list_users(status, None, search, page, size)
    
    return {
        "items": [UserResponse.model_validate(u) for u in users],
        "total": total,
        "page": page,
        "size": size,
    }


@router.post("", response_model=UserResponse)
async def create_user(
    data: UserCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.USER_CREATE)),
):
    """Create new user."""
    service = UserService(db, user.tenant_id)
    new_user = await service.create_user(data, user.user_id)
    return UserResponse.model_validate(new_user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Get user by ID."""
    service = UserService(db, user.tenant_id)
    target_user = await service.get_user(user_id)
    return UserResponse.model_validate(target_user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    data: UserUpdate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.USER_UPDATE)),
):
    """Update user."""
    service = UserService(db, user.tenant_id)
    updated_user = await service.update_user(user_id, data)
    return UserResponse.model_validate(updated_user)


@router.delete("/{user_id}")
async def delete_user(
    user_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.USER_DELETE)),
):
    """Delete user."""
    service = UserService(db, user.tenant_id)
    await service.delete_user(user_id)
    return {"success": True, "message": "User deleted"}


@router.post("/{user_id}/roles")
async def assign_roles(
    user_id: UUID,
    role_ids: list[UUID],
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.USER_MANAGE_ROLES)),
):
    """Assign roles to user."""
    service = UserService(db, user.tenant_id)
    updated_user = await service.assign_roles(user_id, role_ids)
    return UserResponse.model_validate(updated_user)


# Student endpoints

@router.post("/students", response_model=UserResponse)
async def create_student(
    data: StudentCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.STUDENT_CREATE)),
):
    """Create student."""
    service = UserService(db, user.tenant_id)
    student = await service.create_student(data)
    return UserResponse.model_validate(student)


# Teacher endpoints

@router.post("/teachers", response_model=UserResponse)
async def create_teacher(
    data: TeacherCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.TEACHER_CREATE)),
):
    """Create teacher."""
    service = UserService(db, user.tenant_id)
    teacher = await service.create_teacher(data)
    return UserResponse.model_validate(teacher)
