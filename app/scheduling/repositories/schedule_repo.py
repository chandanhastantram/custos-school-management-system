"""
CUSTOS Schedule Repository

Data access layer for schedule entries and academic calendar.
"""

from datetime import date, timedelta
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import select, func, and_, or_, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundError, ValidationError
from app.scheduling.models.schedule import (
    ScheduleEntry, 
    AcademicCalendarDay, 
    ScheduleEntryStatus,
    CalendarDayType,
)


class ScheduleRepository:
    """Repository for schedule entry CRUD operations."""
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
    
    # ============================================
    # Academic Calendar Operations
    # ============================================
    
    async def create_calendar_day(self, **data) -> AcademicCalendarDay:
        """Create a calendar day entry."""
        day = AcademicCalendarDay(
            tenant_id=self.tenant_id,
            **data
        )
        self.session.add(day)
        await self.session.flush()
        await self.session.refresh(day)
        return day
    
    async def create_calendar_days_bulk(
        self, 
        academic_year_id: UUID,
        days_data: List[dict],
    ) -> List[AcademicCalendarDay]:
        """Create multiple calendar days at once."""
        created = []
        for data in days_data:
            day = AcademicCalendarDay(
                tenant_id=self.tenant_id,
                academic_year_id=academic_year_id,
                **data
            )
            self.session.add(day)
            created.append(day)
        await self.session.flush()
        return created
    
    async def get_calendar_day(
        self, 
        day_id: UUID,
    ) -> Optional[AcademicCalendarDay]:
        """Get calendar day by ID."""
        query = select(AcademicCalendarDay).where(
            AcademicCalendarDay.id == day_id,
            AcademicCalendarDay.tenant_id == self.tenant_id,
            AcademicCalendarDay.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_calendar_day_by_date(
        self, 
        academic_year_id: UUID,
        target_date: date,
    ) -> Optional[AcademicCalendarDay]:
        """Get calendar day by date."""
        query = select(AcademicCalendarDay).where(
            AcademicCalendarDay.tenant_id == self.tenant_id,
            AcademicCalendarDay.academic_year_id == academic_year_id,
            AcademicCalendarDay.date == target_date,
            AcademicCalendarDay.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_working_days(
        self,
        academic_year_id: UUID,
        start_date: date,
        end_date: date,
    ) -> List[date]:
        """
        Get list of working days in a date range.
        
        If no calendar entries exist, assumes Mon-Sat are working days.
        """
        # Check if we have calendar entries for this year
        calendar_query = select(AcademicCalendarDay).where(
            AcademicCalendarDay.tenant_id == self.tenant_id,
            AcademicCalendarDay.academic_year_id == academic_year_id,
            AcademicCalendarDay.date >= start_date,
            AcademicCalendarDay.date <= end_date,
            AcademicCalendarDay.deleted_at.is_(None),
        )
        result = await self.session.execute(calendar_query)
        calendar_days = {day.date: day for day in result.scalars().all()}
        
        working_days = []
        current = start_date
        
        while current <= end_date:
            if current in calendar_days:
                # Use calendar entry
                if calendar_days[current].is_working_day:
                    working_days.append(current)
            else:
                # Default: Mon-Sat are working (Sunday = 6)
                if current.weekday() != 6:  # Not Sunday
                    working_days.append(current)
            current += timedelta(days=1)
        
        return working_days
    
    async def list_calendar_days(
        self,
        academic_year_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        is_working_day: Optional[bool] = None,
    ) -> List[AcademicCalendarDay]:
        """List calendar days with filters."""
        query = select(AcademicCalendarDay).where(
            AcademicCalendarDay.tenant_id == self.tenant_id,
            AcademicCalendarDay.academic_year_id == academic_year_id,
            AcademicCalendarDay.deleted_at.is_(None),
        )
        
        if start_date:
            query = query.where(AcademicCalendarDay.date >= start_date)
        if end_date:
            query = query.where(AcademicCalendarDay.date <= end_date)
        if is_working_day is not None:
            query = query.where(AcademicCalendarDay.is_working_day == is_working_day)
        
        query = query.order_by(AcademicCalendarDay.date)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def update_calendar_day(
        self, 
        day_id: UUID, 
        **data,
    ) -> AcademicCalendarDay:
        """Update a calendar day."""
        day = await self.get_calendar_day(day_id)
        if not day:
            raise ResourceNotFoundError("AcademicCalendarDay", day_id)
        
        for key, value in data.items():
            if value is not None and hasattr(day, key):
                setattr(day, key, value)
        
        await self.session.flush()
        await self.session.refresh(day)
        return day
    
    async def delete_calendar_day(self, day_id: UUID) -> None:
        """Soft delete a calendar day."""
        day = await self.get_calendar_day(day_id)
        if not day:
            raise ResourceNotFoundError("AcademicCalendarDay", day_id)
        await day.soft_delete()
        await self.session.flush()
    
    # ============================================
    # Schedule Entry Operations
    # ============================================
    
    async def create_entry(self, **data) -> ScheduleEntry:
        """Create a schedule entry."""
        entry = ScheduleEntry(
            tenant_id=self.tenant_id,
            **data
        )
        self.session.add(entry)
        await self.session.flush()
        await self.session.refresh(entry)
        return entry
    
    async def create_entries_bulk(
        self, 
        entries_data: List[dict],
    ) -> List[ScheduleEntry]:
        """Create multiple schedule entries at once."""
        created = []
        for data in entries_data:
            entry = ScheduleEntry(
                tenant_id=self.tenant_id,
                **data
            )
            self.session.add(entry)
            created.append(entry)
        await self.session.flush()
        return created
    
    async def get_entry(self, entry_id: UUID) -> Optional[ScheduleEntry]:
        """Get schedule entry by ID."""
        query = select(ScheduleEntry).where(
            ScheduleEntry.id == entry_id,
            ScheduleEntry.tenant_id == self.tenant_id,
            ScheduleEntry.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def list_entries(
        self,
        lesson_plan_id: Optional[UUID] = None,
        class_id: Optional[UUID] = None,
        teacher_id: Optional[UUID] = None,
        subject_id: Optional[UUID] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        status: Optional[ScheduleEntryStatus] = None,
        page: int = 1,
        size: int = 100,
    ) -> Tuple[List[ScheduleEntry], int]:
        """List schedule entries with filtering and pagination."""
        query = select(ScheduleEntry).where(
            ScheduleEntry.tenant_id == self.tenant_id,
            ScheduleEntry.deleted_at.is_(None),
        )
        
        if lesson_plan_id:
            query = query.where(ScheduleEntry.lesson_plan_id == lesson_plan_id)
        if class_id:
            query = query.where(ScheduleEntry.class_id == class_id)
        if teacher_id:
            query = query.where(ScheduleEntry.teacher_id == teacher_id)
        if subject_id:
            query = query.where(ScheduleEntry.subject_id == subject_id)
        if start_date:
            query = query.where(ScheduleEntry.date >= start_date)
        if end_date:
            query = query.where(ScheduleEntry.date <= end_date)
        if status:
            query = query.where(ScheduleEntry.status == status)
        
        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.session.scalar(count_query) or 0
        
        # Paginate
        query = query.order_by(ScheduleEntry.date, ScheduleEntry.period_number)
        query = query.offset((page - 1) * size).limit(size)
        
        result = await self.session.execute(query)
        return list(result.scalars().all()), total
    
    async def get_entries_by_class_date(
        self,
        class_id: UUID,
        start_date: date,
        end_date: date,
        section_id: Optional[UUID] = None,
    ) -> List[ScheduleEntry]:
        """Get schedule entries for a class in date range."""
        query = select(ScheduleEntry).where(
            ScheduleEntry.tenant_id == self.tenant_id,
            ScheduleEntry.class_id == class_id,
            ScheduleEntry.date >= start_date,
            ScheduleEntry.date <= end_date,
            ScheduleEntry.deleted_at.is_(None),
        )
        
        if section_id:
            query = query.where(
                or_(
                    ScheduleEntry.section_id == section_id,
                    ScheduleEntry.section_id.is_(None),
                )
            )
        
        query = query.order_by(ScheduleEntry.date, ScheduleEntry.period_number)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_entries_by_teacher_date(
        self,
        teacher_id: UUID,
        start_date: date,
        end_date: date,
    ) -> List[ScheduleEntry]:
        """Get schedule entries for a teacher in date range."""
        query = select(ScheduleEntry).where(
            ScheduleEntry.tenant_id == self.tenant_id,
            ScheduleEntry.teacher_id == teacher_id,
            ScheduleEntry.date >= start_date,
            ScheduleEntry.date <= end_date,
            ScheduleEntry.deleted_at.is_(None),
        )
        
        query = query.order_by(ScheduleEntry.date, ScheduleEntry.period_number)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_entries_by_lesson_plan(
        self,
        lesson_plan_id: UUID,
    ) -> List[ScheduleEntry]:
        """Get all schedule entries for a lesson plan."""
        query = select(ScheduleEntry).where(
            ScheduleEntry.tenant_id == self.tenant_id,
            ScheduleEntry.lesson_plan_id == lesson_plan_id,
            ScheduleEntry.deleted_at.is_(None),
        )
        query = query.order_by(ScheduleEntry.date, ScheduleEntry.period_number)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def update_entry(self, entry_id: UUID, **data) -> ScheduleEntry:
        """Update a schedule entry."""
        entry = await self.get_entry(entry_id)
        if not entry:
            raise ResourceNotFoundError("ScheduleEntry", entry_id)
        
        for key, value in data.items():
            if value is not None and hasattr(entry, key):
                setattr(entry, key, value)
        
        await self.session.flush()
        await self.session.refresh(entry)
        return entry
    
    async def update_entry_status(
        self,
        entry_id: UUID,
        status: ScheduleEntryStatus,
        completed_by: Optional[UUID] = None,
    ) -> ScheduleEntry:
        """Update entry status."""
        from datetime import datetime
        
        entry = await self.get_entry(entry_id)
        if not entry:
            raise ResourceNotFoundError("ScheduleEntry", entry_id)
        
        entry.status = status
        if status == ScheduleEntryStatus.COMPLETED:
            entry.completed_at = datetime.utcnow()
            entry.completed_by = completed_by
        
        await self.session.flush()
        await self.session.refresh(entry)
        return entry
    
    async def delete_entry(self, entry_id: UUID) -> None:
        """Soft delete a schedule entry."""
        entry = await self.get_entry(entry_id)
        if not entry:
            raise ResourceNotFoundError("ScheduleEntry", entry_id)
        await entry.soft_delete()
        await self.session.flush()
    
    async def delete_entries_for_lesson_plan(
        self, 
        lesson_plan_id: UUID,
    ) -> int:
        """Delete all schedule entries for a lesson plan."""
        # Get entries first
        entries = await self.get_entries_by_lesson_plan(lesson_plan_id)
        count = 0
        for entry in entries:
            await entry.soft_delete()
            count += 1
        await self.session.flush()
        return count
    
    # ============================================
    # Stats
    # ============================================
    
    async def get_stats(
        self,
        lesson_plan_id: Optional[UUID] = None,
        class_id: Optional[UUID] = None,
        teacher_id: Optional[UUID] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> dict:
        """Get schedule statistics."""
        base_filter = and_(
            ScheduleEntry.tenant_id == self.tenant_id,
            ScheduleEntry.deleted_at.is_(None),
        )
        
        if lesson_plan_id:
            base_filter = and_(base_filter, ScheduleEntry.lesson_plan_id == lesson_plan_id)
        if class_id:
            base_filter = and_(base_filter, ScheduleEntry.class_id == class_id)
        if teacher_id:
            base_filter = and_(base_filter, ScheduleEntry.teacher_id == teacher_id)
        if start_date:
            base_filter = and_(base_filter, ScheduleEntry.date >= start_date)
        if end_date:
            base_filter = and_(base_filter, ScheduleEntry.date <= end_date)
        
        # Total entries
        total_query = select(func.count(ScheduleEntry.id)).where(base_filter)
        total = await self.session.scalar(total_query) or 0
        
        # By status
        planned = await self.session.scalar(
            select(func.count(ScheduleEntry.id)).where(
                base_filter, 
                ScheduleEntry.status == ScheduleEntryStatus.PLANNED
            )
        ) or 0
        
        completed = await self.session.scalar(
            select(func.count(ScheduleEntry.id)).where(
                base_filter, 
                ScheduleEntry.status == ScheduleEntryStatus.COMPLETED
            )
        ) or 0
        
        delayed = await self.session.scalar(
            select(func.count(ScheduleEntry.id)).where(
                base_filter, 
                ScheduleEntry.status == ScheduleEntryStatus.DELAYED
            )
        ) or 0
        
        skipped = await self.session.scalar(
            select(func.count(ScheduleEntry.id)).where(
                base_filter, 
                ScheduleEntry.status == ScheduleEntryStatus.SKIPPED
            )
        ) or 0
        
        completion_rate = completed / total if total > 0 else 0.0
        
        return {
            "total_entries": total,
            "planned_entries": planned,
            "completed_entries": completed,
            "delayed_entries": delayed,
            "skipped_entries": skipped,
            "completion_rate": round(completion_rate, 2),
        }
