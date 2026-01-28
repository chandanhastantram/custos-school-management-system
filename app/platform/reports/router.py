"""
CUSTOS Report Router
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth.dependencies import CurrentUser, require_permission
from app.users.rbac import Permission
from app.platform.reports.service import ReportService


router = APIRouter(tags=["Reports"])


@router.get("/my-report")
async def get_my_report(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    subject_id: Optional[UUID] = None,
):
    """Get my performance report."""
    service = ReportService(db, user.tenant_id)
    return await service.get_student_report(user.user_id, subject_id)


@router.get("/student/{student_id}")
async def get_student_report(
    student_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    subject_id: Optional[UUID] = None,
    _=Depends(require_permission(Permission.REPORT_VIEW_CLASS)),
):
    """Get student report."""
    service = ReportService(db, user.tenant_id)
    return await service.get_student_report(student_id, subject_id)


@router.get("/class/{section_id}")
async def get_class_report(
    section_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    subject_id: Optional[UUID] = None,
    _=Depends(require_permission(Permission.REPORT_VIEW_CLASS)),
):
    """Get class report."""
    service = ReportService(db, user.tenant_id)
    return await service.get_class_report(section_id, subject_id)


@router.get("/teacher/{teacher_id}")
async def get_teacher_report(
    teacher_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.REPORT_VIEW_ALL)),
):
    """Get teacher report."""
    service = ReportService(db, user.tenant_id)
    return await service.get_teacher_report(teacher_id)
