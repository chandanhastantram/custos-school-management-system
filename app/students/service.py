"""
CUSTOS Student Lifecycle Service

State resolution, enforcement, and side-effects.

CORE ALGORITHM:
    resolve_student_state(student_id, as_of_date):
        return latest_event where effective_date <= as_of_date
        order by effective_date desc, created_at desc

ENFORCEMENT:
    assert_student_active(student_id) -> raises if not ACTIVE
"""

import logging
from datetime import date, datetime, timezone
from typing import Optional, List, Tuple
from uuid import UUID
from dataclasses import dataclass

from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.students.lifecycle import (
    StudentLifecycleState,
    StudentLifecycleEvent,
    NON_ACTIVE_STATES,
    TERMINAL_STATES,
    CLEANUP_TRIGGER_STATES,
)
from app.users.models import StudentProfile

logger = logging.getLogger(__name__)


class StudentNotActiveError(HTTPException):
    """Raised when operation requires an active student."""
    
    def __init__(
        self,
        student_id: UUID,
        current_state: StudentLifecycleState,
        effective_date: date,
    ):
        super().__init__(
            status_code=403,
            detail={
                "error": "student_not_active",
                "student_id": str(student_id),
                "current_state": current_state.value,
                "effective_date": effective_date.isoformat(),
                "message": f"Student is not active (state: {current_state.value})",
            },
        )


@dataclass
class ResolvedState:
    """Result of state resolution."""
    student_id: UUID
    state: StudentLifecycleState
    effective_date: date
    reason: Optional[str] = None
    is_active: bool = True


class StudentLifecycleService:
    """
    Central service for student lifecycle management.
    
    Responsibilities:
    1. State resolution (with date-effective support)
    2. State transitions (with validation)
    3. Enforcement guard
    4. Side-effects coordination
    """
    
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
    
    async def resolve_state(
        self,
        student_id: UUID,
        as_of_date: Optional[date] = None,
    ) -> ResolvedState:
        """
        Resolve student state as of a specific date.
        
        Core algorithm:
        - Find latest event where effective_date <= as_of_date
        - If no events, return ACTIVE (default state)
        """
        if as_of_date is None:
            as_of_date = date.today()
        
        # Find latest applicable event
        query = (
            select(StudentLifecycleEvent)
            .where(
                StudentLifecycleEvent.student_id == student_id,
                StudentLifecycleEvent.tenant_id == self.tenant_id,
                StudentLifecycleEvent.effective_date <= as_of_date,
                StudentLifecycleEvent.is_deleted == False,
            )
            .order_by(
                StudentLifecycleEvent.effective_date.desc(),
                StudentLifecycleEvent.created_at.desc(),
            )
            .limit(1)
        )
        
        result = await self.db.execute(query)
        event = result.scalar_one_or_none()
        
        if event:
            return ResolvedState(
                student_id=student_id,
                state=event.new_state,
                effective_date=event.effective_date,
                reason=event.reason,
                is_active=event.new_state == StudentLifecycleState.ACTIVE,
            )
        
        # No events = student is ACTIVE since creation
        student_query = select(StudentProfile).where(
            StudentProfile.id == student_id,
            StudentProfile.tenant_id == self.tenant_id,
        )
        student_result = await self.db.execute(student_query)
        student = student_result.scalar_one_or_none()
        
        default_date = student.created_at.date() if student else as_of_date
        
        return ResolvedState(
            student_id=student_id,
            state=StudentLifecycleState.ACTIVE,
            effective_date=default_date,
            is_active=True,
        )
    
    async def assert_student_active(
        self,
        student_id: UUID,
        as_of_date: Optional[date] = None,
    ) -> ResolvedState:
        """
        Central guard: Assert student is ACTIVE.
        
        Raises StudentNotActiveError if student is not active.
        
        Usage:
            # In any service that requires active student
            resolved = await lifecycle_service.assert_student_active(student_id)
        """
        resolved = await self.resolve_state(student_id, as_of_date)
        
        if not resolved.is_active:
            raise StudentNotActiveError(
                student_id=student_id,
                current_state=resolved.state,
                effective_date=resolved.effective_date,
            )
        
        return resolved
    
    async def transition_state(
        self,
        student_id: UUID,
        new_state: StudentLifecycleState,
        effective_date: date,
        reason: str,
        actor_id: UUID,
        reference_document: Optional[str] = None,
    ) -> StudentLifecycleEvent:
        """
        Transition student to a new lifecycle state.
        
        Steps:
        1. Resolve current state
        2. Validate transition
        3. Create event
        4. Update cache on StudentProfile
        5. Trigger side-effects if needed
        6. Audit log
        """
        # Get current state
        current = await self.resolve_state(student_id)
        
        # Validate transition
        self._validate_transition(current.state, new_state)
        
        # Create event
        event = StudentLifecycleEvent(
            tenant_id=self.tenant_id,
            student_id=student_id,
            previous_state=current.state,
            new_state=new_state,
            effective_date=effective_date,
            reason=reason,
            reference_document=reference_document,
            created_by_id=actor_id,
        )
        self.db.add(event)
        
        # Update cache on student profile if effective today or earlier
        if effective_date <= date.today():
            await self.db.execute(
                update(StudentProfile)
                .where(StudentProfile.id == student_id)
                .values(
                    current_lifecycle_state=new_state.value,
                    current_state_effective_date=effective_date,
                )
            )
        
        await self.db.commit()
        await self.db.refresh(event)
        
        # Trigger side-effects
        await self._trigger_side_effects(student_id, new_state, effective_date)
        
        # Audit log
        await self._audit_transition(event, actor_id)
        
        logger.info(
            f"Student {student_id} transitioned: "
            f"{current.state.value} -> {new_state.value} "
            f"effective {effective_date}"
        )
        
        return event
    
    def _validate_transition(
        self,
        from_state: StudentLifecycleState,
        to_state: StudentLifecycleState,
    ):
        """Validate state transition is allowed."""
        # Cannot transition from terminal states (except by admin override)
        if from_state in TERMINAL_STATES and to_state != StudentLifecycleState.ACTIVE:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "invalid_transition",
                    "message": f"Cannot transition from {from_state.value} state",
                    "from_state": from_state.value,
                    "to_state": to_state.value,
                },
            )
        
        # Same state transition is a no-op (but allowed)
        if from_state == to_state:
            logger.warning(f"No-op transition: {from_state.value} -> {to_state.value}")
    
    async def _trigger_side_effects(
        self,
        student_id: UUID,
        new_state: StudentLifecycleState,
        effective_date: date,
    ):
        """
        Trigger automatic side-effects based on state change.
        
        Only triggers if effective_date is today or earlier.
        """
        if effective_date > date.today():
            # Future-dated event, no immediate side-effects
            return
        
        if new_state not in NON_ACTIVE_STATES:
            return
        
        if new_state in CLEANUP_TRIGGER_STATES:
            # Trigger: Transport unassign, Hostel checkout
            await self._cleanup_resources(student_id)
        
        # Cancel future invoices for non-active students
        await self._cancel_future_invoices(student_id)
        
        # Freeze analytics snapshots
        await self._freeze_analytics(student_id)
    
    async def _cleanup_resources(self, student_id: UUID):
        """Cleanup transport and hostel assignments."""
        try:
            # Transport unassign (if module exists)
            # This would call transport service
            logger.info(f"Would unassign transport for student {student_id}")
        except Exception as e:
            logger.warning(f"Transport cleanup failed: {e}")
        
        try:
            # Hostel checkout (if module exists)
            logger.info(f"Would checkout hostel for student {student_id}")
        except Exception as e:
            logger.warning(f"Hostel cleanup failed: {e}")
    
    async def _cancel_future_invoices(self, student_id: UUID):
        """Cancel future fee invoices."""
        try:
            # This would call fees service
            logger.info(f"Would cancel future invoices for student {student_id}")
        except Exception as e:
            logger.warning(f"Invoice cancellation failed: {e}")
    
    async def _freeze_analytics(self, student_id: UUID):
        """Mark analytics as frozen for this student."""
        try:
            # This would mark student analytics as frozen
            logger.info(f"Would freeze analytics for student {student_id}")
        except Exception as e:
            logger.warning(f"Analytics freeze failed: {e}")
    
    async def _audit_transition(self, event: StudentLifecycleEvent, actor_id: UUID):
        """Log transition in governance audit."""
        try:
            from app.governance.service import GovernanceService
            from app.governance.models import ActionType, EntityType
            
            governance = GovernanceService(self.db, self.tenant_id)
            await governance.log_action(
                action_type=ActionType.UPDATE,
                entity_type=EntityType.STUDENT,
                entity_id=event.student_id,
                entity_name=f"lifecycle:{event.previous_state.value}->{event.new_state.value}",
                actor_user_id=actor_id,
                description=event.reason,
                metadata={
                    "previous_state": event.previous_state.value,
                    "new_state": event.new_state.value,
                    "effective_date": event.effective_date.isoformat(),
                },
            )
        except Exception as e:
            logger.warning(f"Audit logging failed: {e}")
    
    async def get_lifecycle_history(
        self,
        student_id: UUID,
        limit: int = 50,
    ) -> List[StudentLifecycleEvent]:
        """Get lifecycle event history for a student."""
        query = (
            select(StudentLifecycleEvent)
            .where(
                StudentLifecycleEvent.student_id == student_id,
                StudentLifecycleEvent.tenant_id == self.tenant_id,
                StudentLifecycleEvent.is_deleted == False,
            )
            .order_by(
                StudentLifecycleEvent.effective_date.desc(),
                StudentLifecycleEvent.created_at.desc(),
            )
            .limit(limit)
        )
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_students_by_state(
        self,
        state: StudentLifecycleState,
        as_of_date: Optional[date] = None,
    ) -> List[UUID]:
        """Get all students in a specific state."""
        if as_of_date is None:
            as_of_date = date.today()
        
        # Use cached state for efficiency
        query = (
            select(StudentProfile.id)
            .where(
                StudentProfile.tenant_id == self.tenant_id,
                StudentProfile.current_lifecycle_state == state.value,
                StudentProfile.is_deleted == False,
            )
        )
        
        result = await self.db.execute(query)
        return [row[0] for row in result.fetchall()]
    
    async def get_active_student_count(self) -> int:
        """Get count of active students."""
        from sqlalchemy import func
        
        query = (
            select(func.count(StudentProfile.id))
            .where(
                StudentProfile.tenant_id == self.tenant_id,
                StudentProfile.current_lifecycle_state == StudentLifecycleState.ACTIVE.value,
                StudentProfile.is_deleted == False,
            )
        )
        
        result = await self.db.execute(query)
        return result.scalar() or 0


# Convenience function for common use case
async def assert_student_active(
    db: AsyncSession,
    tenant_id: UUID,
    student_id: UUID,
    as_of_date: Optional[date] = None,
) -> ResolvedState:
    """
    Central guard: Assert student is active.
    
    Usage in any service:
        from app.students.service import assert_student_active
        
        await assert_student_active(db, tenant_id, student_id)
    """
    service = StudentLifecycleService(db, tenant_id)
    return await service.assert_student_active(student_id, as_of_date)
