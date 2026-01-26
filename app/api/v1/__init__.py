"""
CUSTOS API V1 Router

Main router for v1 API endpoints.
"""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.questions import router as questions_router
from app.api.v1.ai import router as ai_router
from app.api.v1.corrections import router as corrections_router
from app.api.v1.reports import router as reports_router
from app.api.v1.subscription import router as subscription_router
from app.api.v1.academic import router as academic_router
from app.api.v1.assignments import router as assignments_router
from app.api.v1.tenants import router as tenants_router
from app.api.v1.calendar import router as calendar_router
from app.api.v1.posts import router as posts_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.files import router as files_router
from app.api.v1.gamification import router as gamification_router


router = APIRouter(prefix="/v1")

# Authentication
router.include_router(auth_router)

# User Management
router.include_router(users_router)

# Tenant Management (School Registration)
router.include_router(tenants_router)

# Academic Structure
router.include_router(academic_router)

# Questions & Assignments
router.include_router(questions_router)
router.include_router(assignments_router)

# Grading & Corrections
router.include_router(corrections_router)

# AI Features
router.include_router(ai_router)

# Reports & Analytics
router.include_router(reports_router)

# Calendar & Scheduling
router.include_router(calendar_router)

# Posts & Notifications
router.include_router(posts_router)
router.include_router(notifications_router)

# Files & Storage
router.include_router(files_router)

# Gamification
router.include_router(gamification_router)

# Subscription & Billing
router.include_router(subscription_router)
