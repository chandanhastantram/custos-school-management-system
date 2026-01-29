"""
CUSTOS Timetable Service

Business logic for timetable management.
"""

from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.scheduling.repositories.timetable_repo import TimetableRepository
from app.scheduling.models.timetable import Timetable, TimetableEntry, DAY_OF_WEEK_NAMES
from app.scheduling.schemas.timetable import (
    TimetableCreate,
    TimetableUpdate,
    TimetableEntryCreate,
    TimetableEntryBulkCreate,
    TimetableEntryUpdate,
    PeriodSlot,
    DaySchedule,
    ClassTimetableView,
    TeacherTimetableView,
    TimetableStats,
)


class TimetableService:
    """
    Timetable service.
    
    Handles:
    - Timetable CRUD
    - Entry management
    - Conflict validation
    - Timetable views (class/teacher)
    """
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
        self.repo = TimetableRepository(session, tenant_id)
    
    # ============================================
    # Timetable Operations
    # ============================================
    
    async def create_timetable(self, data: TimetableCreate) -> Timetable:
        """Create a new timetable."""
        return await self.repo.create_timetable(**data.model_dump())
    
    async def get_timetable(
        self, 
        timetable_id: UUID, 
        include_entries: bool = False,
    ) -> Optional[Timetable]:
        """Get timetable by ID."""
        return await self.repo.get_timetable(timetable_id, include_entries)
    
    async def list_timetables(
        self,
        academic_year_id: Optional[UUID] = None,
        is_active: Optional[bool] = None,
        page: int = 1,
        size: int = 20,
    ) -> Tuple[List[Timetable], int]:
        """List timetables with filtering."""
        return await self.repo.list_timetables(
            academic_year_id=academic_year_id,
            is_active=is_active,
            page=page,
            size=size,
        )
    
    async def update_timetable(
        self, 
        timetable_id: UUID, 
        data: TimetableUpdate,
    ) -> Timetable:
        """Update a timetable."""
        update_data = data.model_dump(exclude_unset=True)
        return await self.repo.update_timetable(timetable_id, **update_data)
    
    async def delete_timetable(self, timetable_id: UUID) -> None:
        """Soft delete a timetable."""
        await self.repo.delete_timetable(timetable_id)
    
    async def activate_timetable(self, timetable_id: UUID) -> Timetable:
        """Activate a timetable."""
        return await self.repo.update_timetable(timetable_id, is_active=True)
    
    async def deactivate_timetable(self, timetable_id: UUID) -> Timetable:
        """Deactivate a timetable."""
        return await self.repo.update_timetable(timetable_id, is_active=False)
    
    # ============================================
    # Entry Operations
    # ============================================
    
    async def add_entry(
        self, 
        timetable_id: UUID, 
        data: TimetableEntryCreate,
    ) -> TimetableEntry:
        """Add an entry to the timetable."""
        return await self.repo.create_entry(timetable_id, **data.model_dump())
    
    async def add_entries_bulk(
        self, 
        timetable_id: UUID, 
        data: TimetableEntryBulkCreate,
    ) -> List[TimetableEntry]:
        """Add multiple entries at once."""
        entries_data = [entry.model_dump() for entry in data.entries]
        return await self.repo.create_entries_bulk(timetable_id, entries_data)
    
    async def get_entry(self, entry_id: UUID) -> Optional[TimetableEntry]:
        """Get entry by ID."""
        return await self.repo.get_entry(entry_id)
    
    async def list_entries(
        self, 
        timetable_id: UUID,
        class_id: Optional[UUID] = None,
        teacher_id: Optional[UUID] = None,
        day_of_week: Optional[int] = None,
    ) -> List[TimetableEntry]:
        """List entries for a timetable."""
        return await self.repo.list_entries(
            timetable_id,
            class_id=class_id,
            teacher_id=teacher_id,
            day_of_week=day_of_week,
        )
    
    async def update_entry(
        self, 
        entry_id: UUID, 
        data: TimetableEntryUpdate,
    ) -> TimetableEntry:
        """Update an entry."""
        update_data = data.model_dump(exclude_unset=True)
        return await self.repo.update_entry(entry_id, **update_data)
    
    async def delete_entry(self, entry_id: UUID) -> None:
        """Soft delete an entry."""
        await self.repo.delete_entry(entry_id)
    
    # ============================================
    # View Methods
    # ============================================
    
    async def get_class_timetable(
        self,
        class_id: UUID,
        academic_year_id: UUID,
        section_id: Optional[UUID] = None,
        max_periods: int = 8,
    ) -> ClassTimetableView:
        """
        Get formatted timetable view for a class.
        
        Returns a structured view with days and periods.
        """
        entries = await self.repo.get_class_entries(
            class_id, academic_year_id, section_id
        )
        
        # Build schedule structure (6 days, configurable periods)
        schedule = []
        for day in range(6):  # Monday to Saturday
            periods = []
            for period in range(1, max_periods + 1):
                # Find entry for this slot
                entry = next(
                    (e for e in entries 
                     if e.day_of_week == day and e.period_number == period),
                    None
                )
                
                slot = PeriodSlot(
                    period_number=period,
                    subject_id=entry.subject_id if entry else None,
                    subject_name=None,  # TODO: Join with subject table
                    teacher_id=entry.teacher_id if entry else None,
                    teacher_name=None,  # TODO: Join with user table
                    room=entry.room if entry else None,
                    entry_id=entry.id if entry else None,
                )
                periods.append(slot)
            
            schedule.append(DaySchedule(
                day_of_week=day,
                day_name=DAY_OF_WEEK_NAMES[day],
                periods=periods,
            ))
        
        # Get timetable info (use first entry's timetable)
        timetable_id = entries[0].timetable_id if entries else None
        timetable_name = ""
        if timetable_id:
            timetable = await self.repo.get_timetable(timetable_id)
            timetable_name = timetable.name if timetable else ""
        
        return ClassTimetableView(
            class_id=class_id,
            class_name=None,  # TODO: Join with class table
            section_id=section_id,
            section_name=None,
            timetable_id=timetable_id,
            timetable_name=timetable_name,
            schedule=schedule,
        )
    
    async def get_teacher_timetable(
        self,
        teacher_id: UUID,
        academic_year_id: UUID,
        max_periods: int = 8,
    ) -> TeacherTimetableView:
        """
        Get formatted timetable view for a teacher.
        
        Shows all classes the teacher teaches across the week.
        """
        entries = await self.repo.get_teacher_entries(teacher_id, academic_year_id)
        
        # Build schedule structure
        schedule = []
        total_periods = 0
        
        for day in range(6):  # Monday to Saturday
            periods = []
            for period in range(1, max_periods + 1):
                # Find entry for this slot
                entry = next(
                    (e for e in entries 
                     if e.day_of_week == day and e.period_number == period),
                    None
                )
                
                if entry:
                    total_periods += 1
                
                slot = PeriodSlot(
                    period_number=period,
                    subject_id=entry.subject_id if entry else None,
                    subject_name=None,  # TODO: Join
                    class_id=entry.class_id if entry else None,
                    class_name=None,  # TODO: Join
                    room=entry.room if entry else None,
                    entry_id=entry.id if entry else None,
                )
                periods.append(slot)
            
            schedule.append(DaySchedule(
                day_of_week=day,
                day_name=DAY_OF_WEEK_NAMES[day],
                periods=periods,
            ))
        
        return TeacherTimetableView(
            teacher_id=teacher_id,
            teacher_name=None,  # TODO: Join with user table
            schedule=schedule,
            total_periods_per_week=total_periods,
        )
    
    # ============================================
    # Stats
    # ============================================
    
    async def get_stats(
        self, 
        academic_year_id: Optional[UUID] = None,
    ) -> TimetableStats:
        """Get timetable statistics."""
        stats = await self.repo.get_stats(academic_year_id)
        return TimetableStats(**stats)
