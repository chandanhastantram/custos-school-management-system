"""
CUSTOS Attendance Module

Student and teacher attendance management.
"""

from app.attendance.models import (
    StudentAttendance,
    AttendanceSummary,
    LeaveRequest,
    TeacherAttendance,
    AttendanceStatus,
    LeaveRequestStatus,
    LeaveType,
)
from app.attendance.service import AttendanceService
from app.attendance.router import router as attendance_router

__all__ = [
    "StudentAttendance",
    "AttendanceSummary",
    "LeaveRequest",
    "TeacherAttendance",
    "AttendanceStatus",
    "LeaveRequestStatus",
    "LeaveType",
    "AttendanceService",
    "attendance_router",
]
