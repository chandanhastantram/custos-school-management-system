"""
CUSTOS Scheduling Repositories Init
"""

from app.scheduling.repositories.timetable_repo import TimetableRepository
from app.scheduling.repositories.schedule_repo import ScheduleRepository

__all__ = [
    "TimetableRepository",
    "ScheduleRepository",
]
