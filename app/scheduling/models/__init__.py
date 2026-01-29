"""
CUSTOS Scheduling Models Init
"""

from app.scheduling.models.timetable import Timetable, TimetableEntry
from app.scheduling.models.schedule import ScheduleEntry, AcademicCalendarDay

__all__ = [
    "Timetable",
    "TimetableEntry",
    "ScheduleEntry",
    "AcademicCalendarDay",
]
