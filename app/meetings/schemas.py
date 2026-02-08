"""
CUSTOS Online Meetings Schemas

Pydantic schemas for meetings and virtual classrooms.
"""

from datetime import datetime, date, time
from enum import Enum
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


# ============================================
# Enums
# ============================================

class MeetingStatus(str, Enum):
    SCHEDULED = "scheduled"
    LIVE = "live"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    RESCHEDULED = "rescheduled"


class MeetingPlatform(str, Enum):
    ZOOM = "zoom"
    GOOGLE_MEET = "google_meet"
    MICROSOFT_TEAMS = "microsoft_teams"
    WEBEX = "webex"
    JITSI = "jitsi"
    CUSTOM = "custom"


class MeetingType(str, Enum):
    LECTURE = "lecture"
    LAB = "lab"
    TUTORIAL = "tutorial"
    SEMINAR = "seminar"
    WEBINAR = "webinar"
    FACULTY_MEETING = "faculty_meeting"
    PARENT_TEACHER = "parent_teacher"
    COUNSELING = "counseling"
    EXAM = "exam"
    OTHER = "other"


class ParticipantRole(str, Enum):
    HOST = "host"
    CO_HOST = "co_host"
    PRESENTER = "presenter"
    ATTENDEE = "attendee"


# ============================================
# Meeting Schemas
# ============================================

class MeetingCreate(BaseModel):
    """Schema for creating a meeting."""
    title: str = Field(..., min_length=5, max_length=300)
    description: Optional[str] = None
    meeting_type: MeetingType = MeetingType.LECTURE
    platform: MeetingPlatform = MeetingPlatform.GOOGLE_MEET
    
    meeting_date: date
    start_time: time
    end_time: time
    duration_minutes: int = Field(60, ge=15, le=480)
    timezone: str = "Asia/Kolkata"
    
    # Optional external meeting details
    meeting_url: Optional[str] = None
    passcode: Optional[str] = None
    
    # Academic context
    class_id: Optional[UUID] = None
    section_id: Optional[UUID] = None
    subject_id: Optional[UUID] = None
    
    # Settings
    allow_recording: bool = True
    auto_recording: bool = False
    mute_on_entry: bool = True
    require_registration: bool = False
    max_participants: Optional[int] = None
    enable_waiting_room: bool = False
    
    # Recurrence
    is_recurring: bool = False
    recurrence_pattern: Optional[str] = None
    recurrence_end_date: Optional[date] = None
    
    # Participants to invite
    participant_ids: Optional[List[UUID]] = None


class MeetingUpdate(BaseModel):
    """Schema for updating a meeting."""
    title: Optional[str] = Field(None, min_length=5, max_length=300)
    description: Optional[str] = None
    meeting_type: Optional[MeetingType] = None
    status: Optional[MeetingStatus] = None
    
    meeting_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    
    meeting_url: Optional[str] = None
    passcode: Optional[str] = None
    
    allow_recording: Optional[bool] = None
    mute_on_entry: Optional[bool] = None
    enable_waiting_room: Optional[bool] = None


class MeetingResponse(BaseModel):
    """Schema for meeting response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    meeting_code: str
    title: str
    description: Optional[str] = None
    meeting_type: MeetingType
    status: MeetingStatus
    platform: MeetingPlatform
    
    meeting_url: Optional[str] = None
    meeting_id: Optional[str] = None
    passcode: Optional[str] = None
    
    host_id: UUID
    meeting_date: date
    start_time: time
    end_time: time
    duration_minutes: int
    timezone: str
    
    is_recurring: bool
    recurrence_pattern: Optional[str] = None
    
    class_id: Optional[UUID] = None
    section_id: Optional[UUID] = None
    subject_id: Optional[UUID] = None
    
    allow_recording: bool
    mute_on_entry: bool
    enable_waiting_room: bool
    
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    recording_url: Optional[str] = None
    
    total_participants: int
    created_at: datetime


class MeetingListResponse(BaseModel):
    """Schema for paginated meeting list."""
    items: List[MeetingResponse]
    total: int
    page: int
    page_size: int
    pages: int


class MeetingJoinInfo(BaseModel):
    """Schema for meeting join information."""
    meeting_url: str
    passcode: Optional[str] = None
    dial_in_number: Optional[str] = None
    meeting_id: Optional[str] = None
    platform: MeetingPlatform


# ============================================
# Participant Schemas
# ============================================

class ParticipantAdd(BaseModel):
    """Schema for adding participants."""
    user_ids: List[UUID]
    role: ParticipantRole = ParticipantRole.ATTENDEE
    send_invitation: bool = True


class ParticipantResponse(BaseModel):
    """Schema for participant response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    meeting_id: UUID
    user_id: UUID
    role: ParticipantRole
    invitation_sent: bool
    rsvp_status: Optional[str] = None
    rsvp_at: Optional[datetime] = None


# ============================================
# Attendance Schemas
# ============================================

class AttendanceMarkRequest(BaseModel):
    """Schema for marking attendance."""
    user_id: UUID
    join_time: Optional[datetime] = None
    device_type: Optional[str] = None


class AttendanceResponse(BaseModel):
    """Schema for attendance response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    meeting_id: UUID
    user_id: UUID
    status: str
    join_time: Optional[datetime] = None
    leave_time: Optional[datetime] = None
    duration_minutes: int
    join_count: int


class MeetingAttendanceReport(BaseModel):
    """Schema for meeting attendance report."""
    meeting_id: UUID
    meeting_title: str
    meeting_date: date
    scheduled_duration: int
    actual_duration: Optional[int] = None
    total_invited: int
    total_attended: int
    attendance_rate: float
    attendees: List[AttendanceResponse]


# ============================================
# Resource Schemas
# ============================================

class ResourceCreate(BaseModel):
    """Schema for adding meeting resource."""
    name: str = Field(..., min_length=1, max_length=200)
    resource_type: str
    file_url: Optional[str] = None
    external_url: Optional[str] = None
    is_downloadable: bool = True


class ResourceResponse(BaseModel):
    """Schema for resource response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    meeting_id: UUID
    name: str
    resource_type: str
    file_url: Optional[str] = None
    external_url: Optional[str] = None
    shared_by: UUID
    shared_at: datetime
    is_downloadable: bool
    download_count: int


# ============================================
# Platform Config Schemas
# ============================================

class PlatformConfigCreate(BaseModel):
    """Schema for creating platform config."""
    platform: MeetingPlatform
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    account_id: Optional[str] = None
    default_duration: int = 60
    default_settings: Optional[dict] = None


class PlatformConfigResponse(BaseModel):
    """Schema for platform config response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    platform: MeetingPlatform
    is_active: bool
    default_duration: int
    last_verified_at: Optional[datetime] = None


# ============================================
# Statistics Schemas
# ============================================

class MeetingStatistics(BaseModel):
    """Schema for meeting statistics."""
    total_meetings: int
    completed_meetings: int
    cancelled_meetings: int
    total_duration_hours: float
    avg_attendance_rate: float
    most_used_platform: str
