"""
CUSTOS Transport Management Models

Vehicles, drivers, routes, stops, and student transport assignments.
"""

from datetime import datetime, date, time
from enum import Enum
from typing import Optional, List
from uuid import UUID

from sqlalchemy import String, Text, Boolean, Date, Time, DateTime, ForeignKey, Index, Integer, Numeric
from sqlalchemy import Enum as SQLEnum, UniqueConstraint, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import TenantBaseModel


class VehicleType(str, Enum):
    """Types of transport vehicles."""
    BUS = "bus"
    VAN = "van"
    MINI_BUS = "mini_bus"
    AUTO = "auto"


class RouteShift(str, Enum):
    """Route shift timing."""
    MORNING = "morning"
    EVENING = "evening"
    BOTH = "both"


class Vehicle(TenantBaseModel):
    """
    Transport Vehicle.
    
    Represents a school bus, van, or other transport vehicle.
    """
    __tablename__ = "transport_vehicles"
    
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "vehicle_number",
            name="uq_vehicle_number",
        ),
        Index("ix_transport_vehicles_tenant", "tenant_id", "is_active"),
    )
    
    # Vehicle details
    vehicle_number: Mapped[str] = mapped_column(String(50), nullable=False)
    vehicle_type: Mapped[VehicleType] = mapped_column(
        SQLEnum(VehicleType),
        default=VehicleType.BUS,
    )
    
    # Make and model
    make: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Capacity
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=40)
    
    # Registration and insurance
    registration_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    registration_expiry: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    insurance_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    insurance_expiry: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Fitness
    fitness_certificate: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    fitness_expiry: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Soft delete
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class Driver(TenantBaseModel):
    """
    Transport Driver.
    
    Represents a driver assigned to school transport.
    """
    __tablename__ = "transport_drivers"
    
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "license_number",
            name="uq_driver_license",
        ),
        Index("ix_transport_drivers_tenant", "tenant_id", "is_active"),
    )
    
    # Personal details
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    alternate_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # License details
    license_number: Mapped[str] = mapped_column(String(50), nullable=False)
    license_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # LMV, HMV, etc.
    license_expiry: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Emergency contact
    emergency_contact_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    emergency_contact_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Blood group (for emergency)
    blood_group: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    
    # Photo
    photo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Soft delete
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class Route(TenantBaseModel):
    """
    Transport Route.
    
    Represents a defined route with stops.
    """
    __tablename__ = "transport_routes"
    
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "name",
            name="uq_route_name",
        ),
        Index("ix_transport_routes_tenant", "tenant_id", "is_active"),
    )
    
    # Route details
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # R1, R2, etc.
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Shift
    shift: Mapped[RouteShift] = mapped_column(
        SQLEnum(RouteShift),
        default=RouteShift.BOTH,
    )
    
    # Distance (in km)
    distance_km: Mapped[Optional[float]] = mapped_column(Numeric(8, 2), nullable=True)
    
    # Estimated duration (in minutes)
    estimated_duration_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Start and end locations
    start_location: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    end_location: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Soft delete
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Relationships
    stops: Mapped[List["RouteStop"]] = relationship(
        "RouteStop",
        back_populates="route",
        order_by="RouteStop.stop_order",
        lazy="selectin",
    )


class RouteStop(TenantBaseModel):
    """
    Route Stop.
    
    Individual pickup/drop point on a route.
    """
    __tablename__ = "transport_route_stops"
    
    __table_args__ = (
        UniqueConstraint(
            "route_id", "stop_order",
            name="uq_route_stop_order",
        ),
        Index("ix_route_stops_route", "route_id"),
    )
    
    # Reference to route
    route_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("transport_routes.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Stop details
    stop_name: Mapped[str] = mapped_column(String(200), nullable=False)
    stop_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Location (optional for future GPS)
    latitude: Mapped[Optional[float]] = mapped_column(Numeric(10, 8), nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Numeric(11, 8), nullable=True)
    
    # Times
    pickup_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    drop_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    
    # Order on route
    stop_order: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Landmark
    landmark: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationship
    route: Mapped["Route"] = relationship("Route", back_populates="stops")


class TransportAssignment(TenantBaseModel):
    """
    Transport Assignment.
    
    Links a route to a vehicle and driver for an academic year.
    """
    __tablename__ = "transport_assignments"
    
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "route_id", "academic_year_id", "shift",
            name="uq_transport_assignment",
        ),
        Index("ix_transport_assignments_tenant", "tenant_id", "is_active"),
        Index("ix_transport_assignments_route", "route_id"),
        Index("ix_transport_assignments_vehicle", "vehicle_id"),
        Index("ix_transport_assignments_driver", "driver_id"),
    )
    
    # Route
    route_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("transport_routes.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Vehicle
    vehicle_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("transport_vehicles.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Driver
    driver_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("transport_drivers.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Academic year
    academic_year_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("academic_years.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Shift (for routes with BOTH, can have separate assignments)
    shift: Mapped[RouteShift] = mapped_column(
        SQLEnum(RouteShift),
        default=RouteShift.BOTH,
    )
    
    # Helper/attendant name
    helper_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    helper_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class StudentTransport(TenantBaseModel):
    """
    Student Transport Assignment.
    
    Links a student to a route and stop.
    """
    __tablename__ = "student_transport"
    
    __table_args__ = (
        Index("ix_student_transport_tenant", "tenant_id", "is_active"),
        Index("ix_student_transport_student", "student_id"),
        Index("ix_student_transport_route", "route_id"),
    )
    
    # Student
    student_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Route
    route_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("transport_routes.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Pickup stop
    pickup_stop_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("transport_route_stops.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Drop stop (can be different)
    drop_stop_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("transport_route_stops.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Date range
    assigned_from: Mapped[date] = mapped_column(Date, nullable=False)
    assigned_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Academic year
    academic_year_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("academic_years.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Guardian contact for pickup (override)
    guardian_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    guardian_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class TransportFeeLink(TenantBaseModel):
    """
    Transport Fee Link.
    
    Links student transport to fee invoices.
    """
    __tablename__ = "transport_fee_links"
    
    __table_args__ = (
        Index("ix_transport_fee_links_tenant", "tenant_id"),
        Index("ix_transport_fee_links_student", "student_id"),
    )
    
    # Student
    student_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Transport assignment
    student_transport_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("student_transport.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Monthly fee amount
    monthly_fee: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    
    # Linked invoice (when generated)
    linked_invoice_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("fee_invoices.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Month and year
    fee_month: Mapped[int] = mapped_column(Integer, nullable=False)
    fee_year: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Payment status
    is_paid: Mapped[bool] = mapped_column(Boolean, default=False)
    paid_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
