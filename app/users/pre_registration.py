"""
CUSTOS Pre-Registration Models

For inviting users before they join.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import TenantBaseModel


class PreRegistrationStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    REGISTERED = "registered"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class PreRegisteredUser(TenantBaseModel):
    """
    Pre-registered user for invitation-based onboarding.
    
    Admins can pre-register students, teachers, and parents
    before they create their accounts.
    """
    __tablename__ = "pre_registered_users"
    
    # Contact
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Identity
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Role assignment
    role_code: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # For students
    section_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True), 
        ForeignKey("sections.id"),
        nullable=True,
    )
    admission_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # For parents - linked student
    linked_student_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )
    
    # For teachers
    employee_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Status tracking
    status: Mapped[PreRegistrationStatus] = mapped_column(
        SQLEnum(PreRegistrationStatus), 
        default=PreRegistrationStatus.PENDING
    )
    
    # Invitation
    invitation_sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    invitation_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, unique=True)
    invitation_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # When user completes registration
    registered_user_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )
    registered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Who created this pre-registration
    created_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
