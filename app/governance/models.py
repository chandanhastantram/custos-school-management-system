"""
CUSTOS Governance, Compliance & Audit Models

Enterprise-grade audit trails for legal defensibility.

CORE PRINCIPLES:
1. IMMUTABLE AUDIT LOGS - Append-only, never update/delete
2. Role-based access to audit data
3. Inspection-ready exports
4. Works across ALL modules
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, Index, Integer
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB, INET
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import TenantBaseModel


# ============================================
# Enums
# ============================================

class ActionType(str, Enum):
    """Types of auditable actions."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    SOFT_DELETE = "soft_delete"
    RESTORE = "restore"
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET = "password_reset"
    ROLE_CHANGE = "role_change"
    PERMISSION_GRANT = "permission_grant"
    PERMISSION_REVOKE = "permission_revoke"
    EXPORT = "export"
    IMPORT = "import"
    APPROVE = "approve"
    REJECT = "reject"
    SUBMIT = "submit"
    GENERATE = "generate"
    PROCESS = "process"
    PAYMENT = "payment"
    REFUND = "refund"


class EntityType(str, Enum):
    """Types of entities that can be audited."""
    USER = "user"
    STUDENT = "student"
    TEACHER = "teacher"
    PARENT = "parent"
    CLASS = "class"
    SUBJECT = "subject"
    SYLLABUS = "syllabus"
    LESSON_PLAN = "lesson_plan"
    QUESTION = "question"
    ASSIGNMENT = "assignment"
    WORKSHEET = "worksheet"
    ATTENDANCE = "attendance"
    FEE = "fee"
    PAYMENT = "payment"
    TRANSPORT = "transport"
    HOSTEL = "hostel"
    EMPLOYEE = "employee"
    PAYROLL = "payroll"
    SALARY_SLIP = "salary_slip"
    LEAVE = "leave"
    ANALYTICS = "analytics"
    REPORT = "report"
    SCHEDULE = "schedule"
    TIMETABLE = "timetable"
    CALENDAR = "calendar"
    DAILY_LOOP = "daily_loop"
    WEEKLY_TEST = "weekly_test"
    LESSON_TEST = "lesson_test"
    CONSENT = "consent"
    EXPORT = "export"
    TENANT = "tenant"
    SYSTEM = "system"


class AccessType(str, Enum):
    """Types of data access."""
    READ = "read"
    EXPORT = "export"
    DOWNLOAD = "download"
    PRINT = "print"
    API_ACCESS = "api_access"


class SubjectType(str, Enum):
    """Types of consent subjects."""
    STUDENT = "student"
    EMPLOYEE = "employee"
    PARENT = "parent"


class ConsentType(str, Enum):
    """Types of consent."""
    DATA_PROCESSING = "data_processing"
    PHOTO_VIDEO = "photo_video"
    BIOMETRIC = "biometric"
    COMMUNICATION = "communication"
    MARKETING = "marketing"
    THIRD_PARTY_SHARING = "third_party_sharing"


class InspectionScope(str, Enum):
    """Scope of inspection exports."""
    ACADEMIC = "academic"
    FINANCE = "finance"
    HR = "hr"
    TRANSPORT = "transport"
    HOSTEL = "hostel"
    ATTENDANCE = "attendance"
    FULL = "full"


class InspectionStatus(str, Enum):
    """Status of inspection exports."""
    PENDING = "pending"
    PROCESSING = "processing"
    GENERATED = "generated"
    DOWNLOADED = "downloaded"
    EXPIRED = "expired"
    FAILED = "failed"


# ============================================
# Audit Log (IMMUTABLE)
# ============================================

class AuditLog(TenantBaseModel):
    """
    Immutable Audit Log.
    
    This table is APPEND-ONLY. Records are NEVER updated or deleted.
    This is critical for legal defensibility and compliance.
    
    Every significant action in the system creates an audit log entry.
    """
    __tablename__ = "governance_audit_logs"
    
    __table_args__ = (
        Index("ix_audit_tenant_timestamp", "tenant_id", "timestamp"),
        Index("ix_audit_actor", "actor_user_id"),
        Index("ix_audit_entity", "entity_type", "entity_id"),
        Index("ix_audit_action", "action_type"),
    )
    
    # Actor information
    actor_user_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    actor_role: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    actor_email: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # Action
    action_type: Mapped[ActionType] = mapped_column(
        SQLEnum(ActionType),
        nullable=False,
    )
    
    # Entity being acted upon
    entity_type: Mapped[EntityType] = mapped_column(
        SQLEnum(EntityType),
        nullable=False,
    )
    entity_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
    )
    entity_name: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    
    # Change details (for updates)
    old_value_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    new_value_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # Additional context
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # Request context
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    request_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Timestamp (immutable)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    
    # NOTE: No updated_at - this record is NEVER updated


# ============================================
# Data Access Log
# ============================================

class DataAccessLog(TenantBaseModel):
    """
    Tracks who accessed what data and when.
    
    Important for GDPR/privacy compliance and identifying data breaches.
    """
    __tablename__ = "governance_data_access_logs"
    
    __table_args__ = (
        Index("ix_data_access_tenant_timestamp", "tenant_id", "timestamp"),
        Index("ix_data_access_user", "user_id"),
        Index("ix_data_access_resource", "accessed_resource"),
    )
    
    # Who accessed
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False,
    )
    user_role: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    user_email: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # What was accessed
    accessed_resource: Mapped[str] = mapped_column(String(300), nullable=False)
    resource_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    resource_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
    )
    
    # How it was accessed
    access_type: Mapped[AccessType] = mapped_column(
        SQLEnum(AccessType),
        nullable=False,
    )
    
    # Context
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    request_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Result
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    records_accessed: Mapped[int] = mapped_column(Integer, default=1)
    
    # Timestamp
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )


# ============================================
# Consent Record
# ============================================

class ConsentRecord(TenantBaseModel):
    """
    Tracks consent for data processing.
    
    Required for GDPR and child data protection compliance.
    """
    __tablename__ = "governance_consent_records"
    
    __table_args__ = (
        Index("ix_consent_tenant_subject", "tenant_id", "subject_type", "subject_id"),
        Index("ix_consent_type", "consent_type"),
    )
    
    # Who gave consent
    subject_type: Mapped[SubjectType] = mapped_column(
        SQLEnum(SubjectType),
        nullable=False,
    )
    subject_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )
    subject_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # For students, capture guardian info
    guardian_user_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    guardian_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    guardian_relation: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # What consent
    consent_type: Mapped[ConsentType] = mapped_column(
        SQLEnum(ConsentType),
        nullable=False,
    )
    consent_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    consent_version: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Status
    granted: Mapped[bool] = mapped_column(Boolean, default=False)
    granted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    granted_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    
    # Revocation
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    revoked_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    revocation_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Expiry
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    # Metadata
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)


# ============================================
# Inspection Export
# ============================================

class InspectionExport(TenantBaseModel):
    """
    Tracks inspection/compliance exports.
    
    Used for government inspections, audits, and legal requests.
    """
    __tablename__ = "governance_inspection_exports"
    
    __table_args__ = (
        Index("ix_inspection_tenant_status", "tenant_id", "status"),
    )
    
    # Who requested
    requested_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False,
    )
    requestor_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    requestor_role: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # What scope
    scope: Mapped[InspectionScope] = mapped_column(
        SQLEnum(InspectionScope),
        nullable=False,
    )
    
    # Filters
    date_from: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    date_to: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    filters_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # Status
    status: Mapped[InspectionStatus] = mapped_column(
        SQLEnum(InspectionStatus),
        default=InspectionStatus.PENDING,
    )
    
    # File
    file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    file_format: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    file_checksum: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Timing
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    generated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    downloaded_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    # Reference
    reference_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    purpose: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Error tracking
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
