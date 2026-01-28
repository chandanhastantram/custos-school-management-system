"""
CUSTOS Lesson Planning Service

Business logic for lesson plan management.
"""

from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.academics.repositories.lesson_plan_repo import LessonPlanRepository
from app.academics.models.lesson_plans import (
    LessonPlan, LessonPlanUnit, TeachingProgress,
    LessonPlanStatus, ProgressStatus,
)
from app.academics.schemas.lesson_plans import (
    LessonPlanCreate, LessonPlanUpdate,
    LessonPlanUnitCreate, LessonPlanUnitUpdate, BulkUnitCreate,
    TeachingProgressCreate, TeachingProgressUpdate,
    ReorderUnitsRequest, LessonPlanStats,
)


class LessonPlanService:
    """
    Lesson planning service.
    
    Handles:
    - Lesson plan lifecycle (draft → active → completed)
    - Unit management (topic mapping)
    - Teaching progress tracking
    """
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
        self.repo = LessonPlanRepository(session, tenant_id)
    
    # ========================================
    # LessonPlan Operations
    # ========================================
    
    async def create_plan(
        self, 
        teacher_id: UUID, 
        data: LessonPlanCreate,
    ) -> LessonPlan:
        """Create a new lesson plan."""
        return await self.repo.create_plan(
            teacher_id=teacher_id,
            **data.model_dump(),
        )
    
    async def get_plan(
        self, 
        plan_id: UUID, 
        include_units: bool = True,
    ) -> LessonPlan:
        """Get lesson plan by ID."""
        if include_units:
            return await self.repo.get_plan_with_units(plan_id)
        return await self.repo.get_plan(plan_id)
    
    async def list_plans(
        self,
        teacher_id: Optional[UUID] = None,
        class_id: Optional[UUID] = None,
        subject_id: Optional[UUID] = None,
        status: Optional[LessonPlanStatus] = None,
        academic_year_id: Optional[UUID] = None,
        page: int = 1,
        size: int = 20,
    ) -> Tuple[List[LessonPlan], int]:
        """List lesson plans with filters."""
        return await self.repo.list_plans(
            teacher_id=teacher_id,
            class_id=class_id,
            subject_id=subject_id,
            status=status,
            academic_year_id=academic_year_id,
            page=page,
            size=size,
        )
    
    async def update_plan(
        self, 
        plan_id: UUID, 
        data: LessonPlanUpdate,
    ) -> LessonPlan:
        """Update a lesson plan."""
        update_data = data.model_dump(exclude_unset=True)
        return await self.repo.update_plan(plan_id, **update_data)
    
    async def delete_plan(self, plan_id: UUID) -> None:
        """Delete a lesson plan."""
        await self.repo.delete_plan(plan_id)
    
    async def activate_plan(self, plan_id: UUID) -> LessonPlan:
        """Activate a lesson plan (draft → active)."""
        return await self.repo.activate_plan(plan_id)
    
    async def complete_plan(self, plan_id: UUID) -> LessonPlan:
        """Complete a lesson plan (active → completed)."""
        return await self.repo.complete_plan(plan_id)
    
    async def archive_plan(self, plan_id: UUID) -> LessonPlan:
        """Archive a lesson plan."""
        return await self.repo.archive_plan(plan_id)
    
    async def check_plan_ownership(
        self, 
        plan_id: UUID, 
        user_id: UUID,
    ) -> bool:
        """Check if user owns the plan."""
        plan = await self.repo.get_plan(plan_id)
        return plan.teacher_id == user_id
    
    # ========================================
    # LessonPlanUnit Operations
    # ========================================
    
    async def add_unit(
        self, 
        plan_id: UUID, 
        data: LessonPlanUnitCreate,
    ) -> LessonPlanUnit:
        """Add a unit to the lesson plan."""
        return await self.repo.create_unit(
            plan_id=plan_id,
            **data.model_dump(),
        )
    
    async def add_units_bulk(
        self, 
        plan_id: UUID, 
        data: BulkUnitCreate,
    ) -> List[LessonPlanUnit]:
        """Add multiple units at once."""
        units_data = [u.model_dump() for u in data.units]
        return await self.repo.create_units_bulk(plan_id, units_data)
    
    async def get_unit(
        self, 
        unit_id: UUID,
        include_progress: bool = False,
    ) -> LessonPlanUnit:
        """Get unit by ID."""
        if include_progress:
            return await self.repo.get_unit_with_progress(unit_id)
        return await self.repo.get_unit(unit_id)
    
    async def list_units(self, plan_id: UUID) -> List[LessonPlanUnit]:
        """List units for a plan."""
        return await self.repo.list_units(plan_id)
    
    async def update_unit(
        self, 
        unit_id: UUID, 
        data: LessonPlanUnitUpdate,
    ) -> LessonPlanUnit:
        """Update a unit."""
        update_data = data.model_dump(exclude_unset=True)
        return await self.repo.update_unit(unit_id, **update_data)
    
    async def delete_unit(self, unit_id: UUID) -> None:
        """Delete a unit."""
        await self.repo.delete_unit(unit_id)
    
    async def reorder_units(
        self, 
        plan_id: UUID, 
        data: ReorderUnitsRequest,
    ) -> None:
        """Reorder units in a plan."""
        await self.repo.reorder_units(plan_id, data.unit_ids)
    
    # ========================================
    # TeachingProgress Operations
    # ========================================
    
    async def record_progress(
        self,
        unit_id: UUID,
        recorded_by: UUID,
        data: TeachingProgressCreate,
    ) -> TeachingProgress:
        """Record teaching progress for a unit."""
        return await self.repo.create_progress(
            unit_id=unit_id,
            recorded_by=recorded_by,
            **data.model_dump(),
        )
    
    async def get_progress(self, progress_id: UUID) -> TeachingProgress:
        """Get progress entry by ID."""
        return await self.repo.get_progress(progress_id)
    
    async def list_progress(self, unit_id: UUID) -> List[TeachingProgress]:
        """List progress entries for a unit."""
        return await self.repo.list_progress(unit_id)
    
    async def update_progress(
        self,
        progress_id: UUID,
        data: TeachingProgressUpdate,
    ) -> TeachingProgress:
        """Update progress entry."""
        update_data = data.model_dump(exclude_unset=True)
        return await self.repo.update_progress(progress_id, **update_data)
    
    async def delete_progress(self, progress_id: UUID) -> None:
        """Delete progress entry."""
        await self.repo.delete_progress(progress_id)
    
    # ========================================
    # Statistics
    # ========================================
    
    async def get_teacher_stats(
        self, 
        teacher_id: UUID,
        academic_year_id: Optional[UUID] = None,
    ) -> LessonPlanStats:
        """Get statistics for a teacher's plans."""
        from sqlalchemy import select, func
        
        base_query = select(LessonPlan).where(
            LessonPlan.tenant_id == self.tenant_id,
            LessonPlan.teacher_id == teacher_id,
            LessonPlan.is_deleted == False,
        )
        
        if academic_year_id:
            base_query = base_query.where(
                LessonPlan.academic_year_id == academic_year_id
            )
        
        # Total plans
        total = (await self.session.execute(
            select(func.count()).select_from(base_query.subquery())
        )).scalar() or 0
        
        # By status
        draft = (await self.session.execute(
            select(func.count()).select_from(
                base_query.where(LessonPlan.status == LessonPlanStatus.DRAFT).subquery()
            )
        )).scalar() or 0
        
        active = (await self.session.execute(
            select(func.count()).select_from(
                base_query.where(LessonPlan.status == LessonPlanStatus.ACTIVE).subquery()
            )
        )).scalar() or 0
        
        completed = (await self.session.execute(
            select(func.count()).select_from(
                base_query.where(LessonPlan.status == LessonPlanStatus.COMPLETED).subquery()
            )
        )).scalar() or 0
        
        # Periods
        periods_query = select(
            func.sum(LessonPlan.total_periods),
            func.sum(LessonPlan.completed_periods),
        ).where(
            LessonPlan.tenant_id == self.tenant_id,
            LessonPlan.teacher_id == teacher_id,
            LessonPlan.is_deleted == False,
        )
        
        if academic_year_id:
            periods_query = periods_query.where(
                LessonPlan.academic_year_id == academic_year_id
            )
        
        periods_result = (await self.session.execute(periods_query)).first()
        total_periods = periods_result[0] or 0
        completed_periods = periods_result[1] or 0
        
        # Units count
        units_base = select(LessonPlanUnit).join(LessonPlan).where(
            LessonPlan.tenant_id == self.tenant_id,
            LessonPlan.teacher_id == teacher_id,
            LessonPlan.is_deleted == False,
            LessonPlanUnit.is_deleted == False,
        )
        
        total_units = (await self.session.execute(
            select(func.count()).select_from(units_base.subquery())
        )).scalar() or 0
        
        completed_units = (await self.session.execute(
            select(func.count()).select_from(
                units_base.where(
                    LessonPlanUnit.status == ProgressStatus.COMPLETED
                ).subquery()
            )
        )).scalar() or 0
        
        completion_rate = (
            (completed_periods / total_periods * 100) 
            if total_periods > 0 else 0
        )
        
        return LessonPlanStats(
            total_plans=total,
            draft_plans=draft,
            active_plans=active,
            completed_plans=completed,
            total_units=total_units,
            completed_units=completed_units,
            total_periods=total_periods,
            completed_periods=completed_periods,
            completion_rate=round(completion_rate, 1),
        )
    
    async def get_class_coverage(
        self,
        class_id: UUID,
        subject_id: UUID,
    ) -> dict:
        """Get syllabus coverage for a class-subject."""
        from sqlalchemy import select, func
        
        # Get all plans for this class-subject
        plans = await self.repo.list_plans(
            class_id=class_id,
            subject_id=subject_id,
            status=LessonPlanStatus.ACTIVE,
        )
        
        if not plans[0]:
            return {
                "class_id": str(class_id),
                "subject_id": str(subject_id),
                "total_units": 0,
                "completed_units": 0,
                "coverage_percent": 0,
            }
        
        # Aggregate units
        total = 0
        completed = 0
        for plan in plans[0]:
            total += plan.total_periods
            completed += plan.completed_periods
        
        coverage = (completed / total * 100) if total > 0 else 0
        
        return {
            "class_id": str(class_id),
            "subject_id": str(subject_id),
            "total_periods": total,
            "completed_periods": completed,
            "coverage_percent": round(coverage, 1),
            "plans_count": len(plans[0]),
        }
