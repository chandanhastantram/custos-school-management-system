"""
CUSTOS Scheduling Routers Init
"""

from app.scheduling.routers.timetable import router as timetable_router
from app.scheduling.routers.schedule import router as schedule_router

__all__ = [
    "timetable_router",
    "schedule_router",
]
