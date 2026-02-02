"""
CUSTOS Example Background Jobs

These are example implementations showing how to use the job framework.
Each module should define its own jobs following this pattern.
"""

from typing import Any, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.jobs import (
    AbstractJob,
    JobType,
    register_job,
    RetryableError,
    NonRetryableError,
)


@register_job
class AIInsightJob(AbstractJob):
    """
    Background job for generating AI insights.
    
    Example of a long-running AI job with proper:
    - Idempotency
    - Retry on network errors
    - Audit logging
    """
    
    job_type = JobType.AI_INSIGHT
    
    def __init__(
        self,
        tenant_id: UUID,
        job_id: UUID,
        insight_type: str,
    ):
        super().__init__(tenant_id)
        self.job_id = job_id
        self.insight_type = insight_type
    
    def get_job_key(self) -> str:
        """Unique key for idempotency."""
        return f"ai_insight:{self.job_id}"
    
    def get_entity_type(self) -> str:
        return "ANALYTICS"
    
    def get_entity_id(self) -> Optional[UUID]:
        return self.job_id
    
    def _get_serializable_params(self) -> dict:
        """Parameters for RQ serialization."""
        return {
            "job_id": str(self.job_id),
            "insight_type": self.insight_type,
        }
    
    async def execute(self, session: AsyncSession) -> Any:
        """Execute the insight generation."""
        from app.insights.service import InsightsService
        
        service = InsightsService(session, self.tenant_id)
        
        # Generate insight (this may call AI)
        result = await service.generate_insight(self.job_id)
        
        return {
            "job_id": str(self.job_id),
            "insights_generated": len(result) if isinstance(result, list) else 1,
        }
    
    async def on_success(self, session: AsyncSession, result: Any) -> None:
        """Update job status on success."""
        # Could send notification, update dashboard, etc.
        pass
    
    async def on_failure(self, session: AsyncSession, error: Exception) -> None:
        """Handle failure."""
        # Could send alert, update job record, etc.
        pass


@register_job
class AnalyticsSnapshotJob(AbstractJob):
    """
    Background job for generating analytics snapshots.
    
    Example of a fast, single-attempt job.
    """
    
    job_type = JobType.ANALYTICS_SNAPSHOT
    
    def __init__(
        self,
        tenant_id: UUID,
        target_date: str,  # ISO format
        target_type: str,  # "student", "class", "teacher"
        target_id: Optional[UUID] = None,
    ):
        super().__init__(tenant_id)
        self.target_date = target_date
        self.target_type = target_type
        self.target_id = target_id
    
    def get_job_key(self) -> str:
        """Unique key for idempotency."""
        if self.target_id:
            return f"analytics_snapshot:{self.target_date}:{self.target_type}:{self.target_id}"
        return f"analytics_snapshot:{self.target_date}:{self.target_type}:all"
    
    def get_entity_type(self) -> str:
        return "ANALYTICS"
    
    def _get_serializable_params(self) -> dict:
        return {
            "target_date": self.target_date,
            "target_type": self.target_type,
            "target_id": str(self.target_id) if self.target_id else None,
        }
    
    async def execute(self, session: AsyncSession) -> Any:
        """Execute snapshot generation."""
        from app.analytics.service import AnalyticsService
        from datetime import date
        
        service = AnalyticsService(session, self.tenant_id)
        
        target_date = date.fromisoformat(self.target_date)
        
        # Generate snapshots based on target
        if self.target_type == "student" and self.target_id:
            count = await service.generate_student_snapshot(self.target_id, target_date)
        elif self.target_type == "class" and self.target_id:
            count = await service.generate_class_snapshot(self.target_id, target_date)
        else:
            count = await service.generate_all_snapshots(target_date)
        
        return {
            "date": self.target_date,
            "type": self.target_type,
            "snapshots_generated": count,
        }


@register_job
class ExportInspectionJob(AbstractJob):
    """
    Background job for generating inspection exports.
    
    Example of an export job with audit requirements.
    """
    
    job_type = JobType.EXPORT_INSPECTION
    
    def __init__(
        self,
        tenant_id: UUID,
        export_id: UUID,
        export_type: str,
        requested_by: UUID,
    ):
        super().__init__(tenant_id)
        self.export_id = export_id
        self.export_type = export_type
        self.requested_by = requested_by
        self._actor_user_id = requested_by  # Set for audit
    
    def get_job_key(self) -> str:
        return f"export_inspection:{self.export_id}"
    
    def get_entity_type(self) -> str:
        return "EXPORT"
    
    def get_entity_id(self) -> Optional[UUID]:
        return self.export_id
    
    def _get_serializable_params(self) -> dict:
        return {
            "export_id": str(self.export_id),
            "export_type": self.export_type,
            "requested_by": str(self.requested_by),
        }
    
    async def execute(self, session: AsyncSession) -> Any:
        """Execute export generation."""
        from app.governance.service import GovernanceService
        
        service = GovernanceService(session, self.tenant_id)
        
        # Generate the export
        export = await service.generate_export(self.export_id)
        
        return {
            "export_id": str(self.export_id),
            "file_path": export.file_path if export else None,
            "status": "completed",
        }
