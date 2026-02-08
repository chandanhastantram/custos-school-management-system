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


# Report Card Endpoints
@router.get("/report-card/{student_id}")
async def get_report_card(
    student_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    academic_year: str = "2024-25",
    term: str = "Mid-Term",
):
    """
    Get student's report card data.
    
    Returns comprehensive report card including:
    - Subject-wise marks and grades
    - Attendance summary
    - Teacher remarks
    - Overall grade
    """
    service = ReportService(db, user.tenant_id)
    return await service.generate_report_card(student_id, academic_year, term)


@router.get("/report-card/{student_id}/pdf")
async def get_report_card_pdf(
    student_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    academic_year: str = "2024-25",
    term: str = "Mid-Term",
):
    """
    Get report card data formatted for PDF generation.
    
    The frontend will use this data to generate and download the PDF.
    """
    service = ReportService(db, user.tenant_id)
    return await service.get_report_card_pdf_data(student_id, academic_year, term)


@router.get("/class/{section_id}/report-cards")
async def get_class_report_cards(
    section_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    academic_year: str = "2024-25",
    term: str = "Mid-Term",
    _=Depends(require_permission(Permission.REPORT_VIEW_CLASS)),
):
    """Get report cards for all students in a class."""
    from app.users.models import User, StudentProfile
    from sqlalchemy.orm import selectinload
    
    # Get all students in section
    query = select(User).join(StudentProfile).where(
        User.tenant_id == user.tenant_id,
        StudentProfile.section_id == section_id,
    )
    result = await db.execute(query)
    students = list(result.scalars().all())
    
    service = ReportService(db, user.tenant_id)
    report_cards = []
    for student in students:
        rc = await service.generate_report_card(student.id, academic_year, term)
        report_cards.append(rc)
    
    return {
        "section_id": str(section_id),
        "academic_year": academic_year,
        "term": term,
        "report_cards": report_cards,
        "total": len(report_cards),
    }

