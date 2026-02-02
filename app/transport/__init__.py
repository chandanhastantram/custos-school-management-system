"""
CUSTOS Transport Management Module

School transport, vehicles, drivers, routes, and student assignments.
"""

from app.transport.models import (
    Vehicle,
    Driver,
    Route,
    RouteStop,
    TransportAssignment,
    StudentTransport,
    TransportFeeLink,
    VehicleType,
    RouteShift,
)
from app.transport.service import TransportService
from app.transport.router import router as transport_router

__all__ = [
    # Models
    "Vehicle",
    "Driver",
    "Route",
    "RouteStop",
    "TransportAssignment",
    "StudentTransport",
    "TransportFeeLink",
    # Enums
    "VehicleType",
    "RouteShift",
    # Service
    "TransportService",
    # Router
    "transport_router",
]
