"""
CUSTOS Calendar Module

School calendar, events, and holidays.
"""

from app.calendar.models import CalendarEvent, EventType, EventScope
from app.calendar.service import CalendarService
from app.calendar.router import router as calendar_router

__all__ = [
    "CalendarEvent",
    "EventType",
    "EventScope",
    "CalendarService",
    "calendar_router",
]
