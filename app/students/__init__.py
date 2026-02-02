"""
CUSTOS Student Module

Student lifecycle management and state tracking.

KEY CONCEPTS:

1. LIFECYCLE STATES:
   - ACTIVE: Currently studying (default)
   - INACTIVE: Temporarily inactive (medical/personal)
   - SUSPENDED: Disciplinary, time-bound
   - TRANSFERRED_OUT: Left school mid-year
   - GRADUATED: Completed final academic year
   - DROPPED: Permanent dropout

2. DATE-EFFECTIVE:
   States have effective dates. A student can be:
   - "On medical leave starting last week"
   - "Transferring effective next Monday"

3. EVENT-BASED:
   Events are the source of truth.
   StudentProfile.current_lifecycle_state is just a cache.

4. ENFORCEMENT:
   Only ACTIVE students participate in operations:
   - Attendance
   - Learning
   - Exams
   - Fees (new invoices)
   - Transport/Hostel

USAGE:

1. Assert student is active (guard):

    from app.students import assert_student_active
    
    await assert_student_active(db, tenant_id, student_id)
    # Raises StudentNotActiveError if not active

2. Transition state:

    from app.students import StudentLifecycleService
    
    service = StudentLifecycleService(db, tenant_id)
    await service.transition_state(
        student_id=student_id,
        new_state=StudentLifecycleState.TRANSFERRED_OUT,
        effective_date=date.today(),
        reason="Family relocated",
        actor_id=admin_user_id,
    )

3. Check state as of specific date:

    service = StudentLifecycleService(db, tenant_id)
    resolved = await service.resolve_state(student_id, as_of_date)
    print(resolved.state, resolved.is_active)
"""

# Lifecycle
from app.students.lifecycle import (
    StudentLifecycleState,
    StudentLifecycleEvent,
    NON_ACTIVE_STATES,
    TERMINAL_STATES,
    CLEANUP_TRIGGER_STATES,
)

# Service
from app.students.service import (
    StudentLifecycleService,
    StudentNotActiveError,
    ResolvedState,
    assert_student_active,
)

# Router (import separately to avoid circular deps)
# from app.students.router import router as students_router

__all__ = [
    # Lifecycle
    "StudentLifecycleState",
    "StudentLifecycleEvent",
    "NON_ACTIVE_STATES",
    "TERMINAL_STATES",
    "CLEANUP_TRIGGER_STATES",
    # Service
    "StudentLifecycleService",
    "StudentNotActiveError",
    "ResolvedState",
    "assert_student_active",
]
