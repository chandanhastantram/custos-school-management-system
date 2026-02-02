"""
CUSTOS Governance Router

API endpoints for audit trails, compliance, and inspection exports.

SECURITY:
- Admin/Principal only for most operations
- Read-only access for compliance officers
- NO access for teachers, students, parents
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth.dependencies import CurrentUser, require_permission
from app.users.rbac import Permission
from app.governance.service import GovernanceService
from app.governance.models import (
    ActionType,
    EntityType,
    AccessType,
    SubjectType,
    ConsentType,
    InspectionScope,
    InspectionStatus,
)
from app.governance.schemas import (
    AuditLogResponse,
    AuditLogListItem,
    AuditLogFilter,
    DataAccessLogResponse,
    DataAccessLogListItem,
    DataAccessLogFilter,
    ConsentRecordResponse,
    ConsentRecordListItem,
    ConsentGrantRequest,
    ConsentRevokeRequest,
    ConsentFilter,
    InspectionExportResponse,
    InspectionExportListItem,
    InspectionExportRequest,
    InspectionExportFilter,
    GovernanceSummary,
)


router = APIRouter(tags=["Governance"])


# ============================================
# Audit Log Endpoints
# ============================================

@router.get("/audit-logs", response_model=List[AuditLogListItem])
async def get_audit_logs(
    request: Request,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    action_type: Optional[ActionType] = None,
    entity_type: Optional[EntityType] = None,
    entity_id: Optional[UUID] = None,
    actor_user_id: Optional[UUID] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    _=Depends(require_permission(Permission.AUDIT_VIEW)),
):
    """
    Get audit logs with optional filtering.
    
    Admin/Principal only. Returns immutable audit trail.
    """
    service = GovernanceService(db, user.tenant_id)
    
    # Log this data access
    await service.log_data_access(
        user_id=user.id,
        user_role=user.role,
        user_email=user.email,
        accessed_resource="audit_logs",
        access_type=AccessType.READ,
        request_path=str(request.url.path),
        ip_address=request.client.host if request.client else None,
    )
    
    filters = AuditLogFilter(
        action_type=action_type,
        entity_type=entity_type,
        entity_id=entity_id,
        actor_user_id=actor_user_id,
        date_from=date_from,
        date_to=date_to,
        search=search,
    )
    
    logs = await service.get_audit_logs(filters, skip, limit)
    
    return [
        AuditLogListItem(
            id=log.id,
            actor_email=log.actor_email,
            actor_role=log.actor_role,
            action_type=log.action_type,
            entity_type=log.entity_type,
            entity_name=log.entity_name,
            description=log.description,
            timestamp=log.timestamp,
        )
        for log in logs
    ]


@router.get("/audit-logs/{log_id}", response_model=AuditLogResponse)
async def get_audit_log_detail(
    log_id: UUID,
    request: Request,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.AUDIT_VIEW)),
):
    """
    Get detailed audit log entry.
    
    Admin/Principal only. Includes old/new values for changes.
    """
    service = GovernanceService(db, user.tenant_id)
    
    log = await service.get_audit_log_by_id(log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Audit log not found")
    
    # Log this detail access
    await service.log_data_access(
        user_id=user.id,
        user_role=user.role,
        user_email=user.email,
        accessed_resource=f"audit_log:{log_id}",
        access_type=AccessType.READ,
        resource_id=log_id,
        request_path=str(request.url.path),
        ip_address=request.client.host if request.client else None,
    )
    
    return AuditLogResponse.model_validate(log)


# ============================================
# Data Access Log Endpoints
# ============================================

@router.get("/data-access", response_model=List[DataAccessLogListItem])
async def get_data_access_logs(
    request: Request,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    user_id: Optional[UUID] = None,
    resource_type: Optional[str] = None,
    access_type: Optional[AccessType] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    _=Depends(require_permission(Permission.AUDIT_VIEW)),
):
    """
    Get data access logs for privacy compliance.
    
    Admin/Principal only. Shows who accessed what data.
    """
    service = GovernanceService(db, user.tenant_id)
    
    filters = DataAccessLogFilter(
        user_id=user_id,
        resource_type=resource_type,
        access_type=access_type,
        date_from=date_from,
        date_to=date_to,
    )
    
    logs = await service.get_data_access_logs(filters, skip, limit)
    
    return [
        DataAccessLogListItem(
            id=log.id,
            user_email=log.user_email,
            user_role=log.user_role,
            accessed_resource=log.accessed_resource,
            access_type=log.access_type,
            records_accessed=log.records_accessed,
            timestamp=log.timestamp,
        )
        for log in logs
    ]


# ============================================
# Consent Endpoints
# ============================================

@router.get("/consents", response_model=List[ConsentRecordListItem])
async def get_consent_records(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    subject_type: Optional[SubjectType] = None,
    subject_id: Optional[UUID] = None,
    consent_type: Optional[ConsentType] = None,
    granted: Optional[bool] = None,
    revoked: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    _=Depends(require_permission(Permission.CONSENT_MANAGE)),
):
    """
    Get consent records with filtering.
    
    Admin/Principal only.
    """
    service = GovernanceService(db, user.tenant_id)
    
    filters = ConsentFilter(
        subject_type=subject_type,
        subject_id=subject_id,
        consent_type=consent_type,
        granted=granted,
        revoked=revoked,
    )
    
    records = await service.get_consent_records(filters, skip, limit)
    
    return [
        ConsentRecordListItem(
            id=record.id,
            subject_type=record.subject_type,
            subject_name=record.subject_name,
            consent_type=record.consent_type,
            granted=record.granted,
            granted_at=record.granted_at,
            revoked=record.revoked,
        )
        for record in records
    ]


@router.get("/consents/{consent_id}", response_model=ConsentRecordResponse)
async def get_consent_detail(
    consent_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.CONSENT_MANAGE)),
):
    """
    Get detailed consent record.
    
    Admin/Principal only.
    """
    service = GovernanceService(db, user.tenant_id)
    
    records = await service.get_consent_records(
        ConsentFilter(subject_id=None),  # Get by ID
        skip=0,
        limit=1000,
    )
    
    record = next((r for r in records if r.id == consent_id), None)
    if not record:
        raise HTTPException(status_code=404, detail="Consent record not found")
    
    return ConsentRecordResponse.model_validate(record)


@router.post("/consents", response_model=ConsentRecordResponse)
async def grant_consent(
    data: ConsentGrantRequest,
    request: Request,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.CONSENT_MANAGE)),
):
    """
    Record consent grant.
    
    Admin/Principal only. For minors, guardian info required.
    """
    service = GovernanceService(db, user.tenant_id)
    
    consent = await service.grant_consent(
        subject_type=data.subject_type,
        subject_id=data.subject_id,
        consent_type=data.consent_type,
        subject_name=data.subject_name,
        guardian_user_id=data.guardian_user_id,
        guardian_name=data.guardian_name,
        guardian_relation=data.guardian_relation,
        consent_text=data.consent_text,
        consent_version=data.consent_version,
        expires_at=data.expires_at,
        ip_address=request.client.host if request.client else None,
        granted_by=user.id,
    )
    
    return ConsentRecordResponse.model_validate(consent)


@router.post("/consents/{consent_id}/revoke", response_model=ConsentRecordResponse)
async def revoke_consent(
    consent_id: UUID,
    data: ConsentRevokeRequest,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.CONSENT_MANAGE)),
):
    """
    Revoke a consent record.
    
    Admin/Principal only. Revocation is immediate.
    """
    service = GovernanceService(db, user.tenant_id)
    
    consent = await service.revoke_consent(
        consent_id=consent_id,
        revoked_by=user.id,
        reason=data.reason,
    )
    
    return ConsentRecordResponse.model_validate(consent)


@router.get("/consents/check/{subject_type}/{subject_id}/{consent_type}")
async def check_consent_status(
    subject_type: SubjectType,
    subject_id: UUID,
    consent_type: ConsentType,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.CONSENT_MANAGE)),
):
    """
    Check if subject has active consent.
    
    Admin/Principal only.
    """
    service = GovernanceService(db, user.tenant_id)
    
    has_consent = await service.check_consent(subject_type, subject_id, consent_type)
    
    return {
        "subject_type": subject_type,
        "subject_id": subject_id,
        "consent_type": consent_type,
        "has_active_consent": has_consent,
    }


# ============================================
# Inspection Export Endpoints
# ============================================

@router.get("/inspection-exports", response_model=List[InspectionExportListItem])
async def get_inspection_exports(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    scope: Optional[InspectionScope] = None,
    status: Optional[InspectionStatus] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    _=Depends(require_permission(Permission.AUDIT_EXPORT)),
):
    """
    Get inspection export requests.
    
    Admin/Principal only.
    """
    service = GovernanceService(db, user.tenant_id)
    
    filters = InspectionExportFilter(
        scope=scope,
        status=status,
        date_from=date_from,
        date_to=date_to,
    )
    
    exports = await service.get_inspection_exports(filters, skip, limit)
    
    return [
        InspectionExportListItem(
            id=export.id,
            requestor_name=export.requestor_name,
            scope=export.scope,
            status=export.status,
            requested_at=export.requested_at,
            generated_at=export.generated_at,
            reference_number=export.reference_number,
        )
        for export in exports
    ]


@router.get("/inspection-exports/{export_id}", response_model=InspectionExportResponse)
async def get_inspection_export_detail(
    export_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.AUDIT_EXPORT)),
):
    """
    Get detailed inspection export.
    
    Admin/Principal and Compliance Officer access.
    """
    service = GovernanceService(db, user.tenant_id)
    
    export = await service.get_inspection_export_by_id(export_id)
    if not export:
        raise HTTPException(status_code=404, detail="Export not found")
    
    return InspectionExportResponse.model_validate(export)


@router.post("/inspection-exports", response_model=InspectionExportResponse)
async def create_inspection_export(
    data: InspectionExportRequest,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.AUDIT_EXPORT)),
):
    """
    Request a new inspection export.
    
    Admin/Principal only. Creates export request and starts generation.
    """
    service = GovernanceService(db, user.tenant_id)
    
    export = await service.create_inspection_export(
        scope=data.scope,
        requested_by=user.id,
        requestor_name=user.email,
        requestor_role=user.role,
        date_from=datetime.combine(data.date_from, datetime.min.time()) if data.date_from else None,
        date_to=datetime.combine(data.date_to, datetime.max.time()) if data.date_to else None,
        filters_json=data.filters_json,
        purpose=data.purpose,
        notes=data.notes,
        file_format=data.file_format,
    )
    
    # Try to generate immediately (for now - could be async in production)
    export = await service.generate_inspection_export(export.id)
    
    return InspectionExportResponse.model_validate(export)


@router.post("/inspection-exports/{export_id}/download")
async def download_inspection_export(
    export_id: UUID,
    request: Request,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.AUDIT_EXPORT)),
):
    """
    Download an inspection export file.
    
    Admin/Principal only. Marks export as downloaded.
    """
    service = GovernanceService(db, user.tenant_id)
    
    export = await service.get_inspection_export_by_id(export_id)
    if not export:
        raise HTTPException(status_code=404, detail="Export not found")
    
    if export.status != InspectionStatus.GENERATED:
        raise HTTPException(
            status_code=400,
            detail=f"Export is not ready. Status: {export.status.value}",
        )
    
    # Mark as downloaded
    export = await service.mark_export_downloaded(export_id)
    
    # Log the export download
    await service.log_data_access(
        user_id=user.id,
        user_role=user.role,
        user_email=user.email,
        accessed_resource=f"inspection_export:{export.reference_number}",
        access_type=AccessType.DOWNLOAD,
        resource_id=export_id,
        request_path=str(request.url.path),
        ip_address=request.client.host if request.client else None,
    )
    
    # In production, would return actual file
    return {
        "message": "Export marked as downloaded",
        "reference_number": export.reference_number,
        "file_path": export.file_path,
        "file_size_bytes": export.file_size_bytes,
        "file_checksum": export.file_checksum,
    }


# ============================================
# Summary Endpoints
# ============================================

@router.get("/summary", response_model=GovernanceSummary)
async def get_governance_summary(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.AUDIT_VIEW)),
):
    """
    Get governance dashboard summary.
    
    Admin/Principal only.
    """
    service = GovernanceService(db, user.tenant_id)
    data = await service.get_governance_summary()
    
    return GovernanceSummary(**data)
