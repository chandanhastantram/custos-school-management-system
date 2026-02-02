"""
CUSTOS Attendance Schemas

Pydantic schemas for attendance API.
"""

from datetime import datetime, date, time
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, field_validator

from app.attendance.models import AttendanceStatus, LeaveRequestStatus, LeaveType


# ============================================
# Student Attendance Schemas
# ============================================

class MarkAttendanceRequest(BaseModel):
    """Schema for marking single student attendance."""
    student_id: UUID
    status: AttendanceStatus
    check_in_time: Optional[time] = None
    check_out_time: Optional[time] = None
    late_minutes: int = 0
    remarks: Optional[str] = Field(None, max_length=500)


class BulkAttendanceRequest(BaseModel):
    """Schema for marking attendance for multiple students."""
    attendance_date: date
    class_id: UUID
    section_id: Optional[UUID] = None
    records: List[MarkAttendanceRequest]


class AttendanceRecordResponse(BaseModel):
    """Schema for attendance record response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    student_id: UUID
    class_id: UUID
    section_id: Optional[UUID] = None
    attendance_date: date
    status: AttendanceStatus
    check_in_time: Optional[time] = None
    check_out_time: Optional[time] = None
    late_minutes: int = 0
    remarks: Optional[str] = None
    marked_by: Optional[UUID] = None
    marked_at: Optional[datetime] = None


class StudentAttendanceSummaryResponse(BaseModel):
    """Schema for student attendance summary."""
    model_config = ConfigDict(from_attributes=True)
    
    student_id: UUID
    year: int
    month: int
    total_days: int = 0
    present_days: int = 0
    absent_days: int = 0
    late_days: int = 0
    half_days: int = 0
    excused_days: int = 0
    attendance_percentage: float = 0.0


class DailyAttendanceReport(BaseModel):
    """Schema for daily class attendance report."""
    attendance_date: date
    class_id: UUID
    class_name: str
    section_id: Optional[UUID] = None
    section_name: Optional[str] = None
    total_students: int = 0
    present_count: int = 0
    absent_count: int = 0
    late_count: int = 0
    not_marked_count: int = 0


class AttendanceCalendarDay(BaseModel):
    """Schema for calendar view of attendance."""
    date: date
    status: AttendanceStatus
    remarks: Optional[str] = None


class MonthlyAttendanceCalendar(BaseModel):
    """Schema for monthly calendar view."""
    student_id: UUID
    year: int
    month: int
    days: List[AttendanceCalendarDay] = []
    summary: StudentAttendanceSummaryResponse


# ============================================
# Leave Request Schemas
# ============================================

class LeaveRequestCreate(BaseModel):
    """Schema for creating a leave request."""
    student_id: UUID
    leave_type: LeaveType = LeaveType.CASUAL
    start_date: date
    end_date: date
    reason: str = Field(..., min_length=10, max_length=1000)
    attachments: Optional[List[Dict[str, Any]]] = None
    
    @field_validator("end_date")
    @classmethod
    def end_date_must_be_after_start(cls, v, info):
        if "start_date" in info.data and v < info.data["start_date"]:
            raise ValueError("End date must be on or after start date")
        return v


class LeaveRequestResponse(BaseModel):
    """Schema for leave request response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    student_id: UUID
    requested_by: UUID
    leave_type: LeaveType
    start_date: date
    end_date: date
    reason: str
    attachments: Optional[List[Dict[str, Any]]] = None
    status: LeaveRequestStatus
    reviewed_by: Optional[UUID] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    created_at: datetime


class LeaveRequestReview(BaseModel):
    """Schema for reviewing a leave request."""
    status: LeaveRequestStatus
    review_notes: Optional[str] = Field(None, max_length=500)


# ============================================
# Teacher Attendance Schemas
# ============================================

class MarkTeacherAttendanceRequest(BaseModel):
    """Schema for marking teacher attendance."""
    teacher_id: UUID
    status: AttendanceStatus
    check_in_time: Optional[time] = None
    check_out_time: Optional[time] = None
    remarks: Optional[str] = Field(None, max_length=500)


class TeacherAttendanceResponse(BaseModel):
    """Schema for teacher attendance response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    teacher_id: UUID
    attendance_date: date
    status: AttendanceStatus
    check_in_time: Optional[time] = None
    check_out_time: Optional[time] = None
    remarks: Optional[str] = None
    marked_by: Optional[UUID] = None
