"""
CUSTOS Lesson Planning Repository

Data access layer for lesson plans.
"""

from datetime import datetime, timezone
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ResourceNotFoundError, ValidationError
from app.academics.models.lesson_plans import (
    LessonPlan, LessonPlanUnit, TeachingProgress,
    LessonPlanStatus, ProgressStatus,
)


class LessonPlanRepository:
    """Repository for lesson plan CRUD operations."""
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
    
    # ========================================
    # LessonPlan CRUD
    # ========================================
    
    async def create_plan(self, teacher_id: UUID, **data) -> LessonPlan:
        """Create a new lesson plan."""
        plan = LessonPlan(
            tenant_id=self.tenant_id,
            teacher_id=teacher_id,
            **data,
        )
        self.session.add(plan)
        await self.session.commit()
        await self.session.refresh(plan)
        return plan
    
    async def get_plan(self, plan_id: UUID) -> LessonPlan:
        """Get lesson plan by ID."""
        query = select(LessonPlan).where(
            LessonPlan.tenant_id == self.tenant_id,
            LessonPlan.id == plan_id,
            LessonPlan.is_deleted == False,
        )
        result = await self.session.execute(query)
        plan = result.scalar_one_or_none()
        if not plan:
            raise ResourceNotFoundError("LessonPlan", str(plan_id))
        return plan
    
    async def get_plan_with_units(self, plan_id: UUID) -> LessonPlan:
        """Get lesson plan with units loaded."""
        query = select(LessonPlan).where(
            LessonPlan.tenant_id == self.tenant_id,
            LessonPlan.id == plan_id,
            LessonPlan.is_deleted == False,
        ).options(
            selectinload(LessonPlan.units).selectinload(LessonPlanUnit.progress_entries)
        )
        result = await self.session.execute(query)
        plan = result.scalar_one_or_none()
        if not plan:
            raise ResourceNotFoundError("LessonPlan", str(plan_id))
        return plan
    
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
        """List lesson plans with filtering and pagination."""
        query = select(LessonPlan).where(
            LessonPlan.tenant_id == self.tenant_id,
            LessonPlan.is_deleted == False,
        )
        
        if teacher_id:
            query = query.where(LessonPlan.teacher_id == teacher_id)
        if class_id:
            query = query.where(LessonPlan.class_id == class_id)
        if subject_id:
            query = query.where(LessonPlan.subject_id == subject_id)
        if status:
            query = query.where(LessonPlan.status == status)
        if academic_year_id:
            query = query.where(LessonPlan.academic_year_id == academic_year_id)
        
        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.session.execute(count_query)).scalar() or 0
        
        # Paginate
        skip = (page - 1) * size
        query = query.order_by(LessonPlan.start_date.desc()).offset(skip).limit(size)
        result = await self.session.execute(query)
        
        return list(result.scalars().all()), total
    
    async def update_plan(self, plan_id: UUID, **data) -> LessonPlan:
        """Update a lesson plan."""
        plan = await self.get_plan(plan_id)
        
        if plan.status == LessonPlanStatus.COMPLETED:
            raise ValidationError("Cannot update completed lesson plan")
        
        for key, value in data.items():
            if value is not None:
                setattr(plan, key, value)
        
        await self.session.commit()
        await self.session.refresh(plan)
        return plan
    
    async def delete_plan(self, plan_id: UUID) -> None:
        """Soft delete a lesson plan."""
        plan = await self.get_plan(plan_id)
        plan.soft_delete()
        await self.session.commit()
    
    async def activate_plan(self, plan_id: UUID) -> LessonPlan:
        """Activate a lesson plan."""
        plan = await self.get_plan(plan_id)
        
        if plan.status != LessonPlanStatus.DRAFT:
            raise ValidationError("Only draft plans can be activated")
        
        # Check if has units
        units_count = await self.session.execute(
            select(func.count()).where(
                LessonPlanUnit.lesson_plan_id == plan_id,
                LessonPlanUnit.is_deleted == False,
            )
        )
        if (units_count.scalar() or 0) == 0:
            raise ValidationError("Cannot activate plan without units")
        
        plan.status = LessonPlanStatus.ACTIVE
        plan.activated_at = datetime.now(timezone.utc)
        
        await self.session.commit()
        await self.session.refresh(plan)
        return plan
    
    async def complete_plan(self, plan_id: UUID) -> LessonPlan:
        """Mark lesson plan as completed."""
        plan = await self.get_plan(plan_id)
        
        if plan.status != LessonPlanStatus.ACTIVE:
            raise ValidationError("Only active plans can be completed")
        
        plan.status = LessonPlanStatus.COMPLETED
        plan.completed_at = datetime.now(timezone.utc)
        
        await self.session.commit()
        await self.session.refresh(plan)
        return plan
    
    async def archive_plan(self, plan_id: UUID) -> LessonPlan:
        """Archive a lesson plan."""
        plan = await self.get_plan(plan_id)
        plan.status = LessonPlanStatus.ARCHIVED
        await self.session.commit()
        await self.session.refresh(plan)
        return plan
    
    async def _recalculate_plan_totals(self, plan_id: UUID) -> None:
        """Recalculate plan totals from units."""
        # Total periods
        total_query = select(func.sum(LessonPlanUnit.estimated_periods)).where(
            LessonPlanUnit.lesson_plan_id == plan_id,
            LessonPlanUnit.is_deleted == False,
        )
        total = (await self.session.execute(total_query)).scalar() or 0
        
        # Completed periods
        completed_query = select(func.sum(LessonPlanUnit.completed_periods)).where(
            LessonPlanUnit.lesson_plan_id == plan_id,
            LessonPlanUnit.is_deleted == False,
        )
        completed = (await self.session.execute(completed_query)).scalar() or 0
        
        await self.session.execute(
            update(LessonPlan).where(
                LessonPlan.id == plan_id
            ).values(
                total_periods=total,
                completed_periods=completed,
            )
        )
        await self.session.commit()
    
    # ========================================
    # LessonPlanUnit CRUD
    # ========================================
    
    async def create_unit(self, plan_id: UUID, **data) -> LessonPlanUnit:
        """Create a lesson plan unit."""
        plan = await self.get_plan(plan_id)
        
        if plan.status == LessonPlanStatus.COMPLETED:
            raise ValidationError("Cannot add units to completed plan")
        
        unit = LessonPlanUnit(
            tenant_id=self.tenant_id,
            lesson_plan_id=plan_id,
            **data,
        )
        self.session.add(unit)
        await self.session.commit()
        await self.session.refresh(unit)
        
        await self._recalculate_plan_totals(plan_id)
        
        return unit
    
    async def create_units_bulk(
        self, 
        plan_id: UUID, 
        units_data: List[dict],
    ) -> List[LessonPlanUnit]:
        """Create multiple units at once."""
        plan = await self.get_plan(plan_id)
        
        if plan.status == LessonPlanStatus.COMPLETED:
            raise ValidationError("Cannot add units to completed plan")
        
        units = []
        for idx, data in enumerate(units_data):
            unit = LessonPlanUnit(
                tenant_id=self.tenant_id,
                lesson_plan_id=plan_id,
                order=data.get("order", idx),
                **{k: v for k, v in data.items() if k != "order"},
            )
            self.session.add(unit)
            units.append(unit)
        
        await self.session.commit()
        
        for unit in units:
            await self.session.refresh(unit)
        
        await self._recalculate_plan_totals(plan_id)
        
        return units
    
    async def get_unit(self, unit_id: UUID) -> LessonPlanUnit:
        """Get unit by ID."""
        query = select(LessonPlanUnit).where(
            LessonPlanUnit.tenant_id == self.tenant_id,
            LessonPlanUnit.id == unit_id,
            LessonPlanUnit.is_deleted == False,
        )
        result = await self.session.execute(query)
        unit = result.scalar_one_or_none()
        if not unit:
            raise ResourceNotFoundError("LessonPlanUnit", str(unit_id))
        return unit
    
    async def get_unit_with_progress(self, unit_id: UUID) -> LessonPlanUnit:
        """Get unit with progress entries."""
        query = select(LessonPlanUnit).where(
            LessonPlanUnit.tenant_id == self.tenant_id,
            LessonPlanUnit.id == unit_id,
            LessonPlanUnit.is_deleted == False,
        ).options(selectinload(LessonPlanUnit.progress_entries))
        result = await self.session.execute(query)
        unit = result.scalar_one_or_none()
        if not unit:
            raise ResourceNotFoundError("LessonPlanUnit", str(unit_id))
        return unit
    
    async def list_units(self, plan_id: UUID) -> List[LessonPlanUnit]:
        """List units for a plan."""
        query = select(LessonPlanUnit).where(
            LessonPlanUnit.tenant_id == self.tenant_id,
            LessonPlanUnit.lesson_plan_id == plan_id,
            LessonPlanUnit.is_deleted == False,
        ).order_by(LessonPlanUnit.order)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def update_unit(self, unit_id: UUID, **data) -> LessonPlanUnit:
        """Update a unit."""
        unit = await self.get_unit(unit_id)
        
        # Check plan status
        plan = await self.get_plan(unit.lesson_plan_id)
        if plan.status == LessonPlanStatus.COMPLETED:
            raise ValidationError("Cannot update units in completed plan")
        
        old_periods = unit.estimated_periods
        
        for key, value in data.items():
            if value is not None:
                setattr(unit, key, value)
        
        await self.session.commit()
        await self.session.refresh(unit)
        
        # Recalculate if periods changed
        if data.get("estimated_periods") and data["estimated_periods"] != old_periods:
            await self._recalculate_plan_totals(unit.lesson_plan_id)
        
        return unit
    
    async def delete_unit(self, unit_id: UUID) -> None:
        """Soft delete a unit."""
        unit = await self.get_unit(unit_id)
        plan_id = unit.lesson_plan_id
        
        plan = await self.get_plan(plan_id)
        if plan.status == LessonPlanStatus.COMPLETED:
            raise ValidationError("Cannot delete units from completed plan")
        
        unit.soft_delete()
        await self.session.commit()
        
        await self._recalculate_plan_totals(plan_id)
    
    async def reorder_units(self, plan_id: UUID, unit_ids: List[UUID]) -> None:
        """Reorder units."""
        for order, unit_id in enumerate(unit_ids):
            await self.session.execute(
                update(LessonPlanUnit).where(
                    LessonPlanUnit.id == unit_id,
                    LessonPlanUnit.lesson_plan_id == plan_id,
                ).values(order=order)
            )
        await self.session.commit()
    
    async def _update_unit_status(self, unit_id: UUID) -> None:
        """Update unit status based on progress."""
        unit = await self.get_unit(unit_id)
        
        if unit.completed_periods >= unit.estimated_periods:
            unit.status = ProgressStatus.COMPLETED
        elif unit.completed_periods > 0:
            unit.status = ProgressStatus.IN_PROGRESS
        else:
            unit.status = ProgressStatus.PLANNED
        
        await self.session.commit()
    
    # ========================================
    # TeachingProgress CRUD
    # ========================================
    
    async def create_progress(
        self, 
        unit_id: UUID, 
        recorded_by: UUID,
        **data,
    ) -> TeachingProgress:
        """Create teaching progress entry."""
        unit = await self.get_unit(unit_id)
        
        # Check plan is active
        plan = await self.get_plan(unit.lesson_plan_id)
        if plan.status not in [LessonPlanStatus.ACTIVE, LessonPlanStatus.DRAFT]:
            raise ValidationError("Can only record progress for active/draft plans")
        
        progress = TeachingProgress(
            tenant_id=self.tenant_id,
            lesson_plan_unit_id=unit_id,
            recorded_by=recorded_by,
            **data,
        )
        self.session.add(progress)
        
        # Update unit completed periods
        if data.get("status") == ProgressStatus.COMPLETED:
            unit.completed_periods += data.get("periods_taught", 1)
        
        await self.session.commit()
        await self.session.refresh(progress)
        
        # Update unit status
        await self._update_unit_status(unit_id)
        await self._recalculate_plan_totals(unit.lesson_plan_id)
        
        return progress
    
    async def get_progress(self, progress_id: UUID) -> TeachingProgress:
        """Get progress entry by ID."""
        query = select(TeachingProgress).where(
            TeachingProgress.tenant_id == self.tenant_id,
            TeachingProgress.id == progress_id,
            TeachingProgress.is_deleted == False,
        )
        result = await self.session.execute(query)
        progress = result.scalar_one_or_none()
        if not progress:
            raise ResourceNotFoundError("TeachingProgress", str(progress_id))
        return progress
    
    async def list_progress(self, unit_id: UUID) -> List[TeachingProgress]:
        """List progress entries for a unit."""
        query = select(TeachingProgress).where(
            TeachingProgress.tenant_id == self.tenant_id,
            TeachingProgress.lesson_plan_unit_id == unit_id,
            TeachingProgress.is_deleted == False,
        ).order_by(TeachingProgress.date.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def update_progress(self, progress_id: UUID, **data) -> TeachingProgress:
        """Update progress entry."""
        progress = await self.get_progress(progress_id)
        
        old_periods = progress.periods_taught
        old_status = progress.status
        
        for key, value in data.items():
            if value is not None:
                setattr(progress, key, value)
        
        await self.session.commit()
        await self.session.refresh(progress)
        
        # Recalculate unit if periods changed
        if data.get("periods_taught") or data.get("status"):
            unit = await self.get_unit(progress.lesson_plan_unit_id)
            
            # Adjust completed periods
            if old_status == ProgressStatus.COMPLETED:
                unit.completed_periods -= old_periods
            if progress.status == ProgressStatus.COMPLETED:
                unit.completed_periods += progress.periods_taught
            
            await self.session.commit()
            await self._update_unit_status(progress.lesson_plan_unit_id)
            await self._recalculate_plan_totals(unit.lesson_plan_id)
        
        return progress
    
    async def delete_progress(self, progress_id: UUID) -> None:
        """Delete progress entry."""
        progress = await self.get_progress(progress_id)
        unit = await self.get_unit(progress.lesson_plan_unit_id)
        
        # Adjust completed periods
        if progress.status == ProgressStatus.COMPLETED:
            unit.completed_periods -= progress.periods_taught
        
        progress.soft_delete()
        await self.session.commit()
        
        await self._update_unit_status(unit.id)
        await self._recalculate_plan_totals(unit.lesson_plan_id)
