"""
CUSTOS Hostel Management Router

API endpoints for hostel management.
"""

from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth.dependencies import CurrentUser, require_permission, require_role
from app.users.rbac import Permission, SystemRole
from app.hostel.service import HostelService
from app.hostel.models import HostelGender
from app.hostel.schemas import (
    # Hostel
    HostelCreate, HostelUpdate, HostelResponse, HostelListItem,
    # Room
    RoomCreate, RoomUpdate, RoomResponse, RoomListItem,
    # Bed
    BedCreate, BedResponse, BedUpdate,
    # Warden
    WardenCreate, WardenUpdate, WardenAssign, WardenResponse, WardenListItem,
    # Student Assignment
    StudentHostelAssignRequest, StudentHostelUnassignRequest,
    StudentHostelAssignmentResponse, StudentHostelDetail,
    StudentHostelCheckIn, StudentHostelCheckOut,
    # Occupancy
    HostelOccupancy, AvailableBed,
    # Fee
    HostelFeeLinkCreate, HostelFeeLinkResponse,
)


router = APIRouter(tags=["Hostel"])


# ============================================
# Hostel Management
# ============================================

@router.post("/hostels", response_model=HostelResponse, status_code=201)
async def create_hostel(
    data: HostelCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.HOSTEL_MANAGE)),
):
    """
    Create a new hostel.
    
    Requires HOSTEL_MANAGE permission.
    """
    service = HostelService(db, user.tenant_id)
    hostel = await service.create_hostel(data)
    return HostelResponse.model_validate(hostel)


@router.get("/hostels", response_model=List[HostelListItem])
async def list_hostels(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    active_only: bool = True,
    gender: Optional[HostelGender] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=50),
    _=Depends(require_permission(Permission.HOSTEL_VIEW)),
):
    """List all hostels."""
    service = HostelService(db, user.tenant_id)
    hostels, _ = await service.list_hostels(active_only, gender, page, size)
    
    result = []
    for h in hostels:
        # Calculate occupancy
        rooms_count = len(h.rooms) if h.rooms else 0
        total_beds = sum(len(r.beds) for r in h.rooms) if h.rooms else 0
        occupied = sum(1 for r in h.rooms for b in r.beds if b.is_occupied) if h.rooms else 0
        
        result.append(HostelListItem(
            id=h.id,
            name=h.name,
            code=h.code,
            gender=h.gender,
            total_capacity=h.total_capacity,
            is_active=h.is_active,
            rooms_count=rooms_count,
            occupied_beds=occupied,
        ))
    
    return result


@router.get("/hostels/{hostel_id}", response_model=HostelResponse)
async def get_hostel(
    hostel_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.HOSTEL_VIEW)),
):
    """Get a hostel by ID."""
    service = HostelService(db, user.tenant_id)
    hostel = await service.get_hostel(hostel_id)
    return HostelResponse.model_validate(hostel)


@router.patch("/hostels/{hostel_id}", response_model=HostelResponse)
async def update_hostel(
    hostel_id: UUID,
    data: HostelUpdate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.HOSTEL_MANAGE)),
):
    """Update a hostel."""
    service = HostelService(db, user.tenant_id)
    hostel = await service.update_hostel(hostel_id, data)
    return HostelResponse.model_validate(hostel)


@router.delete("/hostels/{hostel_id}")
async def delete_hostel(
    hostel_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.HOSTEL_MANAGE)),
):
    """Delete a hostel (soft delete)."""
    service = HostelService(db, user.tenant_id)
    await service.delete_hostel(hostel_id)
    return {"success": True, "message": "Hostel deleted"}


# ============================================
# Room Management
# ============================================

@router.post("/rooms", response_model=RoomResponse, status_code=201)
async def create_room(
    data: RoomCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.HOSTEL_MANAGE)),
):
    """
    Create a new room in a hostel.
    
    Requires HOSTEL_MANAGE permission.
    """
    service = HostelService(db, user.tenant_id)
    room = await service.create_room(data)
    return RoomResponse.model_validate(room)


@router.get("/hostels/{hostel_id}/rooms", response_model=List[RoomListItem])
async def list_rooms(
    hostel_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    active_only: bool = True,
    floor: Optional[int] = None,
    _=Depends(require_permission(Permission.HOSTEL_VIEW)),
):
    """List all rooms in a hostel."""
    service = HostelService(db, user.tenant_id)
    rooms = await service.list_rooms(hostel_id, active_only, floor)
    
    result = []
    for r in rooms:
        beds_count = len(r.beds) if r.beds else 0
        occupied = sum(1 for b in r.beds if b.is_occupied) if r.beds else 0
        
        result.append(RoomListItem(
            id=r.id,
            hostel_id=r.hostel_id,
            room_number=r.room_number,
            floor=r.floor,
            capacity=r.capacity,
            is_active=r.is_active,
            beds_count=beds_count,
            occupied_beds=occupied,
            available_beds=beds_count - occupied,
        ))
    
    return result


@router.get("/rooms/{room_id}", response_model=RoomResponse)
async def get_room(
    room_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.HOSTEL_VIEW)),
):
    """Get a room by ID with beds."""
    service = HostelService(db, user.tenant_id)
    room = await service.get_room(room_id)
    return RoomResponse.model_validate(room)


@router.patch("/rooms/{room_id}", response_model=RoomResponse)
async def update_room(
    room_id: UUID,
    data: RoomUpdate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.HOSTEL_MANAGE)),
):
    """Update a room."""
    service = HostelService(db, user.tenant_id)
    room = await service.update_room(room_id, data)
    return RoomResponse.model_validate(room)


@router.delete("/rooms/{room_id}")
async def delete_room(
    room_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.HOSTEL_MANAGE)),
):
    """Delete a room (soft delete)."""
    service = HostelService(db, user.tenant_id)
    await service.delete_room(room_id)
    return {"success": True, "message": "Room deleted"}


# ============================================
# Bed Management
# ============================================

@router.post("/rooms/{room_id}/beds", response_model=List[BedResponse], status_code=201)
async def create_beds(
    room_id: UUID,
    beds: List[BedCreate],
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.HOSTEL_MANAGE)),
):
    """
    Create multiple beds in a room.
    
    Pass an array of beds.
    """
    service = HostelService(db, user.tenant_id)
    created_beds = await service.create_beds(room_id, beds)
    return [BedResponse.model_validate(b) for b in created_beds]


@router.patch("/beds/{bed_id}", response_model=BedResponse)
async def update_bed(
    bed_id: UUID,
    data: BedUpdate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.HOSTEL_MANAGE)),
):
    """Update a bed."""
    service = HostelService(db, user.tenant_id)
    bed = await service.update_bed(bed_id, data)
    return BedResponse.model_validate(bed)


# ============================================
# Warden Management
# ============================================

@router.post("/wardens", response_model=WardenResponse, status_code=201)
async def create_warden(
    data: WardenCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.HOSTEL_MANAGE)),
):
    """
    Create a new warden.
    
    Requires HOSTEL_MANAGE permission.
    """
    service = HostelService(db, user.tenant_id)
    warden = await service.create_warden(data)
    return WardenResponse.model_validate(warden)


@router.get("/wardens", response_model=List[WardenListItem])
async def list_wardens(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    active_only: bool = True,
    hostel_id: Optional[UUID] = None,
    _=Depends(require_permission(Permission.HOSTEL_VIEW)),
):
    """List all wardens."""
    service = HostelService(db, user.tenant_id)
    wardens = await service.list_wardens(active_only, hostel_id)
    
    return [
        WardenListItem(
            id=w.id,
            name=w.name,
            phone=w.phone,
            is_chief_warden=w.is_chief_warden,
            assigned_hostel_id=w.assigned_hostel_id,
            hostel_name=w.hostel.name if w.hostel else None,
            is_active=w.is_active,
        )
        for w in wardens
    ]


@router.get("/wardens/{warden_id}", response_model=WardenResponse)
async def get_warden(
    warden_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.HOSTEL_VIEW)),
):
    """Get a warden by ID."""
    service = HostelService(db, user.tenant_id)
    warden = await service.get_warden(warden_id)
    
    return WardenResponse(
        id=warden.id,
        tenant_id=warden.tenant_id,
        name=warden.name,
        phone=warden.phone,
        alternate_phone=warden.alternate_phone,
        email=warden.email,
        address=warden.address,
        user_id=warden.user_id,
        assigned_hostel_id=warden.assigned_hostel_id,
        is_chief_warden=warden.is_chief_warden,
        assigned_from=warden.assigned_from,
        assigned_to=warden.assigned_to,
        is_active=warden.is_active,
        notes=warden.notes,
        created_at=warden.created_at,
        hostel_name=warden.hostel.name if warden.hostel else None,
    )


@router.patch("/wardens/{warden_id}", response_model=WardenResponse)
async def update_warden(
    warden_id: UUID,
    data: WardenUpdate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.HOSTEL_MANAGE)),
):
    """Update a warden."""
    service = HostelService(db, user.tenant_id)
    warden = await service.update_warden(warden_id, data)
    return WardenResponse.model_validate(warden)


@router.post("/assign-warden", response_model=WardenResponse)
async def assign_warden_to_hostel(
    data: WardenAssign,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.HOSTEL_MANAGE)),
):
    """Assign a warden to a hostel."""
    service = HostelService(db, user.tenant_id)
    warden = await service.assign_warden(data)
    return WardenResponse.model_validate(warden)


@router.post("/wardens/{warden_id}/unassign")
async def unassign_warden(
    warden_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.HOSTEL_MANAGE)),
):
    """Unassign a warden from their hostel."""
    service = HostelService(db, user.tenant_id)
    await service.unassign_warden(warden_id)
    return {"success": True, "message": "Warden unassigned"}


# ============================================
# Student Assignment
# ============================================

@router.post("/students/assign", response_model=StudentHostelAssignmentResponse, status_code=201)
async def assign_student_to_hostel(
    data: StudentHostelAssignRequest,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.HOSTEL_ASSIGN)),
):
    """
    Assign a student to a hostel bed.
    
    Validates:
    - Hostel, room, bed exist and are linked
    - Bed is not occupied
    - Student doesn't have active assignment
    """
    service = HostelService(db, user.tenant_id)
    assignment = await service.assign_student_to_bed(data)
    return StudentHostelAssignmentResponse.model_validate(assignment)


@router.post("/students/unassign")
async def unassign_student_from_hostel(
    data: StudentHostelUnassignRequest,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.HOSTEL_ASSIGN)),
):
    """Unassign a student from hostel."""
    service = HostelService(db, user.tenant_id)
    await service.unassign_student(data)
    return {"success": True, "message": "Student unassigned from hostel"}


@router.post("/students/check-in", response_model=StudentHostelAssignmentResponse)
async def check_in_student(
    data: StudentHostelCheckIn,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.HOSTEL_ASSIGN)),
):
    """Record student check-in."""
    service = HostelService(db, user.tenant_id)
    assignment = await service.check_in_student(data.student_id)
    return StudentHostelAssignmentResponse.model_validate(assignment)


@router.post("/students/check-out", response_model=StudentHostelAssignmentResponse)
async def check_out_student(
    data: StudentHostelCheckOut,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.HOSTEL_ASSIGN)),
):
    """Record student check-out (temporary)."""
    service = HostelService(db, user.tenant_id)
    assignment = await service.check_out_student(data.student_id)
    return StudentHostelAssignmentResponse.model_validate(assignment)


@router.get("/students/hostel/{hostel_id}", response_model=List[StudentHostelAssignmentResponse])
async def list_students_in_hostel(
    hostel_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    active_only: bool = True,
    _=Depends(require_permission(Permission.HOSTEL_VIEW)),
):
    """List all students in a hostel."""
    service = HostelService(db, user.tenant_id)
    assignments = await service.list_students_in_hostel(hostel_id, active_only)
    return [StudentHostelAssignmentResponse.model_validate(a) for a in assignments]


# ============================================
# Parent / Student View
# ============================================

@router.get("/my-details/{student_id}", response_model=StudentHostelDetail)
async def get_student_hostel_detail(
    student_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """
    Get hostel details for a student.
    
    Available to parents viewing their children.
    """
    # Verify access
    if SystemRole.PARENT.value not in user.roles and SystemRole.STUDENT.value not in user.roles:
        if SystemRole.TEACHER.value not in user.roles and SystemRole.PRINCIPAL.value not in user.roles:
            if SystemRole.SUB_ADMIN.value not in user.roles:
                raise HTTPException(status_code=403, detail="Access denied")
    
    service = HostelService(db, user.tenant_id)
    detail = await service.get_student_hostel_detail(student_id)
    
    if not detail:
        raise HTTPException(status_code=404, detail="No hostel assignment found")
    
    return detail


# ============================================
# Occupancy
# ============================================

@router.get("/occupancy", response_model=List[HostelOccupancy])
async def get_all_occupancy(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.HOSTEL_VIEW)),
):
    """Get occupancy status for all hostels."""
    service = HostelService(db, user.tenant_id)
    return await service.get_all_occupancy()


@router.get("/occupancy/{hostel_id}", response_model=HostelOccupancy)
async def get_hostel_occupancy(
    hostel_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.HOSTEL_VIEW)),
):
    """Get occupancy status for a specific hostel."""
    service = HostelService(db, user.tenant_id)
    return await service.get_hostel_occupancy(hostel_id)


@router.get("/available-beds", response_model=List[AvailableBed])
async def get_available_beds(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    hostel_id: Optional[UUID] = None,
    floor: Optional[int] = None,
    _=Depends(require_permission(Permission.HOSTEL_VIEW)),
):
    """Get list of available beds."""
    service = HostelService(db, user.tenant_id)
    return await service.get_available_beds(hostel_id, floor)


# ============================================
# Fee Links
# ============================================

@router.post("/fees", response_model=HostelFeeLinkResponse, status_code=201)
async def create_hostel_fee_link(
    data: HostelFeeLinkCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.HOSTEL_MANAGE)),
):
    """Create a hostel fee link for billing."""
    service = HostelService(db, user.tenant_id)
    fee_link = await service.create_hostel_fee_link(data)
    return HostelFeeLinkResponse.model_validate(fee_link)


@router.get("/fees/student/{student_id}", response_model=List[HostelFeeLinkResponse])
async def get_student_hostel_fees(
    student_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.HOSTEL_VIEW)),
):
    """Get hostel fees for a student."""
    service = HostelService(db, user.tenant_id)
    fees = await service.get_student_hostel_fees(student_id)
    return [HostelFeeLinkResponse.model_validate(f) for f in fees]
