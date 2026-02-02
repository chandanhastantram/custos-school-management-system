"""
CUSTOS Governance Service

Enterprise-grade audit logging and compliance service.

CORE PRINCIPLES:
1. IMMUTABLE AUDIT LOGS - Append-only, never update/delete
2. Log every significant action
3. Capture context (IP, user agent, request ID)
4. Support inspection exports
"""

import json
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundError, ValidationError
from app.governance.models import (
    AuditLog,
    DataAccessLog,
    ConsentRecord,
    InspectionExport,
    ActionType,
    EntityType,
    AccessType,
    SubjectType,
    ConsentType,
    InspectionScope,
    InspectionStatus,
)
from app.governance.schemas import (
    AuditLogCreateInternal,
    DataAccessLogCreateInternal,
    AuditLogFilter,
    DataAccessLogFilter,
    ConsentFilter,
    InspectionExportFilter,
)


class GovernanceService:
    """
    Service for governance, compliance, and audit operations.
    
    This service is CRITICAL for enterprise deployment.
    Audit logs are APPEND-ONLY and IMMUTABLE.
    """
    
    # Export expiry duration
    EXPORT_EXPIRY_HOURS = 72
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
    
    # ============================================
    # Audit Log Operations (APPEND-ONLY)
    # ============================================
    
    async def log_action(
        self,
        action_type: ActionType,
        entity_type: EntityType,
        entity_id: Optional[UUID] = None,
        entity_name: Optional[str] = None,
        actor_user_id: Optional[UUID] = None,
        actor_role: Optional[str] = None,
        actor_email: Optional[str] = None,
        old_value: Optional[Any] = None,
        new_value: Optional[Any] = None,
        description: Optional[str] = None,
        metadata: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> AuditLog:
        """
        Log an action to the audit trail.
        
        This is the PRIMARY method for audit logging.
        Called from all modules when significant actions occur.
        
        Audit logs are APPEND-ONLY and IMMUTABLE.
        """
        # Serialize values to JSON-safe format
        old_value_json = self._serialize_value(old_value) if old_value is not None else None
        new_value_json = self._serialize_value(new_value) if new_value is not None else None
        
        audit_log = AuditLog(
            tenant_id=self.tenant_id,
            actor_user_id=actor_user_id,
            actor_role=actor_role,
            actor_email=actor_email,
            action_type=action_type,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=entity_name,
            old_value_json=old_value_json,
            new_value_json=new_value_json,
            description=description,
            metadata_json=metadata,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            timestamp=datetime.now(timezone.utc),
        )
        
        self.session.add(audit_log)
        await self.session.commit()
        await self.session.refresh(audit_log)
        return audit_log
    
    async def log_action_from_schema(self, data: AuditLogCreateInternal) -> AuditLog:
        """Log action from internal schema."""
        return await self.log_action(
            action_type=data.action_type,
            entity_type=data.entity_type,
            entity_id=data.entity_id,
            entity_name=data.entity_name,
            actor_user_id=data.actor_user_id,
            actor_role=data.actor_role,
            actor_email=data.actor_email,
            old_value=data.old_value_json,
            new_value=data.new_value_json,
            description=data.description,
            metadata=data.metadata_json,
            ip_address=data.ip_address,
            user_agent=data.user_agent,
            request_id=data.request_id,
        )
    
    def _serialize_value(self, value: Any) -> dict:
        """Serialize a value to JSON-safe format."""
        if isinstance(value, dict):
            return {k: self._serialize_single(v) for k, v in value.items()}
        elif hasattr(value, "__dict__"):
            return {k: self._serialize_single(v) for k, v in value.__dict__.items() if not k.startswith("_")}
        else:
            return {"value": self._serialize_single(value)}
    
    def _serialize_single(self, value: Any) -> Any:
        """Serialize a single value."""
        if isinstance(value, UUID):
            return str(value)
        elif isinstance(value, datetime):
            return value.isoformat()
        elif hasattr(value, "value"):  # Enum
            return value.value
        else:
            return value
    
    async def get_audit_logs(
        self,
        filters: Optional[AuditLogFilter] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[AuditLog]:
        """
        Get audit logs with optional filtering.
        
        Ordered by timestamp descending (newest first).
        """
        query = select(AuditLog).where(
            AuditLog.tenant_id == self.tenant_id
        )
        
        if filters:
            if filters.action_type:
                query = query.where(AuditLog.action_type == filters.action_type)
            if filters.entity_type:
                query = query.where(AuditLog.entity_type == filters.entity_type)
            if filters.entity_id:
                query = query.where(AuditLog.entity_id == filters.entity_id)
            if filters.actor_user_id:
                query = query.where(AuditLog.actor_user_id == filters.actor_user_id)
            if filters.date_from:
                query = query.where(AuditLog.timestamp >= filters.date_from)
            if filters.date_to:
                query = query.where(AuditLog.timestamp <= filters.date_to)
            if filters.search:
                search_term = f"%{filters.search}%"
                query = query.where(
                    or_(
                        AuditLog.description.ilike(search_term),
                        AuditLog.entity_name.ilike(search_term),
                        AuditLog.actor_email.ilike(search_term),
                    )
                )
        
        query = query.order_by(desc(AuditLog.timestamp)).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_audit_log_by_id(self, log_id: UUID) -> Optional[AuditLog]:
        """Get a single audit log by ID."""
        query = select(AuditLog).where(
            AuditLog.tenant_id == self.tenant_id,
            AuditLog.id == log_id,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def count_audit_logs(
        self,
        filters: Optional[AuditLogFilter] = None,
    ) -> int:
        """Count audit logs with optional filtering."""
        query = select(func.count(AuditLog.id)).where(
            AuditLog.tenant_id == self.tenant_id
        )
        
        if filters:
            if filters.action_type:
                query = query.where(AuditLog.action_type == filters.action_type)
            if filters.entity_type:
                query = query.where(AuditLog.entity_type == filters.entity_type)
            if filters.date_from:
                query = query.where(AuditLog.timestamp >= filters.date_from)
            if filters.date_to:
                query = query.where(AuditLog.timestamp <= filters.date_to)
        
        result = await self.session.execute(query)
        return result.scalar() or 0
    
    # ============================================
    # Data Access Log Operations
    # ============================================
    
    async def log_data_access(
        self,
        user_id: UUID,
        accessed_resource: str,
        access_type: AccessType,
        user_role: Optional[str] = None,
        user_email: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_path: Optional[str] = None,
        success: bool = True,
        records_accessed: int = 1,
    ) -> DataAccessLog:
        """
        Log data access for privacy compliance.
        
        Tracks who accessed what data and when.
        """
        log = DataAccessLog(
            tenant_id=self.tenant_id,
            user_id=user_id,
            user_role=user_role,
            user_email=user_email,
            accessed_resource=accessed_resource,
            resource_type=resource_type,
            resource_id=resource_id,
            access_type=access_type,
            ip_address=ip_address,
            user_agent=user_agent,
            request_path=request_path,
            success=success,
            records_accessed=records_accessed,
            timestamp=datetime.now(timezone.utc),
        )
        
        self.session.add(log)
        await self.session.commit()
        await self.session.refresh(log)
        return log
    
    async def log_data_access_from_schema(
        self,
        data: DataAccessLogCreateInternal,
    ) -> DataAccessLog:
        """Log data access from internal schema."""
        return await self.log_data_access(
            user_id=data.user_id,
            user_role=data.user_role,
            user_email=data.user_email,
            accessed_resource=data.accessed_resource,
            resource_type=data.resource_type,
            resource_id=data.resource_id,
            access_type=data.access_type,
            ip_address=data.ip_address,
            user_agent=data.user_agent,
            request_path=data.request_path,
            success=data.success,
            records_accessed=data.records_accessed,
        )
    
    async def get_data_access_logs(
        self,
        filters: Optional[DataAccessLogFilter] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[DataAccessLog]:
        """Get data access logs with optional filtering."""
        query = select(DataAccessLog).where(
            DataAccessLog.tenant_id == self.tenant_id
        )
        
        if filters:
            if filters.user_id:
                query = query.where(DataAccessLog.user_id == filters.user_id)
            if filters.resource_type:
                query = query.where(DataAccessLog.resource_type == filters.resource_type)
            if filters.access_type:
                query = query.where(DataAccessLog.access_type == filters.access_type)
            if filters.date_from:
                query = query.where(DataAccessLog.timestamp >= filters.date_from)
            if filters.date_to:
                query = query.where(DataAccessLog.timestamp <= filters.date_to)
        
        query = query.order_by(desc(DataAccessLog.timestamp)).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    # ============================================
    # Consent Operations
    # ============================================
    
    async def grant_consent(
        self,
        subject_type: SubjectType,
        subject_id: UUID,
        consent_type: ConsentType,
        subject_name: Optional[str] = None,
        guardian_user_id: Optional[UUID] = None,
        guardian_name: Optional[str] = None,
        guardian_relation: Optional[str] = None,
        consent_text: Optional[str] = None,
        consent_version: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        ip_address: Optional[str] = None,
        granted_by: Optional[UUID] = None,
    ) -> ConsentRecord:
        """
        Record consent grant.
        
        For minors, guardian information is required.
        """
        # Check for existing active consent
        existing = await self._get_active_consent(subject_type, subject_id, consent_type)
        if existing:
            # Revoke old consent before granting new
            existing.revoked = True
            existing.revoked_at = datetime.now(timezone.utc)
            existing.revoked_by = granted_by
            existing.revocation_reason = "Superseded by new consent"
        
        consent = ConsentRecord(
            tenant_id=self.tenant_id,
            subject_type=subject_type,
            subject_id=subject_id,
            subject_name=subject_name,
            guardian_user_id=guardian_user_id,
            guardian_name=guardian_name,
            guardian_relation=guardian_relation,
            consent_type=consent_type,
            consent_text=consent_text,
            consent_version=consent_version,
            granted=True,
            granted_at=datetime.now(timezone.utc),
            granted_ip=ip_address,
            revoked=False,
            expires_at=expires_at,
        )
        
        self.session.add(consent)
        await self.session.commit()
        await self.session.refresh(consent)
        
        # Log the consent grant
        await self.log_action(
            action_type=ActionType.CREATE,
            entity_type=EntityType.CONSENT,
            entity_id=consent.id,
            entity_name=f"{consent_type.value} consent for {subject_type.value}",
            actor_user_id=granted_by or guardian_user_id,
            description=f"Consent granted: {consent_type.value}",
        )
        
        return consent
    
    async def revoke_consent(
        self,
        consent_id: UUID,
        revoked_by: UUID,
        reason: Optional[str] = None,
    ) -> ConsentRecord:
        """
        Revoke a consent record.
        
        Consent revocation is immediate and permanent.
        """
        query = select(ConsentRecord).where(
            ConsentRecord.tenant_id == self.tenant_id,
            ConsentRecord.id == consent_id,
        )
        result = await self.session.execute(query)
        consent = result.scalar_one_or_none()
        
        if not consent:
            raise ResourceNotFoundError("Consent record not found")
        
        if consent.revoked:
            raise ValidationError("Consent already revoked")
        
        consent.revoked = True
        consent.revoked_at = datetime.now(timezone.utc)
        consent.revoked_by = revoked_by
        consent.revocation_reason = reason
        
        await self.session.commit()
        await self.session.refresh(consent)
        
        # Log the revocation
        await self.log_action(
            action_type=ActionType.UPDATE,
            entity_type=EntityType.CONSENT,
            entity_id=consent.id,
            entity_name=f"{consent.consent_type.value} consent",
            actor_user_id=revoked_by,
            description=f"Consent revoked: {reason or 'No reason provided'}",
        )
        
        return consent
    
    async def _get_active_consent(
        self,
        subject_type: SubjectType,
        subject_id: UUID,
        consent_type: ConsentType,
    ) -> Optional[ConsentRecord]:
        """Get active consent for a subject and type."""
        query = select(ConsentRecord).where(
            ConsentRecord.tenant_id == self.tenant_id,
            ConsentRecord.subject_type == subject_type,
            ConsentRecord.subject_id == subject_id,
            ConsentRecord.consent_type == consent_type,
            ConsentRecord.granted == True,
            ConsentRecord.revoked == False,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def check_consent(
        self,
        subject_type: SubjectType,
        subject_id: UUID,
        consent_type: ConsentType,
    ) -> bool:
        """Check if subject has active consent of given type."""
        consent = await self._get_active_consent(subject_type, subject_id, consent_type)
        if not consent:
            return False
        
        # Check expiry
        if consent.expires_at and consent.expires_at < datetime.now(timezone.utc):
            return False
        
        return True
    
    async def get_consent_records(
        self,
        filters: Optional[ConsentFilter] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ConsentRecord]:
        """Get consent records with optional filtering."""
        query = select(ConsentRecord).where(
            ConsentRecord.tenant_id == self.tenant_id
        )
        
        if filters:
            if filters.subject_type:
                query = query.where(ConsentRecord.subject_type == filters.subject_type)
            if filters.subject_id:
                query = query.where(ConsentRecord.subject_id == filters.subject_id)
            if filters.consent_type:
                query = query.where(ConsentRecord.consent_type == filters.consent_type)
            if filters.granted is not None:
                query = query.where(ConsentRecord.granted == filters.granted)
            if filters.revoked is not None:
                query = query.where(ConsentRecord.revoked == filters.revoked)
        
        query = query.order_by(desc(ConsentRecord.created_at)).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_subject_consents(
        self,
        subject_type: SubjectType,
        subject_id: UUID,
    ) -> List[ConsentRecord]:
        """Get all consent records for a subject."""
        query = select(ConsentRecord).where(
            ConsentRecord.tenant_id == self.tenant_id,
            ConsentRecord.subject_type == subject_type,
            ConsentRecord.subject_id == subject_id,
        ).order_by(desc(ConsentRecord.created_at))
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    # ============================================
    # Inspection Export Operations
    # ============================================
    
    async def create_inspection_export(
        self,
        scope: InspectionScope,
        requested_by: UUID,
        requestor_name: Optional[str] = None,
        requestor_role: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        filters_json: Optional[dict] = None,
        purpose: Optional[str] = None,
        notes: Optional[str] = None,
        file_format: str = "json",
    ) -> InspectionExport:
        """
        Create a new inspection export request.
        
        The actual export generation can be done synchronously or async.
        """
        # Generate reference number
        ref_number = f"INS-{datetime.now().strftime('%Y%m%d')}-{str(uuid4())[:8].upper()}"
        
        export = InspectionExport(
            tenant_id=self.tenant_id,
            requested_by=requested_by,
            requestor_name=requestor_name,
            requestor_role=requestor_role,
            scope=scope,
            date_from=date_from,
            date_to=date_to,
            filters_json=filters_json,
            status=InspectionStatus.PENDING,
            file_format=file_format,
            requested_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=self.EXPORT_EXPIRY_HOURS),
            reference_number=ref_number,
            purpose=purpose,
            notes=notes,
        )
        
        self.session.add(export)
        await self.session.commit()
        await self.session.refresh(export)
        
        # Log the export request
        await self.log_action(
            action_type=ActionType.EXPORT,
            entity_type=EntityType.EXPORT,
            entity_id=export.id,
            entity_name=f"Inspection Export: {scope.value}",
            actor_user_id=requested_by,
            description=f"Inspection export requested: {scope.value} scope",
            metadata={"reference_number": ref_number},
        )
        
        return export
    
    async def generate_inspection_export(
        self,
        export_id: UUID,
    ) -> InspectionExport:
        """
        Generate the actual export file.
        
        This is a placeholder implementation.
        In production, this would generate actual data exports.
        """
        query = select(InspectionExport).where(
            InspectionExport.tenant_id == self.tenant_id,
            InspectionExport.id == export_id,
        )
        result = await self.session.execute(query)
        export = result.scalar_one_or_none()
        
        if not export:
            raise ResourceNotFoundError("Export not found")
        
        if export.status not in [InspectionStatus.PENDING, InspectionStatus.FAILED]:
            raise ValidationError(f"Export is already {export.status.value}")
        
        export.status = InspectionStatus.PROCESSING
        await self.session.commit()
        
        try:
            # Generate export data based on scope
            export_data = await self._generate_export_data(
                export.scope, export.date_from, export.date_to, export.filters_json
            )
            
            # Save to file (placeholder - would use file storage in production)
            file_content = json.dumps(export_data, indent=2, default=str)
            file_path = f"exports/{export.reference_number}.{export.file_format}"
            file_size = len(file_content.encode("utf-8"))
            file_checksum = hashlib.sha256(file_content.encode()).hexdigest()
            
            export.status = InspectionStatus.GENERATED
            export.file_path = file_path
            export.file_size_bytes = file_size
            export.file_checksum = file_checksum
            export.generated_at = datetime.now(timezone.utc)
            
        except Exception as e:
            export.status = InspectionStatus.FAILED
            export.error_message = str(e)
        
        await self.session.commit()
        await self.session.refresh(export)
        return export
    
    async def _generate_export_data(
        self,
        scope: InspectionScope,
        date_from: Optional[datetime],
        date_to: Optional[datetime],
        filters_json: Optional[dict],
    ) -> dict:
        """
        Generate export data based on scope.
        
        Placeholder implementation - returns metadata only.
        In production, this would query actual data.
        """
        export_data = {
            "export_metadata": {
                "tenant_id": str(self.tenant_id),
                "scope": scope.value,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "date_range": {
                    "from": date_from.isoformat() if date_from else None,
                    "to": date_to.isoformat() if date_to else None,
                },
                "filters": filters_json,
            },
            "data": {},
        }
        
        if scope == InspectionScope.ACADEMIC:
            export_data["data"] = {
                "students": [],
                "classes": [],
                "subjects": [],
                "attendance": [],
                "assessments": [],
            }
        elif scope == InspectionScope.FINANCE:
            export_data["data"] = {
                "fee_structures": [],
                "payments": [],
                "invoices": [],
            }
        elif scope == InspectionScope.HR:
            export_data["data"] = {
                "employees": [],
                "payroll_runs": [],
                "salary_slips": [],
                "leave_records": [],
            }
        elif scope == InspectionScope.TRANSPORT:
            export_data["data"] = {
                "vehicles": [],
                "routes": [],
                "assignments": [],
            }
        elif scope == InspectionScope.HOSTEL:
            export_data["data"] = {
                "hostels": [],
                "rooms": [],
                "assignments": [],
            }
        elif scope == InspectionScope.ATTENDANCE:
            export_data["data"] = {
                "attendance_records": [],
            }
        elif scope == InspectionScope.FULL:
            export_data["data"] = {
                "academic": {},
                "finance": {},
                "hr": {},
                "transport": {},
                "hostel": {},
                "attendance": {},
                "audit_logs": [],
            }
        
        return export_data
    
    async def get_inspection_exports(
        self,
        filters: Optional[InspectionExportFilter] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[InspectionExport]:
        """Get inspection exports with optional filtering."""
        query = select(InspectionExport).where(
            InspectionExport.tenant_id == self.tenant_id
        )
        
        if filters:
            if filters.scope:
                query = query.where(InspectionExport.scope == filters.scope)
            if filters.status:
                query = query.where(InspectionExport.status == filters.status)
            if filters.date_from:
                query = query.where(InspectionExport.requested_at >= filters.date_from)
            if filters.date_to:
                query = query.where(InspectionExport.requested_at <= filters.date_to)
        
        query = query.order_by(desc(InspectionExport.requested_at)).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_inspection_export_by_id(
        self,
        export_id: UUID,
    ) -> Optional[InspectionExport]:
        """Get a single inspection export by ID."""
        query = select(InspectionExport).where(
            InspectionExport.tenant_id == self.tenant_id,
            InspectionExport.id == export_id,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def mark_export_downloaded(
        self,
        export_id: UUID,
    ) -> InspectionExport:
        """Mark an export as downloaded."""
        export = await self.get_inspection_export_by_id(export_id)
        if not export:
            raise ResourceNotFoundError("Export not found")
        
        if export.status != InspectionStatus.GENERATED:
            raise ValidationError("Export is not ready for download")
        
        export.status = InspectionStatus.DOWNLOADED
        export.downloaded_at = datetime.now(timezone.utc)
        
        await self.session.commit()
        await self.session.refresh(export)
        return export
    
    # ============================================
    # Summary Operations
    # ============================================
    
    async def get_governance_summary(self) -> dict:
        """Get governance summary for dashboard."""
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Audit logs
        total_audit = await self.count_audit_logs()
        audit_today = await self.count_audit_logs(
            AuditLogFilter(date_from=today_start)
        )
        
        # Data access logs
        data_access_query = select(func.count(DataAccessLog.id)).where(
            DataAccessLog.tenant_id == self.tenant_id
        )
        result = await self.session.execute(data_access_query)
        total_data_access = result.scalar() or 0
        
        data_access_today_query = data_access_query.where(
            DataAccessLog.timestamp >= today_start
        )
        result = await self.session.execute(data_access_today_query)
        data_access_today = result.scalar() or 0
        
        # Consents
        pending_consents_query = select(func.count(ConsentRecord.id)).where(
            ConsentRecord.tenant_id == self.tenant_id,
            ConsentRecord.granted == False,
            ConsentRecord.revoked == False,
        )
        result = await self.session.execute(pending_consents_query)
        pending_consents = result.scalar() or 0
        
        active_consents_query = select(func.count(ConsentRecord.id)).where(
            ConsentRecord.tenant_id == self.tenant_id,
            ConsentRecord.granted == True,
            ConsentRecord.revoked == False,
        )
        result = await self.session.execute(active_consents_query)
        active_consents = result.scalar() or 0
        
        revoked_consents_query = select(func.count(ConsentRecord.id)).where(
            ConsentRecord.tenant_id == self.tenant_id,
            ConsentRecord.revoked == True,
        )
        result = await self.session.execute(revoked_consents_query)
        revoked_consents = result.scalar() or 0
        
        # Exports
        pending_exports_query = select(func.count(InspectionExport.id)).where(
            InspectionExport.tenant_id == self.tenant_id,
            InspectionExport.status == InspectionStatus.PENDING,
        )
        result = await self.session.execute(pending_exports_query)
        pending_exports = result.scalar() or 0
        
        generated_exports_query = select(func.count(InspectionExport.id)).where(
            InspectionExport.tenant_id == self.tenant_id,
            InspectionExport.status == InspectionStatus.GENERATED,
        )
        result = await self.session.execute(generated_exports_query)
        generated_exports = result.scalar() or 0
        
        return {
            "total_audit_logs": total_audit,
            "audit_logs_today": audit_today,
            "total_data_access_logs": total_data_access,
            "data_access_today": data_access_today,
            "pending_consents": pending_consents,
            "active_consents": active_consents,
            "revoked_consents": revoked_consents,
            "pending_exports": pending_exports,
            "generated_exports": generated_exports,
        }
