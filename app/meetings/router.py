"""
CUSTOS Online Meetings Router

API endpoints for virtual classroom and meeting management.
"""

from datetime import date
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_tenant_id
from app.auth.dependencies import get_current_user, require_roles
from app.auth.schemas import UserResponse

from app.meetings.service import MeetingsService
from app.meetings.schemas import (
    MeetingCreate, MeetingUpdate, MeetingResponse, MeetingListResponse,
    MeetingJoinInfo, ParticipantAdd, ParticipantResponse,
    AttendanceResponse, MeetingAttendanceReport, MeetingType, MeetingPlatform,
)


router = APIRouter(tags=["Online Meetings"])


def get_meetings_service(
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
) -> MeetingsService:
    """Get meetings service instance."""
    return MeetingsService(db, tenant_id)


# ============================================
# Meeting CRUD Endpoints
# ============================================

@router.get("/types", response_model=List[str])
async def get_meeting_types():
    """Get list of meeting types."""
    return [t.value for t in MeetingType]


@router.get("/platforms", response_model=List[str])
async def get_platforms():
    """Get list of meeting platforms."""
    return [p.value for p in MeetingPlatform]


@router.post("/", response_model=MeetingResponse, status_code=status.HTTP_201_CREATED)
async def create_meeting(
    data: MeetingCreate,
    service: MeetingsService = Depends(get_meetings_service),
    current_user: UserResponse = Depends(require_roles(["admin", "principal", "sub_admin", "teacher"])),
):
    """Create a new meeting (faculty/admin only)."""
    meeting = await service.create_meeting(data, current_user.id)
    return MeetingResponse.model_validate(meeting)


@router.get("/", response_model=MeetingListResponse)
async def list_meetings(
    meeting_status: Optional[str] = Query(None, alias="status"),
    meeting_date: Optional[date] = Query(None),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: MeetingsService = Depends(get_meetings_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """List meetings. Users see their own, staff sees all."""
    is_staff = current_user.role in ["admin", "principal", "sub_admin"]
    participant_id = None if is_staff else current_user.id
    
    meetings, total = await service.list_meetings(
        participant_id=participant_id,
        status=meeting_status,
        meeting_date=meeting_date,
        from_date=from_date,
        to_date=to_date,
        page=page,
        page_size=page_size,
    )
    
    return MeetingListResponse(
        items=[MeetingResponse.model_validate(m) for m in meetings],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.get("/upcoming", response_model=List[MeetingResponse])
async def get_upcoming_meetings(
    limit: int = Query(10, ge=1, le=50),
    service: MeetingsService = Depends(get_meetings_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """Get upcoming meetings for current user."""
    meetings = await service.get_upcoming_meetings(current_user.id, limit)
    return [MeetingResponse.model_validate(m) for m in meetings]


@router.get("/live", response_model=List[MeetingResponse])
async def get_live_meetings(
    service: MeetingsService = Depends(get_meetings_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """Get currently live meetings for current user."""
    meetings = await service.get_live_meetings(current_user.id)
    return [MeetingResponse.model_validate(m) for m in meetings]


@router.get("/{meeting_id}", response_model=MeetingResponse)
async def get_meeting(
    meeting_id: UUID,
    service: MeetingsService = Depends(get_meetings_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """Get meeting details."""
    meeting = await service.get_meeting(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return MeetingResponse.model_validate(meeting)


@router.put("/{meeting_id}", response_model=MeetingResponse)
async def update_meeting(
    meeting_id: UUID,
    data: MeetingUpdate,
    service: MeetingsService = Depends(get_meetings_service),
    current_user: UserResponse = Depends(require_roles(["admin", "principal", "sub_admin", "teacher"])),
):
    """Update a meeting."""
    meeting = await service.update_meeting(meeting_id, data, current_user.id)
    return MeetingResponse.model_validate(meeting)


@router.post("/{meeting_id}/start", response_model=MeetingResponse)
async def start_meeting(
    meeting_id: UUID,
    service: MeetingsService = Depends(get_meetings_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """Start a meeting (host only)."""
    meeting = await service.start_meeting(meeting_id, current_user.id)
    return MeetingResponse.model_validate(meeting)


@router.post("/{meeting_id}/end", response_model=MeetingResponse)
async def end_meeting(
    meeting_id: UUID,
    service: MeetingsService = Depends(get_meetings_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """End a meeting (host only)."""
    meeting = await service.end_meeting(meeting_id, current_user.id)
    return MeetingResponse.model_validate(meeting)


@router.post("/{meeting_id}/cancel", response_model=MeetingResponse)
async def cancel_meeting(
    meeting_id: UUID,
    service: MeetingsService = Depends(get_meetings_service),
    current_user: UserResponse = Depends(require_roles(["admin", "principal", "sub_admin", "teacher"])),
):
    """Cancel a meeting."""
    meeting = await service.cancel_meeting(meeting_id, current_user.id)
    return MeetingResponse.model_validate(meeting)


@router.get("/{meeting_id}/join", response_model=MeetingJoinInfo)
async def get_join_info(
    meeting_id: UUID,
    service: MeetingsService = Depends(get_meetings_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """Get meeting join information."""
    meeting = await service.get_meeting(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    if not meeting.meeting_url:
        raise HTTPException(status_code=400, detail="Meeting URL not available")
    
    return MeetingJoinInfo(
        meeting_url=meeting.meeting_url,
        passcode=meeting.passcode,
        dial_in_number=meeting.dial_in_number,
        meeting_id=meeting.meeting_id,
        platform=meeting.platform,
    )


# ============================================
# Participant Endpoints
# ============================================

@router.post("/{meeting_id}/participants", response_model=List[ParticipantResponse])
async def add_participants(
    meeting_id: UUID,
    data: ParticipantAdd,
    service: MeetingsService = Depends(get_meetings_service),
    current_user: UserResponse = Depends(require_roles(["admin", "principal", "sub_admin", "teacher"])),
):
    """Add participants to a meeting."""
    participants = await service.add_participants(meeting_id, data)
    return [ParticipantResponse.model_validate(p) for p in participants]


@router.get("/{meeting_id}/participants", response_model=List[ParticipantResponse])
async def get_participants(
    meeting_id: UUID,
    service: MeetingsService = Depends(get_meetings_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """Get meeting participants."""
    participants = await service.get_meeting_participants(meeting_id)
    return [ParticipantResponse.model_validate(p) for p in participants]


# ============================================
# Attendance Endpoints
# ============================================

@router.post("/{meeting_id}/attendance/join", response_model=AttendanceResponse)
async def join_meeting(
    meeting_id: UUID,
    device_type: Optional[str] = Query(None),
    service: MeetingsService = Depends(get_meetings_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """Record user joining a meeting."""
    attendance = await service.mark_attendance(
        meeting_id, current_user.id, device_type
    )
    return AttendanceResponse.model_validate(attendance)


@router.post("/{meeting_id}/attendance/leave", response_model=AttendanceResponse)
async def leave_meeting(
    meeting_id: UUID,
    service: MeetingsService = Depends(get_meetings_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """Record user leaving a meeting."""
    attendance = await service.mark_leave(meeting_id, current_user.id)
    return AttendanceResponse.model_validate(attendance)


@router.get("/{meeting_id}/attendance", response_model=List[AttendanceResponse])
async def get_meeting_attendance(
    meeting_id: UUID,
    service: MeetingsService = Depends(get_meetings_service),
    current_user: UserResponse = Depends(require_roles(["admin", "principal", "sub_admin", "teacher"])),
):
    """Get meeting attendance records."""
    attendance = await service.get_meeting_attendance(meeting_id)
    return [AttendanceResponse.model_validate(a) for a in attendance]
