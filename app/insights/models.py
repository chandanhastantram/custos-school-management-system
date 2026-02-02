"""
CUSTOS AI Insights & Decision Support Models

Explainable AI that advises, never decides.

CORE PHILOSOPHY:
1. AI EXPLAINS — IT NEVER DECIDES
2. NO STUDENT COMPARISON
3. NO AUTOMATED ACTIONS
4. GOVERNANCE FIRST
5. INSIGHTS ARE SUGGESTIONS ONLY
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List
from uuid import UUID

from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, Index, Integer, Numeric
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import TenantBaseModel


# ============================================
# Enums
# ============================================

class InsightType(str, Enum):
    """Types of insights that can be requested."""
    STUDENT = "student"       # Teacher/Admin: individual student patterns
    CLASS = "class"           # Teacher/Admin: class-level patterns
    TEACHER = "teacher"       # Admin/Self: teaching effectiveness
    SCHOOL = "school"         # Admin only: school-wide patterns


class InsightCategory(str, Enum):
    """Categories of generated insights."""
    ENGAGEMENT = "engagement"     # Participation patterns
    MASTERY = "mastery"           # Learning outcomes
    ATTENDANCE = "attendance"     # Attendance patterns
    COVERAGE = "coverage"         # Syllabus coverage
    PACING = "pacing"             # Learning pace
    RECOVERY = "recovery"         # Improvement after struggles
    CONSISTENCY = "consistency"   # Pattern stability


class InsightSeverity(str, Enum):
    """Severity levels for insights."""
    INFO = "info"           # Positive or neutral observation
    WARNING = "warning"     # Needs attention
    CRITICAL = "critical"   # Urgent attention needed


class JobStatus(str, Enum):
    """Status of insight generation jobs."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class RequestorRole(str, Enum):
    """Role of the person requesting insights."""
    ADMIN = "admin"
    PRINCIPAL = "principal"
    TEACHER = "teacher"


# ============================================
# Insight Job
# ============================================

class InsightJob(TenantBaseModel):
    """
    Insight Generation Job.
    
    Tracks requests for AI-generated insights with full audit trail.
    Every insight request is logged for governance.
    """
    __tablename__ = "insights_jobs"
    
    __table_args__ = (
        Index("ix_insight_job_tenant_status", "tenant_id", "status"),
        Index("ix_insight_job_requestor", "requested_by"),
    )
    
    # Who requested
    requested_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False,
    )
    requestor_role: Mapped[RequestorRole] = mapped_column(
        SQLEnum(RequestorRole),
        nullable=False,
    )
    requestor_email: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # What type of insight
    insight_type: Mapped[InsightType] = mapped_column(
        SQLEnum(InsightType),
        nullable=False,
    )
    
    # Target (depends on insight_type)
    target_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,  # null for SCHOOL type
    )
    target_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # Period
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Source snapshots (references only, not raw data)
    snapshot_ids_json: Mapped[Optional[List]] = mapped_column(JSONB, nullable=True)
    
    # Status
    status: Mapped[JobStatus] = mapped_column(
        SQLEnum(JobStatus),
        default=JobStatus.PENDING,
    )
    
    # AI usage tracking
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    prompt_version: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    model_used: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Timing
    processing_started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Error tracking
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Request context (for audit)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    
    # Relationships
    insights: Mapped[List["GeneratedInsight"]] = relationship(
        "GeneratedInsight",
        back_populates="job",
        lazy="selectin",
    )


# ============================================
# Generated Insight
# ============================================

class GeneratedInsight(TenantBaseModel):
    """
    Generated Insight.
    
    Human-readable, explainable insight generated by AI.
    
    CRITICAL RULES:
    - No raw student data
    - No identifiable information in titles/explanations
    - Evidence references snapshot IDs only
    - Suggestions are advisory, never mandatory
    """
    __tablename__ = "insights_generated"
    
    __table_args__ = (
        Index("ix_insight_job", "insight_job_id"),
        Index("ix_insight_category", "category"),
        Index("ix_insight_severity", "severity"),
    )
    
    # Parent job
    insight_job_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("insights_jobs.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Category and severity
    category: Mapped[InsightCategory] = mapped_column(
        SQLEnum(InsightCategory),
        nullable=False,
    )
    severity: Mapped[InsightSeverity] = mapped_column(
        SQLEnum(InsightSeverity),
        default=InsightSeverity.INFO,
    )
    
    # Content (human-readable, no raw data)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    explanation_text: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Evidence (references ONLY, not raw data)
    evidence_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # Suggested actions (array of advisory text)
    suggested_actions: Mapped[Optional[List]] = mapped_column(JSONB, nullable=True)
    
    # Confidence
    confidence_score: Mapped[Decimal] = mapped_column(
        Numeric(3, 2),
        default=Decimal("0.5"),
    )
    
    # Metadata
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    is_actionable: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationship
    job: Mapped["InsightJob"] = relationship(
        "InsightJob",
        back_populates="insights",
    )


# ============================================
# Insight Quota (per tenant/month)
# ============================================

class InsightQuota(TenantBaseModel):
    """
    Insight Quota Tracking.
    
    Controls AI usage per tenant per month.
    """
    __tablename__ = "insights_quotas"
    
    __table_args__ = (
        Index("ix_insight_quota_tenant_month", "tenant_id", "month", "year"),
    )
    
    # Period
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Limits
    max_requests: Mapped[int] = mapped_column(Integer, default=100)
    max_tokens: Mapped[int] = mapped_column(Integer, default=100000)
    
    # Usage
    requests_used: Mapped[int] = mapped_column(Integer, default=0)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    
    # Last request
    last_request_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
