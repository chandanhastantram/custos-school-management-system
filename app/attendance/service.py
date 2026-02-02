"""
CUSTOS Attendance Service

Business logic for attendance management.
"""

from datetime import datetime, date, timezone
from typing import Optional, List, Tuple, Dict
from uuid import UUID
from calendar import monthrange

from sqlalchemy import select, func, and_, or_, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundError, ValidationError
from app.attendance.models import (
    StudentAttendance, AttendanceSummary, LeaveRequest, TeacherAttendance,
    AttendanceStatus, LeaveRequestStatus, LeaveType,
)
from app.attendance.schemas import (
    MarkAttendanceRequest, BulkAttendanceRequest,
    LeaveRequestCreate, LeaveRequestReview,
    MarkTeacherAttendanceRequest,
    StudentAttendanceSummaryResponse, AttendanceCalendarDay,
)


class AttendanceService:
    """Service for attendance management."""
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
    
    # ============================================
    # Student Attendance
    # ============================================
    
    async def mark_student_attendance(
        self,
        attendance_date: date,
        class_id: UUID,
        data: MarkAttendanceRequest,
        marked_by: UUID,
        section_id: Optional[UUID] = None,
        academic_year_id: Optional[UUID] = None,
    ) -> StudentAttendance:
        """Mark attendance for a single student."""
        # Check if already exists
        query = select(StudentAttendance).where(
            StudentAttendance.tenant_id == self.tenant_id,
            StudentAttendance.student_id == data.student_id,
            StudentAttendance.attendance_date == attendance_date,
        )
        result = await self.session.execute(query)
        existing = result.scalar_one_or_none()
        
        if existing:
            # Update existing
            existing.status = data.status
            existing.check_in_time = data.check_in_time
            existing.check_out_time = data.check_out_time
            existing.late_minutes = data.late_minutes
            existing.remarks = data.remarks
            existing.marked_by = marked_by
            existing.marked_at = datetime.now(timezone.utc)
            attendance = existing
        else:
            # Create new
            attendance = StudentAttendance(
                tenant_id=self.tenant_id,
                student_id=data.student_id,
                class_id=class_id,
                section_id=section_id,
                attendance_date=attendance_date,
                status=data.status,
                check_in_time=data.check_in_time,
                check_out_time=data.check_out_time,
                late_minutes=data.late_minutes,
                remarks=data.remarks,
                marked_by=marked_by,
                marked_at=datetime.now(timezone.utc),
                academic_year_id=academic_year_id,
            )
            self.session.add(attendance)
        
        await self.session.commit()
        await self.session.refresh(attendance)
        return attendance
    
    async def mark_bulk_attendance(
        self,
        data: BulkAttendanceRequest,
        marked_by: UUID,
        academic_year_id: Optional[UUID] = None,
    ) -> int:
        """Mark attendance for multiple students."""
        count = 0
        for record in data.records:
            await self.mark_student_attendance(
                attendance_date=data.attendance_date,
                class_id=data.class_id,
                data=record,
                marked_by=marked_by,
                section_id=data.section_id,
                academic_year_id=academic_year_id,
            )
            count += 1
        
        return count
    
    async def get_student_attendance(
        self,
        student_id: UUID,
        start_date: date,
        end_date: date,
    ) -> List[StudentAttendance]:
        """Get attendance records for a student in date range."""
        query = select(StudentAttendance).where(
            StudentAttendance.tenant_id == self.tenant_id,
            StudentAttendance.student_id == student_id,
            StudentAttendance.attendance_date >= start_date,
            StudentAttendance.attendance_date <= end_date,
        ).order_by(StudentAttendance.attendance_date)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_class_attendance(
        self,
        class_id: UUID,
        attendance_date: date,
        section_id: Optional[UUID] = None,
    ) -> List[StudentAttendance]:
        """Get attendance for a class on a specific date."""
        query = select(StudentAttendance).where(
            StudentAttendance.tenant_id == self.tenant_id,
            StudentAttendance.class_id == class_id,
            StudentAttendance.attendance_date == attendance_date,
        )
        
        if section_id:
            query = query.where(StudentAttendance.section_id == section_id)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_attendance_summary(
        self,
        student_id: UUID,
        year: int,
        month: int,
    ) -> StudentAttendanceSummaryResponse:
        """Get or calculate attendance summary for a month."""
        # Check for cached summary
        query = select(AttendanceSummary).where(
            AttendanceSummary.tenant_id == self.tenant_id,
            AttendanceSummary.student_id == student_id,
            AttendanceSummary.year == year,
            AttendanceSummary.month == month,
        )
        result = await self.session.execute(query)
        cached = result.scalar_one_or_none()
        
        if cached:
            return StudentAttendanceSummaryResponse.model_validate(cached)
        
        # Calculate from records
        start_date = date(year, month, 1)
        _, last_day = monthrange(year, month)
        end_date = date(year, month, last_day)
        
        records = await self.get_student_attendance(student_id, start_date, end_date)
        
        # Count each status
        present = sum(1 for r in records if r.status == AttendanceStatus.PRESENT)
        absent = sum(1 for r in records if r.status == AttendanceStatus.ABSENT)
        late = sum(1 for r in records if r.status == AttendanceStatus.LATE)
        half_day = sum(1 for r in records if r.status == AttendanceStatus.HALF_DAY)
        excused = sum(1 for r in records if r.status == AttendanceStatus.EXCUSED)
        
        total = present + absent + late + half_day + excused
        percentage = (present + late + half_day * 0.5) / total * 100 if total > 0 else 0
        
        return StudentAttendanceSummaryResponse(
            student_id=student_id,
            year=year,
            month=month,
            total_days=total,
            present_days=present,
            absent_days=absent,
            late_days=late,
            half_days=half_day,
            excused_days=excused,
            attendance_percentage=round(percentage, 2),
        )
    
    async def get_monthly_calendar(
        self,
        student_id: UUID,
        year: int,
        month: int,
    ) -> Dict:
        """Get attendance calendar for a month."""
        start_date = date(year, month, 1)
        _, last_day = monthrange(year, month)
        end_date = date(year, month, last_day)
        
        records = await self.get_student_attendance(student_id, start_date, end_date)
        
        days = []
        for record in records:
            days.append(AttendanceCalendarDay(
                date=record.attendance_date,
                status=record.status,
                remarks=record.remarks,
            ))
        
        summary = await self.get_attendance_summary(student_id, year, month)
        
        return {
            "student_id": str(student_id),
            "year": year,
            "month": month,
            "days": [d.model_dump() for d in days],
            "summary": summary.model_dump(),
        }
    
    # ============================================
    # Leave Requests
    # ============================================
    
    async def create_leave_request(
        self,
        data: LeaveRequestCreate,
        requested_by: UUID,
    ) -> LeaveRequest:
        """Create a leave request."""
        # Validate dates
        if data.start_date > data.end_date:
            raise ValidationError("End date must be after start date")
        
        leave_request = LeaveRequest(
            tenant_id=self.tenant_id,
            student_id=data.student_id,
            requested_by=requested_by,
            leave_type=data.leave_type,
            start_date=data.start_date,
            end_date=data.end_date,
            reason=data.reason,
            attachments=data.attachments,
        )
        
        self.session.add(leave_request)
        await self.session.commit()
        await self.session.refresh(leave_request)
        return leave_request
    
    async def get_leave_request(self, request_id: UUID) -> LeaveRequest:
        """Get a leave request by ID."""
        query = select(LeaveRequest).where(
            LeaveRequest.tenant_id == self.tenant_id,
            LeaveRequest.id == request_id,
        )
        result = await self.session.execute(query)
        leave_request = result.scalar_one_or_none()
        
        if not leave_request:
            raise ResourceNotFoundError("LeaveRequest", str(request_id))
        
        return leave_request
    
    async def review_leave_request(
        self,
        request_id: UUID,
        data: LeaveRequestReview,
        reviewed_by: UUID,
    ) -> LeaveRequest:
        """Review (approve/reject) a leave request."""
        leave_request = await self.get_leave_request(request_id)
        
        leave_request.status = data.status
        leave_request.reviewed_by = reviewed_by
        leave_request.reviewed_at = datetime.now(timezone.utc)
        leave_request.review_notes = data.review_notes
        
        # If approved, mark attendance as excused
        if data.status == LeaveRequestStatus.APPROVED:
            await self._mark_leave_period_as_excused(leave_request)
        
        await self.session.commit()
        await self.session.refresh(leave_request)
        return leave_request
    
    async def _mark_leave_period_as_excused(self, leave_request: LeaveRequest) -> None:
        """Mark attendance as excused for approved leave period."""
        current = leave_request.start_date
        while current <= leave_request.end_date:
            # Check if record exists
            query = select(StudentAttendance).where(
                StudentAttendance.tenant_id == self.tenant_id,
                StudentAttendance.student_id == leave_request.student_id,
                StudentAttendance.attendance_date == current,
            )
            result = await self.session.execute(query)
            existing = result.scalar_one_or_none()
            
            if existing:
                existing.status = AttendanceStatus.EXCUSED
                existing.remarks = f"Leave approved: {leave_request.reason[:100]}"
            
            # Move to next day
            from datetime import timedelta
            current = current + timedelta(days=1)
    
    async def get_student_leave_requests(
        self,
        student_id: UUID,
        status: Optional[LeaveRequestStatus] = None,
    ) -> List[LeaveRequest]:
        """Get leave requests for a student."""
        query = select(LeaveRequest).where(
            LeaveRequest.tenant_id == self.tenant_id,
            LeaveRequest.student_id == student_id,
        )
        
        if status:
            query = query.where(LeaveRequest.status == status)
        
        query = query.order_by(LeaveRequest.created_at.desc())
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_pending_leave_requests(
        self,
        class_id: Optional[UUID] = None,
    ) -> List[LeaveRequest]:
        """Get all pending leave requests for review."""
        query = select(LeaveRequest).where(
            LeaveRequest.tenant_id == self.tenant_id,
            LeaveRequest.status == LeaveRequestStatus.PENDING,
        ).order_by(LeaveRequest.created_at)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    # ============================================
    # Teacher Attendance
    # ============================================
    
    async def mark_teacher_attendance(
        self,
        attendance_date: date,
        data: MarkTeacherAttendanceRequest,
        marked_by: UUID,
    ) -> TeacherAttendance:
        """Mark attendance for a teacher."""
        query = select(TeacherAttendance).where(
            TeacherAttendance.tenant_id == self.tenant_id,
            TeacherAttendance.teacher_id == data.teacher_id,
            TeacherAttendance.attendance_date == attendance_date,
        )
        result = await self.session.execute(query)
        existing = result.scalar_one_or_none()
        
        if existing:
            existing.status = data.status
            existing.check_in_time = data.check_in_time
            existing.check_out_time = data.check_out_time
            existing.remarks = data.remarks
            existing.marked_by = marked_by
            attendance = existing
        else:
            attendance = TeacherAttendance(
                tenant_id=self.tenant_id,
                teacher_id=data.teacher_id,
                attendance_date=attendance_date,
                status=data.status,
                check_in_time=data.check_in_time,
                check_out_time=data.check_out_time,
                remarks=data.remarks,
                marked_by=marked_by,
            )
            self.session.add(attendance)
        
        await self.session.commit()
        await self.session.refresh(attendance)
        return attendance
    
    async def get_teacher_attendance(
        self,
        teacher_id: UUID,
        start_date: date,
        end_date: date,
    ) -> List[TeacherAttendance]:
        """Get attendance records for a teacher."""
        query = select(TeacherAttendance).where(
            TeacherAttendance.tenant_id == self.tenant_id,
            TeacherAttendance.teacher_id == teacher_id,
            TeacherAttendance.attendance_date >= start_date,
            TeacherAttendance.attendance_date <= end_date,
        ).order_by(TeacherAttendance.attendance_date)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    # ============================================
    # Reports
    # ============================================
    
    async def get_class_daily_report(
        self,
        class_id: UUID,
        attendance_date: date,
        section_id: Optional[UUID] = None,
    ) -> Dict:
        """Get daily attendance report for a class."""
        records = await self.get_class_attendance(class_id, attendance_date, section_id)
        
        present = sum(1 for r in records if r.status == AttendanceStatus.PRESENT)
        absent = sum(1 for r in records if r.status == AttendanceStatus.ABSENT)
        late = sum(1 for r in records if r.status == AttendanceStatus.LATE)
        not_marked = sum(1 for r in records if r.status == AttendanceStatus.NOT_MARKED)
        
        return {
            "attendance_date": attendance_date.isoformat(),
            "class_id": str(class_id),
            "section_id": str(section_id) if section_id else None,
            "total_students": len(records),
            "present_count": present,
            "absent_count": absent,
            "late_count": late,
            "not_marked_count": not_marked,
            "attendance_percentage": round(present / len(records) * 100, 2) if records else 0,
        }
