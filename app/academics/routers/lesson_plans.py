"""
CUSTOS Lesson Planning Router

API endpoints for lesson plan management.
"""

from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import AuthorizationError
from app.auth.dependencies import CurrentUser, require_permission
from app.users.rbac import Permission, SystemRole
from app.academics.services.lesson_plan_service import LessonPlanService
from app.academics.models.lesson_plans import LessonPlanStatus
from app.academics.schemas.lesson_plans import (
    LessonPlanCreate, LessonPlanUpdate, 
    LessonPlanResponse, LessonPlanWithUnits, LessonPlanSummary,
    LessonPlanUnitCreate, LessonPlanUnitUpdate, LessonPlanUnitResponse,
    LessonPlanUnitWithProgress, BulkUnitCreate,
    TeachingProgressCreate, TeachingProgressUpdate, TeachingProgressResponse,
    ReorderUnitsRequest, LessonPlanStats,
)


router = APIRouter(tags=["Lesson Planning"])


# ============================================
# Helper: Check ownership or admin
# ============================================

async def check_plan_access(
    service: LessonPlanService,
    plan_id: UUID,
    user_id: UUID,
    user_roles: List[str],
    require_ownership: bool = False,
) -> bool:
    """Check if user can access/modify the plan."""
    # Admins can access all
    admin_roles = {SystemRole.SUPER_ADMIN.value, SystemRole.PRINCIPAL.value}
    if any(r in admin_roles for r in user_roles):
        return True
    
    # Check ownership
    is_owner = await service.check_plan_ownership(plan_id, user_id)
    
    if require_ownership and not is_owner:
        raise AuthorizationError("You can only modify your own lesson plans")
    
    return is_owner


# ============================================
# LessonPlan Endpoints
# ============================================

@router.post("", response_model=LessonPlanResponse, status_code=201)
async def create_lesson_plan(
    data: LessonPlanCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.LESSON_CREATE)),
):
    """
    Create a new lesson plan.
    
    Teachers create their own plans.
    """
    service = LessonPlanService(db, user.tenant_id)
    return await service.create_plan(user.id, data)


@router.get("", response_model=dict)
async def list_lesson_plans(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    teacher_id: Optional[UUID] = None,
    class_id: Optional[UUID] = None,
    subject_id: Optional[UUID] = None,
    status: Optional[LessonPlanStatus] = None,
    academic_year_id: Optional[UUID] = None,
    mine_only: bool = False,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    _=Depends(require_permission(Permission.LESSON_VIEW)),
):
    """
    List lesson plans.
    
    - Teachers see their own plans by default (mine_only=True)
    - Admins can filter by teacher_id
    """
    service = LessonPlanService(db, user.tenant_id)
    
    # Teachers only see their own unless admin
    admin_roles = {SystemRole.SUPER_ADMIN.value, SystemRole.PRINCIPAL.value}
    user_roles = [r.code for r in user.roles] if user.roles else []
    
    if mine_only or not any(r in admin_roles for r in user_roles):
        teacher_id = user.id
    
    plans, total = await service.list_plans(
        teacher_id=teacher_id,
        class_id=class_id,
        subject_id=subject_id,
        status=status,
        academic_year_id=academic_year_id,
        page=page,
        size=size,
    )
    
    return {
        "items": plans,
        "total": total,
        "page": page,
        "size": size,
    }


@router.get("/my-stats", response_model=LessonPlanStats)
async def get_my_stats(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    academic_year_id: Optional[UUID] = None,
):
    """Get lesson plan statistics for current teacher."""
    service = LessonPlanService(db, user.tenant_id)
    return await service.get_teacher_stats(user.id, academic_year_id)


@router.get("/{plan_id}", response_model=LessonPlanWithUnits)
async def get_lesson_plan(
    plan_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.LESSON_VIEW)),
):
    """Get lesson plan details with units."""
    service = LessonPlanService(db, user.tenant_id)
    
    user_roles = [r.code for r in user.roles] if user.roles else []
    await check_plan_access(service, plan_id, user.id, user_roles)
    
    plan = await service.get_plan(plan_id, include_units=True)
    
    # Add progress percent
    progress_percent = (
        (plan.completed_periods / plan.total_periods * 100)
        if plan.total_periods > 0 else 0
    )
    
    response = LessonPlanWithUnits.model_validate(plan)
    response.progress_percent = round(progress_percent, 1)
    
    return response


@router.patch("/{plan_id}", response_model=LessonPlanResponse)
async def update_lesson_plan(
    plan_id: UUID,
    data: LessonPlanUpdate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.LESSON_UPDATE)),
):
    """Update lesson plan (only owner can update)."""
    service = LessonPlanService(db, user.tenant_id)
    
    user_roles = [r.code for r in user.roles] if user.roles else []
    await check_plan_access(service, plan_id, user.id, user_roles, require_ownership=True)
    
    return await service.update_plan(plan_id, data)


@router.delete("/{plan_id}", status_code=204)
async def delete_lesson_plan(
    plan_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.LESSON_DELETE)),
):
    """Delete lesson plan (only owner can delete)."""
    service = LessonPlanService(db, user.tenant_id)
    
    user_roles = [r.code for r in user.roles] if user.roles else []
    await check_plan_access(service, plan_id, user.id, user_roles, require_ownership=True)
    
    await service.delete_plan(plan_id)


@router.post("/{plan_id}/activate", response_model=LessonPlanResponse)
async def activate_lesson_plan(
    plan_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.LESSON_UPDATE)),
):
    """Activate a draft lesson plan."""
    service = LessonPlanService(db, user.tenant_id)
    
    user_roles = [r.code for r in user.roles] if user.roles else []
    await check_plan_access(service, plan_id, user.id, user_roles, require_ownership=True)
    
    return await service.activate_plan(plan_id)


@router.post("/{plan_id}/complete", response_model=LessonPlanResponse)
async def complete_lesson_plan(
    plan_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.LESSON_UPDATE)),
):
    """Mark an active lesson plan as completed."""
    service = LessonPlanService(db, user.tenant_id)
    
    user_roles = [r.code for r in user.roles] if user.roles else []
    await check_plan_access(service, plan_id, user.id, user_roles, require_ownership=True)
    
    return await service.complete_plan(plan_id)


@router.post("/{plan_id}/archive", response_model=LessonPlanResponse)
async def archive_lesson_plan(
    plan_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.LESSON_UPDATE)),
):
    """Archive a lesson plan."""
    service = LessonPlanService(db, user.tenant_id)
    
    user_roles = [r.code for r in user.roles] if user.roles else []
    await check_plan_access(service, plan_id, user.id, user_roles, require_ownership=True)
    
    return await service.archive_plan(plan_id)


# ============================================
# LessonPlanUnit Endpoints
# ============================================

@router.post("/{plan_id}/units", response_model=LessonPlanUnitResponse, status_code=201)
async def add_unit_to_plan(
    plan_id: UUID,
    data: LessonPlanUnitCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.LESSON_CREATE)),
):
    """Add a topic unit to the lesson plan."""
    service = LessonPlanService(db, user.tenant_id)
    
    user_roles = [r.code for r in user.roles] if user.roles else []
    await check_plan_access(service, plan_id, user.id, user_roles, require_ownership=True)
    
    return await service.add_unit(plan_id, data)


@router.post("/{plan_id}/units/bulk", response_model=List[LessonPlanUnitResponse], status_code=201)
async def add_units_bulk(
    plan_id: UUID,
    data: BulkUnitCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.LESSON_CREATE)),
):
    """Add multiple topic units at once."""
    service = LessonPlanService(db, user.tenant_id)
    
    user_roles = [r.code for r in user.roles] if user.roles else []
    await check_plan_access(service, plan_id, user.id, user_roles, require_ownership=True)
    
    return await service.add_units_bulk(plan_id, data)


@router.get("/{plan_id}/units", response_model=List[LessonPlanUnitResponse])
async def list_plan_units(
    plan_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.LESSON_VIEW)),
):
    """List units for a lesson plan."""
    service = LessonPlanService(db, user.tenant_id)
    
    user_roles = [r.code for r in user.roles] if user.roles else []
    await check_plan_access(service, plan_id, user.id, user_roles)
    
    return await service.list_units(plan_id)


@router.post("/{plan_id}/units/reorder", status_code=204)
async def reorder_plan_units(
    plan_id: UUID,
    data: ReorderUnitsRequest,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.LESSON_UPDATE)),
):
    """Reorder units in a plan."""
    service = LessonPlanService(db, user.tenant_id)
    
    user_roles = [r.code for r in user.roles] if user.roles else []
    await check_plan_access(service, plan_id, user.id, user_roles, require_ownership=True)
    
    await service.reorder_units(plan_id, data)


@router.get("/units/{unit_id}", response_model=LessonPlanUnitWithProgress)
async def get_unit(
    unit_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.LESSON_VIEW)),
):
    """Get unit details with progress history."""
    service = LessonPlanService(db, user.tenant_id)
    return await service.get_unit(unit_id, include_progress=True)


@router.patch("/units/{unit_id}", response_model=LessonPlanUnitResponse)
async def update_unit(
    unit_id: UUID,
    data: LessonPlanUnitUpdate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.LESSON_UPDATE)),
):
    """Update a unit."""
    service = LessonPlanService(db, user.tenant_id)
    
    # Get unit to check plan ownership
    unit = await service.get_unit(unit_id)
    user_roles = [r.code for r in user.roles] if user.roles else []
    await check_plan_access(service, unit.lesson_plan_id, user.id, user_roles, require_ownership=True)
    
    return await service.update_unit(unit_id, data)


@router.delete("/units/{unit_id}", status_code=204)
async def delete_unit(
    unit_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.LESSON_DELETE)),
):
    """Delete a unit."""
    service = LessonPlanService(db, user.tenant_id)
    
    unit = await service.get_unit(unit_id)
    user_roles = [r.code for r in user.roles] if user.roles else []
    await check_plan_access(service, unit.lesson_plan_id, user.id, user_roles, require_ownership=True)
    
    await service.delete_unit(unit_id)


# ============================================
# TeachingProgress Endpoints
# ============================================

@router.post("/units/{unit_id}/progress", response_model=TeachingProgressResponse, status_code=201)
async def record_progress(
    unit_id: UUID,
    data: TeachingProgressCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.LESSON_UPDATE)),
):
    """Record teaching progress for a unit."""
    service = LessonPlanService(db, user.tenant_id)
    
    # Get unit to check plan ownership
    unit = await service.get_unit(unit_id)
    user_roles = [r.code for r in user.roles] if user.roles else []
    await check_plan_access(service, unit.lesson_plan_id, user.id, user_roles, require_ownership=True)
    
    return await service.record_progress(unit_id, user.id, data)


@router.get("/units/{unit_id}/progress", response_model=List[TeachingProgressResponse])
async def list_progress(
    unit_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.LESSON_VIEW)),
):
    """List progress entries for a unit."""
    service = LessonPlanService(db, user.tenant_id)
    return await service.list_progress(unit_id)


@router.patch("/progress/{progress_id}", response_model=TeachingProgressResponse)
async def update_progress(
    progress_id: UUID,
    data: TeachingProgressUpdate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.LESSON_UPDATE)),
):
    """Update a progress entry."""
    service = LessonPlanService(db, user.tenant_id)
    return await service.update_progress(progress_id, data)


@router.delete("/progress/{progress_id}", status_code=204)
async def delete_progress(
    progress_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.LESSON_DELETE)),
):
    """Delete a progress entry."""
    service = LessonPlanService(db, user.tenant_id)
    await service.delete_progress(progress_id)


# ============================================
# Coverage & Analysis
# ============================================

@router.get("/coverage/{class_id}/{subject_id}")
async def get_class_coverage(
    class_id: UUID,
    subject_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.LESSON_VIEW)),
):
    """Get syllabus coverage for a class-subject."""
    service = LessonPlanService(db, user.tenant_id)
    return await service.get_class_coverage(class_id, subject_id)
