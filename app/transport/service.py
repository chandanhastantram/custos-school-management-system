"""
CUSTOS Transport Management Service

Business logic for transport operations.
"""

from datetime import datetime, date, timezone
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ResourceNotFoundError, ValidationError
from app.transport.models import (
    Vehicle, Driver, Route, RouteStop, TransportAssignment,
    StudentTransport, TransportFeeLink, VehicleType, RouteShift,
)
from app.transport.schemas import (
    VehicleCreate, VehicleUpdate,
    DriverCreate, DriverUpdate,
    RouteCreate, RouteUpdate, RouteStopCreate, RouteStopUpdate,
    TransportAssignmentCreate, TransportAssignmentUpdate,
    StudentTransportAssign, StudentTransportUnassign,
    RouteCapacityStatus, StudentTransportDetail,
    TransportFeeLinkCreate,
)


class TransportService:
    """Service for transport management operations."""
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
    
    # ============================================
    # Vehicle Management
    # ============================================
    
    async def create_vehicle(self, data: VehicleCreate) -> Vehicle:
        """Create a new vehicle."""
        # Check for duplicate vehicle number
        existing = await self._get_vehicle_by_number(data.vehicle_number)
        if existing:
            raise ValidationError(f"Vehicle with number {data.vehicle_number} already exists")
        
        vehicle = Vehicle(
            tenant_id=self.tenant_id,
            vehicle_number=data.vehicle_number,
            vehicle_type=data.vehicle_type,
            make=data.make,
            model=data.model,
            year=data.year,
            capacity=data.capacity,
            registration_number=data.registration_number,
            registration_expiry=data.registration_expiry,
            insurance_number=data.insurance_number,
            insurance_expiry=data.insurance_expiry,
            fitness_certificate=data.fitness_certificate,
            fitness_expiry=data.fitness_expiry,
            notes=data.notes,
        )
        
        self.session.add(vehicle)
        await self.session.commit()
        await self.session.refresh(vehicle)
        return vehicle
    
    async def update_vehicle(self, vehicle_id: UUID, data: VehicleUpdate) -> Vehicle:
        """Update a vehicle."""
        vehicle = await self.get_vehicle(vehicle_id)
        
        update_data = data.model_dump(exclude_unset=True)
        
        # Check for duplicate vehicle number if changing
        if "vehicle_number" in update_data:
            existing = await self._get_vehicle_by_number(update_data["vehicle_number"])
            if existing and existing.id != vehicle_id:
                raise ValidationError(f"Vehicle with number {update_data['vehicle_number']} already exists")
        
        for key, value in update_data.items():
            setattr(vehicle, key, value)
        
        await self.session.commit()
        await self.session.refresh(vehicle)
        return vehicle
    
    async def get_vehicle(self, vehicle_id: UUID) -> Vehicle:
        """Get a vehicle by ID."""
        query = select(Vehicle).where(
            Vehicle.tenant_id == self.tenant_id,
            Vehicle.id == vehicle_id,
            Vehicle.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        vehicle = result.scalar_one_or_none()
        
        if not vehicle:
            raise ResourceNotFoundError("Vehicle", str(vehicle_id))
        
        return vehicle
    
    async def _get_vehicle_by_number(self, vehicle_number: str) -> Optional[Vehicle]:
        """Get vehicle by vehicle number."""
        query = select(Vehicle).where(
            Vehicle.tenant_id == self.tenant_id,
            Vehicle.vehicle_number == vehicle_number,
            Vehicle.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def list_vehicles(
        self,
        active_only: bool = True,
        vehicle_type: Optional[VehicleType] = None,
        page: int = 1,
        size: int = 20,
    ) -> Tuple[List[Vehicle], int]:
        """List vehicles with filters."""
        query = select(Vehicle).where(
            Vehicle.tenant_id == self.tenant_id,
            Vehicle.deleted_at.is_(None),
        )
        
        if active_only:
            query = query.where(Vehicle.is_active == True)
        
        if vehicle_type:
            query = query.where(Vehicle.vehicle_type == vehicle_type)
        
        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.session.execute(count_query)).scalar() or 0
        
        # Pagination
        skip = (page - 1) * size
        query = query.order_by(Vehicle.vehicle_number).offset(skip).limit(size)
        
        result = await self.session.execute(query)
        return list(result.scalars().all()), total
    
    async def delete_vehicle(self, vehicle_id: UUID) -> None:
        """Soft delete a vehicle."""
        vehicle = await self.get_vehicle(vehicle_id)
        vehicle.deleted_at = datetime.now(timezone.utc)
        vehicle.is_active = False
        await self.session.commit()
    
    # ============================================
    # Driver Management
    # ============================================
    
    async def create_driver(self, data: DriverCreate) -> Driver:
        """Create a new driver."""
        # Check for duplicate license number
        existing = await self._get_driver_by_license(data.license_number)
        if existing:
            raise ValidationError(f"Driver with license {data.license_number} already exists")
        
        driver = Driver(
            tenant_id=self.tenant_id,
            name=data.name,
            phone=data.phone,
            alternate_phone=data.alternate_phone,
            email=data.email,
            address=data.address,
            license_number=data.license_number,
            license_type=data.license_type,
            license_expiry=data.license_expiry,
            emergency_contact_name=data.emergency_contact_name,
            emergency_contact_phone=data.emergency_contact_phone,
            blood_group=data.blood_group,
            photo_url=data.photo_url,
            notes=data.notes,
        )
        
        self.session.add(driver)
        await self.session.commit()
        await self.session.refresh(driver)
        return driver
    
    async def update_driver(self, driver_id: UUID, data: DriverUpdate) -> Driver:
        """Update a driver."""
        driver = await self.get_driver(driver_id)
        
        update_data = data.model_dump(exclude_unset=True)
        
        # Check for duplicate license if changing
        if "license_number" in update_data:
            existing = await self._get_driver_by_license(update_data["license_number"])
            if existing and existing.id != driver_id:
                raise ValidationError(f"Driver with license {update_data['license_number']} already exists")
        
        for key, value in update_data.items():
            setattr(driver, key, value)
        
        await self.session.commit()
        await self.session.refresh(driver)
        return driver
    
    async def get_driver(self, driver_id: UUID) -> Driver:
        """Get a driver by ID."""
        query = select(Driver).where(
            Driver.tenant_id == self.tenant_id,
            Driver.id == driver_id,
            Driver.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        driver = result.scalar_one_or_none()
        
        if not driver:
            raise ResourceNotFoundError("Driver", str(driver_id))
        
        return driver
    
    async def _get_driver_by_license(self, license_number: str) -> Optional[Driver]:
        """Get driver by license number."""
        query = select(Driver).where(
            Driver.tenant_id == self.tenant_id,
            Driver.license_number == license_number,
            Driver.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def list_drivers(
        self,
        active_only: bool = True,
        page: int = 1,
        size: int = 20,
    ) -> Tuple[List[Driver], int]:
        """List drivers with filters."""
        query = select(Driver).where(
            Driver.tenant_id == self.tenant_id,
            Driver.deleted_at.is_(None),
        )
        
        if active_only:
            query = query.where(Driver.is_active == True)
        
        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.session.execute(count_query)).scalar() or 0
        
        # Pagination
        skip = (page - 1) * size
        query = query.order_by(Driver.name).offset(skip).limit(size)
        
        result = await self.session.execute(query)
        return list(result.scalars().all()), total
    
    async def delete_driver(self, driver_id: UUID) -> None:
        """Soft delete a driver."""
        driver = await self.get_driver(driver_id)
        driver.deleted_at = datetime.now(timezone.utc)
        driver.is_active = False
        await self.session.commit()
    
    # ============================================
    # Route Management
    # ============================================
    
    async def create_route(self, data: RouteCreate) -> Route:
        """Create a new route."""
        # Check for duplicate route name
        existing = await self._get_route_by_name(data.name)
        if existing:
            raise ValidationError(f"Route with name '{data.name}' already exists")
        
        route = Route(
            tenant_id=self.tenant_id,
            name=data.name,
            code=data.code,
            description=data.description,
            shift=data.shift,
            distance_km=data.distance_km,
            estimated_duration_minutes=data.estimated_duration_minutes,
            start_location=data.start_location,
            end_location=data.end_location,
        )
        
        self.session.add(route)
        await self.session.commit()
        await self.session.refresh(route)
        return route
    
    async def update_route(self, route_id: UUID, data: RouteUpdate) -> Route:
        """Update a route."""
        route = await self.get_route(route_id)
        
        update_data = data.model_dump(exclude_unset=True)
        
        # Check for duplicate name if changing
        if "name" in update_data:
            existing = await self._get_route_by_name(update_data["name"])
            if existing and existing.id != route_id:
                raise ValidationError(f"Route with name '{update_data['name']}' already exists")
        
        for key, value in update_data.items():
            setattr(route, key, value)
        
        await self.session.commit()
        await self.session.refresh(route)
        return route
    
    async def get_route(self, route_id: UUID, include_stops: bool = True) -> Route:
        """Get a route by ID."""
        query = select(Route).where(
            Route.tenant_id == self.tenant_id,
            Route.id == route_id,
            Route.deleted_at.is_(None),
        )
        
        if include_stops:
            query = query.options(selectinload(Route.stops))
        
        result = await self.session.execute(query)
        route = result.scalar_one_or_none()
        
        if not route:
            raise ResourceNotFoundError("Route", str(route_id))
        
        return route
    
    async def _get_route_by_name(self, name: str) -> Optional[Route]:
        """Get route by name."""
        query = select(Route).where(
            Route.tenant_id == self.tenant_id,
            Route.name == name,
            Route.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def list_routes(
        self,
        active_only: bool = True,
        shift: Optional[RouteShift] = None,
        page: int = 1,
        size: int = 20,
    ) -> Tuple[List[Route], int]:
        """List routes with filters."""
        query = select(Route).where(
            Route.tenant_id == self.tenant_id,
            Route.deleted_at.is_(None),
        )
        
        if active_only:
            query = query.where(Route.is_active == True)
        
        if shift:
            query = query.where(or_(Route.shift == shift, Route.shift == RouteShift.BOTH))
        
        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.session.execute(count_query)).scalar() or 0
        
        # Pagination
        skip = (page - 1) * size
        query = query.options(selectinload(Route.stops)).order_by(Route.name).offset(skip).limit(size)
        
        result = await self.session.execute(query)
        return list(result.scalars().all()), total
    
    async def delete_route(self, route_id: UUID) -> None:
        """Soft delete a route."""
        route = await self.get_route(route_id)
        route.deleted_at = datetime.now(timezone.utc)
        route.is_active = False
        await self.session.commit()
    
    # ============================================
    # Route Stop Management
    # ============================================
    
    async def add_route_stops(
        self,
        route_id: UUID,
        stops: List[RouteStopCreate],
    ) -> List[RouteStop]:
        """Add multiple stops to a route."""
        route = await self.get_route(route_id, include_stops=False)
        
        created_stops = []
        for stop_data in stops:
            stop = RouteStop(
                tenant_id=self.tenant_id,
                route_id=route_id,
                stop_name=stop_data.stop_name,
                stop_address=stop_data.stop_address,
                latitude=stop_data.latitude,
                longitude=stop_data.longitude,
                pickup_time=stop_data.pickup_time,
                drop_time=stop_data.drop_time,
                stop_order=stop_data.stop_order,
                landmark=stop_data.landmark,
            )
            self.session.add(stop)
            created_stops.append(stop)
        
        await self.session.commit()
        
        for stop in created_stops:
            await self.session.refresh(stop)
        
        return created_stops
    
    async def update_route_stop(
        self,
        stop_id: UUID,
        data: RouteStopUpdate,
    ) -> RouteStop:
        """Update a route stop."""
        query = select(RouteStop).where(
            RouteStop.id == stop_id,
        )
        result = await self.session.execute(query)
        stop = result.scalar_one_or_none()
        
        if not stop:
            raise ResourceNotFoundError("RouteStop", str(stop_id))
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(stop, key, value)
        
        await self.session.commit()
        await self.session.refresh(stop)
        return stop
    
    async def delete_route_stop(self, stop_id: UUID) -> None:
        """Delete a route stop."""
        query = select(RouteStop).where(RouteStop.id == stop_id)
        result = await self.session.execute(query)
        stop = result.scalar_one_or_none()
        
        if not stop:
            raise ResourceNotFoundError("RouteStop", str(stop_id))
        
        await self.session.delete(stop)
        await self.session.commit()
    
    # ============================================
    # Transport Assignment (Route + Vehicle + Driver)
    # ============================================
    
    async def assign_vehicle_and_driver(
        self,
        data: TransportAssignmentCreate,
    ) -> TransportAssignment:
        """Assign a vehicle and driver to a route for an academic year."""
        # Validate route exists
        route = await self.get_route(data.route_id)
        
        # Validate vehicle exists
        vehicle = await self.get_vehicle(data.vehicle_id)
        
        # Validate driver exists
        driver = await self.get_driver(data.driver_id)
        
        # Check for existing active assignment
        query = select(TransportAssignment).where(
            TransportAssignment.tenant_id == self.tenant_id,
            TransportAssignment.route_id == data.route_id,
            TransportAssignment.academic_year_id == data.academic_year_id,
            TransportAssignment.shift == data.shift,
            TransportAssignment.is_active == True,
        )
        result = await self.session.execute(query)
        existing = result.scalar_one_or_none()
        
        if existing:
            raise ValidationError("Route already has an active assignment for this shift and year")
        
        assignment = TransportAssignment(
            tenant_id=self.tenant_id,
            route_id=data.route_id,
            vehicle_id=data.vehicle_id,
            driver_id=data.driver_id,
            academic_year_id=data.academic_year_id,
            shift=data.shift,
            helper_name=data.helper_name,
            helper_phone=data.helper_phone,
            notes=data.notes,
        )
        
        self.session.add(assignment)
        await self.session.commit()
        await self.session.refresh(assignment)
        return assignment
    
    async def update_transport_assignment(
        self,
        assignment_id: UUID,
        data: TransportAssignmentUpdate,
    ) -> TransportAssignment:
        """Update a transport assignment."""
        query = select(TransportAssignment).where(
            TransportAssignment.tenant_id == self.tenant_id,
            TransportAssignment.id == assignment_id,
        )
        result = await self.session.execute(query)
        assignment = result.scalar_one_or_none()
        
        if not assignment:
            raise ResourceNotFoundError("TransportAssignment", str(assignment_id))
        
        update_data = data.model_dump(exclude_unset=True)
        
        # Validate new vehicle/driver if provided
        if "vehicle_id" in update_data:
            await self.get_vehicle(update_data["vehicle_id"])
        if "driver_id" in update_data:
            await self.get_driver(update_data["driver_id"])
        
        for key, value in update_data.items():
            setattr(assignment, key, value)
        
        await self.session.commit()
        await self.session.refresh(assignment)
        return assignment
    
    async def list_transport_assignments(
        self,
        academic_year_id: Optional[UUID] = None,
        active_only: bool = True,
        page: int = 1,
        size: int = 20,
    ) -> Tuple[List[TransportAssignment], int]:
        """List transport assignments."""
        query = select(TransportAssignment).where(
            TransportAssignment.tenant_id == self.tenant_id,
        )
        
        if academic_year_id:
            query = query.where(TransportAssignment.academic_year_id == academic_year_id)
        
        if active_only:
            query = query.where(TransportAssignment.is_active == True)
        
        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.session.execute(count_query)).scalar() or 0
        
        # Pagination
        skip = (page - 1) * size
        query = query.offset(skip).limit(size)
        
        result = await self.session.execute(query)
        return list(result.scalars().all()), total
    
    # ============================================
    # Student Transport Assignment
    # ============================================
    
    async def assign_student_to_route(
        self,
        data: StudentTransportAssign,
    ) -> StudentTransport:
        """Assign a student to a transport route."""
        # Validate route exists
        route = await self.get_route(data.route_id)
        
        # Check route capacity
        capacity_status = await self.get_route_capacity_status(data.route_id)
        if capacity_status.available_seats <= 0:
            raise ValidationError(f"Route '{route.name}' is at full capacity")
        
        # Check if student already has active transport
        existing = await self._get_active_student_transport(data.student_id)
        if existing:
            raise ValidationError("Student already has an active transport assignment")
        
        # Validate stops belong to route
        if data.pickup_stop_id:
            await self._validate_stop_belongs_to_route(data.pickup_stop_id, data.route_id)
        if data.drop_stop_id:
            await self._validate_stop_belongs_to_route(data.drop_stop_id, data.route_id)
        
        student_transport = StudentTransport(
            tenant_id=self.tenant_id,
            student_id=data.student_id,
            route_id=data.route_id,
            pickup_stop_id=data.pickup_stop_id,
            drop_stop_id=data.drop_stop_id,
            assigned_from=data.assigned_from,
            assigned_to=data.assigned_to,
            academic_year_id=data.academic_year_id,
            guardian_name=data.guardian_name,
            guardian_phone=data.guardian_phone,
            notes=data.notes,
        )
        
        self.session.add(student_transport)
        await self.session.commit()
        await self.session.refresh(student_transport)
        return student_transport
    
    async def unassign_student(self, data: StudentTransportUnassign) -> None:
        """Unassign a student from transport."""
        assignment = await self._get_active_student_transport(data.student_id)
        
        if not assignment:
            raise ResourceNotFoundError("StudentTransport", str(data.student_id))
        
        unassign_date = data.unassign_date or date.today()
        assignment.assigned_to = unassign_date
        assignment.is_active = False
        
        await self.session.commit()
    
    async def _get_active_student_transport(
        self,
        student_id: UUID,
    ) -> Optional[StudentTransport]:
        """Get active transport assignment for a student."""
        query = select(StudentTransport).where(
            StudentTransport.tenant_id == self.tenant_id,
            StudentTransport.student_id == student_id,
            StudentTransport.is_active == True,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def _validate_stop_belongs_to_route(
        self,
        stop_id: UUID,
        route_id: UUID,
    ) -> None:
        """Validate a stop belongs to a route."""
        query = select(RouteStop).where(
            RouteStop.id == stop_id,
            RouteStop.route_id == route_id,
        )
        result = await self.session.execute(query)
        stop = result.scalar_one_or_none()
        
        if not stop:
            raise ValidationError(f"Stop does not belong to the specified route")
    
    async def get_route_capacity_status(self, route_id: UUID) -> RouteCapacityStatus:
        """Get capacity status for a route."""
        route = await self.get_route(route_id)
        
        # Get assigned vehicle capacity
        query = select(TransportAssignment).where(
            TransportAssignment.tenant_id == self.tenant_id,
            TransportAssignment.route_id == route_id,
            TransportAssignment.is_active == True,
        )
        result = await self.session.execute(query)
        assignment = result.scalar_one_or_none()
        
        vehicle_capacity = 0
        if assignment:
            vehicle = await self.get_vehicle(assignment.vehicle_id)
            vehicle_capacity = vehicle.capacity
        
        # Count assigned students
        count_query = select(func.count()).where(
            StudentTransport.tenant_id == self.tenant_id,
            StudentTransport.route_id == route_id,
            StudentTransport.is_active == True,
        )
        assigned_count = (await self.session.execute(count_query)).scalar() or 0
        
        available = max(0, vehicle_capacity - assigned_count)
        utilization = (assigned_count / vehicle_capacity * 100) if vehicle_capacity > 0 else 0
        
        return RouteCapacityStatus(
            route_id=route_id,
            route_name=route.name,
            vehicle_capacity=vehicle_capacity,
            assigned_students=assigned_count,
            available_seats=available,
            utilization_percentage=round(utilization, 2),
        )
    
    async def get_student_transport_detail(
        self,
        student_id: UUID,
    ) -> Optional[StudentTransportDetail]:
        """Get detailed transport info for a student (parent view)."""
        # Get student transport assignment
        assignment = await self._get_active_student_transport(student_id)
        
        if not assignment:
            return None
        
        # Get route
        route = await self.get_route(assignment.route_id)
        
        # Get transport assignment (vehicle + driver)
        query = select(TransportAssignment).where(
            TransportAssignment.tenant_id == self.tenant_id,
            TransportAssignment.route_id == assignment.route_id,
            TransportAssignment.is_active == True,
        )
        result = await self.session.execute(query)
        transport_assignment = result.scalar_one_or_none()
        
        vehicle = None
        driver = None
        if transport_assignment:
            vehicle = await self.get_vehicle(transport_assignment.vehicle_id)
            driver = await self.get_driver(transport_assignment.driver_id)
        
        # Get stops
        pickup_stop = None
        drop_stop = None
        if assignment.pickup_stop_id:
            query = select(RouteStop).where(RouteStop.id == assignment.pickup_stop_id)
            result = await self.session.execute(query)
            pickup_stop = result.scalar_one_or_none()
        if assignment.drop_stop_id:
            query = select(RouteStop).where(RouteStop.id == assignment.drop_stop_id)
            result = await self.session.execute(query)
            drop_stop = result.scalar_one_or_none()
        
        return StudentTransportDetail(
            student_id=student_id,
            student_name="",  # To be filled by caller with student name
            route_name=route.name,
            route_code=route.code,
            vehicle_number=vehicle.vehicle_number if vehicle else None,
            vehicle_type=vehicle.vehicle_type.value if vehicle else None,
            driver_name=driver.name if driver else None,
            driver_phone=driver.phone if driver else None,
            helper_name=transport_assignment.helper_name if transport_assignment else None,
            helper_phone=transport_assignment.helper_phone if transport_assignment else None,
            pickup_stop_name=pickup_stop.stop_name if pickup_stop else None,
            pickup_time=pickup_stop.pickup_time if pickup_stop else None,
            drop_stop_name=drop_stop.stop_name if drop_stop else None,
            drop_time=drop_stop.drop_time if drop_stop else None,
            guardian_name=assignment.guardian_name,
            guardian_phone=assignment.guardian_phone,
        )
    
    async def list_students_on_route(
        self,
        route_id: UUID,
        active_only: bool = True,
    ) -> List[StudentTransport]:
        """List all students assigned to a route."""
        query = select(StudentTransport).where(
            StudentTransport.tenant_id == self.tenant_id,
            StudentTransport.route_id == route_id,
        )
        
        if active_only:
            query = query.where(StudentTransport.is_active == True)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    # ============================================
    # Transport Fee Links (Optional)
    # ============================================
    
    async def create_transport_fee_link(
        self,
        data: TransportFeeLinkCreate,
    ) -> TransportFeeLink:
        """Create a transport fee link."""
        fee_link = TransportFeeLink(
            tenant_id=self.tenant_id,
            student_id=data.student_id,
            student_transport_id=data.student_transport_id,
            monthly_fee=data.monthly_fee,
            fee_month=data.fee_month,
            fee_year=data.fee_year,
        )
        
        self.session.add(fee_link)
        await self.session.commit()
        await self.session.refresh(fee_link)
        return fee_link
    
    async def get_student_transport_fees(
        self,
        student_id: UUID,
    ) -> List[TransportFeeLink]:
        """Get transport fees for a student."""
        query = select(TransportFeeLink).where(
            TransportFeeLink.tenant_id == self.tenant_id,
            TransportFeeLink.student_id == student_id,
        ).order_by(
            TransportFeeLink.fee_year.desc(),
            TransportFeeLink.fee_month.desc(),
        )
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
