"""
CUSTOS Online Meetings Models

Virtual classroom and meeting management.
"""

from datetime import datetime, date, time
from enum import Enum
from typing import Optional, List
from uuid import UUID

from sqlalchemy import (
    String, Text, Integer, Boolean, Date, Time, DateTime,
    ForeignKey, UniqueConstraint, Index, JSON
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import TenantBaseModel


# ============================================
# Enums
# ============================================

class MeetingStatus(str, Enum):
    """Meeting status."""
    SCHEDULED = "scheduled"
    LIVE = "live"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    RESCHEDULED = "rescheduled"


class MeetingPlatform(str, Enum):
    """Meeting platform options."""
    ZOOM = "zoom"
    GOOGLE_MEET = "google_meet"
    MICROSOFT_TEAMS = "microsoft_teams"
    WEBEX = "webex"
    JITSI = "jitsi"
    CUSTOM = "custom"


class MeetingType(str, Enum):
    """Types of meetings."""
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
    """Participant roles in meeting."""
    HOST = "host"
    CO_HOST = "co_host"
    PRESENTER = "presenter"
    ATTENDEE = "attendee"


class AttendanceStatus(str, Enum):
    """Meeting attendance status."""
    JOINED = "joined"
    LEFT = "left"
    ABSENT = "absent"
    LATE = "late"


# ============================================
# Online Meeting
# ============================================

class OnlineMeeting(TenantBaseModel):
    """
    Online meeting/virtual classroom.
    
    Supports multiple platforms and meeting types.
    """
    __tablename__ = "online_meetings"
    __table_args__ = (
        Index("ix_meeting_tenant_status", "tenant_id", "status"),
        Index("ix_meeting_date", "tenant_id", "meeting_date"),
        Index("ix_meeting_host", "tenant_id", "host_id"),
        {"extend_existing": True},
    )
    
    # Meeting identification
    meeting_code: Mapped[str] = mapped_column(String(50), unique=True)
    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Type and status
    meeting_type: Mapped[MeetingType] = mapped_column(
        SQLEnum(MeetingType, name="meeting_type_enum"),
        default=MeetingType.LECTURE
    )
    status: Mapped[MeetingStatus] = mapped_column(
        SQLEnum(MeetingStatus, name="meeting_status_enum"),
        default=MeetingStatus.SCHEDULED
    )
    
    # Platform
    platform: Mapped[MeetingPlatform] = mapped_column(
        SQLEnum(MeetingPlatform, name="meeting_platform_enum"),
        default=MeetingPlatform.GOOGLE_MEET
    )
    
    # Meeting links
    meeting_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    meeting_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Platform meeting ID
    passcode: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    dial_in_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Host
    host_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    co_host_ids: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    
    # Schedule
    meeting_date: Mapped[date] = mapped_column(Date)
    start_time: Mapped[time] = mapped_column(Time(timezone=True))
    end_time: Mapped[time] = mapped_column(Time(timezone=True))
    duration_minutes: Mapped[int] = mapped_column(Integer, default=60)
    timezone: Mapped[str] = mapped_column(String(50), default="Asia/Kolkata")
    
    # Recurrence
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    recurrence_pattern: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # daily, weekly, monthly
    recurrence_end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    parent_meeting_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("online_meetings.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Academic context
    class_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("classes.id", ondelete="SET NULL"),
        nullable=True,
    )
    section_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("sections.id", ondelete="SET NULL"),
        nullable=True,
    )
    subject_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Settings
    allow_recording: Mapped[bool] = mapped_column(Boolean, default=True)
    auto_recording: Mapped[bool] = mapped_column(Boolean, default=False)
    mute_on_entry: Mapped[bool] = mapped_column(Boolean, default=True)
    require_registration: Mapped[bool] = mapped_column(Boolean, default=False)
    max_participants: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    enable_waiting_room: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Actual timing
    actual_start_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    actual_end_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Recording
    recording_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    recording_duration_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Statistics
    max_concurrent_participants: Mapped[int] = mapped_column(Integer, default=0)
    total_participants: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    participants: Mapped[List["MeetingParticipant"]] = relationship(
        "MeetingParticipant",
        back_populates="meeting",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    attendance_records: Mapped[List["MeetingAttendance"]] = relationship(
        "MeetingAttendance",
        back_populates="meeting",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


# ============================================
# Meeting Participant
# ============================================

class MeetingParticipant(TenantBaseModel):
    """
    Meeting participant (invited users).
    """
    __tablename__ = "meeting_participants"
    __table_args__ = (
        UniqueConstraint(
            "meeting_id", "user_id",
            name="uq_meeting_participant"
        ),
        Index("ix_participant_meeting", "meeting_id"),
        Index("ix_participant_user", "user_id"),
        {"extend_existing": True},
    )
    
    meeting_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("online_meetings.id", ondelete="CASCADE"),
    )
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    
    # Role
    role: Mapped[ParticipantRole] = mapped_column(
        SQLEnum(ParticipantRole, name="participant_role_enum"),
        default=ParticipantRole.ATTENDEE
    )
    
    # Invitation
    invited_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    invitation_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # RSVP
    rsvp_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # accepted, declined, tentative
    rsvp_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Relationship
    meeting: Mapped["OnlineMeeting"] = relationship(
        "OnlineMeeting", back_populates="participants"
    )


# ============================================
# Meeting Attendance
# ============================================

class MeetingAttendance(TenantBaseModel):
    """
    Meeting attendance tracking.
    
    Records join/leave events for participants.
    """
    __tablename__ = "meeting_attendance"
    __table_args__ = (
        Index("ix_attendance_meeting", "meeting_id"),
        Index("ix_attendance_user", "user_id"),
        {"extend_existing": True},
    )
    
    meeting_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("online_meetings.id", ondelete="CASCADE"),
    )
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    
    # Status
    status: Mapped[AttendanceStatus] = mapped_column(
        SQLEnum(AttendanceStatus, name="meeting_attendance_status_enum"),
        default=AttendanceStatus.ABSENT
    )
    
    # Timing
    join_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    leave_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    duration_minutes: Mapped[int] = mapped_column(Integer, default=0)
    
    # Multiple joins tracking
    join_count: Mapped[int] = mapped_column(Integer, default=0)
    join_leave_log: Mapped[Optional[List[dict]]] = mapped_column(JSON, nullable=True)
    
    # Device info
    device_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Relationship
    meeting: Mapped["OnlineMeeting"] = relationship(
        "OnlineMeeting", back_populates="attendance_records"
    )


# ============================================
# Meeting Resource
# ============================================

class MeetingResource(TenantBaseModel):
    """
    Resources/materials shared in a meeting.
    """
    __tablename__ = "meeting_resources"
    __table_args__ = (
        Index("ix_resource_meeting", "meeting_id"),
        {"extend_existing": True},
    )
    
    meeting_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("online_meetings.id", ondelete="CASCADE"),
    )
    
    # Resource info
    name: Mapped[str] = mapped_column(String(200))
    resource_type: Mapped[str] = mapped_column(String(50))  # document, video, link, etc.
    file_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    external_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Shared by
    shared_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    shared_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    
    # Access
    is_downloadable: Mapped[bool] = mapped_column(Boolean, default=True)
    download_count: Mapped[int] = mapped_column(Integer, default=0)


# ============================================
# Platform Integration Config
# ============================================

class MeetingPlatformConfig(TenantBaseModel):
    """
    Platform-specific configuration for meetings.
    """
    __tablename__ = "meeting_platform_configs"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "platform",
            name="uq_platform_config"
        ),
        {"extend_existing": True},
    )
    
    platform: Mapped[MeetingPlatform] = mapped_column(
        SQLEnum(MeetingPlatform, name="meeting_platform_enum"),
    )
    
    # API credentials (encrypted in practice)
    api_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    api_secret: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    account_id: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # OAuth tokens
    access_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    refresh_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    token_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Webhook URL for callbacks
    webhook_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    webhook_secret: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # Default settings
    default_duration: Mapped[int] = mapped_column(Integer, default=60)
    default_settings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
