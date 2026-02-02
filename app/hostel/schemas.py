"""
CUSTOS Hostel Management Schemas

Pydantic schemas for hostel API.
"""

from datetime import datetime, date
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from app.hostel.models import HostelGender


# ============================================
# Hostel Schemas
# ============================================

class HostelCreate(BaseModel):
    """Schema for creating a hostel."""
    name: str = Field(..., max_length=200)
    code: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = None
    gender: HostelGender = HostelGender.MIXED
    address: Optional[str] = None
    building_name: Optional[str] = Field(None, max_length=200)
    total_capacity: int = Field(0, ge=0)
    floor_count: int = Field(1, ge=1)
    contact_phone: Optional[str] = Field(None, max_length=20)
    contact_email: Optional[str] = Field(None, max_length=200)
    notes: Optional[str] = None


class HostelUpdate(BaseModel):
    """Schema for updating a hostel."""
    name: Optional[str] = Field(None, max_length=200)
    code: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = None
    gender: Optional[HostelGender] = None
    address: Optional[str] = None
    building_name: Optional[str] = Field(None, max_length=200)
    total_capacity: Optional[int] = Field(None, ge=0)
    floor_count: Optional[int] = Field(None, ge=1)
    contact_phone: Optional[str] = Field(None, max_length=20)
    contact_email: Optional[str] = Field(None, max_length=200)
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class HostelResponse(BaseModel):
    """Schema for hostel response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    name: str
    code: Optional[str] = None
    description: Optional[str] = None
    gender: HostelGender
    address: Optional[str] = None
    building_name: Optional[str] = None
    total_capacity: int
    floor_count: int
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    is_active: bool
    notes: Optional[str] = None
    created_at: datetime


class HostelListItem(BaseModel):
    """Schema for listing hostels."""
    id: UUID
    name: str
    code: Optional[str] = None
    gender: HostelGender
    total_capacity: int
    is_active: bool
    rooms_count: int = 0
    occupied_beds: int = 0


# ============================================
# Room Schemas
# ============================================

class RoomCreate(BaseModel):
    """Schema for creating a room."""
    hostel_id: UUID
    room_number: str = Field(..., max_length=20)
    room_type: Optional[str] = Field(None, max_length=50)
    floor: int = Field(0, ge=0)
    capacity: int = Field(1, ge=1, le=20)
    has_attached_bathroom: bool = False
    has_ac: bool = False
    notes: Optional[str] = None


class RoomUpdate(BaseModel):
    """Schema for updating a room."""
    room_number: Optional[str] = Field(None, max_length=20)
    room_type: Optional[str] = Field(None, max_length=50)
    floor: Optional[int] = Field(None, ge=0)
    capacity: Optional[int] = Field(None, ge=1, le=20)
    has_attached_bathroom: Optional[bool] = None
    has_ac: Optional[bool] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class BedResponse(BaseModel):
    """Schema for bed response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    room_id: UUID
    bed_number: str
    bed_type: Optional[str] = None
    is_active: bool
    is_occupied: bool


class RoomResponse(BaseModel):
    """Schema for room response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    hostel_id: UUID
    room_number: str
    room_type: Optional[str] = None
    floor: int
    capacity: int
    has_attached_bathroom: bool
    has_ac: bool
    is_active: bool
    notes: Optional[str] = None
    created_at: datetime
    beds: List[BedResponse] = []


class RoomListItem(BaseModel):
    """Schema for listing rooms."""
    id: UUID
    hostel_id: UUID
    room_number: str
    floor: int
    capacity: int
    is_active: bool
    beds_count: int = 0
    occupied_beds: int = 0
    available_beds: int = 0


# ============================================
# Bed Schemas
# ============================================

class BedCreate(BaseModel):
    """Schema for creating a bed."""
    bed_number: str = Field(..., max_length=20)
    bed_type: Optional[str] = Field(None, max_length=50)


class BulkBedCreate(BaseModel):
    """Schema for creating multiple beds."""
    room_id: UUID
    beds: List[BedCreate]


class BedUpdate(BaseModel):
    """Schema for updating a bed."""
    bed_number: Optional[str] = Field(None, max_length=20)
    bed_type: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None


# ============================================
# Warden Schemas
# ============================================

class WardenCreate(BaseModel):
    """Schema for creating a warden."""
    name: str = Field(..., max_length=200)
    phone: str = Field(..., max_length=20)
    alternate_phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=200)
    address: Optional[str] = None
    user_id: Optional[UUID] = None
    is_chief_warden: bool = False
    notes: Optional[str] = None


class WardenUpdate(BaseModel):
    """Schema for updating a warden."""
    name: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=20)
    alternate_phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=200)
    address: Optional[str] = None
    is_chief_warden: Optional[bool] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class WardenAssign(BaseModel):
    """Schema for assigning a warden to hostel."""
    warden_id: UUID
    hostel_id: UUID
    assigned_from: Optional[date] = None
    assigned_to: Optional[date] = None


class WardenResponse(BaseModel):
    """Schema for warden response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    name: str
    phone: str
    alternate_phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    user_id: Optional[UUID] = None
    assigned_hostel_id: Optional[UUID] = None
    is_chief_warden: bool
    assigned_from: Optional[date] = None
    assigned_to: Optional[date] = None
    is_active: bool
    notes: Optional[str] = None
    created_at: datetime
    
    # Denormalized
    hostel_name: Optional[str] = None


class WardenListItem(BaseModel):
    """Schema for listing wardens."""
    id: UUID
    name: str
    phone: str
    is_chief_warden: bool
    assigned_hostel_id: Optional[UUID] = None
    hostel_name: Optional[str] = None
    is_active: bool


# ============================================
# Student Assignment Schemas
# ============================================

class StudentHostelAssignRequest(BaseModel):
    """Schema for assigning a student to hostel."""
    student_id: UUID
    hostel_id: UUID
    room_id: UUID
    bed_id: UUID
    academic_year_id: Optional[UUID] = None
    assigned_from: date
    assigned_to: Optional[date] = None
    guardian_name: Optional[str] = Field(None, max_length=200)
    guardian_phone: Optional[str] = Field(None, max_length=20)
    guardian_relation: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None


class StudentHostelUnassignRequest(BaseModel):
    """Schema for unassigning a student from hostel."""
    student_id: UUID
    checkout_date: Optional[date] = None


class StudentHostelCheckIn(BaseModel):
    """Schema for student check-in."""
    student_id: UUID


class StudentHostelCheckOut(BaseModel):
    """Schema for student check-out."""
    student_id: UUID


class StudentHostelAssignmentResponse(BaseModel):
    """Schema for student hostel assignment response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    student_id: UUID
    hostel_id: UUID
    room_id: UUID
    bed_id: UUID
    academic_year_id: Optional[UUID] = None
    assigned_from: date
    assigned_to: Optional[date] = None
    checked_in_at: Optional[datetime] = None
    checked_out_at: Optional[datetime] = None
    guardian_name: Optional[str] = None
    guardian_phone: Optional[str] = None
    guardian_relation: Optional[str] = None
    is_active: bool
    notes: Optional[str] = None
    created_at: datetime


class StudentHostelDetail(BaseModel):
    """Detailed hostel info for a student (parent view)."""
    student_id: UUID
    student_name: str
    
    # Hostel info
    hostel_name: str
    hostel_code: Optional[str] = None
    hostel_address: Optional[str] = None
    
    # Room info
    room_number: str
    floor: int
    room_type: Optional[str] = None
    
    # Bed info
    bed_number: str
    
    # Warden info
    warden_name: Optional[str] = None
    warden_phone: Optional[str] = None
    
    # Assignment dates
    assigned_from: date
    assigned_to: Optional[date] = None
    
    # Status
    checked_in_at: Optional[datetime] = None
    checked_out_at: Optional[datetime] = None
    
    # Guardian
    guardian_name: Optional[str] = None
    guardian_phone: Optional[str] = None


# ============================================
# Occupancy Schemas
# ============================================

class HostelOccupancy(BaseModel):
    """Schema for hostel occupancy status."""
    hostel_id: UUID
    hostel_name: str
    gender: HostelGender
    total_beds: int
    occupied_beds: int
    available_beds: int
    occupancy_percentage: float


class RoomOccupancy(BaseModel):
    """Schema for room occupancy."""
    room_id: UUID
    room_number: str
    floor: int
    total_beds: int
    occupied_beds: int
    available_beds: int


class AvailableBed(BaseModel):
    """Schema for an available bed."""
    bed_id: UUID
    bed_number: str
    bed_type: Optional[str] = None
    room_id: UUID
    room_number: str
    floor: int
    hostel_id: UUID
    hostel_name: str


# ============================================
# Fee Link Schemas
# ============================================

class HostelFeeLinkCreate(BaseModel):
    """Schema for creating a hostel fee link."""
    student_id: UUID
    assignment_id: Optional[UUID] = None
    monthly_fee: float = Field(..., gt=0)
    fee_month: int = Field(..., ge=1, le=12)
    fee_year: int


class HostelFeeLinkResponse(BaseModel):
    """Schema for hostel fee link response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    student_id: UUID
    assignment_id: Optional[UUID] = None
    monthly_fee: float
    fee_month: int
    fee_year: int
    linked_invoice_id: Optional[UUID] = None
    is_paid: bool
    paid_at: Optional[datetime] = None
