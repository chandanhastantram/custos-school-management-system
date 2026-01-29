"""
CUSTOS API v1 Router

Aggregates all domain routers.
"""

from fastapi import APIRouter

# Auth & Core
from app.auth.router import router as auth_router
from app.tenants.router import router as tenants_router
from app.users.router import router as users_router

# Academics
from app.academics.routers.structure import router as structure_router
from app.academics.routers.questions import router as questions_router
from app.academics.routers.assignments import router as assignments_router
from app.academics.routers.syllabus import router as syllabus_router
from app.academics.routers.lesson_plans import router as lesson_plans_router
from app.academics.routers.teaching_assignments import router as teaching_assignments_router

# Scheduling
from app.scheduling.routers.timetable import router as timetable_router
from app.scheduling.routers.schedule import router as schedule_router

# Learning
from app.learning.routers.daily_loops import router as daily_loops_router
from app.learning.routers.weekly_tests import router as weekly_tests_router

# AI
from app.ai.router import router as ai_router

# Billing
from app.billing.router import router as billing_router

# Platform Features
from app.platform.notifications.router import router as notifications_router
from app.platform.files.router import router as files_router
from app.platform.gamification.router import router as gamification_router
from app.platform.reports.router import router as reports_router
from app.platform.admin.router import router as platform_admin_router


router = APIRouter(prefix="/v1")

# Authentication
router.include_router(auth_router)

# Tenants (School Registration)
router.include_router(tenants_router)

# User Management
router.include_router(users_router)

# Academic Structure
router.include_router(structure_router, prefix="/academic")

# Questions
router.include_router(questions_router, prefix="/questions")

# Assignments
router.include_router(assignments_router, prefix="/assignments")

# Syllabus Engine (Curriculum)
router.include_router(syllabus_router, prefix="/academics/syllabus")

# Lesson Planning
router.include_router(lesson_plans_router, prefix="/academics/lesson-plans")

# Teaching Assignments (Teacher ↔ Class ↔ Subject)
router.include_router(teaching_assignments_router, prefix="/academics/teaching-assignments")

# Scheduling (Timetables)
router.include_router(timetable_router, prefix="/scheduling/timetables")

# Scheduling (Schedule Orchestration)
router.include_router(schedule_router, prefix="/scheduling")

# Learning (Daily Loops)
router.include_router(daily_loops_router, prefix="/loops")

# Learning (Weekly Evaluation)
router.include_router(weekly_tests_router, prefix="/loops/weekly")

# AI Features
router.include_router(ai_router, prefix="/ai")

# Billing
router.include_router(billing_router, prefix="/billing")

# Notifications
router.include_router(notifications_router, prefix="/notifications")

# Files
router.include_router(files_router, prefix="/files")

# Gamification
router.include_router(gamification_router, prefix="/gamification")

# Reports
router.include_router(reports_router, prefix="/reports")

# Platform Admin (non-tenant-scoped)
router.include_router(platform_admin_router)
