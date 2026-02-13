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
from app.learning.routers.lesson_evaluation import router as lesson_evaluation_router

# AI
from app.ai.router import router as ai_router
from app.ai.ocr_router import router as ocr_router
from app.ai.question_gen_router import router as question_gen_router

# Billing
from app.billing.router import router as billing_router

# Finance (Fees)
from app.finance.router import router as finance_router

# Payments (Gateway)
from app.payments.router import router as payments_router

# Parent Portal
from app.parents.router import router as parents_router

# Announcements
from app.announcements.router import router as announcements_router

# Attendance
from app.attendance.router import router as attendance_router

# Calendar
from app.calendar.router import router as calendar_router

# Transport
from app.transport.router import router as transport_router

# Hostel
from app.hostel.router import router as hostel_router

# HR & Payroll
from app.hr.router import router as hr_router

# Analytics
from app.analytics.router import router as analytics_router

# Governance
from app.governance.router import router as governance_router
from app.core.corrections_router import router as corrections_router

# AI Insights
from app.insights.router import router as insights_router

# Platform Features
from app.platform.notifications.router import router as notifications_router
from app.platform.files.router import router as files_router
from app.platform.gamification.router import router as gamification_router
from app.platform.reports.router import router as reports_router
from app.platform.admin.router import router as platform_admin_router

# Examinations (Exam Registration, Hall Tickets, Results)
from app.examinations.router import router as examinations_router

# Helpdesk (Support Tickets, Applications)
from app.helpdesk.router import router as helpdesk_router

# Activity Points (Extracurricular Activities)
from app.activity_points.router import router as activity_points_router

# Online Meetings (Virtual Classroom)
from app.meetings.router import router as meetings_router

# Messages (Internal Messaging & Inbox)
from app.messages.router import router as messages_router

# Feedback & Surveys
from app.feedback.router import router as feedback_router

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

# Learning (Lesson Evaluation & Adaptive)
router.include_router(lesson_evaluation_router, prefix="/loops/lesson")

# AI Features
router.include_router(ai_router, prefix="/ai")

# AI OCR Engine
router.include_router(ocr_router, prefix="/ai/ocr")

# AI Question Generator
router.include_router(question_gen_router, prefix="/ai")

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

# Finance (Fees)
router.include_router(finance_router, prefix="/finance")

# Payments (Gateway Integration)
router.include_router(payments_router, prefix="/payments")

# Parent Portal
router.include_router(parents_router, prefix="/parents")

# Announcements
router.include_router(announcements_router, prefix="/announcements")

# Attendance
router.include_router(attendance_router, prefix="/attendance")

# Calendar
router.include_router(calendar_router, prefix="/calendar")

# Transport
router.include_router(transport_router, prefix="/transport")

# Hostel
router.include_router(hostel_router, prefix="/hostel")

# HR & Payroll
router.include_router(hr_router, prefix="/hr")

# Analytics
router.include_router(analytics_router, prefix="/analytics")

# Governance
router.include_router(governance_router, prefix="/governance")

# Corrections (Safe Reversal Framework)
router.include_router(corrections_router, prefix="/corrections")

# AI Insights
router.include_router(insights_router, prefix="/insights")

# Platform Admin (non-tenant-scoped)
router.include_router(platform_admin_router)

# Examinations (Exam Registration, Hall Tickets, Results, Revaluation)
router.include_router(examinations_router, prefix="/examinations")

# Helpdesk (Support Tickets, Applications, Transcripts, Grace Marks)
router.include_router(helpdesk_router, prefix="/helpdesk")

# Activity Points (Extracurricular Activities, Submissions, Certificates)
router.include_router(activity_points_router, prefix="/activity-points")

# Online Meetings (Virtual Classroom, Attendance Tracking)
router.include_router(meetings_router, prefix="/meetings")

# Messages (Internal Messaging, Inbox, Circulars)
router.include_router(messages_router, prefix="/messages")

# Feedback & Surveys (Course/Faculty/General Feedback)
router.include_router(feedback_router, prefix="/feedback")

# Library Management
from app.library.router import router as library_router
router.include_router(library_router, prefix="/library")

