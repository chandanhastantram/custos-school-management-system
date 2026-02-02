"""
CUSTOS AI Insights Router

API endpoints for AI-powered decision support.

CORE PHILOSOPHY:
1. AI EXPLAINS — IT NEVER DECIDES
2. NO STUDENT COMPARISON
3. NO AUTOMATED ACTIONS
4. GOVERNANCE FIRST
5. INSIGHTS ARE SUGGESTIONS ONLY

SECURITY:
- Students: NO ACCESS
- Parents: NO ACCESS
- Teachers: Own classes and self only
- Admins: Full access
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth.dependencies import CurrentUser, require_permission
from app.users.rbac import Permission, SystemRole
from app.insights.service import InsightsService
from app.insights.models import (
    InsightType,
    InsightCategory,
    InsightSeverity,
    JobStatus,
    RequestorRole,
)
from app.insights.schemas import (
    InsightRequestCreate,
    InsightRequestResponse,
    InsightJobResponse,
    InsightJobListItem,
    InsightJobWithInsights,
    GeneratedInsightResponse,
    GeneratedInsightListItem,
    InsightQuotaResponse,
    InsightSummary,
)


router = APIRouter(tags=["Insights"])


def _get_requestor_role(user_role: str) -> RequestorRole:
    """Map user role to requestor role."""
    if user_role in [SystemRole.SUPER_ADMIN.value, SystemRole.PRINCIPAL.value]:
        return RequestorRole.PRINCIPAL
    elif user_role == SystemRole.SUB_ADMIN.value:
        return RequestorRole.ADMIN
    elif user_role == SystemRole.TEACHER.value:
        return RequestorRole.TEACHER
    else:
        raise HTTPException(
            status_code=403,
            detail="Only administrators and teachers can access AI insights"
        )


# ============================================
# Request Insights
# ============================================

@router.post("/request", response_model=InsightRequestResponse)
async def request_insight(
    data: InsightRequestCreate,
    request: Request,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.INSIGHTS_REQUEST)),
):
    """
    Request AI-generated insights.
    
    RULES:
    - Students & Parents: NO ACCESS
    - Teachers: STUDENT (own class), CLASS (own), TEACHER (self only)
    - Admins: All insight types
    
    AI will analyze anonymized data and provide explainable insights.
    Insights are SUGGESTIONS only, never automated decisions.
    """
    requestor_role = _get_requestor_role(user.role)
    
    service = InsightsService(db, user.tenant_id)
    
    try:
        job = await service.request_insight(
            requestor_id=user.id,
            requestor_role=requestor_role,
            requestor_email=user.email,
            insight_type=data.insight_type,
            target_id=data.target_id,
            period_start=data.period_start,
            period_end=data.period_end,
            ip_address=request.client.host if request.client else None,
        )
        
        # Generate insights synchronously for now
        # In production, this could be async with a job queue
        job = await service.generate_insight(job.id)
        
        return InsightRequestResponse(
            job_id=job.id,
            insight_type=job.insight_type,
            target_id=job.target_id,
            status=job.status,
            message="Insights generated successfully" if job.status == JobStatus.COMPLETED else "Insight generation in progress",
            estimated_time_seconds=None,
        )
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================
# Admin/Principal Endpoints
# ============================================

@router.get("/jobs", response_model=List[InsightJobListItem])
async def get_all_jobs(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    insight_type: Optional[InsightType] = None,
    status: Optional[JobStatus] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    _=Depends(require_permission(Permission.INSIGHTS_VIEW)),
):
    """
    Get all insight jobs (Admin/Principal only).
    
    Returns a list of all insight generation jobs.
    """
    requestor_role = _get_requestor_role(user.role)
    
    # Teachers can only see their own jobs
    requestor_id = user.id if requestor_role == RequestorRole.TEACHER else None
    
    service = InsightsService(db, user.tenant_id)
    jobs = await service.get_jobs(
        requestor_id=requestor_id,
        insight_type=insight_type,
        status=status,
        skip=skip,
        limit=limit,
    )
    
    return [
        InsightJobListItem(
            id=job.id,
            insight_type=job.insight_type,
            target_name=job.target_name,
            status=job.status,
            created_at=job.created_at,
            insight_count=len(job.insights) if job.insights else 0,
        )
        for job in jobs
    ]


@router.get("/jobs/{job_id}", response_model=InsightJobWithInsights)
async def get_job_detail(
    job_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.INSIGHTS_VIEW)),
):
    """
    Get insight job with all generated insights.
    
    Returns the job details and all insights generated for it.
    """
    requestor_role = _get_requestor_role(user.role)
    service = InsightsService(db, user.tenant_id)
    
    job = await service.get_job_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Teachers can only view their own jobs
    if requestor_role == RequestorRole.TEACHER and job.requested_by != user.id:
        raise HTTPException(
            status_code=403,
            detail="Teachers can only view their own insight requests"
        )
    
    insights = await service.get_insights_for_job(job_id)
    
    return InsightJobWithInsights(
        job=InsightJobResponse(
            id=job.id,
            tenant_id=job.tenant_id,
            requested_by=job.requested_by,
            requestor_role=job.requestor_role,
            requestor_email=job.requestor_email,
            insight_type=job.insight_type,
            target_id=job.target_id,
            target_name=job.target_name,
            period_start=job.period_start,
            period_end=job.period_end,
            status=job.status,
            tokens_used=job.tokens_used,
            created_at=job.created_at,
            completed_at=job.completed_at,
            insight_count=len(insights),
        ),
        insights=[
            GeneratedInsightResponse(
                id=i.id,
                insight_job_id=i.insight_job_id,
                category=i.category,
                severity=i.severity,
                title=i.title,
                explanation_text=i.explanation_text,
                evidence_json=i.evidence_json,
                suggested_actions=i.suggested_actions,
                confidence_score=float(i.confidence_score),
                is_actionable=i.is_actionable,
                created_at=i.created_at,
            )
            for i in insights
        ],
    )


# ============================================
# Teacher Endpoints
# ============================================

@router.get("/my-insights", response_model=List[InsightJobListItem])
async def get_my_insights(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    insight_type: Optional[InsightType] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    _=Depends(require_permission(Permission.INSIGHTS_VIEW)),
):
    """
    Get my insight requests (Teacher endpoint).
    
    Teachers can view all insight requests they have made.
    """
    service = InsightsService(db, user.tenant_id)
    
    jobs = await service.get_my_insights(
        user_id=user.id,
        skip=skip,
        limit=limit,
    )
    
    # Filter by type if specified
    if insight_type:
        jobs = [j for j in jobs if j.insight_type == insight_type]
    
    return [
        InsightJobListItem(
            id=job.id,
            insight_type=job.insight_type,
            target_name=job.target_name,
            status=job.status,
            created_at=job.created_at,
            insight_count=len(job.insights) if job.insights else 0,
        )
        for job in jobs
    ]


# ============================================
# Quota Endpoints
# ============================================

@router.get("/quota", response_model=InsightQuotaResponse)
async def get_quota_status(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.INSIGHTS_VIEW)),
):
    """
    Get current AI insight quota status.
    
    Shows monthly usage and remaining quota.
    """
    service = InsightsService(db, user.tenant_id)
    quota_data = await service.get_quota_status()
    
    return InsightQuotaResponse(**quota_data)


# ============================================
# Summary Endpoints
# ============================================

@router.get("/summary", response_model=InsightSummary)
async def get_insights_summary(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.INSIGHTS_VIEW)),
):
    """
    Get insights summary for dashboard.
    
    Admin/Principal only - shows overview of all insights.
    """
    requestor_role = _get_requestor_role(user.role)
    
    if requestor_role == RequestorRole.TEACHER:
        raise HTTPException(
            status_code=403,
            detail="Summary is admin-only"
        )
    
    service = InsightsService(db, user.tenant_id)
    summary = await service.get_insight_summary()
    
    return InsightSummary(**summary)


# ============================================
# Health Check
# ============================================

@router.get("/health")
async def insights_health():
    """Health check for insights service."""
    return {
        "status": "healthy",
        "service": "AI Insights & Decision Support",
        "version": "1.0",
        "philosophy": [
            "AI EXPLAINS — IT NEVER DECIDES",
            "NO STUDENT COMPARISON",
            "NO AUTOMATED ACTIONS",
            "GOVERNANCE FIRST",
            "INSIGHTS ARE SUGGESTIONS ONLY",
        ],
    }
