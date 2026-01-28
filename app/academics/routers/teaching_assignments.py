"""
CUSTOS Teaching Assignment Router

API endpoints for teaching assignments.
"""

from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth.dependencies import CurrentUser, require_permission
from app.users.rbac import Permission, SystemRole
from app.academics.services.teaching_assignment_service import TeachingAssignmentService
from app.academics.schemas.teaching_assignments import (
    TeachingAssignmentCreate,
    TeachingAssignmentBulkCreate,
    TeachingAssignmentUpdate,
    TeachingAssignmentResponse,
    TeachingAssignmentStats,
    TeacherAssignmentSummary,
    ClassAssignmentSummary,
)


router = APIRouter(tags=["Teaching Assignments"])


# ============================================
# CRUD Endpoints
# ============================================

@router.post("", response_model=TeachingAssignmentResponse, status_code=201)
async def create_teaching_assignment(
    data: TeachingAssignmentCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.TEACHER_CREATE)),
):
    """
    Create a teaching assignment (Admin only).
    
    Assigns a teacher to teach a subject in a class for the academic year.
    """
    service = TeachingAssignmentService(db, user.tenant_id)
    return await service.create(data)


@router.post("/bulk", response_model=List[TeachingAssignmentResponse], status_code=201)
async def create_teaching_assignments_bulk(
    data: TeachingAssignmentBulkCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.TEACHER_CREATE)),
):
    """
    Create multiple teaching assignments at once (Admin only).
    
    Duplicates are skipped silently.
    """
    service = TeachingAssignmentService(db, user.tenant_id)
    return await service.create_bulk(data)


@router.get("", response_model=dict)
async def list_teaching_assignments(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    academic_year_id: Optional[UUID] = None,
    teacher_id: Optional[UUID] = None,
    class_id: Optional[UUID] = None,
    section_id: Optional[UUID] = None,
    subject_id: Optional[UUID] = None,
    is_active: Optional[bool] = True,
    is_primary: Optional[bool] = None,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    _=Depends(require_permission(Permission.TEACHER_VIEW)),
):
    """
    List teaching assignments with filters.
    
    Teachers can only see their own assignments unless admin.
    """
    service = TeachingAssignmentService(db, user.tenant_id)
    
    # Check if user is admin
    user_roles = [r.code for r in user.roles] if user.roles else []
    admin_roles = {SystemRole.SUPER_ADMIN.value, SystemRole.PRINCIPAL.value, SystemRole.SUB_ADMIN.value}
    
    # Non-admins can only see their own
    if not any(r in admin_roles for r in user_roles):
        teacher_id = user.id
    
    assignments, total = await service.list(
        academic_year_id=academic_year_id,
        teacher_id=teacher_id,
        class_id=class_id,
        section_id=section_id,
        subject_id=subject_id,
        is_active=is_active,
        is_primary=is_primary,
        page=page,
        size=size,
    )
    
    return {
        "items": assignments,
        "total": total,
        "page": page,
        "size": size,
    }


@router.get("/stats", response_model=TeachingAssignmentStats)
async def get_assignment_stats(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    academic_year_id: Optional[UUID] = None,
    _=Depends(require_permission(Permission.TEACHER_VIEW)),
):
    """Get teaching assignment statistics."""
    service = TeachingAssignmentService(db, user.tenant_id)
    return await service.get_stats(academic_year_id)


@router.get("/my-assignments", response_model=List[TeachingAssignmentResponse])
async def get_my_assignments(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    academic_year_id: Optional[UUID] = None,
):
    """Get current user's teaching assignments."""
    service = TeachingAssignmentService(db, user.tenant_id)
    return await service.get_teacher_assignments(user.id, academic_year_id)


@router.get("/my-summary", response_model=TeacherAssignmentSummary)
async def get_my_summary(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    academic_year_id: Optional[UUID] = None,
):
    """Get current user's assignment summary."""
    service = TeachingAssignmentService(db, user.tenant_id)
    return await service.get_teacher_summary(user.id, academic_year_id)


@router.get("/{assignment_id}", response_model=TeachingAssignmentResponse)
async def get_teaching_assignment(
    assignment_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.TEACHER_VIEW)),
):
    """Get a specific teaching assignment."""
    service = TeachingAssignmentService(db, user.tenant_id)
    return await service.get(assignment_id)


@router.patch("/{assignment_id}", response_model=TeachingAssignmentResponse)
async def update_teaching_assignment(
    assignment_id: UUID,
    data: TeachingAssignmentUpdate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.TEACHER_UPDATE)),
):
    """Update a teaching assignment (Admin only)."""
    service = TeachingAssignmentService(db, user.tenant_id)
    return await service.update(assignment_id, data)


@router.delete("/{assignment_id}", status_code=204)
async def delete_teaching_assignment(
    assignment_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.TEACHER_DELETE)),
):
    """Delete a teaching assignment (Admin only)."""
    service = TeachingAssignmentService(db, user.tenant_id)
    await service.delete(assignment_id)


@router.post("/{assignment_id}/deactivate", response_model=TeachingAssignmentResponse)
async def deactivate_teaching_assignment(
    assignment_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.TEACHER_UPDATE)),
):
    """Deactivate a teaching assignment (instead of deleting)."""
    service = TeachingAssignmentService(db, user.tenant_id)
    return await service.deactivate(assignment_id)


# ============================================
# Lookup Endpoints
# ============================================

@router.get("/by-teacher/{teacher_id}", response_model=List[TeachingAssignmentResponse])
async def get_assignments_by_teacher(
    teacher_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    academic_year_id: Optional[UUID] = None,
    _=Depends(require_permission(Permission.TEACHER_VIEW)),
):
    """Get all assignments for a specific teacher."""
    service = TeachingAssignmentService(db, user.tenant_id)
    return await service.get_teacher_assignments(teacher_id, academic_year_id)


@router.get("/by-teacher/{teacher_id}/summary", response_model=TeacherAssignmentSummary)
async def get_teacher_summary(
    teacher_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    academic_year_id: Optional[UUID] = None,
    _=Depends(require_permission(Permission.TEACHER_VIEW)),
):
    """Get assignment summary for a specific teacher."""
    service = TeachingAssignmentService(db, user.tenant_id)
    return await service.get_teacher_summary(teacher_id, academic_year_id)


@router.get("/by-class/{class_id}", response_model=List[TeachingAssignmentResponse])
async def get_assignments_by_class(
    class_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    academic_year_id: Optional[UUID] = None,
    _=Depends(require_permission(Permission.CLASS_VIEW)),
):
    """Get all assignments for a specific class."""
    service = TeachingAssignmentService(db, user.tenant_id)
    return await service.get_class_assignments(class_id, academic_year_id)


@router.get("/by-class/{class_id}/summary", response_model=ClassAssignmentSummary)
async def get_class_summary(
    class_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    academic_year_id: Optional[UUID] = None,
    _=Depends(require_permission(Permission.CLASS_VIEW)),
):
    """Get assignment summary for a specific class."""
    service = TeachingAssignmentService(db, user.tenant_id)
    return await service.get_class_summary(class_id, academic_year_id)


@router.get("/by-subject/{subject_id}", response_model=List[TeachingAssignmentResponse])
async def get_assignments_by_subject(
    subject_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    academic_year_id: Optional[UUID] = None,
    _=Depends(require_permission(Permission.SUBJECT_VIEW)),
):
    """Get all assignments for a specific subject."""
    service = TeachingAssignmentService(db, user.tenant_id)
    return await service.get_subject_assignments(subject_id, academic_year_id)


@router.get("/lookup/teacher-for-class-subject")
async def lookup_teacher_for_class_subject(
    class_id: UUID,
    subject_id: UUID,
    academic_year_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    section_id: Optional[UUID] = None,
    _=Depends(require_permission(Permission.TEACHER_VIEW)),
):
    """
    Lookup the primary teacher for a class-subject combination.
    
    Used by timetable and lesson planning.
    """
    service = TeachingAssignmentService(db, user.tenant_id)
    assignment = await service.get_teacher_for_class_subject(
        class_id, subject_id, academic_year_id, section_id
    )
    
    if assignment:
        return TeachingAssignmentResponse.model_validate(assignment)
    return None
