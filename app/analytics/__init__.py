"""
CUSTOS Analytics & Performance Intelligence Module

Deterministic analytics engine with strict role-based visibility.

CORE PRINCIPLES:
1. NO student-to-student comparison
2. Activity Score visible to students, Actual Score hidden
3. Strict role-based visibility
4. No AI - pure aggregation only
5. No rankings or leaderboards
"""

from app.analytics.models import (
    StudentAnalyticsSnapshot,
    TeacherAnalyticsSnapshot,
    ClassAnalyticsSnapshot,
    AnalyticsPeriod,
)
from app.analytics.service import AnalyticsService
from app.analytics.router import router as analytics_router

__all__ = [
    # Models
    "StudentAnalyticsSnapshot",
    "TeacherAnalyticsSnapshot",
    "ClassAnalyticsSnapshot",
    "AnalyticsPeriod",
    # Service
    "AnalyticsService",
    # Router
    "analytics_router",
]
