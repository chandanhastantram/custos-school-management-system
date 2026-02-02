"""
CUSTOS Attendance Router

API endpoints for attendance management.
"""

from datetime import date, datetime
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth.dependencies import CurrentUser, require_permission
from app.users.rbac import Permission
from app.attendance.service import AttendanceService
from app.attendance.models import AttendanceStatus, LeaveRequestStatus
from app.attendance.schemas import (
    MarkAttendanceRequest,
    BulkAttendanceRequest,
    AttendanceRecordResponse,
    StudentAttendanceSummaryResponse,
    LeaveRequestCreate,
    LeaveRequestResponse,
    LeaveRequestReview,
    MarkTeacherAttendanceRequest,
    TeacherAttendanceResponse,
)


router = APIRouter(tags=["Attendance"])


# ============================================
# Student Attendance
# ============================================

@router.post("/students/mark", response_model=AttendanceRecordResponse)
async def mark_single_attendance(
    attendance_date: date,
    class_id: UUID,
    data: MarkAttendanceRequest,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    section_id: Optional[UUID] = None,
    _=Depends(require_permission(Permission.ATTENDANCE_MARK)),
):
    """Mark attendance for a single student."""
    service = AttendanceService(db, user.tenant_id)
    record = await service.mark_student_attendance(
        attendance_date=attendance_date,
        class_id=class_id,
        data=data,
        marked_by=user.user_id,
        section_id=section_id,
    )
    return AttendanceRecordResponse.model_validate(record)


@router.post("/students/mark-bulk")
async def mark_bulk_attendance(
    data: BulkAttendanceRequest,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.ATTENDANCE_MARK)),
):
    """Mark attendance for multiple students at once."""
    service = AttendanceService(db, user.tenant_id)
    count = await service.mark_bulk_attendance(data, user.user_id)
    return {"success": True, "records_updated": count}


@router.get("/students/{student_id}", response_model=List[AttendanceRecordResponse])
async def get_student_attendance(
    student_id: UUID,
    start_date: date,
    end_date: date,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.ATTENDANCE_VIEW)),
):
    """Get attendance records for a student."""
    service = AttendanceService(db, user.tenant_id)
    records = await service.get_student_attendance(student_id, start_date, end_date)
    return [AttendanceRecordResponse.model_validate(r) for r in records]


@router.get("/students/{student_id}/summary", response_model=StudentAttendanceSummaryResponse)
async def get_student_summary(
    student_id: UUID,
    year: int,
    month: int,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.ATTENDANCE_VIEW)),
):
    """Get monthly attendance summary for a student."""
    service = AttendanceService(db, user.tenant_id)
    return await service.get_attendance_summary(student_id, year, month)


@router.get("/students/{student_id}/calendar")
async def get_student_calendar(
    student_id: UUID,
    year: int,
    month: int,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.ATTENDANCE_VIEW)),
):
    """Get attendance calendar for a student."""
    service = AttendanceService(db, user.tenant_id)
    return await service.get_monthly_calendar(student_id, year, month)


@router.get("/class/{class_id}/daily")
async def get_class_daily_attendance(
    class_id: UUID,
    attendance_date: date,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    section_id: Optional[UUID] = None,
    _=Depends(require_permission(Permission.ATTENDANCE_VIEW)),
):
    """Get daily attendance for a class."""
    service = AttendanceService(db, user.tenant_id)
    records = await service.get_class_attendance(class_id, attendance_date, section_id)
    return [AttendanceRecordResponse.model_validate(r) for r in records]


@router.get("/class/{class_id}/report")
async def get_class_daily_report(
    class_id: UUID,
    attendance_date: date,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    section_id: Optional[UUID] = None,
    _=Depends(require_permission(Permission.ATTENDANCE_VIEW)),
):
    """Get daily attendance report for a class."""
    service = AttendanceService(db, user.tenant_id)
    return await service.get_class_daily_report(class_id, attendance_date, section_id)


# ============================================
# Leave Requests
# ============================================

@router.post("/leave-requests", response_model=LeaveRequestResponse, status_code=201)
async def create_leave_request(
    data: LeaveRequestCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a leave request.
    
    Can be created by parents or students.
    """
    service = AttendanceService(db, user.tenant_id)
    leave_request = await service.create_leave_request(data, user.user_id)
    return LeaveRequestResponse.model_validate(leave_request)


@router.get("/leave-requests/{request_id}", response_model=LeaveRequestResponse)
async def get_leave_request(
    request_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Get a leave request by ID."""
    service = AttendanceService(db, user.tenant_id)
    leave_request = await service.get_leave_request(request_id)
    return LeaveRequestResponse.model_validate(leave_request)


@router.post("/leave-requests/{request_id}/review", response_model=LeaveRequestResponse)
async def review_leave_request(
    request_id: UUID,
    data: LeaveRequestReview,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.ATTENDANCE_MARK)),
):
    """Review (approve/reject) a leave request."""
    service = AttendanceService(db, user.tenant_id)
    leave_request = await service.review_leave_request(request_id, data, user.user_id)
    return LeaveRequestResponse.model_validate(leave_request)


@router.get("/leave-requests/student/{student_id}", response_model=List[LeaveRequestResponse])
async def get_student_leave_requests(
    student_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    status: Optional[LeaveRequestStatus] = None,
):
    """Get leave requests for a student."""
    service = AttendanceService(db, user.tenant_id)
    requests = await service.get_student_leave_requests(student_id, status)
    return [LeaveRequestResponse.model_validate(r) for r in requests]


@router.get("/leave-requests/pending", response_model=List[LeaveRequestResponse])
async def get_pending_leave_requests(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.ATTENDANCE_MARK)),
):
    """Get all pending leave requests for review."""
    service = AttendanceService(db, user.tenant_id)
    requests = await service.get_pending_leave_requests()
    return [LeaveRequestResponse.model_validate(r) for r in requests]


# ============================================
# Teacher Attendance
# ============================================

@router.post("/teachers/mark", response_model=TeacherAttendanceResponse)
async def mark_teacher_attendance(
    attendance_date: date,
    data: MarkTeacherAttendanceRequest,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.ATTENDANCE_MARK)),
):
    """Mark attendance for a teacher."""
    service = AttendanceService(db, user.tenant_id)
    record = await service.mark_teacher_attendance(attendance_date, data, user.user_id)
    return TeacherAttendanceResponse.model_validate(record)


@router.get("/teachers/{teacher_id}", response_model=List[TeacherAttendanceResponse])
async def get_teacher_attendance(
    teacher_id: UUID,
    start_date: date,
    end_date: date,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.ATTENDANCE_VIEW)),
):
    """Get attendance records for a teacher."""
    service = AttendanceService(db, user.tenant_id)
    records = await service.get_teacher_attendance(teacher_id, start_date, end_date)
    return [TeacherAttendanceResponse.model_validate(r) for r in records]
