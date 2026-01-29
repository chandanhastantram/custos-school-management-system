"""
CUSTOS Schedule Service

Business logic for schedule orchestration.
"""

from datetime import date, timedelta
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundError, ValidationError
from app.scheduling.repositories.schedule_repo import ScheduleRepository
from app.scheduling.models.schedule import (
    ScheduleEntry, 
    AcademicCalendarDay, 
    ScheduleEntryStatus,
)
from app.scheduling.models.timetable import Timetable, TimetableEntry, DAY_OF_WEEK_NAMES
from app.academics.models.lesson_plans import LessonPlan, LessonPlanUnit, LessonPlanStatus
from app.scheduling.schemas.schedule import (
    CalendarDayCreate,
    CalendarDayBulkCreate,
    CalendarDayUpdate,
    ScheduleEntryUpdate,
    GenerateScheduleRequest,
    GenerateScheduleResult,
    DailyPeriodSlot,
    DailySchedule,
    ClassScheduleView,
    TeacherScheduleView,
    ScheduleStats,
)


class ScheduleService:
    """
    Schedule orchestration service.
    
    Handles:
    - Academic calendar management
    - Schedule generation from lesson plans
    - Schedule views for class/teacher/student
    - Status updates
    """
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
        self.repo = ScheduleRepository(session, tenant_id)
    
    # ============================================
    # Academic Calendar Operations
    # ============================================
    
    async def create_calendar_day(self, data: CalendarDayCreate) -> AcademicCalendarDay:
        """Create a calendar day entry."""
        return await self.repo.create_calendar_day(**data.model_dump())
    
    async def create_calendar_days_bulk(
        self, 
        data: CalendarDayBulkCreate,
    ) -> List[AcademicCalendarDay]:
        """Create multiple calendar days at once."""
        days_data = [d.model_dump() for d in data.days]
        return await self.repo.create_calendar_days_bulk(data.academic_year_id, days_data)
    
    async def get_calendar_day(self, day_id: UUID) -> Optional[AcademicCalendarDay]:
        """Get calendar day by ID."""
        return await self.repo.get_calendar_day(day_id)
    
    async def list_calendar_days(
        self,
        academic_year_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        is_working_day: Optional[bool] = None,
    ) -> List[AcademicCalendarDay]:
        """List calendar days with filters."""
        return await self.repo.list_calendar_days(
            academic_year_id=academic_year_id,
            start_date=start_date,
            end_date=end_date,
            is_working_day=is_working_day,
        )
    
    async def update_calendar_day(
        self, 
        day_id: UUID, 
        data: CalendarDayUpdate,
    ) -> AcademicCalendarDay:
        """Update a calendar day."""
        update_data = data.model_dump(exclude_unset=True)
        return await self.repo.update_calendar_day(day_id, **update_data)
    
    async def delete_calendar_day(self, day_id: UUID) -> None:
        """Delete a calendar day."""
        await self.repo.delete_calendar_day(day_id)
    
    # ============================================
    # Schedule Generation
    # ============================================
    
    async def generate_schedule(
        self,
        lesson_plan_id: UUID,
        request: GenerateScheduleRequest,
    ) -> GenerateScheduleResult:
        """
        Generate schedule entries from a lesson plan.
        
        Algorithm:
        1. Load lesson plan units in order
        2. Load active timetable entries for class+subject+teacher
        3. Load academic calendar working days
        4. Skip holidays & non-working days
        5. Assign lesson plan units to timetable periods sequentially
        6. Create ScheduleEntry rows
        """
        warnings = []
        
        # 1. Load lesson plan with units
        lesson_plan = await self._get_lesson_plan(lesson_plan_id)
        if not lesson_plan:
            raise ResourceNotFoundError("LessonPlan", lesson_plan_id)
        
        if lesson_plan.status not in [LessonPlanStatus.DRAFT, LessonPlanStatus.ACTIVE]:
            raise ValidationError(
                "Cannot generate schedule for completed/archived lesson plans"
            )
        
        # Get units ordered by sequence
        units = await self._get_lesson_plan_units(lesson_plan_id)
        if not units:
            raise ValidationError("Lesson plan has no units to schedule")
        
        # 2. Calculate total periods needed
        total_periods_needed = sum(u.estimated_periods for u in units)
        
        # 3. Get date range
        start_date = request.start_date or lesson_plan.start_date
        end_date = request.end_date or lesson_plan.end_date
        
        if start_date > end_date:
            raise ValidationError("Start date must be before end date")
        
        # 4. If regenerating, delete existing entries
        if request.regenerate:
            deleted = await self.repo.delete_entries_for_lesson_plan(lesson_plan_id)
            if deleted > 0:
                warnings.append(f"Deleted {deleted} existing schedule entries")
        else:
            # Check if schedule already exists
            existing = await self.repo.get_entries_by_lesson_plan(lesson_plan_id)
            if existing:
                raise ValidationError(
                    "Schedule already exists for this lesson plan. "
                    "Set regenerate=true to replace it."
                )
        
        # 5. Load timetable entries for this class+subject+teacher
        timetable_entries = await self._get_timetable_entries(
            class_id=lesson_plan.class_id,
            subject_id=lesson_plan.subject_id,
            teacher_id=lesson_plan.teacher_id,
            academic_year_id=lesson_plan.academic_year_id,
        )
        
        if not timetable_entries:
            raise ValidationError(
                "No timetable entries found for this class+subject+teacher. "
                "Please create timetable entries first."
            )
        
        # Group timetable entries by day_of_week
        timetable_by_day = {}
        for entry in timetable_entries:
            day = entry.day_of_week
            if day not in timetable_by_day:
                timetable_by_day[day] = []
            timetable_by_day[day].append(entry)
        
        # Sort periods within each day
        for day in timetable_by_day:
            timetable_by_day[day].sort(key=lambda e: e.period_number)
        
        # 6. Get working days in the date range
        working_days = await self.repo.get_working_days(
            academic_year_id=lesson_plan.academic_year_id,
            start_date=start_date,
            end_date=end_date,
        )
        
        if not working_days:
            raise ValidationError("No working days found in the specified date range")
        
        # 7. Generate schedule entries
        entries_to_create = []
        unit_index = 0
        periods_remaining_for_unit = units[unit_index].estimated_periods if units else 0
        periods_scheduled = 0
        units_scheduled = 0
        working_days_used = set()
        
        for working_day in working_days:
            day_of_week = working_day.weekday()
            
            # Check if we have timetable entries for this day
            if day_of_week not in timetable_by_day:
                continue
            
            # Get periods for this day
            for tt_entry in timetable_by_day[day_of_week]:
                # Check if we've scheduled all units
                if unit_index >= len(units):
                    break
                
                current_unit = units[unit_index]
                
                # Create schedule entry
                entry_data = {
                    "timetable_entry_id": tt_entry.id,
                    "lesson_plan_unit_id": current_unit.id,
                    "lesson_plan_id": lesson_plan_id,
                    "class_id": lesson_plan.class_id,
                    "section_id": lesson_plan.section_id,
                    "subject_id": lesson_plan.subject_id,
                    "teacher_id": lesson_plan.teacher_id,
                    "topic_id": current_unit.topic_id,
                    "date": working_day,
                    "day_of_week": day_of_week,
                    "period_number": tt_entry.period_number,
                    "status": ScheduleEntryStatus.PLANNED,
                }
                entries_to_create.append(entry_data)
                
                periods_scheduled += 1
                periods_remaining_for_unit -= 1
                working_days_used.add(working_day)
                
                # Move to next unit if current is fully scheduled
                if periods_remaining_for_unit <= 0:
                    units_scheduled += 1
                    unit_index += 1
                    if unit_index < len(units):
                        periods_remaining_for_unit = units[unit_index].estimated_periods
        
        # 8. Create all entries
        if entries_to_create:
            await self.repo.create_entries_bulk(entries_to_create)
        
        # Check if all periods were scheduled
        if periods_scheduled < total_periods_needed:
            warnings.append(
                f"Only {periods_scheduled}/{total_periods_needed} periods could be scheduled. "
                "Consider extending the date range or adding more timetable periods."
            )
        
        # Find actual date range used
        actual_start = min(e["date"] for e in entries_to_create) if entries_to_create else start_date
        actual_end = max(e["date"] for e in entries_to_create) if entries_to_create else end_date
        
        return GenerateScheduleResult(
            lesson_plan_id=lesson_plan_id,
            total_entries_created=len(entries_to_create),
            start_date=actual_start,
            end_date=actual_end,
            units_scheduled=units_scheduled,
            periods_scheduled=periods_scheduled,
            working_days_used=len(working_days_used),
            warnings=warnings,
        )
    
    async def _get_lesson_plan(self, lesson_plan_id: UUID) -> Optional[LessonPlan]:
        """Get lesson plan by ID."""
        query = select(LessonPlan).where(
            LessonPlan.id == lesson_plan_id,
            LessonPlan.tenant_id == self.tenant_id,
            LessonPlan.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def _get_lesson_plan_units(self, lesson_plan_id: UUID) -> List[LessonPlanUnit]:
        """Get lesson plan units ordered by sequence."""
        query = select(LessonPlanUnit).where(
            LessonPlanUnit.lesson_plan_id == lesson_plan_id,
            LessonPlanUnit.tenant_id == self.tenant_id,
            LessonPlanUnit.deleted_at.is_(None),
        ).order_by(LessonPlanUnit.order)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def _get_timetable_entries(
        self,
        class_id: UUID,
        subject_id: UUID,
        teacher_id: UUID,
        academic_year_id: UUID,
    ) -> List[TimetableEntry]:
        """Get timetable entries for class+subject+teacher."""
        # First get active timetables for this academic year
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
            TimetableEntry.subject_id == subject_id,
            TimetableEntry.teacher_id == teacher_id,
            TimetableEntry.deleted_at.is_(None),
        ).order_by(TimetableEntry.day_of_week, TimetableEntry.period_number)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    # ============================================
    # Schedule Entry Operations
    # ============================================
    
    async def get_entry(self, entry_id: UUID) -> Optional[ScheduleEntry]:
        """Get schedule entry by ID."""
        return await self.repo.get_entry(entry_id)
    
    async def list_entries(
        self,
        lesson_plan_id: Optional[UUID] = None,
        class_id: Optional[UUID] = None,
        teacher_id: Optional[UUID] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        status: Optional[ScheduleEntryStatus] = None,
        page: int = 1,
        size: int = 100,
    ) -> Tuple[List[ScheduleEntry], int]:
        """List schedule entries with filtering."""
        return await self.repo.list_entries(
            lesson_plan_id=lesson_plan_id,
            class_id=class_id,
            teacher_id=teacher_id,
            start_date=start_date,
            end_date=end_date,
            status=status,
            page=page,
            size=size,
        )
    
    async def update_entry(
        self, 
        entry_id: UUID, 
        data: ScheduleEntryUpdate,
    ) -> ScheduleEntry:
        """Update a schedule entry."""
        update_data = data.model_dump(exclude_unset=True)
        return await self.repo.update_entry(entry_id, **update_data)
    
    async def update_entry_status(
        self,
        entry_id: UUID,
        status: ScheduleEntryStatus,
        user_id: UUID,
    ) -> ScheduleEntry:
        """Update entry status."""
        return await self.repo.update_entry_status(
            entry_id, 
            status, 
            completed_by=user_id if status == ScheduleEntryStatus.COMPLETED else None,
        )
    
    async def delete_entry(self, entry_id: UUID) -> None:
        """Delete a schedule entry."""
        await self.repo.delete_entry(entry_id)
    
    # ============================================
    # Schedule Views
    # ============================================
    
    async def get_class_schedule(
        self,
        class_id: UUID,
        start_date: date,
        end_date: date,
        section_id: Optional[UUID] = None,
        max_periods: int = 8,
    ) -> ClassScheduleView:
        """Get schedule view for a class."""
        entries = await self.repo.get_entries_by_class_date(
            class_id, start_date, end_date, section_id
        )
        
        # Group entries by date
        entries_by_date = {}
        for entry in entries:
            if entry.date not in entries_by_date:
                entries_by_date[entry.date] = []
            entries_by_date[entry.date].append(entry)
        
        # Build daily schedules
        daily_schedules = []
        current = start_date
        while current <= end_date:
            day_entries = entries_by_date.get(current, [])
            
            periods = []
            for period in range(1, max_periods + 1):
                entry = next(
                    (e for e in day_entries if e.period_number == period),
                    None
                )
                
                slot = DailyPeriodSlot(
                    period_number=period,
                    entry_id=entry.id if entry else None,
                    subject_id=entry.subject_id if entry else None,
                    topic_id=entry.topic_id if entry else None,
                    teacher_id=entry.teacher_id if entry else None,
                    status=entry.status if entry else None,
                )
                periods.append(slot)
            
            # Check if it's a working day (has entries or is weekday)
            is_working = current.weekday() != 6 or bool(day_entries)
            
            daily_schedules.append(DailySchedule(
                date=current,
                day_of_week=current.weekday(),
                day_name=DAY_OF_WEEK_NAMES.get(current.weekday(), ""),
                is_working_day=is_working,
                periods=periods,
            ))
            
            current += timedelta(days=1)
        
        return ClassScheduleView(
            class_id=class_id,
            section_id=section_id,
            start_date=start_date,
            end_date=end_date,
            daily_schedules=daily_schedules,
        )
    
    async def get_teacher_schedule(
        self,
        teacher_id: UUID,
        start_date: date,
        end_date: date,
        max_periods: int = 8,
    ) -> TeacherScheduleView:
        """Get schedule view for a teacher."""
        entries = await self.repo.get_entries_by_teacher_date(
            teacher_id, start_date, end_date
        )
        
        # Group entries by date
        entries_by_date = {}
        for entry in entries:
            if entry.date not in entries_by_date:
                entries_by_date[entry.date] = []
            entries_by_date[entry.date].append(entry)
        
        total_periods = len(entries)
        
        # Build daily schedules
        daily_schedules = []
        current = start_date
        while current <= end_date:
            day_entries = entries_by_date.get(current, [])
            
            periods = []
            for period in range(1, max_periods + 1):
                entry = next(
                    (e for e in day_entries if e.period_number == period),
                    None
                )
                
                slot = DailyPeriodSlot(
                    period_number=period,
                    entry_id=entry.id if entry else None,
                    subject_id=entry.subject_id if entry else None,
                    topic_id=entry.topic_id if entry else None,
                    class_id=entry.class_id if entry else None,
                    status=entry.status if entry else None,
                )
                periods.append(slot)
            
            is_working = current.weekday() != 6 or bool(day_entries)
            
            daily_schedules.append(DailySchedule(
                date=current,
                day_of_week=current.weekday(),
                day_name=DAY_OF_WEEK_NAMES.get(current.weekday(), ""),
                is_working_day=is_working,
                periods=periods,
            ))
            
            current += timedelta(days=1)
        
        return TeacherScheduleView(
            teacher_id=teacher_id,
            start_date=start_date,
            end_date=end_date,
            daily_schedules=daily_schedules,
            total_periods=total_periods,
        )
    
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
    ) -> ScheduleStats:
        """Get schedule statistics."""
        stats = await self.repo.get_stats(
            lesson_plan_id=lesson_plan_id,
            class_id=class_id,
            teacher_id=teacher_id,
            start_date=start_date,
            end_date=end_date,
        )
        return ScheduleStats(**stats)
