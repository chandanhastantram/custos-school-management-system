"""
CUSTOS AI Insights Schemas

Pydantic schemas for explainable AI insights.

CORE PHILOSOPHY:
- AI explains, never decides
- No student comparison
- Insights are suggestions only
"""

from datetime import datetime, date
from typing import Optional, List, Any
from uuid import UUID
from decimal import Decimal

from pydantic import BaseModel, Field, ConfigDict, field_validator

from app.insights.models import (
    InsightType,
    InsightCategory,
    InsightSeverity,
    JobStatus,
    RequestorRole,
)


# ============================================
# Insight Request Schemas
# ============================================

class InsightRequestCreate(BaseModel):
    """
    Request to generate AI insights.
    
    RULES:
    - Students/Parents CANNOT request insights
    - Teachers can only request for their own classes
    - Admin can request all types
    """
    insight_type: InsightType
    target_id: Optional[UUID] = None  # Required for STUDENT, CLASS, TEACHER types
    period_start: date
    period_end: date
    
    @field_validator("period_end")
    @classmethod
    def validate_period(cls, v, info):
        if info.data.get("period_start") and v < info.data["period_start"]:
            raise ValueError("period_end must be after period_start")
        return v


class InsightRequestResponse(BaseModel):
    """Response after requesting insights."""
    job_id: UUID
    insight_type: InsightType
    target_id: Optional[UUID] = None
    status: JobStatus
    message: str
    estimated_time_seconds: Optional[int] = None


# ============================================
# Insight Job Schemas
# ============================================

class InsightJobResponse(BaseModel):
    """Insight job details."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    requested_by: UUID
    requestor_role: RequestorRole
    requestor_email: Optional[str] = None
    
    insight_type: InsightType
    target_id: Optional[UUID] = None
    target_name: Optional[str] = None
    
    period_start: datetime
    period_end: datetime
    
    status: JobStatus
    tokens_used: int
    
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    # Number of insights generated
    insight_count: int = 0


class InsightJobListItem(BaseModel):
    """Condensed job for listing."""
    id: UUID
    insight_type: InsightType
    target_name: Optional[str] = None
    status: JobStatus
    created_at: datetime
    insight_count: int = 0


# ============================================
# Generated Insight Schemas
# ============================================

class GeneratedInsightResponse(BaseModel):
    """
    Generated insight response.
    
    Human-readable, explainable insight.
    NO raw data, NO identifiable student information.
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    insight_job_id: UUID
    
    category: InsightCategory
    severity: InsightSeverity
    
    # Human-readable content
    title: str
    explanation_text: str
    
    # Evidence (snapshot references only)
    evidence_json: Optional[dict] = None
    
    # Advisory suggestions (not mandatory)
    suggested_actions: Optional[List[str]] = None
    
    # Confidence (0.0 - 1.0)
    confidence_score: float
    
    # Metadata
    is_actionable: bool = True
    created_at: datetime


class GeneratedInsightListItem(BaseModel):
    """Condensed insight for listing."""
    id: UUID
    category: InsightCategory
    severity: InsightSeverity
    title: str
    confidence_score: float
    is_actionable: bool


# ============================================
# Job with Insights (Complete Response)
# ============================================

class InsightJobWithInsights(BaseModel):
    """Job with all generated insights."""
    job: InsightJobResponse
    insights: List[GeneratedInsightResponse]


# ============================================
# Quota Schemas
# ============================================

class InsightQuotaResponse(BaseModel):
    """Insight quota status."""
    month: int
    year: int
    max_requests: int
    max_tokens: int
    requests_used: int
    tokens_used: int
    requests_remaining: int
    tokens_remaining: int
    usage_percentage: float


# ============================================
# AI Prompt Input (Internal)
# ============================================

class AnonymizedStudentData(BaseModel):
    """
    Anonymized student data for AI input.
    
    CRITICAL: No identifiable information.
    Uses snapshot data only.
    """
    activity_score: float  # NEVER actual_score for students
    daily_participation_pct: float
    weekly_participation_pct: float
    lesson_participation_pct: float
    attendance_pct: float
    trend: str  # "improving", "stable", "declining"
    weak_concept_count: int
    strong_concept_count: int
    # NO name, NO id, NO email, NO raw marks


class AnonymizedClassData(BaseModel):
    """
    Anonymized class data for AI input.
    
    Aggregates only, no individual data.
    """
    student_count: int
    avg_participation: float
    avg_attendance: float
    topic_mastery_distribution: dict  # {topic: avg_mastery}
    weak_topic_count: int
    strong_topic_count: int
    # NO individual student data


class AnonymizedTeacherData(BaseModel):
    """
    Anonymized teacher data for AI input.
    """
    syllabus_coverage_pct: float
    lessons_planned: int
    lessons_completed: int
    schedule_adherence_pct: float
    class_participation_pct: float
    engagement_score: float
    # NO teacher identity in AI input


class AIInsightRequest(BaseModel):
    """
    Internal schema for AI insight generation.
    
    This is what goes to the AI model.
    FULLY ANONYMIZED.
    """
    insight_type: InsightType
    period_description: str  # e.g., "Last 30 days"
    data: dict  # Anonymized data payload
    context: Optional[str] = None


class AIInsightOutput(BaseModel):
    """
    Expected output from AI model.
    """
    insights: List[dict]  # Each with category, severity, title, explanation, actions


# ============================================
# Insight Summary
# ============================================

class InsightSummary(BaseModel):
    """Summary of insights for dashboard."""
    total_jobs: int
    completed_jobs: int
    pending_jobs: int
    total_insights: int
    critical_insights: int
    warning_insights: int
    info_insights: int
    tokens_used_this_month: int
    quota_remaining: int
