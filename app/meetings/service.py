"""
CUSTOS Online Meetings Service

Business logic for virtual classroom and meeting management.
"""

import logging
from datetime import datetime, date, timedelta
from typing import Optional, List, Tuple
from uuid import UUID, uuid4

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.meetings.models import (
    OnlineMeeting, MeetingParticipant, MeetingAttendance, MeetingResource,
    MeetingPlatformConfig, MeetingStatus, MeetingPlatform, ParticipantRole,
    AttendanceStatus
)
from app.meetings.schemas import (
    MeetingCreate, MeetingUpdate, ParticipantAdd, ResourceCreate
)
from app.core.exceptions import NotFoundError, ValidationError

logger = logging.getLogger(__name__)


class MeetingsService:
    """Service for online meetings management."""
    
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
    
    # ============================================
    # Meeting CRUD
    # ============================================
    
    async def create_meeting(
        self,
        data: MeetingCreate,
        host_id: UUID
    ) -> OnlineMeeting:
        """Create a new meeting."""
        meeting = OnlineMeeting(
            tenant_id=self.tenant_id,
            meeting_code=self._generate_meeting_code(),
            title=data.title,
            description=data.description,
            meeting_type=data.meeting_type,
            status=MeetingStatus.SCHEDULED,
            platform=data.platform,
            meeting_url=data.meeting_url,
            passcode=data.passcode,
            host_id=host_id,
            meeting_date=data.meeting_date,
            start_time=data.start_time,
            end_time=data.end_time,
            duration_minutes=data.duration_minutes,
            timezone=data.timezone,
            is_recurring=data.is_recurring,
            recurrence_pattern=data.recurrence_pattern,
            recurrence_end_date=data.recurrence_end_date,
            class_id=data.class_id,
            section_id=data.section_id,
            subject_id=data.subject_id,
            allow_recording=data.allow_recording,
            auto_recording=data.auto_recording,
            mute_on_entry=data.mute_on_entry,
            require_registration=data.require_registration,
            max_participants=data.max_participants,
            enable_waiting_room=data.enable_waiting_room,
        )
        
        self.db.add(meeting)
        await self.db.flush()
        
        # Add host as participant
        host_participant = MeetingParticipant(
            tenant_id=self.tenant_id,
            meeting_id=meeting.id,
            user_id=host_id,
            role=ParticipantRole.HOST,
        )
        self.db.add(host_participant)
        
        # Add invited participants
        if data.participant_ids:
            for user_id in data.participant_ids:
                if user_id != host_id:
                    participant = MeetingParticipant(
                        tenant_id=self.tenant_id,
                        meeting_id=meeting.id,
                        user_id=user_id,
                        role=ParticipantRole.ATTENDEE,
                    )
                    self.db.add(participant)
        
        await self.db.commit()
        await self.db.refresh(meeting)
        
        logger.info(f"Created meeting {meeting.meeting_code} for tenant {self.tenant_id}")
        return meeting
    
    async def get_meeting(self, meeting_id: UUID) -> Optional[OnlineMeeting]:
        """Get meeting by ID."""
        result = await self.db.execute(
            select(OnlineMeeting)
            .options(
                selectinload(OnlineMeeting.participants),
                selectinload(OnlineMeeting.attendance_records)
            )
            .where(
                OnlineMeeting.id == meeting_id,
                OnlineMeeting.tenant_id == self.tenant_id,
                OnlineMeeting.is_deleted == False
            )
        )
        return result.scalar_one_or_none()
    
    async def list_meetings(
        self,
        host_id: Optional[UUID] = None,
        participant_id: Optional[UUID] = None,
        status: Optional[str] = None,
        meeting_date: Optional[date] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[OnlineMeeting], int]:
        """List meetings with filters."""
        query = select(OnlineMeeting).where(
            OnlineMeeting.tenant_id == self.tenant_id,
            OnlineMeeting.is_deleted == False
        )
        
        if host_id:
            query = query.where(OnlineMeeting.host_id == host_id)
        if status:
            query = query.where(OnlineMeeting.status == status)
        if meeting_date:
            query = query.where(OnlineMeeting.meeting_date == meeting_date)
        if from_date:
            query = query.where(OnlineMeeting.meeting_date >= from_date)
        if to_date:
            query = query.where(OnlineMeeting.meeting_date <= to_date)
        
        # Filter by participant
        if participant_id:
            subquery = select(MeetingParticipant.meeting_id).where(
                MeetingParticipant.user_id == participant_id
            )
            query = query.where(
                or_(
                    OnlineMeeting.host_id == participant_id,
                    OnlineMeeting.id.in_(subquery)
                )
            )
        
        # Count
        count_result = await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar()
        
        # Paginate
        query = query.order_by(
            OnlineMeeting.meeting_date.desc(),
            OnlineMeeting.start_time.desc()
        )
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.db.execute(query)
        return result.scalars().all(), total
    
    async def get_upcoming_meetings(
        self,
        user_id: UUID,
        limit: int = 10
    ) -> List[OnlineMeeting]:
        """Get upcoming meetings for a user."""
        today = date.today()
        
        subquery = select(MeetingParticipant.meeting_id).where(
            MeetingParticipant.user_id == user_id
        )
        
        result = await self.db.execute(
            select(OnlineMeeting)
            .where(
                OnlineMeeting.tenant_id == self.tenant_id,
                OnlineMeeting.is_deleted == False,
                OnlineMeeting.meeting_date >= today,
                OnlineMeeting.status.in_([
                    MeetingStatus.SCHEDULED,
                    MeetingStatus.LIVE
                ]),
                or_(
                    OnlineMeeting.host_id == user_id,
                    OnlineMeeting.id.in_(subquery)
                )
            )
            .order_by(OnlineMeeting.meeting_date, OnlineMeeting.start_time)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_live_meetings(self, user_id: UUID) -> List[OnlineMeeting]:
        """Get currently live meetings for a user."""
        subquery = select(MeetingParticipant.meeting_id).where(
            MeetingParticipant.user_id == user_id
        )
        
        result = await self.db.execute(
            select(OnlineMeeting)
            .where(
                OnlineMeeting.tenant_id == self.tenant_id,
                OnlineMeeting.is_deleted == False,
                OnlineMeeting.status == MeetingStatus.LIVE,
                or_(
                    OnlineMeeting.host_id == user_id,
                    OnlineMeeting.id.in_(subquery)
                )
            )
        )
        return result.scalars().all()
    
    async def update_meeting(
        self,
        meeting_id: UUID,
        data: MeetingUpdate,
        updated_by: UUID
    ) -> OnlineMeeting:
        """Update a meeting."""
        meeting = await self.get_meeting(meeting_id)
        if not meeting:
            raise NotFoundError("Meeting not found")
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(meeting, key, value)
        
        await self.db.commit()
        await self.db.refresh(meeting)
        return meeting
    
    async def start_meeting(self, meeting_id: UUID, host_id: UUID) -> OnlineMeeting:
        """Start a meeting (set to LIVE)."""
        meeting = await self.get_meeting(meeting_id)
        if not meeting:
            raise NotFoundError("Meeting not found")
        
        if meeting.host_id != host_id:
            raise ValidationError("Only host can start the meeting")
        
        meeting.status = MeetingStatus.LIVE
        meeting.actual_start_time = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(meeting)
        return meeting
    
    async def end_meeting(self, meeting_id: UUID, host_id: UUID) -> OnlineMeeting:
        """End a meeting."""
        meeting = await self.get_meeting(meeting_id)
        if not meeting:
            raise NotFoundError("Meeting not found")
        
        meeting.status = MeetingStatus.COMPLETED
        meeting.actual_end_time = datetime.utcnow()
        
        # Calculate actual duration
        if meeting.actual_start_time:
            duration = (meeting.actual_end_time - meeting.actual_start_time).seconds // 60
            meeting.recording_duration_minutes = duration
        
        await self.db.commit()
        await self.db.refresh(meeting)
        return meeting
    
    async def cancel_meeting(
        self,
        meeting_id: UUID,
        cancelled_by: UUID
    ) -> OnlineMeeting:
        """Cancel a meeting."""
        meeting = await self.get_meeting(meeting_id)
        if not meeting:
            raise NotFoundError("Meeting not found")
        
        meeting.status = MeetingStatus.CANCELLED
        
        await self.db.commit()
        await self.db.refresh(meeting)
        return meeting
    
    # ============================================
    # Participants
    # ============================================
    
    async def add_participants(
        self,
        meeting_id: UUID,
        data: ParticipantAdd
    ) -> List[MeetingParticipant]:
        """Add participants to a meeting."""
        meeting = await self.get_meeting(meeting_id)
        if not meeting:
            raise NotFoundError("Meeting not found")
        
        participants = []
        for user_id in data.user_ids:
            # Check if already a participant
            existing = await self.db.execute(
                select(MeetingParticipant).where(
                    MeetingParticipant.meeting_id == meeting_id,
                    MeetingParticipant.user_id == user_id,
                )
            )
            if existing.scalar_one_or_none():
                continue
            
            participant = MeetingParticipant(
                tenant_id=self.tenant_id,
                meeting_id=meeting_id,
                user_id=user_id,
                role=data.role,
                invitation_sent=data.send_invitation,
            )
            self.db.add(participant)
            participants.append(participant)
        
        await self.db.commit()
        
        for p in participants:
            await self.db.refresh(p)
        
        return participants
    
    async def get_meeting_participants(
        self,
        meeting_id: UUID
    ) -> List[MeetingParticipant]:
        """Get all participants of a meeting."""
        result = await self.db.execute(
            select(MeetingParticipant).where(
                MeetingParticipant.meeting_id == meeting_id,
                MeetingParticipant.tenant_id == self.tenant_id,
            )
        )
        return result.scalars().all()
    
    # ============================================
    # Attendance
    # ============================================
    
    async def mark_attendance(
        self,
        meeting_id: UUID,
        user_id: UUID,
        device_type: Optional[str] = None
    ) -> MeetingAttendance:
        """Mark user as joined the meeting."""
        meeting = await self.get_meeting(meeting_id)
        if not meeting:
            raise NotFoundError("Meeting not found")
        
        # Check if attendance record exists
        result = await self.db.execute(
            select(MeetingAttendance).where(
                MeetingAttendance.meeting_id == meeting_id,
                MeetingAttendance.user_id == user_id,
                MeetingAttendance.tenant_id == self.tenant_id,
            )
        )
        attendance = result.scalar_one_or_none()
        
        now = datetime.utcnow()
        
        if attendance:
            # Update existing record
            attendance.join_count += 1
            if not attendance.join_leave_log:
                attendance.join_leave_log = []
            attendance.join_leave_log.append({
                "action": "join",
                "time": now.isoformat()
            })
        else:
            # Create new record
            attendance = MeetingAttendance(
                tenant_id=self.tenant_id,
                meeting_id=meeting_id,
                user_id=user_id,
                status=AttendanceStatus.JOINED,
                join_time=now,
                join_count=1,
                device_type=device_type,
                join_leave_log=[{"action": "join", "time": now.isoformat()}]
            )
            self.db.add(attendance)
            
            # Update meeting participant count
            meeting.total_participants += 1
        
        await self.db.commit()
        await self.db.refresh(attendance)
        return attendance
    
    async def mark_leave(
        self,
        meeting_id: UUID,
        user_id: UUID
    ) -> MeetingAttendance:
        """Mark user as left the meeting."""
        result = await self.db.execute(
            select(MeetingAttendance).where(
                MeetingAttendance.meeting_id == meeting_id,
                MeetingAttendance.user_id == user_id,
                MeetingAttendance.tenant_id == self.tenant_id,
            )
        )
        attendance = result.scalar_one_or_none()
        
        if not attendance:
            raise NotFoundError("Attendance record not found")
        
        now = datetime.utcnow()
        attendance.leave_time = now
        attendance.status = AttendanceStatus.LEFT
        
        if attendance.join_time:
            attendance.duration_minutes = int(
                (now - attendance.join_time).seconds / 60
            )
        
        if not attendance.join_leave_log:
            attendance.join_leave_log = []
        attendance.join_leave_log.append({
            "action": "leave",
            "time": now.isoformat()
        })
        
        await self.db.commit()
        await self.db.refresh(attendance)
        return attendance
    
    async def get_meeting_attendance(
        self,
        meeting_id: UUID
    ) -> List[MeetingAttendance]:
        """Get attendance records for a meeting."""
        result = await self.db.execute(
            select(MeetingAttendance).where(
                MeetingAttendance.meeting_id == meeting_id,
                MeetingAttendance.tenant_id == self.tenant_id,
            )
        )
        return result.scalars().all()
    
    # ============================================
    # Helpers
    # ============================================
    
    def _generate_meeting_code(self) -> str:
        """Generate unique meeting code."""
        timestamp = datetime.utcnow().strftime("%Y%m%d")
        random_part = str(uuid4())[:8].upper()
        return f"MTG-{timestamp}-{random_part}"
