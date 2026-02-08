"""
CUSTOS RBAC

Role-Based Access Control definitions.
"""

from enum import Enum
from typing import Set, Dict


class SystemRole(str, Enum):
    """System-defined roles."""
    SUPER_ADMIN = "super_admin"
    PRINCIPAL = "principal"
    SUB_ADMIN = "sub_admin"
    TEACHER = "teacher"
    STUDENT = "student"
    PARENT = "parent"


class Permission(str, Enum):
    """All permissions in the system."""
    
    # Tenant
    TENANT_VIEW = "tenant:view"
    TENANT_UPDATE = "tenant:update"
    
    # Users
    USER_VIEW = "user:view"
    USER_CREATE = "user:create"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    USER_MANAGE_ROLES = "user:manage_roles"
    
    # Students
    STUDENT_VIEW = "student:view"
    STUDENT_CREATE = "student:create"
    STUDENT_UPDATE = "student:update"
    STUDENT_DELETE = "student:delete"
    STUDENT_LIFECYCLE_MANAGE = "student:lifecycle_manage"  # Lifecycle state transitions
    
    # Teachers
    TEACHER_VIEW = "teacher:view"
    TEACHER_CREATE = "teacher:create"
    TEACHER_UPDATE = "teacher:update"
    TEACHER_DELETE = "teacher:delete"
    
    # Teaching Assignments (Teacher ↔ Class ↔ Subject)
    TEACHING_ASSIGNMENT_VIEW = "teaching_assignment:view"
    TEACHING_ASSIGNMENT_CREATE = "teaching_assignment:create"
    TEACHING_ASSIGNMENT_UPDATE = "teaching_assignment:update"
    TEACHING_ASSIGNMENT_DELETE = "teaching_assignment:delete"
    
    # Academic Structure
    CLASS_VIEW = "class:view"
    CLASS_CREATE = "class:create"
    CLASS_UPDATE = "class:update"
    CLASS_DELETE = "class:delete"
    
    SUBJECT_VIEW = "subject:view"
    SUBJECT_CREATE = "subject:create"
    SUBJECT_UPDATE = "subject:update"
    
    SYLLABUS_VIEW = "syllabus:view"
    SYLLABUS_CREATE = "syllabus:create"
    SYLLABUS_UPDATE = "syllabus:update"
    SYLLABUS_DELETE = "syllabus:delete"
    
    LESSON_VIEW = "lesson:view"
    LESSON_CREATE = "lesson:create"
    LESSON_UPDATE = "lesson:update"
    LESSON_DELETE = "lesson:delete"
    
    # Questions
    QUESTION_VIEW = "question:view"
    QUESTION_CREATE = "question:create"
    QUESTION_UPDATE = "question:update"
    QUESTION_DELETE = "question:delete"
    QUESTION_APPROVE = "question:approve"
    
    # Assignments
    ASSIGNMENT_VIEW = "assignment:view"
    ASSIGNMENT_CREATE = "assignment:create"
    ASSIGNMENT_UPDATE = "assignment:update"
    ASSIGNMENT_DELETE = "assignment:delete"
    ASSIGNMENT_GRADE = "assignment:grade"
    ASSIGNMENT_SUBMIT = "assignment:submit"
    ASSIGNMENT_VIEW_SUBMISSIONS = "assignment:view_submissions"
    
    # Worksheets
    WORKSHEET_VIEW = "worksheet:view"
    WORKSHEET_CREATE = "worksheet:create"
    
    # AI Features
    AI_LESSON_PLAN = "ai:lesson_plan"
    AI_QUESTION_GEN = "ai:question_gen"
    AI_DOUBT_SOLVER = "ai:doubt_solver"
    AI_LESSON_PLAN_GENERATE = "ai:lesson_plan_generate"
    AI_OCR_PROCESS = "ai:ocr_process"
    
    # Reports
    REPORT_VIEW_OWN = "report:view_own"
    REPORT_VIEW_CLASS = "report:view_class"
    REPORT_VIEW_ALL = "report:view_all"
    REPORT_EXPORT = "report:export"
    
    # Calendar
    CALENDAR_VIEW = "calendar:view"
    CALENDAR_CREATE = "calendar:create"
    CALENDAR_UPDATE = "calendar:update"
    CALENDAR_DELETE = "calendar:delete"
    
    TIMETABLE_VIEW = "timetable:view"
    TIMETABLE_CREATE = "timetable:create"
    TIMETABLE_UPDATE = "timetable:update"
    TIMETABLE_DELETE = "timetable:delete"
    
    # Schedule Orchestration
    SCHEDULE_VIEW = "schedule:view"
    SCHEDULE_GENERATE = "schedule:generate"
    SCHEDULE_UPDATE = "schedule:update"
    
    # Posts
    POST_VIEW = "post:view"
    POST_CREATE = "post:create"
    POST_UPDATE = "post:update"
    POST_DELETE = "post:delete"
    
    # Notifications
    NOTIFICATION_SEND = "notification:send"
    
    # Billing
    BILLING_VIEW = "billing:view"
    BILLING_MANAGE = "billing:manage"
    
    # Gamification
    GAMIFICATION_MANAGE = "gamification:manage"
    
    # Fees & Finance
    FEE_VIEW = "fee:view"
    FEE_COMPONENT_MANAGE = "fee:component_manage"
    FEE_STRUCTURE_MANAGE = "fee:structure_manage"
    FEE_INVOICE_GENERATE = "fee:invoice_generate"
    FEE_PAYMENT_RECORD = "fee:payment_record"
    
    # Daily Learning Loops
    DAILY_LOOP_VIEW = "daily_loop:view"
    DAILY_LOOP_START = "daily_loop:start"
    DAILY_LOOP_ATTEMPT = "daily_loop:attempt"
    
    # Weekly Evaluation
    WEEKLY_TEST_VIEW = "weekly_test:view"
    WEEKLY_TEST_CREATE = "weekly_test:create"
    WEEKLY_TEST_GENERATE = "weekly_test:generate"
    WEEKLY_TEST_SUBMIT_RESULT = "weekly_test:submit_result"
    
    # Lesson Evaluation & Adaptive
    LESSON_TEST_VIEW = "lesson_test:view"
    LESSON_TEST_CREATE = "lesson_test:create"
    LESSON_TEST_GENERATE = "lesson_test:generate"
    LESSON_TEST_SUBMIT_RESULT = "lesson_test:submit_result"
    ADAPTIVE_VIEW = "adaptive:view"
    
    # Attendance
    ATTENDANCE_VIEW = "attendance:view"
    ATTENDANCE_MARK = "attendance:mark"
    ATTENDANCE_REPORT = "attendance:report"
    LEAVE_REQUEST_VIEW = "leave_request:view"
    LEAVE_REQUEST_APPROVE = "leave_request:approve"
    
    # Announcements
    ANNOUNCEMENT_VIEW = "announcement:view"
    ANNOUNCEMENT_MANAGE = "announcement:manage"
    
    # Payments
    PAYMENT_VIEW = "payment:view"
    PAYMENT_CREATE = "payment:create"
    PAYMENT_REFUND = "payment:refund"
    PAYMENT_GATEWAY_MANAGE = "payment:gateway_manage"
    
    # Transport
    TRANSPORT_VIEW = "transport:view"
    TRANSPORT_MANAGE = "transport:manage"
    TRANSPORT_ASSIGN = "transport:assign"
    
    # Hostel
    HOSTEL_VIEW = "hostel:view"
    HOSTEL_MANAGE = "hostel:manage"
    HOSTEL_ASSIGN = "hostel:assign"
    
    # Library
    LIBRARY_VIEW = "library:view"
    LIBRARY_MANAGE = "library:manage"
    LIBRARY_ISSUE = "library:issue"
    
    # HR & Payroll
    HR_MANAGE = "hr:manage"
    PAYROLL_RUN = "payroll:run"
    PAYROLL_VIEW = "payroll:view"
    LEAVE_APPROVE = "leave:approve"
    LEAVE_APPLY = "leave:apply"
    
    # Analytics
    ANALYTICS_VIEW_ADMIN = "analytics:view_admin"
    ANALYTICS_VIEW_TEACHER = "analytics:view_teacher"
    ANALYTICS_VIEW_STUDENT = "analytics:view_student"
    
    # Governance & Compliance
    AUDIT_VIEW = "audit:view"
    AUDIT_EXPORT = "audit:export"
    CONSENT_MANAGE = "consent:manage"
    
    # AI Insights (NO access for Students/Parents)
    INSIGHTS_REQUEST = "insights:request"
    INSIGHTS_VIEW = "insights:view"
    
    # Corrections (Safe Reversal Framework)
    CORRECTION_REQUEST = "correction:request"    # Request a correction
    CORRECTION_APPROVE = "correction:approve"    # Approve/reject corrections
    CORRECTION_VIEW = "correction:view"          # View correction history
    CORRECTION_OVERRIDE = "correction:override"  # Override time locks
    
    # Surveys & Feedback
    SURVEY_VIEW = "survey:view"
    SURVEY_CREATE = "survey:create"
    SURVEY_UPDATE = "survey:update"
    SURVEY_DELETE = "survey:delete"
    SURVEY_RESULTS_VIEW = "survey:results_view"
    SURVEY_SUBMIT = "survey:submit"  # Student permission


# Role-Permission mapping
ROLE_PERMISSIONS: Dict[SystemRole, Set[Permission]] = {
    SystemRole.SUPER_ADMIN: set(Permission),  # All permissions
    
    SystemRole.PRINCIPAL: {
        Permission.TENANT_VIEW,
        Permission.TENANT_UPDATE,
        Permission.USER_VIEW,
        Permission.USER_CREATE,
        Permission.USER_UPDATE,
        Permission.USER_MANAGE_ROLES,
        Permission.STUDENT_VIEW,
        Permission.STUDENT_CREATE,
        Permission.STUDENT_UPDATE,
        Permission.STUDENT_LIFECYCLE_MANAGE,
        Permission.TEACHER_VIEW,
        Permission.TEACHER_CREATE,
        Permission.TEACHER_UPDATE,
        Permission.CLASS_VIEW,
        Permission.CLASS_CREATE,
        Permission.CLASS_UPDATE,
        Permission.SUBJECT_VIEW,
        Permission.SUBJECT_CREATE,
        Permission.SYLLABUS_VIEW,
        Permission.SYLLABUS_CREATE,
        Permission.LESSON_VIEW,
        Permission.QUESTION_VIEW,
        Permission.QUESTION_APPROVE,
        Permission.ASSIGNMENT_VIEW,
        Permission.REPORT_VIEW_ALL,
        Permission.REPORT_EXPORT,
        Permission.CALENDAR_VIEW,
        Permission.CALENDAR_CREATE,
        Permission.TIMETABLE_VIEW,
        Permission.TIMETABLE_CREATE,
        Permission.TIMETABLE_UPDATE,
        Permission.TIMETABLE_DELETE,
        Permission.POST_VIEW,
        Permission.POST_CREATE,
        Permission.NOTIFICATION_SEND,
        Permission.BILLING_VIEW,
        Permission.TEACHING_ASSIGNMENT_VIEW,
        Permission.TEACHING_ASSIGNMENT_CREATE,
        Permission.TEACHING_ASSIGNMENT_UPDATE,
        Permission.TEACHING_ASSIGNMENT_DELETE,
        Permission.SCHEDULE_VIEW,
        Permission.SCHEDULE_GENERATE,
        Permission.SCHEDULE_UPDATE,
        Permission.DAILY_LOOP_VIEW,
        Permission.DAILY_LOOP_START,
        Permission.WEEKLY_TEST_VIEW,
        Permission.WEEKLY_TEST_CREATE,
        Permission.WEEKLY_TEST_GENERATE,
        Permission.WEEKLY_TEST_SUBMIT_RESULT,
        Permission.LESSON_TEST_VIEW,
        Permission.LESSON_TEST_CREATE,
        Permission.LESSON_TEST_GENERATE,
        Permission.LESSON_TEST_SUBMIT_RESULT,
        Permission.ADAPTIVE_VIEW,
        Permission.AI_LESSON_PLAN_GENERATE,
        Permission.AI_OCR_PROCESS,
        # Transport
        Permission.TRANSPORT_VIEW,
        Permission.TRANSPORT_MANAGE,
        Permission.TRANSPORT_ASSIGN,
        # Hostel
        Permission.HOSTEL_VIEW,
        Permission.HOSTEL_MANAGE,
        Permission.HOSTEL_ASSIGN,
        # HR & Payroll
        Permission.HR_MANAGE,
        Permission.PAYROLL_RUN,
        Permission.PAYROLL_VIEW,
        Permission.LEAVE_APPROVE,
        Permission.LEAVE_APPLY,
        # Analytics
        Permission.ANALYTICS_VIEW_ADMIN,
        # Governance & Compliance
        Permission.AUDIT_VIEW,
        Permission.AUDIT_EXPORT,
        Permission.CONSENT_MANAGE,
        # AI Insights
        Permission.INSIGHTS_REQUEST,
        Permission.INSIGHTS_VIEW,
        # Corrections (Safe Reversal)
        Permission.CORRECTION_REQUEST,
        Permission.CORRECTION_APPROVE,
        Permission.CORRECTION_VIEW,
        Permission.CORRECTION_OVERRIDE,  # Principal can override time locks
        # Surveys & Feedback
        Permission.SURVEY_VIEW,
        Permission.SURVEY_CREATE,
        Permission.SURVEY_UPDATE,
        Permission.SURVEY_DELETE,
        Permission.SURVEY_RESULTS_VIEW,
    },
    
    SystemRole.SUB_ADMIN: {
        Permission.USER_VIEW,
        Permission.USER_CREATE,
        Permission.STUDENT_VIEW,
        Permission.STUDENT_CREATE,
        Permission.STUDENT_UPDATE,
        Permission.STUDENT_LIFECYCLE_MANAGE,
        Permission.TEACHER_VIEW,
        Permission.CLASS_VIEW,
        Permission.SUBJECT_VIEW,
        Permission.SYLLABUS_VIEW,
        Permission.CALENDAR_VIEW,
        Permission.CALENDAR_CREATE,
        Permission.POST_VIEW,
        Permission.POST_CREATE,
        Permission.TEACHING_ASSIGNMENT_VIEW,
        Permission.TEACHING_ASSIGNMENT_CREATE,
        Permission.TEACHING_ASSIGNMENT_UPDATE,
        Permission.TEACHING_ASSIGNMENT_DELETE,
        Permission.SCHEDULE_VIEW,
        Permission.SCHEDULE_GENERATE,
        # Transport
        Permission.TRANSPORT_VIEW,
        Permission.TRANSPORT_MANAGE,
        Permission.TRANSPORT_ASSIGN,
        # Hostel
        Permission.HOSTEL_VIEW,
        Permission.HOSTEL_MANAGE,
        Permission.HOSTEL_ASSIGN,
        # HR & Payroll
        Permission.HR_MANAGE,
        Permission.PAYROLL_RUN,
        Permission.PAYROLL_VIEW,
        Permission.LEAVE_APPROVE,
        Permission.LEAVE_APPLY,
        # Analytics
        Permission.ANALYTICS_VIEW_ADMIN,
        # Governance & Compliance
        Permission.AUDIT_VIEW,
        Permission.AUDIT_EXPORT,
        Permission.CONSENT_MANAGE,
        # AI Insights
        Permission.INSIGHTS_REQUEST,
        Permission.INSIGHTS_VIEW,
        # Corrections (Safe Reversal) - cannot override time locks
        Permission.CORRECTION_REQUEST,
        Permission.CORRECTION_APPROVE,
        Permission.CORRECTION_VIEW,
        # Surveys & Feedback
        Permission.SURVEY_VIEW,
        Permission.SURVEY_CREATE,
        Permission.SURVEY_UPDATE,
        Permission.SURVEY_RESULTS_VIEW,
    },
    
    SystemRole.TEACHER: {
        Permission.STUDENT_VIEW,
        Permission.CLASS_VIEW,
        Permission.SUBJECT_VIEW,
        Permission.SYLLABUS_VIEW,
        Permission.SYLLABUS_UPDATE,
        Permission.LESSON_VIEW,
        Permission.LESSON_CREATE,
        Permission.LESSON_UPDATE,
        Permission.QUESTION_VIEW,
        Permission.QUESTION_CREATE,
        Permission.QUESTION_UPDATE,
        Permission.ASSIGNMENT_VIEW,
        Permission.ASSIGNMENT_CREATE,
        Permission.ASSIGNMENT_UPDATE,
        Permission.ASSIGNMENT_GRADE,
        Permission.ASSIGNMENT_VIEW_SUBMISSIONS,
        Permission.WORKSHEET_VIEW,
        Permission.WORKSHEET_CREATE,
        Permission.AI_LESSON_PLAN,
        Permission.AI_QUESTION_GEN,
        Permission.REPORT_VIEW_CLASS,
        Permission.CALENDAR_VIEW,
        Permission.TIMETABLE_VIEW,
        Permission.POST_VIEW,
        Permission.TEACHING_ASSIGNMENT_VIEW,
        Permission.SCHEDULE_VIEW,
        Permission.SCHEDULE_GENERATE,
        Permission.SCHEDULE_UPDATE,
        Permission.DAILY_LOOP_VIEW,
        Permission.DAILY_LOOP_START,
        Permission.WEEKLY_TEST_VIEW,
        Permission.WEEKLY_TEST_CREATE,
        Permission.WEEKLY_TEST_GENERATE,
        Permission.WEEKLY_TEST_SUBMIT_RESULT,
        Permission.LESSON_TEST_VIEW,
        Permission.LESSON_TEST_CREATE,
        Permission.LESSON_TEST_GENERATE,
        Permission.LESSON_TEST_SUBMIT_RESULT,
        Permission.ADAPTIVE_VIEW,
        Permission.AI_LESSON_PLAN_GENERATE,
        Permission.AI_OCR_PROCESS,
        # HR Self-Service
        Permission.PAYROLL_VIEW,
        Permission.LEAVE_APPLY,
        # Analytics (class-level only)
        Permission.ANALYTICS_VIEW_TEACHER,
        # AI Insights (own classes/self only, enforced in service)
        Permission.INSIGHTS_REQUEST,
        Permission.INSIGHTS_VIEW,
        # Surveys & Feedback (view results for own courses)
        Permission.SURVEY_VIEW,
        Permission.SURVEY_RESULTS_VIEW,
    },
    
    SystemRole.STUDENT: {
        Permission.CLASS_VIEW,
        Permission.SUBJECT_VIEW,
        Permission.SYLLABUS_VIEW,
        Permission.LESSON_VIEW,
        Permission.QUESTION_VIEW,
        Permission.ASSIGNMENT_VIEW,
        Permission.ASSIGNMENT_SUBMIT,
        Permission.WORKSHEET_VIEW,
        Permission.AI_DOUBT_SOLVER,
        Permission.REPORT_VIEW_OWN,
        Permission.CALENDAR_VIEW,
        Permission.TIMETABLE_VIEW,
        Permission.POST_VIEW,
        Permission.SCHEDULE_VIEW,
        Permission.DAILY_LOOP_VIEW,
        Permission.DAILY_LOOP_ATTEMPT,
        Permission.WEEKLY_TEST_VIEW,
        Permission.LESSON_TEST_VIEW,
        Permission.ADAPTIVE_VIEW,
        # Transport
        Permission.TRANSPORT_VIEW,
        # Hostel
        Permission.HOSTEL_VIEW,
        # Analytics (activity score only)
        Permission.ANALYTICS_VIEW_STUDENT,
        # Surveys & Feedback
        Permission.SURVEY_SUBMIT,
    },
    
    SystemRole.PARENT: {
        Permission.CLASS_VIEW,
        Permission.SUBJECT_VIEW,
        Permission.ASSIGNMENT_VIEW,
        Permission.REPORT_VIEW_OWN,
        Permission.CALENDAR_VIEW,
        Permission.POST_VIEW,
        # Transport
        Permission.TRANSPORT_VIEW,
        # Hostel
        Permission.HOSTEL_VIEW,
        # Analytics (child's activity score only)
        Permission.ANALYTICS_VIEW_STUDENT,
    },
}


def check_permission(user_roles: list[str], permission: Permission) -> bool:
    """Check if any of the user's roles have the permission."""
    for role_code in user_roles:
        try:
            role = SystemRole(role_code)
            if permission in ROLE_PERMISSIONS.get(role, set()):
                return True
        except ValueError:
            continue
    return False


def get_role_permissions(role_code: str) -> Set[Permission]:
    """Get all permissions for a role."""
    try:
        role = SystemRole(role_code)
        return ROLE_PERMISSIONS.get(role, set())
    except ValueError:
        return set()


def get_all_permissions() -> list[dict]:
    """Get all permissions with metadata."""
    permissions = []
    for perm in Permission:
        module = perm.value.split(":")[0]
        permissions.append({
            "code": perm.value,
            "name": perm.name.replace("_", " ").title(),
            "module": module,
        })
    return permissions
