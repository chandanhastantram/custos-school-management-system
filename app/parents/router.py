"""
CUSTOS Parent Portal Router

API endpoints for parent dashboard and features.
"""

from typing import Optional, List, Annotated
from uuid import UUID
from datetime import datetime, timezone, date

from fastapi import APIRouter, Depends, Query, HTTPException, Body
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.auth.dependencies import CurrentUser, require_role
from app.users.models import User, ParentProfile, StudentProfile
from app.users.rbac import SystemRole
from app.parents.schemas import (
    ChildSummary, ChildDetail,
    ParentDashboardResponse,
    AttendanceSummary, AcademicSummary,
    FeesSummary, NotificationItem,
)
from app.parents.service import ParentService


router = APIRouter(tags=["Parent Portal"])


# Type alias for parent-authenticated user
ParentUser = Annotated[object, Depends(require_role(SystemRole.PARENT.value))]


def check_parent_role(user: CurrentUser) -> None:
    """Verify user has parent role."""
    if SystemRole.PARENT.value not in user.roles:
        raise HTTPException(status_code=403, detail="Parent access required")


# ============================================
# Dashboard
# ============================================

@router.get("/dashboard", response_model=ParentDashboardResponse)
async def get_parent_dashboard(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """
    Get comprehensive parent dashboard.
    
    Includes all children's summary data.
    """
    check_parent_role(user)
    service = ParentService(db, user.tenant_id)
    return await service.get_dashboard(user.user_id)


# ============================================
# Children Management
# ============================================

@router.get("/children", response_model=List[ChildSummary])
async def list_children(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """List all linked children."""
    check_parent_role(user)
    service = ParentService(db, user.tenant_id)
    return await service.get_children(user.user_id)


@router.get("/children/{student_id}", response_model=ChildDetail)
async def get_child_detail(
    student_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Get detailed information for a specific child."""
    check_parent_role(user)
    service = ParentService(db, user.tenant_id)
    
    # Verify parent-child relationship
    children = await service.get_children(user.user_id)
    child_ids = [c.student_id for c in children]
    
    if student_id not in child_ids:
        raise HTTPException(status_code=403, detail="Not authorized to view this student")
    
    return await service.get_child_detail(student_id)


# ============================================
# Academic Information
# ============================================

@router.get("/children/{student_id}/academics", response_model=AcademicSummary)
async def get_child_academics(
    student_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Get academic performance summary for a child."""
    check_parent_role(user)
    service = ParentService(db, user.tenant_id)
    
    # Verify access
    children = await service.get_children(user.user_id)
    child_ids = [c.student_id for c in children]
    
    if student_id not in child_ids:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return await service.get_academic_summary(student_id)


@router.get("/children/{student_id}/assignments")
async def get_child_assignments(
    student_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=50),
):
    """Get assignments for a child."""
    check_parent_role(user)
    service = ParentService(db, user.tenant_id)
    
    # Verify access
    children = await service.get_children(user.user_id)
    child_ids = [c.student_id for c in children]
    
    if student_id not in child_ids:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return await service.get_assignments(student_id, status, page, size)


@router.get("/children/{student_id}/report-cards")
async def get_child_report_cards(
    student_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Get report cards for a child."""
    check_parent_role(user)
    service = ParentService(db, user.tenant_id)
    
    children = await service.get_children(user.user_id)
    child_ids = [c.student_id for c in children]
    
    if student_id not in child_ids:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return await service.get_report_cards(student_id)


# ============================================
# Attendance
# ============================================

@router.get("/children/{student_id}/attendance", response_model=AttendanceSummary)
async def get_child_attendance(
    student_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    month: Optional[int] = None,
    year: Optional[int] = None,
):
    """Get attendance summary for a child."""
    check_parent_role(user)
    service = ParentService(db, user.tenant_id)
    
    children = await service.get_children(user.user_id)
    child_ids = [c.student_id for c in children]
    
    if student_id not in child_ids:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if not month:
        month = datetime.now().month
    if not year:
        year = datetime.now().year
    
    return await service.get_attendance_summary(student_id, month, year)


# ============================================
# Fees & Payments
# ============================================

@router.get("/children/{student_id}/fees", response_model=FeesSummary)
async def get_child_fees(
    student_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Get fee summary for a child."""
    check_parent_role(user)
    service = ParentService(db, user.tenant_id)
    
    children = await service.get_children(user.user_id)
    child_ids = [c.student_id for c in children]
    
    if student_id not in child_ids:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return await service.get_fees_summary(student_id)


@router.get("/children/{student_id}/invoices")
async def get_child_invoices(
    student_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    status: Optional[str] = None,
):
    """Get invoices for a child."""
    check_parent_role(user)
    service = ParentService(db, user.tenant_id)
    
    children = await service.get_children(user.user_id)
    child_ids = [c.student_id for c in children]
    
    if student_id not in child_ids:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return await service.get_invoices(student_id, status)


@router.get("/children/{student_id}/payment-history")
async def get_child_payment_history(
    student_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=50),
):
    """Get payment history for a child."""
    check_parent_role(user)
    service = ParentService(db, user.tenant_id)
    
    children = await service.get_children(user.user_id)
    child_ids = [c.student_id for c in children]
    
    if student_id not in child_ids:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return await service.get_payment_history(student_id, page, size)


# ============================================
# Timetable & Calendar
# ============================================

@router.get("/children/{student_id}/timetable")
async def get_child_timetable(
    student_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Get class timetable for a child."""
    check_parent_role(user)
    service = ParentService(db, user.tenant_id)
    
    children = await service.get_children(user.user_id)
    child_ids = [c.student_id for c in children]
    
    if student_id not in child_ids:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return await service.get_timetable(student_id)


@router.get("/calendar")
async def get_school_calendar(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    month: Optional[int] = None,
    year: Optional[int] = None,
):
    """Get school calendar events."""
    check_parent_role(user)
    service = ParentService(db, user.tenant_id)
    
    if not month:
        month = datetime.now().month
    if not year:
        year = datetime.now().year
    
    return await service.get_calendar_events(month, year)


# ============================================
# Notifications & Announcements
# ============================================

@router.get("/notifications", response_model=List[NotificationItem])
async def get_notifications(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    unread_only: bool = False,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=50),
):
    """Get parent notifications."""
    check_parent_role(user)
    service = ParentService(db, user.tenant_id)
    return await service.get_notifications(user.user_id, unread_only, page, size)


@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Mark a notification as read."""
    check_parent_role(user)
    service = ParentService(db, user.tenant_id)
    await service.mark_notification_read(notification_id, user.user_id)
    return {"success": True}


@router.get("/announcements")
async def get_announcements(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=50),
):
    """Get school announcements."""
    check_parent_role(user)
    service = ParentService(db, user.tenant_id)
    return await service.get_announcements(page, size)


# ============================================
# Communication
# ============================================

@router.get("/children/{student_id}/teachers")
async def get_child_teachers(
    student_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Get list of teachers for a child's class."""
    check_parent_role(user)
    service = ParentService(db, user.tenant_id)
    
    children = await service.get_children(user.user_id)
    child_ids = [c.student_id for c in children]
    
    if student_id not in child_ids:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return await service.get_teachers(student_id)


@router.post("/messages")
async def send_message(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    teacher_id: UUID = Body(...),
    subject: str = Body(...),
    message: str = Body(...),
    student_id: Optional[UUID] = Body(None),
):
    """Send a message to a teacher."""
    check_parent_role(user)
    service = ParentService(db, user.tenant_id)
    
    if student_id:
        children = await service.get_children(user.user_id)
        child_ids = [c.student_id for c in children]
        
        if student_id not in child_ids:
            raise HTTPException(status_code=403, detail="Not authorized")
    
    return await service.send_message(user.user_id, teacher_id, subject, message, student_id)


# ============================================
# Leave Requests
# ============================================

@router.post("/children/{student_id}/leave-request")
async def submit_leave_request(
    student_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    start_date: date = Body(...),
    end_date: date = Body(...),
    reason: str = Body(...),
):
    """Submit a leave request for a child."""
    check_parent_role(user)
    service = ParentService(db, user.tenant_id)
    
    children = await service.get_children(user.user_id)
    child_ids = [c.student_id for c in children]
    
    if student_id not in child_ids:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return await service.submit_leave_request(
        student_id, user.user_id, start_date, end_date, reason
    )


@router.get("/children/{student_id}/leave-requests")
async def get_leave_requests(
    student_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Get leave request history for a child."""
    check_parent_role(user)
    service = ParentService(db, user.tenant_id)
    
    children = await service.get_children(user.user_id)
    child_ids = [c.student_id for c in children]
    
    if student_id not in child_ids:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return await service.get_leave_requests(student_id)
