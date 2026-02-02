"""
CUSTOS Transport Management Schemas

Pydantic schemas for transport API.
"""

from datetime import datetime, date, time
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, field_validator

from app.transport.models import VehicleType, RouteShift


# ============================================
# Vehicle Schemas
# ============================================

class VehicleCreate(BaseModel):
    """Schema for creating a vehicle."""
    vehicle_number: str = Field(..., max_length=50)
    vehicle_type: VehicleType = VehicleType.BUS
    make: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    year: Optional[int] = None
    capacity: int = Field(40, ge=1, le=100)
    registration_number: Optional[str] = Field(None, max_length=100)
    registration_expiry: Optional[date] = None
    insurance_number: Optional[str] = Field(None, max_length=100)
    insurance_expiry: Optional[date] = None
    fitness_certificate: Optional[str] = Field(None, max_length=100)
    fitness_expiry: Optional[date] = None
    notes: Optional[str] = None


class VehicleUpdate(BaseModel):
    """Schema for updating a vehicle."""
    vehicle_number: Optional[str] = Field(None, max_length=50)
    vehicle_type: Optional[VehicleType] = None
    make: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    year: Optional[int] = None
    capacity: Optional[int] = Field(None, ge=1, le=100)
    registration_number: Optional[str] = Field(None, max_length=100)
    registration_expiry: Optional[date] = None
    insurance_number: Optional[str] = Field(None, max_length=100)
    insurance_expiry: Optional[date] = None
    fitness_certificate: Optional[str] = Field(None, max_length=100)
    fitness_expiry: Optional[date] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class VehicleResponse(BaseModel):
    """Schema for vehicle response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    vehicle_number: str
    vehicle_type: VehicleType
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    capacity: int
    registration_number: Optional[str] = None
    registration_expiry: Optional[date] = None
    insurance_number: Optional[str] = None
    insurance_expiry: Optional[date] = None
    fitness_certificate: Optional[str] = None
    fitness_expiry: Optional[date] = None
    is_active: bool
    notes: Optional[str] = None
    created_at: datetime


class VehicleListItem(BaseModel):
    """Schema for listing vehicles."""
    id: UUID
    vehicle_number: str
    vehicle_type: VehicleType
    capacity: int
    is_active: bool


# ============================================
# Driver Schemas
# ============================================

class DriverCreate(BaseModel):
    """Schema for creating a driver."""
    name: str = Field(..., max_length=200)
    phone: str = Field(..., max_length=20)
    alternate_phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=200)
    address: Optional[str] = None
    license_number: str = Field(..., max_length=50)
    license_type: Optional[str] = Field(None, max_length=20)
    license_expiry: Optional[date] = None
    emergency_contact_name: Optional[str] = Field(None, max_length=200)
    emergency_contact_phone: Optional[str] = Field(None, max_length=20)
    blood_group: Optional[str] = Field(None, max_length=10)
    photo_url: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = None


class DriverUpdate(BaseModel):
    """Schema for updating a driver."""
    name: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=20)
    alternate_phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=200)
    address: Optional[str] = None
    license_number: Optional[str] = Field(None, max_length=50)
    license_type: Optional[str] = Field(None, max_length=20)
    license_expiry: Optional[date] = None
    emergency_contact_name: Optional[str] = Field(None, max_length=200)
    emergency_contact_phone: Optional[str] = Field(None, max_length=20)
    blood_group: Optional[str] = Field(None, max_length=10)
    photo_url: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class DriverResponse(BaseModel):
    """Schema for driver response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    name: str
    phone: str
    alternate_phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    license_number: str
    license_type: Optional[str] = None
    license_expiry: Optional[date] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    blood_group: Optional[str] = None
    photo_url: Optional[str] = None
    is_active: bool
    notes: Optional[str] = None
    created_at: datetime


class DriverListItem(BaseModel):
    """Schema for listing drivers."""
    id: UUID
    name: str
    phone: str
    license_number: str
    is_active: bool


# ============================================
# Route Schemas
# ============================================

class RouteStopCreate(BaseModel):
    """Schema for creating a route stop."""
    stop_name: str = Field(..., max_length=200)
    stop_address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    pickup_time: Optional[time] = None
    drop_time: Optional[time] = None
    stop_order: int = Field(..., ge=1)
    landmark: Optional[str] = Field(None, max_length=300)


class RouteStopUpdate(BaseModel):
    """Schema for updating a route stop."""
    stop_name: Optional[str] = Field(None, max_length=200)
    stop_address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    pickup_time: Optional[time] = None
    drop_time: Optional[time] = None
    stop_order: Optional[int] = Field(None, ge=1)
    landmark: Optional[str] = Field(None, max_length=300)
    is_active: Optional[bool] = None


class RouteStopResponse(BaseModel):
    """Schema for route stop response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    route_id: UUID
    stop_name: str
    stop_address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    pickup_time: Optional[time] = None
    drop_time: Optional[time] = None
    stop_order: int
    landmark: Optional[str] = None
    is_active: bool


class RouteCreate(BaseModel):
    """Schema for creating a route."""
    name: str = Field(..., max_length=200)
    code: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = None
    shift: RouteShift = RouteShift.BOTH
    distance_km: Optional[float] = None
    estimated_duration_minutes: Optional[int] = None
    start_location: Optional[str] = Field(None, max_length=300)
    end_location: Optional[str] = Field(None, max_length=300)


class RouteUpdate(BaseModel):
    """Schema for updating a route."""
    name: Optional[str] = Field(None, max_length=200)
    code: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = None
    shift: Optional[RouteShift] = None
    distance_km: Optional[float] = None
    estimated_duration_minutes: Optional[int] = None
    start_location: Optional[str] = Field(None, max_length=300)
    end_location: Optional[str] = Field(None, max_length=300)
    is_active: Optional[bool] = None


class RouteResponse(BaseModel):
    """Schema for route response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    name: str
    code: Optional[str] = None
    description: Optional[str] = None
    shift: RouteShift
    distance_km: Optional[float] = None
    estimated_duration_minutes: Optional[int] = None
    start_location: Optional[str] = None
    end_location: Optional[str] = None
    is_active: bool
    created_at: datetime
    stops: List[RouteStopResponse] = []


class RouteListItem(BaseModel):
    """Schema for listing routes."""
    id: UUID
    name: str
    code: Optional[str] = None
    shift: RouteShift
    is_active: bool
    stops_count: int = 0


# ============================================
# Transport Assignment Schemas
# ============================================

class TransportAssignmentCreate(BaseModel):
    """Schema for creating a transport assignment."""
    route_id: UUID
    vehicle_id: UUID
    driver_id: UUID
    academic_year_id: UUID
    shift: RouteShift = RouteShift.BOTH
    helper_name: Optional[str] = Field(None, max_length=200)
    helper_phone: Optional[str] = Field(None, max_length=20)
    notes: Optional[str] = None


class TransportAssignmentUpdate(BaseModel):
    """Schema for updating a transport assignment."""
    vehicle_id: Optional[UUID] = None
    driver_id: Optional[UUID] = None
    shift: Optional[RouteShift] = None
    helper_name: Optional[str] = Field(None, max_length=200)
    helper_phone: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class TransportAssignmentResponse(BaseModel):
    """Schema for transport assignment response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    route_id: UUID
    vehicle_id: UUID
    driver_id: UUID
    academic_year_id: UUID
    shift: RouteShift
    helper_name: Optional[str] = None
    helper_phone: Optional[str] = None
    is_active: bool
    notes: Optional[str] = None
    created_at: datetime
    
    # Denormalized for convenience
    route_name: Optional[str] = None
    vehicle_number: Optional[str] = None
    driver_name: Optional[str] = None


# ============================================
# Student Transport Schemas
# ============================================

class StudentTransportAssign(BaseModel):
    """Schema for assigning a student to transport."""
    student_id: UUID
    route_id: UUID
    pickup_stop_id: Optional[UUID] = None
    drop_stop_id: Optional[UUID] = None
    assigned_from: date
    assigned_to: Optional[date] = None
    academic_year_id: Optional[UUID] = None
    guardian_name: Optional[str] = Field(None, max_length=200)
    guardian_phone: Optional[str] = Field(None, max_length=20)
    notes: Optional[str] = None


class StudentTransportUnassign(BaseModel):
    """Schema for unassigning a student from transport."""
    student_id: UUID
    unassign_date: Optional[date] = None  # Defaults to today


class StudentTransportResponse(BaseModel):
    """Schema for student transport response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    student_id: UUID
    route_id: UUID
    pickup_stop_id: Optional[UUID] = None
    drop_stop_id: Optional[UUID] = None
    assigned_from: date
    assigned_to: Optional[date] = None
    guardian_name: Optional[str] = None
    guardian_phone: Optional[str] = None
    is_active: bool
    notes: Optional[str] = None
    created_at: datetime


class StudentTransportDetail(BaseModel):
    """Detailed transport info for a student (parent view)."""
    student_id: UUID
    student_name: str
    route_name: str
    route_code: Optional[str] = None
    
    # Vehicle info
    vehicle_number: Optional[str] = None
    vehicle_type: Optional[str] = None
    
    # Driver info
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None
    
    # Helper info
    helper_name: Optional[str] = None
    helper_phone: Optional[str] = None
    
    # Stop info
    pickup_stop_name: Optional[str] = None
    pickup_time: Optional[time] = None
    drop_stop_name: Optional[str] = None
    drop_time: Optional[time] = None
    
    # Guardian
    guardian_name: Optional[str] = None
    guardian_phone: Optional[str] = None


# ============================================
# Route Capacity
# ============================================

class RouteCapacityStatus(BaseModel):
    """Schema for route capacity status."""
    route_id: UUID
    route_name: str
    vehicle_capacity: int
    assigned_students: int
    available_seats: int
    utilization_percentage: float


# ============================================
# Transport Fee Link Schemas
# ============================================

class TransportFeeLinkCreate(BaseModel):
    """Schema for creating a transport fee link."""
    student_id: UUID
    student_transport_id: Optional[UUID] = None
    monthly_fee: float = Field(..., gt=0)
    fee_month: int = Field(..., ge=1, le=12)
    fee_year: int


class TransportFeeLinkResponse(BaseModel):
    """Schema for transport fee link response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    student_id: UUID
    student_transport_id: Optional[UUID] = None
    monthly_fee: float
    linked_invoice_id: Optional[UUID] = None
    fee_month: int
    fee_year: int
    is_paid: bool
    paid_at: Optional[datetime] = None
