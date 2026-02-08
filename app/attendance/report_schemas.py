"""
CUSTOS Enhanced Attendance Report Schemas

Extended schemas for course-wise, week-wise, and hourly attendance reports.
"""

from datetime import date, time
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


# ============================================
# Course-wise Attendance Report
# ============================================

class CourseAttendanceMetrics(BaseModel):
    """Metrics for course-wise attendance."""
    subject_id: UUID
    subject_name: str
    subject_code: str
    
    total_hours: int              # TH - Total Hours scheduled
    actual_hours: int             # AH - Actual Hours conducted
    duty_leave: int               # DL - Duty Leave hours
    
    hours_present: int            # Hours student was present
    hours_absent: int             # Hours student was absent
    
    attendance_percentage: float  # AH% - Percentage based on actual hours
    effective_percentage: float   # (AH + DL)% - Including duty leave


class StudentCourseAttendance(BaseModel):
    """Student's course-wise attendance."""
    student_id: UUID
    student_name: str
    enrollment_number: str
    
    courses: List[CourseAttendanceMetrics]
    
    total_hours: int
    total_present: int
    total_absent: int
    overall_percentage: float


class CourseWiseReport(BaseModel):
    """Course-wise attendance report for a class."""
    class_id: UUID
    class_name: str
    section_id: Optional[UUID] = None
    section_name: Optional[str] = None
    
    semester: int
    academic_year_id: UUID
    from_date: date
    to_date: date
    
    subjects: List[CourseAttendanceMetrics]
    students: List[StudentCourseAttendance]
    
    # Summary
    total_students: int
    avg_attendance_percentage: float
    below_threshold_count: int
    threshold_percentage: float = 75.0


# ============================================
# Week-wise Attendance Report
# ============================================

class DailyAttendance(BaseModel):
    """Daily attendance for a student."""
    date: date
    day_name: str
    is_holiday: bool
    is_present: bool
    hours_present: int
    hours_absent: int


class WeekAttendance(BaseModel):
    """Weekly attendance summary."""
    week_number: int
    start_date: date
    end_date: date
    
    working_days: int
    days_present: int
    days_absent: int
    
    total_hours: int
    hours_present: int
    hours_absent: int
    
    attendance_percentage: float
    
    daily_breakdown: List[DailyAttendance]


class StudentWeeklyAttendance(BaseModel):
    """Student's week-wise attendance."""
    student_id: UUID
    student_name: str
    enrollment_number: str
    
    weeks: List[WeekAttendance]
    
    total_working_days: int
    total_present: int
    total_absent: int
    overall_percentage: float


class WeekWiseReport(BaseModel):
    """Week-wise attendance report."""
    class_id: UUID
    class_name: str
    section_id: Optional[UUID] = None
    
    from_date: date
    to_date: date
    
    weeks: List[WeekAttendance]
    students: List[StudentWeeklyAttendance]
    
    total_students: int
    avg_attendance_percentage: float


# ============================================
# Hourly Attendance Report
# ============================================

class HourSlot(BaseModel):
    """A single hour/period slot."""
    slot_number: int
    start_time: time
    end_time: time
    subject_name: Optional[str] = None
    subject_code: Optional[str] = None
    teacher_name: Optional[str] = None


class HourlyAttendanceRecord(BaseModel):
    """Attendance for each hour."""
    slot: HourSlot
    is_present: bool
    marked_by: Optional[str] = None
    marked_at: Optional[str] = None
    remarks: Optional[str] = None


class StudentHourlyAttendance(BaseModel):
    """Student's hourly attendance for a day."""
    student_id: UUID
    student_name: str
    enrollment_number: str
    
    hours: List[HourlyAttendanceRecord]
    
    hours_present: int
    hours_absent: int
    is_late: bool


class HourlyAttendanceReport(BaseModel):
    """Hourly attendance report for a day."""
    class_id: UUID
    class_name: str
    section_id: Optional[UUID] = None
    section_name: Optional[str] = None
    
    attendance_date: date
    
    slots: List[HourSlot]
    students: List[StudentHourlyAttendance]
    
    total_students: int
    slot_wise_present: dict  # {slot_number: count_present}


# ============================================
# Attendance Statistics
# ============================================

class AttendanceStatistics(BaseModel):
    """Overall attendance statistics."""
    from_date: date
    to_date: date
    
    total_students: int
    total_working_days: int
    total_hours_conducted: int
    
    avg_daily_attendance: float
    avg_hourly_attendance: float
    
    students_above_threshold: int
    students_below_threshold: int
    threshold_percentage: float = 75.0
    
    # Trend data
    daily_trend: List[dict]  # [{date, percentage}, ...]
    
    # Subject-wise
    subject_wise: List[dict]  # [{subject_name, avg_percentage}, ...]


class AttendanceShortageReport(BaseModel):
    """Report of students with attendance shortage."""
    threshold_percentage: float
    as_of_date: date
    
    students: List[dict]  # [{student_id, name, current_percentage, shortage_hours}, ...]
    total_count: int
