"""
CUSTOS Calendar Service

Business logic for school calendar.
"""

from datetime import datetime, date, timezone
from calendar import monthrange
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundError
from app.calendar.models import CalendarEvent, EventType, EventScope
from app.calendar.schemas import EventCreate, EventUpdate


class CalendarService:
    """Service for school calendar management."""
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
    
    async def create_event(
        self,
        data: EventCreate,
        created_by: UUID,
    ) -> CalendarEvent:
        """Create a calendar event."""
        event = CalendarEvent(
            tenant_id=self.tenant_id,
            title=data.title,
            description=data.description,
            event_type=data.event_type,
            scope=data.scope,
            target_class_ids=[str(c) for c in data.target_class_ids] if data.target_class_ids else None,
            target_section_ids=[str(s) for s in data.target_section_ids] if data.target_section_ids else None,
            start_date=data.start_date,
            end_date=data.end_date or data.start_date,
            start_time=data.start_time,
            end_time=data.end_time,
            is_all_day=data.is_all_day,
            is_holiday=data.is_holiday,
            location=data.location,
            color=data.color,
            is_recurring=data.is_recurring,
            recurrence_pattern=data.recurrence_pattern,
            academic_year_id=data.academic_year_id,
            created_by=created_by,
        )
        
        self.session.add(event)
        await self.session.commit()
        await self.session.refresh(event)
        return event
    
    async def update_event(
        self,
        event_id: UUID,
        data: EventUpdate,
    ) -> CalendarEvent:
        """Update a calendar event."""
        event = await self.get_event(event_id)
        
        update_data = data.model_dump(exclude_unset=True)
        
        if "target_class_ids" in update_data and update_data["target_class_ids"]:
            update_data["target_class_ids"] = [str(c) for c in update_data["target_class_ids"]]
        if "target_section_ids" in update_data and update_data["target_section_ids"]:
            update_data["target_section_ids"] = [str(s) for s in update_data["target_section_ids"]]
        
        for key, value in update_data.items():
            if value is not None:
                setattr(event, key, value)
        
        await self.session.commit()
        await self.session.refresh(event)
        return event
    
    async def get_event(self, event_id: UUID) -> CalendarEvent:
        """Get event by ID."""
        query = select(CalendarEvent).where(
            CalendarEvent.tenant_id == self.tenant_id,
            CalendarEvent.id == event_id,
        )
        result = await self.session.execute(query)
        event = result.scalar_one_or_none()
        
        if not event:
            raise ResourceNotFoundError("CalendarEvent", str(event_id))
        
        return event
    
    async def list_events(
        self,
        start_date: date,
        end_date: date,
        event_type: Optional[EventType] = None,
        published_only: bool = True,
    ) -> List[CalendarEvent]:
        """List events within date range."""
        query = select(CalendarEvent).where(
            CalendarEvent.tenant_id == self.tenant_id,
            or_(
                and_(
                    CalendarEvent.start_date >= start_date,
                    CalendarEvent.start_date <= end_date,
                ),
                and_(
                    CalendarEvent.end_date >= start_date,
                    CalendarEvent.end_date <= end_date,
                ),
                and_(
                    CalendarEvent.start_date <= start_date,
                    CalendarEvent.end_date >= end_date,
                ),
            ),
        )
        
        if published_only:
            query = query.where(CalendarEvent.is_published == True)
        
        if event_type:
            query = query.where(CalendarEvent.event_type == event_type)
        
        query = query.order_by(CalendarEvent.start_date)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_monthly_events(
        self,
        year: int,
        month: int,
    ) -> List[CalendarEvent]:
        """Get events for a specific month."""
        start_date = date(year, month, 1)
        _, last_day = monthrange(year, month)
        end_date = date(year, month, last_day)
        
        return await self.list_events(start_date, end_date)
    
    async def get_holidays(
        self,
        start_date: date,
        end_date: date,
    ) -> List[date]:
        """Get list of holiday dates within range."""
        query = select(CalendarEvent).where(
            CalendarEvent.tenant_id == self.tenant_id,
            CalendarEvent.is_holiday == True,
            CalendarEvent.is_published == True,
            CalendarEvent.start_date <= end_date,
            or_(
                CalendarEvent.end_date >= start_date,
                CalendarEvent.end_date.is_(None),
            ),
        )
        
        result = await self.session.execute(query)
        events = result.scalars().all()
        
        holidays = []
        for event in events:
            current = event.start_date
            event_end = event.end_date or event.start_date
            while current <= event_end and current <= end_date:
                if current >= start_date:
                    holidays.append(current)
                from datetime import timedelta
                current = current + timedelta(days=1)
        
        return sorted(set(holidays))
    
    async def delete_event(self, event_id: UUID) -> None:
        """Delete a calendar event."""
        event = await self.get_event(event_id)
        await self.session.delete(event)
        await self.session.commit()
    
    async def get_upcoming_events(
        self,
        limit: int = 10,
        event_type: Optional[EventType] = None,
    ) -> List[CalendarEvent]:
        """Get upcoming events from today."""
        today = date.today()
        
        query = select(CalendarEvent).where(
            CalendarEvent.tenant_id == self.tenant_id,
            CalendarEvent.is_published == True,
            or_(
                CalendarEvent.start_date >= today,
                CalendarEvent.end_date >= today,
            ),
        )
        
        if event_type:
            query = query.where(CalendarEvent.event_type == event_type)
        
        query = query.order_by(CalendarEvent.start_date).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
