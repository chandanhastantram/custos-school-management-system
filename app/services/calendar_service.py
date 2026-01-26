"""
CUSTOS Calendar Service

Calendar events and timetable management.
"""

from datetime import datetime, date, time, timezone, timedelta
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundError, ValidationError
from app.models.calendar import (
    CalendarEvent, Timetable, TimetableSlot, Holiday,
    EventType, RecurrenceType, DayOfWeek
)
from app.schemas.calendar import EventCreate, TimetableCreate, TimetableSlotCreate


class CalendarService:
    """Calendar management service."""
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
    
    # ==================== Events ====================
    
    async def create_event(
        self,
        data: EventCreate,
        created_by: UUID,
    ) -> CalendarEvent:
        """Create calendar event."""
        event = CalendarEvent(
            tenant_id=self.tenant_id,
            created_by=created_by,
            title=data.title,
            description=data.description,
            event_type=data.event_type,
            start_date=data.start_date,
            end_date=data.end_date,
            start_time=data.start_time,
            end_time=data.end_time,
            is_all_day=data.is_all_day,
            location=data.location,
            color=data.color,
            recurrence=data.recurrence,
            recurrence_end=data.recurrence_end,
            is_public=data.is_public,
            target_roles=data.target_roles,
            target_sections=[str(s) for s in data.target_sections] if data.target_sections else None,
        )
        self.session.add(event)
        await self.session.commit()
        await self.session.refresh(event)
        return event
    
    async def get_events(
        self,
        start_date: date,
        end_date: date,
        event_type: Optional[EventType] = None,
        section_id: Optional[UUID] = None,
    ) -> List[CalendarEvent]:
        """Get events within date range."""
        query = select(CalendarEvent).where(
            CalendarEvent.tenant_id == self.tenant_id,
            CalendarEvent.start_date <= end_date,
            CalendarEvent.end_date >= start_date,
        )
        
        if event_type:
            query = query.where(CalendarEvent.event_type == event_type)
        
        query = query.order_by(CalendarEvent.start_date)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_event(self, event_id: UUID) -> CalendarEvent:
        """Get event by ID."""
        query = select(CalendarEvent).where(
            CalendarEvent.tenant_id == self.tenant_id,
            CalendarEvent.id == event_id
        )
        result = await self.session.execute(query)
        event = result.scalar_one_or_none()
        if not event:
            raise ResourceNotFoundError("Event", str(event_id))
        return event
    
    async def update_event(self, event_id: UUID, data: dict) -> CalendarEvent:
        """Update event."""
        event = await self.get_event(event_id)
        for key, value in data.items():
            if hasattr(event, key) and value is not None:
                setattr(event, key, value)
        await self.session.commit()
        await self.session.refresh(event)
        return event
    
    async def delete_event(self, event_id: UUID) -> bool:
        """Delete event."""
        event = await self.get_event(event_id)
        await self.session.delete(event)
        await self.session.commit()
        return True
    
    # ==================== Holidays ====================
    
    async def create_holiday(
        self,
        name: str,
        holiday_date: date,
        description: str = None,
    ) -> Holiday:
        """Create holiday."""
        holiday = Holiday(
            tenant_id=self.tenant_id,
            name=name,
            date=holiday_date,
            description=description,
        )
        self.session.add(holiday)
        await self.session.commit()
        await self.session.refresh(holiday)
        return holiday
    
    async def get_holidays(
        self,
        start_date: date,
        end_date: date,
    ) -> List[Holiday]:
        """Get holidays in date range."""
        query = select(Holiday).where(
            Holiday.tenant_id == self.tenant_id,
            Holiday.date >= start_date,
            Holiday.date <= end_date,
        ).order_by(Holiday.date)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def is_holiday(self, check_date: date) -> bool:
        """Check if date is a holiday."""
        query = select(Holiday).where(
            Holiday.tenant_id == self.tenant_id,
            Holiday.date == check_date,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None
    
    # ==================== Timetables ====================
    
    async def create_timetable(
        self,
        data: TimetableCreate,
    ) -> Timetable:
        """Create timetable with slots."""
        # Deactivate existing timetables for section
        existing = await self.session.execute(
            select(Timetable).where(
                Timetable.tenant_id == self.tenant_id,
                Timetable.section_id == data.section_id,
                Timetable.is_active == True
            )
        )
        for tt in existing.scalars():
            tt.is_active = False
            tt.effective_to = data.effective_from - timedelta(days=1)
        
        timetable = Timetable(
            tenant_id=self.tenant_id,
            section_id=data.section_id,
            academic_year_id=data.academic_year_id,
            name=data.name,
            effective_from=data.effective_from,
            is_active=True,
        )
        self.session.add(timetable)
        await self.session.flush()
        
        # Add slots
        for slot_data in data.slots:
            slot = TimetableSlot(
                tenant_id=self.tenant_id,
                timetable_id=timetable.id,
                day=slot_data.day,
                period_number=slot_data.period_number,
                start_time=slot_data.start_time,
                end_time=slot_data.end_time,
                subject_id=slot_data.subject_id,
                teacher_id=slot_data.teacher_id,
                room=slot_data.room,
                is_break=slot_data.is_break,
            )
            self.session.add(slot)
        
        await self.session.commit()
        await self.session.refresh(timetable)
        return timetable
    
    async def get_timetable(
        self,
        section_id: UUID,
        active_only: bool = True,
    ) -> Optional[Timetable]:
        """Get timetable for section."""
        query = select(Timetable).where(
            Timetable.tenant_id == self.tenant_id,
            Timetable.section_id == section_id,
        )
        if active_only:
            query = query.where(Timetable.is_active == True)
        query = query.order_by(Timetable.effective_from.desc())
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_timetable_slots(
        self,
        timetable_id: UUID,
        day: Optional[DayOfWeek] = None,
    ) -> List[TimetableSlot]:
        """Get timetable slots."""
        query = select(TimetableSlot).where(
            TimetableSlot.tenant_id == self.tenant_id,
            TimetableSlot.timetable_id == timetable_id,
        )
        if day:
            query = query.where(TimetableSlot.day == day)
        query = query.order_by(TimetableSlot.day, TimetableSlot.period_number)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_teacher_schedule(
        self,
        teacher_id: UUID,
        day: Optional[DayOfWeek] = None,
    ) -> List[TimetableSlot]:
        """Get teacher's schedule."""
        query = select(TimetableSlot).join(Timetable).where(
            TimetableSlot.tenant_id == self.tenant_id,
            TimetableSlot.teacher_id == teacher_id,
            Timetable.is_active == True,
        )
        if day:
            query = query.where(TimetableSlot.day == day)
        query = query.order_by(TimetableSlot.day, TimetableSlot.period_number)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_today_schedule(self, section_id: UUID) -> List[TimetableSlot]:
        """Get today's schedule for section."""
        today = datetime.now(timezone.utc).weekday()
        day_map = {
            0: DayOfWeek.MONDAY,
            1: DayOfWeek.TUESDAY,
            2: DayOfWeek.WEDNESDAY,
            3: DayOfWeek.THURSDAY,
            4: DayOfWeek.FRIDAY,
            5: DayOfWeek.SATURDAY,
            6: DayOfWeek.SUNDAY,
        }
        current_day = day_map[today]
        
        timetable = await self.get_timetable(section_id)
        if not timetable:
            return []
        
        return await self.get_timetable_slots(timetable.id, current_day)
