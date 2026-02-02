"""
CUSTOS Student Lifecycle

Event-based student state tracking.

RULES:
1. Events are the source of truth
2. Student.current_state is a cache for fast access
3. Date-effective: states apply from effective_date
4. Historical records are NEVER altered

STATES:
- ACTIVE: Currently studying (default)
- INACTIVE: Temporarily inactive (medical/personal)
- SUSPENDED: Disciplinary, time-bound
- TRANSFERRED_OUT: Left school mid-year
- GRADUATED: Completed final academic year
- DROPPED: Permanent dropout
"""

from datetime import date, datetime
from enum import Enum
from typing import Optional, List, TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    String, Text, Date, DateTime, ForeignKey,
    Enum as SQLEnum, Index,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import TenantBaseModel

if TYPE_CHECKING:
    from app.users.models import User


class StudentLifecycleState(str, Enum):
    """
    Student lifecycle states.
    
    Only ACTIVE students participate in operations.
    """
    ACTIVE = "active"                    # Currently studying (default)
    INACTIVE = "inactive"                # Temporarily inactive (medical/personal)
    SUSPENDED = "suspended"              # Disciplinary, time-bound
    TRANSFERRED_OUT = "transferred_out"  # Left school mid-year
    GRADUATED = "graduated"              # Completed final academic year
    DROPPED = "dropped"                  # Permanent dropout


# States that indicate student is no longer participating
NON_ACTIVE_STATES = {
    StudentLifecycleState.INACTIVE,
    StudentLifecycleState.SUSPENDED,
    StudentLifecycleState.TRANSFERRED_OUT,
    StudentLifecycleState.GRADUATED,
    StudentLifecycleState.DROPPED,
}

# States that indicate permanent departure (no return expected)
TERMINAL_STATES = {
    StudentLifecycleState.TRANSFERRED_OUT,
    StudentLifecycleState.GRADUATED,
    StudentLifecycleState.DROPPED,
}

# States that trigger resource cleanup (transport, hostel)
CLEANUP_TRIGGER_STATES = {
    StudentLifecycleState.TRANSFERRED_OUT,
    StudentLifecycleState.DROPPED,
}


class StudentLifecycleEvent(TenantBaseModel):
    """
    Event-based lifecycle tracking.
    
    This is the SOURCE OF TRUTH for student state.
    The student.current_lifecycle_state is just a cache.
    
    Supports date-effective changes:
    - Backdate: "Medical leave started last week"
    - Future: "Transfer effective from next Monday"
    """
    __tablename__ = "student_lifecycle_events"
    
    # Reference to student (not User, but StudentProfile)
    student_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # State transition
    previous_state: Mapped[StudentLifecycleState] = mapped_column(
        SQLEnum(StudentLifecycleState),
        nullable=False,
    )
    new_state: Mapped[StudentLifecycleState] = mapped_column(
        SQLEnum(StudentLifecycleState),
        nullable=False,
    )
    
    # When this state becomes effective (DATE, not datetime)
    effective_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )
    
    # Human-readable reason (required)
    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    
    # Optional reference document (file ID or note)
    reference_document: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    
    # Who created this event
    created_by_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Relationships
    created_by: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[created_by_id],
    )
    
    # Composite index for efficient state resolution
    __table_args__ = (
        Index(
            "ix_lifecycle_student_effective",
            "student_id",
            "effective_date",
        ),
        Index(
            "ix_lifecycle_tenant_effective",
            "tenant_id",
            "effective_date",
        ),
    )
    
    def __repr__(self) -> str:
        return (
            f"<LifecycleEvent {self.previous_state.value} -> "
            f"{self.new_state.value} @ {self.effective_date}>"
        )
