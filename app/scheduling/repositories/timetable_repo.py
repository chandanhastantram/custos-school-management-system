"""
CUSTOS Timetable Repository

Data access layer for timetables and entries.
"""

from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import select, func, and_, or_, exists
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ResourceNotFoundError, DuplicateError, ValidationError
from app.scheduling.models.timetable import Timetable, TimetableEntry, DAY_OF_WEEK_NAMES
from app.academics.models.teaching_assignments import TeachingAssignment


class TimetableRepository:
    """Repository for timetable CRUD operations."""
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
    
    # ============================================
    # Timetable Operations
    # ============================================
    
    async def create_timetable(self, **data) -> Timetable:
        """Create a new timetable."""
        timetable = Timetable(
            tenant_id=self.tenant_id,
            **data
        )
        self.session.add(timetable)
        await self.session.flush()
        await self.session.refresh(timetable)
        return timetable
    
    async def get_timetable(
        self, 
        timetable_id: UUID, 
        include_entries: bool = False,
    ) -> Optional[Timetable]:
        """Get timetable by ID."""
        query = select(Timetable).where(
            Timetable.id == timetable_id,
            Timetable.tenant_id == self.tenant_id,
            Timetable.deleted_at.is_(None),
        )
        
        if include_entries:
            query = query.options(selectinload(Timetable.entries))
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def list_timetables(
        self,
        academic_year_id: Optional[UUID] = None,
        is_active: Optional[bool] = None,
        page: int = 1,
        size: int = 20,
    ) -> Tuple[List[Timetable], int]:
        """List timetables with filtering and pagination."""
        query = select(Timetable).where(
            Timetable.tenant_id == self.tenant_id,
            Timetable.deleted_at.is_(None),
        )
        
        if academic_year_id:
            query = query.where(Timetable.academic_year_id == academic_year_id)
        if is_active is not None:
            query = query.where(Timetable.is_active == is_active)
        
        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.session.scalar(count_query) or 0
        
        # Paginate
        query = query.order_by(Timetable.created_at.desc())
        query = query.offset((page - 1) * size).limit(size)
        
        result = await self.session.execute(query)
        return list(result.scalars().all()), total
    
    async def update_timetable(self, timetable_id: UUID, **data) -> Timetable:
        """Update a timetable."""
        timetable = await self.get_timetable(timetable_id)
        if not timetable:
            raise ResourceNotFoundError("Timetable", timetable_id)
        
        for key, value in data.items():
            if value is not None and hasattr(timetable, key):
                setattr(timetable, key, value)
        
        await self.session.flush()
        await self.session.refresh(timetable)
        return timetable
    
    async def delete_timetable(self, timetable_id: UUID) -> None:
        """Soft delete a timetable."""
        timetable = await self.get_timetable(timetable_id)
        if not timetable:
            raise ResourceNotFoundError("Timetable", timetable_id)
        
        await timetable.soft_delete()
        await self.session.flush()
    
    # ============================================
    # TimetableEntry Operations
    # ============================================
    
    async def create_entry(self, timetable_id: UUID, **data) -> TimetableEntry:
        """Create a new timetable entry."""
        # Verify timetable exists
        timetable = await self.get_timetable(timetable_id)
        if not timetable:
            raise ResourceNotFoundError("Timetable", timetable_id)
        
        # Check for conflicts
        await self._check_conflicts(timetable_id, data)
        
        # Validate teaching assignment exists
        await self._validate_teaching_assignment(
            teacher_id=data["teacher_id"],
            class_id=data["class_id"],
            subject_id=data["subject_id"],
            academic_year_id=timetable.academic_year_id,
        )
        
        entry = TimetableEntry(
            tenant_id=self.tenant_id,
            timetable_id=timetable_id,
            **data
        )
        self.session.add(entry)
        await self.session.flush()
        await self.session.refresh(entry)
        return entry
    
    async def create_entries_bulk(
        self, 
        timetable_id: UUID, 
        entries_data: List[dict],
    ) -> List[TimetableEntry]:
        """Create multiple entries at once."""
        timetable = await self.get_timetable(timetable_id)
        if not timetable:
            raise ResourceNotFoundError("Timetable", timetable_id)
        
        created = []
        for data in entries_data:
            try:
                entry = await self.create_entry(timetable_id, **data)
                created.append(entry)
            except (DuplicateError, ValidationError):
                # Skip invalid entries in bulk mode
                continue
        
        return created
    
    async def get_entry(self, entry_id: UUID) -> Optional[TimetableEntry]:
        """Get entry by ID."""
        query = select(TimetableEntry).where(
            TimetableEntry.id == entry_id,
            TimetableEntry.tenant_id == self.tenant_id,
            TimetableEntry.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def list_entries(
        self, 
        timetable_id: UUID,
        class_id: Optional[UUID] = None,
        teacher_id: Optional[UUID] = None,
        day_of_week: Optional[int] = None,
    ) -> List[TimetableEntry]:
        """List entries for a timetable with optional filters."""
        query = select(TimetableEntry).where(
            TimetableEntry.timetable_id == timetable_id,
            TimetableEntry.tenant_id == self.tenant_id,
            TimetableEntry.deleted_at.is_(None),
        )
        
        if class_id:
            query = query.where(TimetableEntry.class_id == class_id)
        if teacher_id:
            query = query.where(TimetableEntry.teacher_id == teacher_id)
        if day_of_week is not None:
            query = query.where(TimetableEntry.day_of_week == day_of_week)
        
        query = query.order_by(
            TimetableEntry.day_of_week,
            TimetableEntry.period_number,
        )
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def update_entry(self, entry_id: UUID, **data) -> TimetableEntry:
        """Update a timetable entry."""
        entry = await self.get_entry(entry_id)
        if not entry:
            raise ResourceNotFoundError("TimetableEntry", entry_id)
        
        # If changing teacher or subject, validate teaching assignment
        if "teacher_id" in data or "subject_id" in data:
            timetable = await self.get_timetable(entry.timetable_id)
            await self._validate_teaching_assignment(
                teacher_id=data.get("teacher_id", entry.teacher_id),
                class_id=entry.class_id,
                subject_id=data.get("subject_id", entry.subject_id),
                academic_year_id=timetable.academic_year_id,
            )
        
        for key, value in data.items():
            if value is not None and hasattr(entry, key):
                setattr(entry, key, value)
        
        await self.session.flush()
        await self.session.refresh(entry)
        return entry
    
    async def delete_entry(self, entry_id: UUID) -> None:
        """Soft delete an entry."""
        entry = await self.get_entry(entry_id)
        if not entry:
            raise ResourceNotFoundError("TimetableEntry", entry_id)
        
        await entry.soft_delete()
        await self.session.flush()
    
    # ============================================
    # View Methods
    # ============================================
    
    async def get_class_entries(
        self,
        class_id: UUID,
        academic_year_id: UUID,
        section_id: Optional[UUID] = None,
    ) -> List[TimetableEntry]:
        """Get all timetable entries for a class."""
        # First find active timetable for this year
        timetable_query = select(Timetable.id).where(
            Timetable.tenant_id == self.tenant_id,
            Timetable.academic_year_id == academic_year_id,
            Timetable.is_active == True,
            Timetable.deleted_at.is_(None),
        )
        
        query = select(TimetableEntry).where(
            TimetableEntry.tenant_id == self.tenant_id,
            TimetableEntry.timetable_id.in_(timetable_query),
            TimetableEntry.class_id == class_id,
            TimetableEntry.deleted_at.is_(None),
        )
        
        if section_id:
            query = query.where(
                or_(
                    TimetableEntry.section_id == section_id,
                    TimetableEntry.section_id.is_(None),
                )
            )
        
        query = query.order_by(
            TimetableEntry.day_of_week,
            TimetableEntry.period_number,
        )
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_teacher_entries(
        self,
        teacher_id: UUID,
        academic_year_id: UUID,
    ) -> List[TimetableEntry]:
        """Get all timetable entries for a teacher."""
        # First find active timetable for this year
        timetable_query = select(Timetable.id).where(
            Timetable.tenant_id == self.tenant_id,
            Timetable.academic_year_id == academic_year_id,
            Timetable.is_active == True,
            Timetable.deleted_at.is_(None),
        )
        
        query = select(TimetableEntry).where(
            TimetableEntry.tenant_id == self.tenant_id,
            TimetableEntry.timetable_id.in_(timetable_query),
            TimetableEntry.teacher_id == teacher_id,
            TimetableEntry.deleted_at.is_(None),
        )
        
        query = query.order_by(
            TimetableEntry.day_of_week,
            TimetableEntry.period_number,
        )
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    # ============================================
    # Validation Methods
    # ============================================
    
    async def _check_conflicts(
        self,
        timetable_id: UUID,
        data: dict,
        exclude_entry_id: Optional[UUID] = None,
    ) -> None:
        """Check for scheduling conflicts."""
        day = data["day_of_week"]
        period = data["period_number"]
        class_id = data["class_id"]
        teacher_id = data["teacher_id"]
        
        # Get timetable to check academic year scope
        timetable = await self.get_timetable(timetable_id)
        
        # Build base query for all entries in same academic year
        base_filter = and_(
            TimetableEntry.tenant_id == self.tenant_id,
            TimetableEntry.day_of_week == day,
            TimetableEntry.period_number == period,
            TimetableEntry.deleted_at.is_(None),
        )
        
        if exclude_entry_id:
            base_filter = and_(base_filter, TimetableEntry.id != exclude_entry_id)
        
        # Check 1: Class slot conflict (same class, same day+period)
        class_conflict_query = select(TimetableEntry).where(
            base_filter,
            TimetableEntry.timetable_id == timetable_id,
            TimetableEntry.class_id == class_id,
        )
        result = await self.session.execute(class_conflict_query)
        existing = result.scalar_one_or_none()
        if existing:
            day_name = DAY_OF_WEEK_NAMES.get(day, str(day))
            raise DuplicateError(
                f"Class already has a subject scheduled for {day_name}, Period {period}"
            )
        
        # Check 2: Teacher conflict (same teacher, same day+period across all timetables in year)
        # Get all timetable IDs for the same academic year
        year_timetables = select(Timetable.id).where(
            Timetable.tenant_id == self.tenant_id,
            Timetable.academic_year_id == timetable.academic_year_id,
            Timetable.deleted_at.is_(None),
        )
        
        teacher_conflict_query = select(TimetableEntry).where(
            base_filter,
            TimetableEntry.timetable_id.in_(year_timetables),
            TimetableEntry.teacher_id == teacher_id,
        )
        result = await self.session.execute(teacher_conflict_query)
        existing = result.scalar_one_or_none()
        if existing:
            day_name = DAY_OF_WEEK_NAMES.get(day, str(day))
            raise DuplicateError(
                f"Teacher is already assigned to another class on {day_name}, Period {period}"
            )
    
    async def _validate_teaching_assignment(
        self,
        teacher_id: UUID,
        class_id: UUID,
        subject_id: UUID,
        academic_year_id: UUID,
    ) -> None:
        """Validate that teacher is assigned to teach this subject in this class."""
        query = select(TeachingAssignment).where(
            TeachingAssignment.tenant_id == self.tenant_id,
            TeachingAssignment.teacher_id == teacher_id,
            TeachingAssignment.class_id == class_id,
            TeachingAssignment.subject_id == subject_id,
            TeachingAssignment.academic_year_id == academic_year_id,
            TeachingAssignment.is_active == True,
            TeachingAssignment.deleted_at.is_(None),
        )
        
        result = await self.session.execute(query)
        assignment = result.scalar_one_or_none()
        
        if not assignment:
            raise ValidationError(
                "Teacher is not assigned to teach this subject in this class. "
                "Please create a Teaching Assignment first."
            )
    
    # ============================================
    # Stats
    # ============================================
    
    async def get_stats(
        self, 
        academic_year_id: Optional[UUID] = None,
    ) -> dict:
        """Get timetable statistics."""
        base_filter = and_(
            Timetable.tenant_id == self.tenant_id,
            Timetable.deleted_at.is_(None),
        )
        
        if academic_year_id:
            base_filter = and_(base_filter, Timetable.academic_year_id == academic_year_id)
        
        # Total timetables
        total_query = select(func.count(Timetable.id)).where(base_filter)
        total = await self.session.scalar(total_query) or 0
        
        # Active timetables
        active_query = select(func.count(Timetable.id)).where(
            base_filter,
            Timetable.is_active == True,
        )
        active = await self.session.scalar(active_query) or 0
        
        # Total entries
        entry_filter = and_(
            TimetableEntry.tenant_id == self.tenant_id,
            TimetableEntry.deleted_at.is_(None),
        )
        entries_query = select(func.count(TimetableEntry.id)).where(entry_filter)
        total_entries = await self.session.scalar(entries_query) or 0
        
        return {
            "total_timetables": total,
            "active_timetables": active,
            "total_entries": total_entries,
            "classes_with_timetable": 0,  # TODO: Calculate from entries
            "classes_without_timetable": 0,  # TODO: Calculate
        }
