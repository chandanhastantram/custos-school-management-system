"""
CUSTOS Hostel Management Service

Business logic for hostel operations.
"""

from datetime import datetime, date, timezone
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ResourceNotFoundError, ValidationError
from app.hostel.models import (
    Hostel, HostelRoom, Bed, Warden, StudentHostelAssignment,
    HostelFeeLink, HostelGender,
)
from app.hostel.schemas import (
    HostelCreate, HostelUpdate,
    RoomCreate, RoomUpdate,
    BedCreate, BedUpdate,
    WardenCreate, WardenUpdate, WardenAssign,
    StudentHostelAssignRequest, StudentHostelUnassignRequest,
    HostelOccupancy, RoomOccupancy, AvailableBed, StudentHostelDetail,
    HostelFeeLinkCreate,
)


class HostelService:
    """Service for hostel management operations."""
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
    
    # ============================================
    # Hostel Management
    # ============================================
    
    async def create_hostel(self, data: HostelCreate) -> Hostel:
        """Create a new hostel."""
        # Check for duplicate name
        existing = await self._get_hostel_by_name(data.name)
        if existing:
            raise ValidationError(f"Hostel with name '{data.name}' already exists")
        
        hostel = Hostel(
            tenant_id=self.tenant_id,
            name=data.name,
            code=data.code,
            description=data.description,
            gender=data.gender,
            address=data.address,
            building_name=data.building_name,
            total_capacity=data.total_capacity,
            floor_count=data.floor_count,
            contact_phone=data.contact_phone,
            contact_email=data.contact_email,
            notes=data.notes,
        )
        
        self.session.add(hostel)
        await self.session.commit()
        await self.session.refresh(hostel)
        return hostel
    
    async def update_hostel(self, hostel_id: UUID, data: HostelUpdate) -> Hostel:
        """Update a hostel."""
        hostel = await self.get_hostel(hostel_id)
        
        update_data = data.model_dump(exclude_unset=True)
        
        # Check for duplicate name if changing
        if "name" in update_data:
            existing = await self._get_hostel_by_name(update_data["name"])
            if existing and existing.id != hostel_id:
                raise ValidationError(f"Hostel with name '{update_data['name']}' already exists")
        
        for key, value in update_data.items():
            setattr(hostel, key, value)
        
        await self.session.commit()
        await self.session.refresh(hostel)
        return hostel
    
    async def get_hostel(self, hostel_id: UUID, include_rooms: bool = False) -> Hostel:
        """Get a hostel by ID."""
        query = select(Hostel).where(
            Hostel.tenant_id == self.tenant_id,
            Hostel.id == hostel_id,
            Hostel.deleted_at.is_(None),
        )
        
        if include_rooms:
            query = query.options(
                selectinload(Hostel.rooms).selectinload(HostelRoom.beds)
            )
        
        result = await self.session.execute(query)
        hostel = result.scalar_one_or_none()
        
        if not hostel:
            raise ResourceNotFoundError("Hostel", str(hostel_id))
        
        return hostel
    
    async def _get_hostel_by_name(self, name: str) -> Optional[Hostel]:
        """Get hostel by name."""
        query = select(Hostel).where(
            Hostel.tenant_id == self.tenant_id,
            Hostel.name == name,
            Hostel.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def list_hostels(
        self,
        active_only: bool = True,
        gender: Optional[HostelGender] = None,
        page: int = 1,
        size: int = 20,
    ) -> Tuple[List[Hostel], int]:
        """List hostels with filters."""
        query = select(Hostel).where(
            Hostel.tenant_id == self.tenant_id,
            Hostel.deleted_at.is_(None),
        )
        
        if active_only:
            query = query.where(Hostel.is_active == True)
        
        if gender:
            query = query.where(or_(
                Hostel.gender == gender,
                Hostel.gender == HostelGender.MIXED,
            ))
        
        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.session.execute(count_query)).scalar() or 0
        
        # Pagination
        skip = (page - 1) * size
        query = query.options(
            selectinload(Hostel.rooms)
        ).order_by(Hostel.name).offset(skip).limit(size)
        
        result = await self.session.execute(query)
        return list(result.scalars().all()), total
    
    async def delete_hostel(self, hostel_id: UUID) -> None:
        """Soft delete a hostel."""
        hostel = await self.get_hostel(hostel_id)
        hostel.deleted_at = datetime.now(timezone.utc)
        hostel.is_active = False
        await self.session.commit()
    
    # ============================================
    # Room Management
    # ============================================
    
    async def create_room(self, data: RoomCreate) -> HostelRoom:
        """Create a new room in a hostel."""
        # Validate hostel exists
        await self.get_hostel(data.hostel_id)
        
        # Check for duplicate room number
        existing = await self._get_room_by_number(data.hostel_id, data.room_number)
        if existing:
            raise ValidationError(f"Room {data.room_number} already exists in this hostel")
        
        room = HostelRoom(
            tenant_id=self.tenant_id,
            hostel_id=data.hostel_id,
            room_number=data.room_number,
            room_type=data.room_type,
            floor=data.floor,
            capacity=data.capacity,
            has_attached_bathroom=data.has_attached_bathroom,
            has_ac=data.has_ac,
            notes=data.notes,
        )
        
        self.session.add(room)
        await self.session.commit()
        await self.session.refresh(room)
        return room
    
    async def update_room(self, room_id: UUID, data: RoomUpdate) -> HostelRoom:
        """Update a room."""
        room = await self.get_room(room_id)
        
        update_data = data.model_dump(exclude_unset=True)
        
        # Check for duplicate room number if changing
        if "room_number" in update_data:
            existing = await self._get_room_by_number(room.hostel_id, update_data["room_number"])
            if existing and existing.id != room_id:
                raise ValidationError(f"Room {update_data['room_number']} already exists in this hostel")
        
        for key, value in update_data.items():
            setattr(room, key, value)
        
        await self.session.commit()
        await self.session.refresh(room)
        return room
    
    async def get_room(self, room_id: UUID, include_beds: bool = True) -> HostelRoom:
        """Get a room by ID."""
        query = select(HostelRoom).where(
            HostelRoom.id == room_id,
            HostelRoom.deleted_at.is_(None),
        )
        
        if include_beds:
            query = query.options(selectinload(HostelRoom.beds))
        
        result = await self.session.execute(query)
        room = result.scalar_one_or_none()
        
        if not room:
            raise ResourceNotFoundError("Room", str(room_id))
        
        return room
    
    async def _get_room_by_number(self, hostel_id: UUID, room_number: str) -> Optional[HostelRoom]:
        """Get room by number in a hostel."""
        query = select(HostelRoom).where(
            HostelRoom.hostel_id == hostel_id,
            HostelRoom.room_number == room_number,
            HostelRoom.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def list_rooms(
        self,
        hostel_id: UUID,
        active_only: bool = True,
        floor: Optional[int] = None,
    ) -> List[HostelRoom]:
        """List rooms in a hostel."""
        query = select(HostelRoom).where(
            HostelRoom.hostel_id == hostel_id,
            HostelRoom.deleted_at.is_(None),
        )
        
        if active_only:
            query = query.where(HostelRoom.is_active == True)
        
        if floor is not None:
            query = query.where(HostelRoom.floor == floor)
        
        query = query.options(
            selectinload(HostelRoom.beds)
        ).order_by(HostelRoom.floor, HostelRoom.room_number)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def delete_room(self, room_id: UUID) -> None:
        """Soft delete a room."""
        room = await self.get_room(room_id)
        room.deleted_at = datetime.now(timezone.utc)
        room.is_active = False
        await self.session.commit()
    
    # ============================================
    # Bed Management
    # ============================================
    
    async def create_beds(self, room_id: UUID, beds: List[BedCreate]) -> List[Bed]:
        """Create multiple beds in a room."""
        room = await self.get_room(room_id, include_beds=False)
        
        created_beds = []
        for bed_data in beds:
            # Check for duplicate bed number
            existing = await self._get_bed_by_number(room_id, bed_data.bed_number)
            if existing:
                raise ValidationError(f"Bed {bed_data.bed_number} already exists in this room")
            
            bed = Bed(
                tenant_id=self.tenant_id,
                room_id=room_id,
                bed_number=bed_data.bed_number,
                bed_type=bed_data.bed_type,
            )
            self.session.add(bed)
            created_beds.append(bed)
        
        await self.session.commit()
        
        for bed in created_beds:
            await self.session.refresh(bed)
        
        return created_beds
    
    async def get_bed(self, bed_id: UUID) -> Bed:
        """Get a bed by ID."""
        query = select(Bed).where(Bed.id == bed_id)
        result = await self.session.execute(query)
        bed = result.scalar_one_or_none()
        
        if not bed:
            raise ResourceNotFoundError("Bed", str(bed_id))
        
        return bed
    
    async def _get_bed_by_number(self, room_id: UUID, bed_number: str) -> Optional[Bed]:
        """Get bed by number in a room."""
        query = select(Bed).where(
            Bed.room_id == room_id,
            Bed.bed_number == bed_number,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def update_bed(self, bed_id: UUID, data: BedUpdate) -> Bed:
        """Update a bed."""
        bed = await self.get_bed(bed_id)
        
        update_data = data.model_dump(exclude_unset=True)
        
        # Check for duplicate bed number if changing
        if "bed_number" in update_data:
            existing = await self._get_bed_by_number(bed.room_id, update_data["bed_number"])
            if existing and existing.id != bed_id:
                raise ValidationError(f"Bed {update_data['bed_number']} already exists in this room")
        
        for key, value in update_data.items():
            setattr(bed, key, value)
        
        await self.session.commit()
        await self.session.refresh(bed)
        return bed
    
    # ============================================
    # Warden Management
    # ============================================
    
    async def create_warden(self, data: WardenCreate) -> Warden:
        """Create a new warden."""
        warden = Warden(
            tenant_id=self.tenant_id,
            name=data.name,
            phone=data.phone,
            alternate_phone=data.alternate_phone,
            email=data.email,
            address=data.address,
            user_id=data.user_id,
            is_chief_warden=data.is_chief_warden,
            notes=data.notes,
        )
        
        self.session.add(warden)
        await self.session.commit()
        await self.session.refresh(warden)
        return warden
    
    async def update_warden(self, warden_id: UUID, data: WardenUpdate) -> Warden:
        """Update a warden."""
        warden = await self.get_warden(warden_id)
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(warden, key, value)
        
        await self.session.commit()
        await self.session.refresh(warden)
        return warden
    
    async def get_warden(self, warden_id: UUID) -> Warden:
        """Get a warden by ID."""
        query = select(Warden).where(
            Warden.tenant_id == self.tenant_id,
            Warden.id == warden_id,
        )
        result = await self.session.execute(query)
        warden = result.scalar_one_or_none()
        
        if not warden:
            raise ResourceNotFoundError("Warden", str(warden_id))
        
        return warden
    
    async def list_wardens(
        self,
        active_only: bool = True,
        hostel_id: Optional[UUID] = None,
    ) -> List[Warden]:
        """List wardens."""
        query = select(Warden).where(
            Warden.tenant_id == self.tenant_id,
        )
        
        if active_only:
            query = query.where(Warden.is_active == True)
        
        if hostel_id:
            query = query.where(Warden.assigned_hostel_id == hostel_id)
        
        query = query.options(
            selectinload(Warden.hostel)
        ).order_by(Warden.name)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def assign_warden(self, data: WardenAssign) -> Warden:
        """Assign a warden to a hostel."""
        warden = await self.get_warden(data.warden_id)
        
        # Validate hostel exists
        await self.get_hostel(data.hostel_id)
        
        warden.assigned_hostel_id = data.hostel_id
        warden.assigned_from = data.assigned_from or date.today()
        warden.assigned_to = data.assigned_to
        
        await self.session.commit()
        await self.session.refresh(warden)
        return warden
    
    async def unassign_warden(self, warden_id: UUID) -> Warden:
        """Unassign a warden from their hostel."""
        warden = await self.get_warden(warden_id)
        warden.assigned_hostel_id = None
        warden.assigned_to = date.today()
        
        await self.session.commit()
        await self.session.refresh(warden)
        return warden
    
    # ============================================
    # Student Assignment
    # ============================================
    
    async def assign_student_to_bed(
        self,
        data: StudentHostelAssignRequest,
    ) -> StudentHostelAssignment:
        """Assign a student to a hostel bed."""
        # Validate hostel exists
        hostel = await self.get_hostel(data.hostel_id)
        
        # Validate room exists and belongs to hostel
        room = await self.get_room(data.room_id)
        if room.hostel_id != data.hostel_id:
            raise ValidationError("Room does not belong to the specified hostel")
        
        # Validate bed exists and belongs to room
        bed = await self.get_bed(data.bed_id)
        if bed.room_id != data.room_id:
            raise ValidationError("Bed does not belong to the specified room")
        
        # Check if bed is already occupied
        if bed.is_occupied:
            raise ValidationError(f"Bed {bed.bed_number} is already occupied")
        
        # Check if student already has active hostel assignment
        existing = await self._get_active_student_assignment(data.student_id)
        if existing:
            raise ValidationError("Student already has an active hostel assignment")
        
        # TODO: Validate student gender matches hostel gender
        # This would require fetching student profile
        
        # Create assignment
        assignment = StudentHostelAssignment(
            tenant_id=self.tenant_id,
            student_id=data.student_id,
            hostel_id=data.hostel_id,
            room_id=data.room_id,
            bed_id=data.bed_id,
            academic_year_id=data.academic_year_id,
            assigned_from=data.assigned_from,
            assigned_to=data.assigned_to,
            guardian_name=data.guardian_name,
            guardian_phone=data.guardian_phone,
            guardian_relation=data.guardian_relation,
            notes=data.notes,
        )
        
        # Mark bed as occupied
        bed.is_occupied = True
        
        self.session.add(assignment)
        await self.session.commit()
        await self.session.refresh(assignment)
        return assignment
    
    async def unassign_student(self, data: StudentHostelUnassignRequest) -> None:
        """Unassign a student from hostel."""
        assignment = await self._get_active_student_assignment(data.student_id)
        
        if not assignment:
            raise ResourceNotFoundError("StudentHostelAssignment", str(data.student_id))
        
        # Update assignment
        checkout_date = data.checkout_date or date.today()
        assignment.assigned_to = checkout_date
        assignment.checked_out_at = datetime.now(timezone.utc)
        assignment.is_active = False
        
        # Mark bed as available
        bed = await self.get_bed(assignment.bed_id)
        bed.is_occupied = False
        
        await self.session.commit()
    
    async def check_in_student(self, student_id: UUID) -> StudentHostelAssignment:
        """Record student check-in."""
        assignment = await self._get_active_student_assignment(student_id)
        
        if not assignment:
            raise ResourceNotFoundError("StudentHostelAssignment", str(student_id))
        
        assignment.checked_in_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(assignment)
        return assignment
    
    async def check_out_student(self, student_id: UUID) -> StudentHostelAssignment:
        """Record student check-out (temporary)."""
        assignment = await self._get_active_student_assignment(student_id)
        
        if not assignment:
            raise ResourceNotFoundError("StudentHostelAssignment", str(student_id))
        
        assignment.checked_out_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(assignment)
        return assignment
    
    async def _get_active_student_assignment(
        self,
        student_id: UUID,
    ) -> Optional[StudentHostelAssignment]:
        """Get active hostel assignment for a student."""
        query = select(StudentHostelAssignment).where(
            StudentHostelAssignment.tenant_id == self.tenant_id,
            StudentHostelAssignment.student_id == student_id,
            StudentHostelAssignment.is_active == True,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_student_hostel_detail(
        self,
        student_id: UUID,
    ) -> Optional[StudentHostelDetail]:
        """Get detailed hostel info for a student (parent view)."""
        assignment = await self._get_active_student_assignment(student_id)
        
        if not assignment:
            return None
        
        # Get hostel
        hostel = await self.get_hostel(assignment.hostel_id)
        
        # Get room
        room = await self.get_room(assignment.room_id, include_beds=False)
        
        # Get bed
        bed = await self.get_bed(assignment.bed_id)
        
        # Get warden
        wardens = await self.list_wardens(hostel_id=assignment.hostel_id)
        chief_warden = next((w for w in wardens if w.is_chief_warden), None)
        warden = chief_warden or (wardens[0] if wardens else None)
        
        return StudentHostelDetail(
            student_id=student_id,
            student_name="",  # To be filled by caller
            hostel_name=hostel.name,
            hostel_code=hostel.code,
            hostel_address=hostel.address,
            room_number=room.room_number,
            floor=room.floor,
            room_type=room.room_type,
            bed_number=bed.bed_number,
            warden_name=warden.name if warden else None,
            warden_phone=warden.phone if warden else None,
            assigned_from=assignment.assigned_from,
            assigned_to=assignment.assigned_to,
            checked_in_at=assignment.checked_in_at,
            checked_out_at=assignment.checked_out_at,
            guardian_name=assignment.guardian_name,
            guardian_phone=assignment.guardian_phone,
        )
    
    # ============================================
    # Occupancy & Availability
    # ============================================
    
    async def get_hostel_occupancy(self, hostel_id: UUID) -> HostelOccupancy:
        """Get occupancy status for a hostel."""
        hostel = await self.get_hostel(hostel_id)
        
        # Count total beds
        total_beds_query = (
            select(func.count(Bed.id))
            .join(HostelRoom, Bed.room_id == HostelRoom.id)
            .where(
                HostelRoom.hostel_id == hostel_id,
                HostelRoom.is_active == True,
                Bed.is_active == True,
            )
        )
        total_beds = (await self.session.execute(total_beds_query)).scalar() or 0
        
        # Count occupied beds
        occupied_beds_query = (
            select(func.count(Bed.id))
            .join(HostelRoom, Bed.room_id == HostelRoom.id)
            .where(
                HostelRoom.hostel_id == hostel_id,
                Bed.is_occupied == True,
            )
        )
        occupied_beds = (await self.session.execute(occupied_beds_query)).scalar() or 0
        
        available = total_beds - occupied_beds
        occupancy_pct = (occupied_beds / total_beds * 100) if total_beds > 0 else 0
        
        return HostelOccupancy(
            hostel_id=hostel_id,
            hostel_name=hostel.name,
            gender=hostel.gender,
            total_beds=total_beds,
            occupied_beds=occupied_beds,
            available_beds=available,
            occupancy_percentage=round(occupancy_pct, 2),
        )
    
    async def get_all_occupancy(self) -> List[HostelOccupancy]:
        """Get occupancy for all hostels."""
        hostels, _ = await self.list_hostels()
        
        result = []
        for hostel in hostels:
            occupancy = await self.get_hostel_occupancy(hostel.id)
            result.append(occupancy)
        
        return result
    
    async def get_available_beds(
        self,
        hostel_id: Optional[UUID] = None,
        floor: Optional[int] = None,
    ) -> List[AvailableBed]:
        """Get list of available beds."""
        query = (
            select(Bed, HostelRoom, Hostel)
            .join(HostelRoom, Bed.room_id == HostelRoom.id)
            .join(Hostel, HostelRoom.hostel_id == Hostel.id)
            .where(
                Hostel.tenant_id == self.tenant_id,
                Hostel.is_active == True,
                HostelRoom.is_active == True,
                Bed.is_active == True,
                Bed.is_occupied == False,
            )
        )
        
        if hostel_id:
            query = query.where(Hostel.id == hostel_id)
        
        if floor is not None:
            query = query.where(HostelRoom.floor == floor)
        
        query = query.order_by(Hostel.name, HostelRoom.room_number, Bed.bed_number)
        
        result = await self.session.execute(query)
        
        available = []
        for bed, room, hostel in result.all():
            available.append(AvailableBed(
                bed_id=bed.id,
                bed_number=bed.bed_number,
                bed_type=bed.bed_type,
                room_id=room.id,
                room_number=room.room_number,
                floor=room.floor,
                hostel_id=hostel.id,
                hostel_name=hostel.name,
            ))
        
        return available
    
    async def list_students_in_hostel(
        self,
        hostel_id: UUID,
        active_only: bool = True,
    ) -> List[StudentHostelAssignment]:
        """List all students in a hostel."""
        query = select(StudentHostelAssignment).where(
            StudentHostelAssignment.tenant_id == self.tenant_id,
            StudentHostelAssignment.hostel_id == hostel_id,
        )
        
        if active_only:
            query = query.where(StudentHostelAssignment.is_active == True)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    # ============================================
    # Fee Links
    # ============================================
    
    async def create_hostel_fee_link(
        self,
        data: HostelFeeLinkCreate,
    ) -> HostelFeeLink:
        """Create a hostel fee link."""
        fee_link = HostelFeeLink(
            tenant_id=self.tenant_id,
            student_id=data.student_id,
            assignment_id=data.assignment_id,
            monthly_fee=data.monthly_fee,
            fee_month=data.fee_month,
            fee_year=data.fee_year,
        )
        
        self.session.add(fee_link)
        await self.session.commit()
        await self.session.refresh(fee_link)
        return fee_link
    
    async def get_student_hostel_fees(
        self,
        student_id: UUID,
    ) -> List[HostelFeeLink]:
        """Get hostel fees for a student."""
        query = select(HostelFeeLink).where(
            HostelFeeLink.tenant_id == self.tenant_id,
            HostelFeeLink.student_id == student_id,
        ).order_by(
            HostelFeeLink.fee_year.desc(),
            HostelFeeLink.fee_month.desc(),
        )
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
