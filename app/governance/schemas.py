"""
CUSTOS Governance Schemas

Pydantic schemas for audit trails, consent, and compliance exports.
"""

from datetime import datetime, date
from typing import Optional, List, Any
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from app.governance.models import (
    ActionType,
    EntityType,
    AccessType,
    SubjectType,
    ConsentType,
    InspectionScope,
    InspectionStatus,
)


# ============================================
# Audit Log Schemas
# ============================================

class AuditLogResponse(BaseModel):
    """Audit log entry response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    
    # Actor
    actor_user_id: Optional[UUID] = None
    actor_role: Optional[str] = None
    actor_email: Optional[str] = None
    
    # Action
    action_type: ActionType
    
    # Entity
    entity_type: EntityType
    entity_id: Optional[UUID] = None
    entity_name: Optional[str] = None
    
    # Changes
    old_value_json: Optional[dict] = None
    new_value_json: Optional[dict] = None
    
    # Context
    description: Optional[str] = None
    ip_address: Optional[str] = None
    
    # Timestamp
    timestamp: datetime


class AuditLogListItem(BaseModel):
    """Condensed audit log for listing."""
    id: UUID
    actor_email: Optional[str] = None
    actor_role: Optional[str] = None
    action_type: ActionType
    entity_type: EntityType
    entity_name: Optional[str] = None
    description: Optional[str] = None
    timestamp: datetime


class AuditLogFilter(BaseModel):
    """Filter for querying audit logs."""
    action_type: Optional[ActionType] = None
    entity_type: Optional[EntityType] = None
    entity_id: Optional[UUID] = None
    actor_user_id: Optional[UUID] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    search: Optional[str] = None


class AuditLogCreateInternal(BaseModel):
    """
    Internal schema for creating audit logs.
    
    This is used by the service layer, not exposed via API.
    """
    actor_user_id: Optional[UUID] = None
    actor_role: Optional[str] = None
    actor_email: Optional[str] = None
    action_type: ActionType
    entity_type: EntityType
    entity_id: Optional[UUID] = None
    entity_name: Optional[str] = None
    old_value_json: Optional[dict] = None
    new_value_json: Optional[dict] = None
    description: Optional[str] = None
    metadata_json: Optional[dict] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None


# ============================================
# Data Access Log Schemas
# ============================================

class DataAccessLogResponse(BaseModel):
    """Data access log entry response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    
    # Who
    user_id: UUID
    user_role: Optional[str] = None
    user_email: Optional[str] = None
    
    # What
    accessed_resource: str
    resource_type: Optional[str] = None
    resource_id: Optional[UUID] = None
    
    # How
    access_type: AccessType
    
    # Result
    success: bool
    records_accessed: int
    
    # Context
    ip_address: Optional[str] = None
    request_path: Optional[str] = None
    
    # When
    timestamp: datetime


class DataAccessLogListItem(BaseModel):
    """Condensed data access log for listing."""
    id: UUID
    user_email: Optional[str] = None
    user_role: Optional[str] = None
    accessed_resource: str
    access_type: AccessType
    records_accessed: int
    timestamp: datetime


class DataAccessLogFilter(BaseModel):
    """Filter for querying data access logs."""
    user_id: Optional[UUID] = None
    resource_type: Optional[str] = None
    access_type: Optional[AccessType] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class DataAccessLogCreateInternal(BaseModel):
    """Internal schema for creating data access logs."""
    user_id: UUID
    user_role: Optional[str] = None
    user_email: Optional[str] = None
    accessed_resource: str
    resource_type: Optional[str] = None
    resource_id: Optional[UUID] = None
    access_type: AccessType
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_path: Optional[str] = None
    success: bool = True
    records_accessed: int = 1


# ============================================
# Consent Schemas
# ============================================

class ConsentRecordResponse(BaseModel):
    """Consent record response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    
    # Subject
    subject_type: SubjectType
    subject_id: UUID
    subject_name: Optional[str] = None
    
    # Guardian (for minors)
    guardian_user_id: Optional[UUID] = None
    guardian_name: Optional[str] = None
    guardian_relation: Optional[str] = None
    
    # Consent
    consent_type: ConsentType
    consent_text: Optional[str] = None
    consent_version: Optional[str] = None
    
    # Status
    granted: bool
    granted_at: Optional[datetime] = None
    revoked: bool
    revoked_at: Optional[datetime] = None
    revocation_reason: Optional[str] = None
    
    # Expiry
    expires_at: Optional[datetime] = None
    
    created_at: datetime


class ConsentRecordListItem(BaseModel):
    """Condensed consent record for listing."""
    id: UUID
    subject_type: SubjectType
    subject_name: Optional[str] = None
    consent_type: ConsentType
    granted: bool
    granted_at: Optional[datetime] = None
    revoked: bool


class ConsentGrantRequest(BaseModel):
    """Request to grant consent."""
    subject_type: SubjectType
    subject_id: UUID
    subject_name: Optional[str] = None
    guardian_user_id: Optional[UUID] = None
    guardian_name: Optional[str] = None
    guardian_relation: Optional[str] = None
    consent_type: ConsentType
    consent_text: Optional[str] = None
    consent_version: Optional[str] = None
    expires_at: Optional[datetime] = None


class ConsentRevokeRequest(BaseModel):
    """Request to revoke consent."""
    reason: Optional[str] = None


class ConsentFilter(BaseModel):
    """Filter for querying consent records."""
    subject_type: Optional[SubjectType] = None
    subject_id: Optional[UUID] = None
    consent_type: Optional[ConsentType] = None
    granted: Optional[bool] = None
    revoked: Optional[bool] = None


# ============================================
# Inspection Export Schemas
# ============================================

class InspectionExportResponse(BaseModel):
    """Inspection export response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    
    # Requestor
    requested_by: UUID
    requestor_name: Optional[str] = None
    requestor_role: Optional[str] = None
    
    # Scope
    scope: InspectionScope
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    
    # Status
    status: InspectionStatus
    
    # File
    file_format: Optional[str] = None
    file_size_bytes: Optional[int] = None
    
    # Timing
    requested_at: datetime
    generated_at: Optional[datetime] = None
    downloaded_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    # Reference
    reference_number: Optional[str] = None
    purpose: Optional[str] = None
    
    # Error
    error_message: Optional[str] = None


class InspectionExportListItem(BaseModel):
    """Condensed inspection export for listing."""
    id: UUID
    requestor_name: Optional[str] = None
    scope: InspectionScope
    status: InspectionStatus
    requested_at: datetime
    generated_at: Optional[datetime] = None
    reference_number: Optional[str] = None


class InspectionExportRequest(BaseModel):
    """Request to create an inspection export."""
    scope: InspectionScope
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    filters_json: Optional[dict] = None
    purpose: Optional[str] = None
    notes: Optional[str] = None
    file_format: str = "json"  # json, csv


class InspectionExportFilter(BaseModel):
    """Filter for querying inspection exports."""
    scope: Optional[InspectionScope] = None
    status: Optional[InspectionStatus] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


# ============================================
# Summary Schemas
# ============================================

class GovernanceSummary(BaseModel):
    """Summary of governance data for admin dashboard."""
    total_audit_logs: int
    audit_logs_today: int
    total_data_access_logs: int
    data_access_today: int
    pending_consents: int
    active_consents: int
    revoked_consents: int
    pending_exports: int
    generated_exports: int


class ComplianceStatus(BaseModel):
    """Compliance status overview."""
    consent_coverage: float  # Percentage of subjects with required consents
    audit_log_retention_days: int
    last_audit_log: Optional[datetime] = None
    pending_inspection_requests: int
    data_access_anomalies: int  # Unusual patterns
