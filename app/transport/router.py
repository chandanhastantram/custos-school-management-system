"""
CUSTOS Transport Management Router

API endpoints for transport management.
"""

from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth.dependencies import CurrentUser, require_permission, require_role
from app.users.rbac import Permission, SystemRole
from app.transport.service import TransportService
from app.transport.models import VehicleType, RouteShift
from app.transport.schemas import (
    # Vehicle
    VehicleCreate, VehicleUpdate, VehicleResponse, VehicleListItem,
    # Driver
    DriverCreate, DriverUpdate, DriverResponse, DriverListItem,
    # Route
    RouteCreate, RouteUpdate, RouteResponse, RouteListItem,
    RouteStopCreate, RouteStopUpdate, RouteStopResponse,
    # Assignment
    TransportAssignmentCreate, TransportAssignmentUpdate, TransportAssignmentResponse,
    # Student Transport
    StudentTransportAssign, StudentTransportUnassign, StudentTransportResponse,
    StudentTransportDetail, RouteCapacityStatus,
    # Fee Link
    TransportFeeLinkCreate, TransportFeeLinkResponse,
)


router = APIRouter(tags=["Transport"])


# ============================================
# Vehicle Management
# ============================================

@router.post("/vehicles", response_model=VehicleResponse, status_code=201)
async def create_vehicle(
    data: VehicleCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.TRANSPORT_MANAGE)),
):
    """
    Create a new transport vehicle.
    
    Requires TRANSPORT_MANAGE permission.
    """
    service = TransportService(db, user.tenant_id)
    vehicle = await service.create_vehicle(data)
    return VehicleResponse.model_validate(vehicle)


@router.get("/vehicles", response_model=List[VehicleListItem])
async def list_vehicles(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    active_only: bool = True,
    vehicle_type: Optional[VehicleType] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=50),
    _=Depends(require_permission(Permission.TRANSPORT_VIEW)),
):
    """List all vehicles."""
    service = TransportService(db, user.tenant_id)
    vehicles, _ = await service.list_vehicles(active_only, vehicle_type, page, size)
    
    return [
        VehicleListItem(
            id=v.id,
            vehicle_number=v.vehicle_number,
            vehicle_type=v.vehicle_type,
            capacity=v.capacity,
            is_active=v.is_active,
        )
        for v in vehicles
    ]


@router.get("/vehicles/{vehicle_id}", response_model=VehicleResponse)
async def get_vehicle(
    vehicle_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.TRANSPORT_VIEW)),
):
    """Get a vehicle by ID."""
    service = TransportService(db, user.tenant_id)
    vehicle = await service.get_vehicle(vehicle_id)
    return VehicleResponse.model_validate(vehicle)


@router.patch("/vehicles/{vehicle_id}", response_model=VehicleResponse)
async def update_vehicle(
    vehicle_id: UUID,
    data: VehicleUpdate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.TRANSPORT_MANAGE)),
):
    """Update a vehicle."""
    service = TransportService(db, user.tenant_id)
    vehicle = await service.update_vehicle(vehicle_id, data)
    return VehicleResponse.model_validate(vehicle)


@router.delete("/vehicles/{vehicle_id}")
async def delete_vehicle(
    vehicle_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.TRANSPORT_MANAGE)),
):
    """Delete a vehicle (soft delete)."""
    service = TransportService(db, user.tenant_id)
    await service.delete_vehicle(vehicle_id)
    return {"success": True, "message": "Vehicle deleted"}


# ============================================
# Driver Management
# ============================================

@router.post("/drivers", response_model=DriverResponse, status_code=201)
async def create_driver(
    data: DriverCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.TRANSPORT_MANAGE)),
):
    """
    Create a new driver.
    
    Requires TRANSPORT_MANAGE permission.
    """
    service = TransportService(db, user.tenant_id)
    driver = await service.create_driver(data)
    return DriverResponse.model_validate(driver)


@router.get("/drivers", response_model=List[DriverListItem])
async def list_drivers(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    active_only: bool = True,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=50),
    _=Depends(require_permission(Permission.TRANSPORT_VIEW)),
):
    """List all drivers."""
    service = TransportService(db, user.tenant_id)
    drivers, _ = await service.list_drivers(active_only, page, size)
    
    return [
        DriverListItem(
            id=d.id,
            name=d.name,
            phone=d.phone,
            license_number=d.license_number,
            is_active=d.is_active,
        )
        for d in drivers
    ]


@router.get("/drivers/{driver_id}", response_model=DriverResponse)
async def get_driver(
    driver_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.TRANSPORT_VIEW)),
):
    """Get a driver by ID."""
    service = TransportService(db, user.tenant_id)
    driver = await service.get_driver(driver_id)
    return DriverResponse.model_validate(driver)


@router.patch("/drivers/{driver_id}", response_model=DriverResponse)
async def update_driver(
    driver_id: UUID,
    data: DriverUpdate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.TRANSPORT_MANAGE)),
):
    """Update a driver."""
    service = TransportService(db, user.tenant_id)
    driver = await service.update_driver(driver_id, data)
    return DriverResponse.model_validate(driver)


@router.delete("/drivers/{driver_id}")
async def delete_driver(
    driver_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.TRANSPORT_MANAGE)),
):
    """Delete a driver (soft delete)."""
    service = TransportService(db, user.tenant_id)
    await service.delete_driver(driver_id)
    return {"success": True, "message": "Driver deleted"}


# ============================================
# Route Management
# ============================================

@router.post("/routes", response_model=RouteResponse, status_code=201)
async def create_route(
    data: RouteCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.TRANSPORT_MANAGE)),
):
    """
    Create a new transport route.
    
    Requires TRANSPORT_MANAGE permission.
    """
    service = TransportService(db, user.tenant_id)
    route = await service.create_route(data)
    return RouteResponse.model_validate(route)


@router.get("/routes", response_model=List[RouteListItem])
async def list_routes(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    active_only: bool = True,
    shift: Optional[RouteShift] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=50),
    _=Depends(require_permission(Permission.TRANSPORT_VIEW)),
):
    """List all routes."""
    service = TransportService(db, user.tenant_id)
    routes, _ = await service.list_routes(active_only, shift, page, size)
    
    return [
        RouteListItem(
            id=r.id,
            name=r.name,
            code=r.code,
            shift=r.shift,
            is_active=r.is_active,
            stops_count=len(r.stops) if r.stops else 0,
        )
        for r in routes
    ]


@router.get("/routes/{route_id}", response_model=RouteResponse)
async def get_route(
    route_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.TRANSPORT_VIEW)),
):
    """Get a route by ID with stops."""
    service = TransportService(db, user.tenant_id)
    route = await service.get_route(route_id)
    return RouteResponse.model_validate(route)


@router.patch("/routes/{route_id}", response_model=RouteResponse)
async def update_route(
    route_id: UUID,
    data: RouteUpdate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.TRANSPORT_MANAGE)),
):
    """Update a route."""
    service = TransportService(db, user.tenant_id)
    route = await service.update_route(route_id, data)
    return RouteResponse.model_validate(route)


@router.delete("/routes/{route_id}")
async def delete_route(
    route_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.TRANSPORT_MANAGE)),
):
    """Delete a route (soft delete)."""
    service = TransportService(db, user.tenant_id)
    await service.delete_route(route_id)
    return {"success": True, "message": "Route deleted"}


@router.get("/routes/{route_id}/capacity", response_model=RouteCapacityStatus)
async def get_route_capacity(
    route_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.TRANSPORT_VIEW)),
):
    """Get capacity status for a route."""
    service = TransportService(db, user.tenant_id)
    return await service.get_route_capacity_status(route_id)


# ============================================
# Route Stops
# ============================================

@router.post("/routes/{route_id}/stops", response_model=List[RouteStopResponse], status_code=201)
async def add_route_stops(
    route_id: UUID,
    stops: List[RouteStopCreate],
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.TRANSPORT_MANAGE)),
):
    """
    Add stops to a route.
    
    Pass an array of stops with their order.
    """
    service = TransportService(db, user.tenant_id)
    created_stops = await service.add_route_stops(route_id, stops)
    return [RouteStopResponse.model_validate(s) for s in created_stops]


@router.patch("/stops/{stop_id}", response_model=RouteStopResponse)
async def update_route_stop(
    stop_id: UUID,
    data: RouteStopUpdate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.TRANSPORT_MANAGE)),
):
    """Update a route stop."""
    service = TransportService(db, user.tenant_id)
    stop = await service.update_route_stop(stop_id, data)
    return RouteStopResponse.model_validate(stop)


@router.delete("/stops/{stop_id}")
async def delete_route_stop(
    stop_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.TRANSPORT_MANAGE)),
):
    """Delete a route stop."""
    service = TransportService(db, user.tenant_id)
    await service.delete_route_stop(stop_id)
    return {"success": True, "message": "Stop deleted"}


# ============================================
# Transport Assignments (Vehicle + Driver + Route)
# ============================================

@router.post("/assignments", response_model=TransportAssignmentResponse, status_code=201)
async def create_transport_assignment(
    data: TransportAssignmentCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.TRANSPORT_MANAGE)),
):
    """
    Assign a vehicle and driver to a route.
    
    This creates the link between route, vehicle, and driver for an academic year.
    """
    service = TransportService(db, user.tenant_id)
    assignment = await service.assign_vehicle_and_driver(data)
    
    # Get denormalized data
    route = await service.get_route(assignment.route_id)
    vehicle = await service.get_vehicle(assignment.vehicle_id)
    driver = await service.get_driver(assignment.driver_id)
    
    return TransportAssignmentResponse(
        id=assignment.id,
        tenant_id=assignment.tenant_id,
        route_id=assignment.route_id,
        vehicle_id=assignment.vehicle_id,
        driver_id=assignment.driver_id,
        academic_year_id=assignment.academic_year_id,
        shift=assignment.shift,
        helper_name=assignment.helper_name,
        helper_phone=assignment.helper_phone,
        is_active=assignment.is_active,
        notes=assignment.notes,
        created_at=assignment.created_at,
        route_name=route.name,
        vehicle_number=vehicle.vehicle_number,
        driver_name=driver.name,
    )


@router.get("/assignments", response_model=List[TransportAssignmentResponse])
async def list_transport_assignments(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    academic_year_id: Optional[UUID] = None,
    active_only: bool = True,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=50),
    _=Depends(require_permission(Permission.TRANSPORT_VIEW)),
):
    """List all transport assignments."""
    service = TransportService(db, user.tenant_id)
    assignments, _ = await service.list_transport_assignments(
        academic_year_id, active_only, page, size
    )
    
    results = []
    for a in assignments:
        route = await service.get_route(a.route_id)
        vehicle = await service.get_vehicle(a.vehicle_id)
        driver = await service.get_driver(a.driver_id)
        
        results.append(TransportAssignmentResponse(
            id=a.id,
            tenant_id=a.tenant_id,
            route_id=a.route_id,
            vehicle_id=a.vehicle_id,
            driver_id=a.driver_id,
            academic_year_id=a.academic_year_id,
            shift=a.shift,
            helper_name=a.helper_name,
            helper_phone=a.helper_phone,
            is_active=a.is_active,
            notes=a.notes,
            created_at=a.created_at,
            route_name=route.name,
            vehicle_number=vehicle.vehicle_number,
            driver_name=driver.name,
        ))
    
    return results


@router.patch("/assignments/{assignment_id}", response_model=TransportAssignmentResponse)
async def update_transport_assignment(
    assignment_id: UUID,
    data: TransportAssignmentUpdate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.TRANSPORT_MANAGE)),
):
    """Update a transport assignment."""
    service = TransportService(db, user.tenant_id)
    assignment = await service.update_transport_assignment(assignment_id, data)
    
    route = await service.get_route(assignment.route_id)
    vehicle = await service.get_vehicle(assignment.vehicle_id)
    driver = await service.get_driver(assignment.driver_id)
    
    return TransportAssignmentResponse(
        id=assignment.id,
        tenant_id=assignment.tenant_id,
        route_id=assignment.route_id,
        vehicle_id=assignment.vehicle_id,
        driver_id=assignment.driver_id,
        academic_year_id=assignment.academic_year_id,
        shift=assignment.shift,
        helper_name=assignment.helper_name,
        helper_phone=assignment.helper_phone,
        is_active=assignment.is_active,
        notes=assignment.notes,
        created_at=assignment.created_at,
        route_name=route.name,
        vehicle_number=vehicle.vehicle_number,
        driver_name=driver.name,
    )


# ============================================
# Student Transport Assignment
# ============================================

@router.post("/students/assign", response_model=StudentTransportResponse, status_code=201)
async def assign_student_to_transport(
    data: StudentTransportAssign,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.TRANSPORT_ASSIGN)),
):
    """
    Assign a student to a transport route.
    
    Validates:
    - Route exists and has capacity
    - Student not already assigned
    - Stops belong to the route
    """
    service = TransportService(db, user.tenant_id)
    assignment = await service.assign_student_to_route(data)
    return StudentTransportResponse.model_validate(assignment)


@router.post("/students/unassign")
async def unassign_student_from_transport(
    data: StudentTransportUnassign,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.TRANSPORT_ASSIGN)),
):
    """Unassign a student from transport."""
    service = TransportService(db, user.tenant_id)
    await service.unassign_student(data)
    return {"success": True, "message": "Student unassigned from transport"}


@router.get("/students/route/{route_id}", response_model=List[StudentTransportResponse])
async def list_students_on_route(
    route_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    active_only: bool = True,
    _=Depends(require_permission(Permission.TRANSPORT_VIEW)),
):
    """List all students assigned to a route."""
    service = TransportService(db, user.tenant_id)
    assignments = await service.list_students_on_route(route_id, active_only)
    return [StudentTransportResponse.model_validate(a) for a in assignments]


# ============================================
# Parent / Student View
# ============================================

@router.get("/my-child/{student_id}", response_model=StudentTransportDetail)
async def get_child_transport_detail(
    student_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """
    Get transport details for a child.
    
    Available to parents viewing their children.
    """
    # Verify parent has access to this student
    # In production, validate parent-child relationship
    if SystemRole.PARENT.value not in user.roles and SystemRole.STUDENT.value not in user.roles:
        if SystemRole.TEACHER.value not in user.roles and SystemRole.PRINCIPAL.value not in user.roles:
            raise HTTPException(status_code=403, detail="Access denied")
    
    service = TransportService(db, user.tenant_id)
    detail = await service.get_student_transport_detail(student_id)
    
    if not detail:
        raise HTTPException(status_code=404, detail="No transport assignment found")
    
    return detail


# ============================================
# Transport Fee Links
# ============================================

@router.post("/fees", response_model=TransportFeeLinkResponse, status_code=201)
async def create_transport_fee_link(
    data: TransportFeeLinkCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.TRANSPORT_MANAGE)),
):
    """Create a transport fee link for billing."""
    service = TransportService(db, user.tenant_id)
    fee_link = await service.create_transport_fee_link(data)
    return TransportFeeLinkResponse.model_validate(fee_link)


@router.get("/fees/student/{student_id}", response_model=List[TransportFeeLinkResponse])
async def get_student_transport_fees(
    student_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.TRANSPORT_VIEW)),
):
    """Get transport fees for a student."""
    service = TransportService(db, user.tenant_id)
    fees = await service.get_student_transport_fees(student_id)
    return [TransportFeeLinkResponse.model_validate(f) for f in fees]
