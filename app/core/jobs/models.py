"""
CUSTOS Job Execution Models

Database models for tracking job executions.

This provides:
- Persistent idempotency (prevent duplicate execution)
- Execution history
- Retry tracking
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import TenantBaseModel


class JobExecution(TenantBaseModel):
    """
    Tracks execution of background jobs.
    
    CRITICAL FOR:
    - Idempotency (same job_key + COMPLETED = skip)
    - Audit trail
    - Debugging failed jobs
    """
    
    __tablename__ = "job_executions"
    
    # ============================================
    # Job Identification
    # ============================================
    
    job_key: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        index=True,
        comment="Unique key for this job instance (for idempotency)",
    )
    
    job_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Type of job (e.g., ai_lesson_plan, ocr_process)",
    )
    
    # ============================================
    # Status Tracking
    # ============================================
    
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        index=True,
        comment="Job status: pending, processing, completed, failed, retrying",
    )
    
    attempt: Mapped[int] = mapped_column(
        Integer,
        default=1,
        comment="Current attempt number",
    )
    
    max_attempts: Mapped[int] = mapped_column(
        Integer,
        default=1,
        comment="Maximum retry attempts",
    )
    
    # ============================================
    # Timing
    # ============================================
    
    queued_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When job was queued",
    )
    
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When execution started",
    )
    
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When execution finished",
    )
    
    # ============================================
    # Result/Error
    # ============================================
    
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Error message if failed",
    )
    
    result_json: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Result data if completed",
    )
    
    # ============================================
    # Context
    # ============================================
    
    actor_user_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="User who triggered this job",
    )
    
    request_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Request ID for tracing",
    )
    
    input_json: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Job input parameters (for debugging)",
    )
    
    # ============================================
    # Indexes
    # ============================================
    
    __table_args__ = (
        # Quick lookup for idempotency check
        Index(
            "ix_job_exec_idempotency",
            "tenant_id",
            "job_key",
            "status",
        ),
        # Find jobs by type and status
        Index(
            "ix_job_exec_type_status",
            "tenant_id",
            "job_type",
            "status",
        ),
        # Find recent jobs
        Index(
            "ix_job_exec_recent",
            "tenant_id",
            "created_at",
        ),
        {"extend_existing": True},
    )
    
    def __repr__(self) -> str:
        return f"<JobExecution {self.job_type}:{self.job_key} ({self.status})>"
    
    @property
    def is_completed(self) -> bool:
        return self.status == "completed"
    
    @property
    def is_failed(self) -> bool:
        return self.status == "failed"
    
    @property
    def is_running(self) -> bool:
        return self.status in ("pending", "processing", "retrying")
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate execution duration."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
