"""
CUSTOS Hostel / Boarding Management Module

Hostels, rooms, beds, wardens, and student assignments.
"""

from app.hostel.models import (
    Hostel,
    HostelRoom,
    Bed,
    Warden,
    StudentHostelAssignment,
    HostelFeeLink,
    HostelGender,
)
from app.hostel.service import HostelService
from app.hostel.router import router as hostel_router

__all__ = [
    # Models
    "Hostel",
    "HostelRoom",
    "Bed",
    "Warden",
    "StudentHostelAssignment",
    "HostelFeeLink",
    # Enums
    "HostelGender",
    # Service
    "HostelService",
    # Router
    "hostel_router",
]
