"""
CUSTOS Reports API Endpoints

Report generation routes.
"""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth import AuthUser, TenantCtx, require_permissions, Permission
from app.services.report_service import ReportService
from app.schemas.report import (
    ReportRequest, ReportResponse,
    StudentReportSummary, ClassAnalytics, TeacherEffectivenessReport,
)
from app.models.report import ReportType, ReportPeriod


router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post("/generate", response_model=ReportResponse)
async def generate_report(
    request: ReportRequest,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    _: AuthUser = Depends(require_permissions(Permission.REPORT_GENERATE)),
):
    """
    Generate a report based on type and parameters.
    
    Supported report types:
    - student_performance
    - class_analytics
    - teacher_effectiveness
    """
    service = ReportService(db, ctx.tenant_id)
    
    if request.report_type == ReportType.STUDENT_PERFORMANCE:
        data = await service.generate_student_report(
            student_id=request.student_id,
            start_date=request.start_date,
            end_date=request.end_date,
            subject_id=request.subject_id,
        )
    elif request.report_type == ReportType.CLASS_ANALYTICS:
        data = await service.generate_class_analytics(
            class_id=request.class_id,
            section_id=request.section_id,
            start_date=request.start_date,
            end_date=request.end_date,
        )
    elif request.report_type == ReportType.TEACHER_EFFECTIVENESS:
        data = await service.generate_teacher_report(
            teacher_id=request.teacher_id,
            start_date=request.start_date,
            end_date=request.end_date,
        )
    else:
        data = {}
    
    # Save report
    report = await service.save_report(
        request=request,
        data=data.model_dump() if hasattr(data, 'model_dump') else data,
        generated_by=ctx.user.user_id,
    )
    
    return ReportResponse.model_validate(report)


@router.get("/student/{student_id}", response_model=StudentReportSummary)
async def get_student_report(
    student_id: UUID,
    start_date: date,
    end_date: date,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    subject_id: UUID = None,
):
    """Get student performance report."""
    # Check if user can view this student's report
    if not ctx.user.is_admin():
        if ctx.user.user_id != student_id:
            # Check if parent or teacher
            pass  # Would need additional checks
    
    service = ReportService(db, ctx.tenant_id)
    return await service.generate_student_report(
        student_id=student_id,
        start_date=start_date,
        end_date=end_date,
        subject_id=subject_id,
    )


@router.get("/class/{class_id}/section/{section_id}", response_model=ClassAnalytics)
async def get_class_analytics(
    class_id: UUID,
    section_id: UUID,
    start_date: date,
    end_date: date,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    _: AuthUser = Depends(require_permissions(Permission.REPORT_VIEW_CLASS)),
):
    """Get class analytics report."""
    service = ReportService(db, ctx.tenant_id)
    return await service.generate_class_analytics(
        class_id=class_id,
        section_id=section_id,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/teacher/{teacher_id}", response_model=TeacherEffectivenessReport)
async def get_teacher_report(
    teacher_id: UUID,
    start_date: date,
    end_date: date,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    _: AuthUser = Depends(require_permissions(Permission.REPORT_VIEW_ALL)),
):
    """Get teacher effectiveness report."""
    service = ReportService(db, ctx.tenant_id)
    return await service.generate_teacher_report(
        teacher_id=teacher_id,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/my-performance", response_model=StudentReportSummary)
async def get_my_performance(
    start_date: date,
    end_date: date,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    subject_id: UUID = None,
):
    """Get own performance report (for students)."""
    service = ReportService(db, ctx.tenant_id)
    return await service.generate_student_report(
        student_id=ctx.user.user_id,
        start_date=start_date,
        end_date=end_date,
        subject_id=subject_id,
    )
