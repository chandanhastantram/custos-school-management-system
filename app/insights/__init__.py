"""
CUSTOS AI Insights & Decision Support Module

Explainable AI that advises, never decides.

CORE PHILOSOPHY:
1. AI EXPLAINS — IT NEVER DECIDES
2. NO STUDENT COMPARISON
3. NO AUTOMATED ACTIONS
4. GOVERNANCE FIRST
5. INSIGHTS ARE SUGGESTIONS ONLY

ACCESS RULES:
- Students: NO ACCESS
- Parents: NO ACCESS
- Teachers: Own classes and self only
- Admins: Full access
"""

from app.insights.models import (
    InsightJob,
    GeneratedInsight,
    InsightQuota,
    InsightType,
    InsightCategory,
    InsightSeverity,
    JobStatus,
    RequestorRole,
)
from app.insights.service import InsightsService
from app.insights.router import router as insights_router

__all__ = [
    # Models
    "InsightJob",
    "GeneratedInsight",
    "InsightQuota",
    # Enums
    "InsightType",
    "InsightCategory",
    "InsightSeverity",
    "JobStatus",
    "RequestorRole",
    # Service
    "InsightsService",
    # Router
    "insights_router",
]
