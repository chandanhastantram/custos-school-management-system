"""
CUSTOS RBAC Module

Role-Based Access Control implementation.
"""

from enum import Enum
from typing import Optional, Set
from functools import wraps


class SystemRole(str, Enum):
    """System-defined roles."""
    SUPER_ADMIN = "super_admin"
    PRINCIPAL = "principal"
    SUB_ADMIN = "sub_admin"
    TEACHER = "teacher"
    STUDENT = "student"
    PARENT = "parent"


class Permission(str, Enum):
    """System permissions."""
    # Tenant
    TENANT_VIEW = "tenant:view"
    TENANT_UPDATE = "tenant:update"
    TENANT_MANAGE = "tenant:manage"
    
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
    
    # Teachers
    TEACHER_VIEW = "teacher:view"
    TEACHER_CREATE = "teacher:create"
    TEACHER_UPDATE = "teacher:update"
    TEACHER_DELETE = "teacher:delete"
    
    # Classes
    CLASS_VIEW = "class:view"
    CLASS_CREATE = "class:create"
    CLASS_UPDATE = "class:update"
    CLASS_DELETE = "class:delete"
    
    # Subjects
    SUBJECT_VIEW = "subject:view"
    SUBJECT_CREATE = "subject:create"
    SUBJECT_UPDATE = "subject:update"
    SUBJECT_DELETE = "subject:delete"
    
    # Syllabus
    SYLLABUS_VIEW = "syllabus:view"
    SYLLABUS_CREATE = "syllabus:create"
    SYLLABUS_UPDATE = "syllabus:update"
    SYLLABUS_DELETE = "syllabus:delete"
    
    # Lessons
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
    
    # Reports
    REPORT_VIEW_OWN = "report:view_own"
    REPORT_VIEW_CLASS = "report:view_class"
    REPORT_VIEW_ALL = "report:view_all"
    REPORT_GENERATE = "report:generate"
    
    # Calendar
    EVENT_VIEW = "event:view"
    EVENT_CREATE = "event:create"
    EVENT_UPDATE = "event:update"
    EVENT_DELETE = "event:delete"
    
    # Timetable
    TIMETABLE_VIEW = "timetable:view"
    TIMETABLE_MANAGE = "timetable:manage"
    
    # Posts
    POST_VIEW = "post:view"
    POST_CREATE = "post:create"
    POST_UPDATE = "post:update"
    POST_DELETE = "post:delete"
    POST_PUBLISH = "post:publish"
    
    # AI Features
    AI_LESSON_PLAN = "ai:lesson_plan"
    AI_QUESTION_GEN = "ai:question_gen"
    AI_WORKSHEET_GEN = "ai:worksheet_gen"
    AI_DOUBT_SOLVER = "ai:doubt_solver"
    
    # Subscription
    SUBSCRIPTION_VIEW = "subscription:view"
    SUBSCRIPTION_MANAGE = "subscription:manage"
    
    # Audit
    AUDIT_VIEW = "audit:view"
    
    # Notifications
    NOTIFICATION_SEND = "notification:send"


# Role hierarchy (higher number = more authority)
ROLE_HIERARCHY = {
    SystemRole.SUPER_ADMIN: 100,
    SystemRole.PRINCIPAL: 80,
    SystemRole.SUB_ADMIN: 60,
    SystemRole.TEACHER: 40,
    SystemRole.STUDENT: 20,
    SystemRole.PARENT: 20,
}

# Default permissions for each role
ROLE_PERMISSIONS: dict[SystemRole, Set[Permission]] = {
    SystemRole.SUPER_ADMIN: set(Permission),  # All permissions
    
    SystemRole.PRINCIPAL: {
        Permission.TENANT_VIEW, Permission.TENANT_UPDATE,
        Permission.USER_VIEW, Permission.USER_CREATE, Permission.USER_UPDATE, Permission.USER_DELETE,
        Permission.USER_MANAGE_ROLES,
        Permission.STUDENT_VIEW, Permission.STUDENT_CREATE, Permission.STUDENT_UPDATE, Permission.STUDENT_DELETE,
        Permission.TEACHER_VIEW, Permission.TEACHER_CREATE, Permission.TEACHER_UPDATE, Permission.TEACHER_DELETE,
        Permission.CLASS_VIEW, Permission.CLASS_CREATE, Permission.CLASS_UPDATE, Permission.CLASS_DELETE,
        Permission.SUBJECT_VIEW, Permission.SUBJECT_CREATE, Permission.SUBJECT_UPDATE, Permission.SUBJECT_DELETE,
        Permission.SYLLABUS_VIEW, Permission.SYLLABUS_CREATE, Permission.SYLLABUS_UPDATE, Permission.SYLLABUS_DELETE,
        Permission.LESSON_VIEW, Permission.LESSON_CREATE, Permission.LESSON_UPDATE, Permission.LESSON_DELETE,
        Permission.QUESTION_VIEW, Permission.QUESTION_CREATE, Permission.QUESTION_UPDATE, 
        Permission.QUESTION_DELETE, Permission.QUESTION_APPROVE,
        Permission.ASSIGNMENT_VIEW, Permission.ASSIGNMENT_CREATE, Permission.ASSIGNMENT_UPDATE,
        Permission.ASSIGNMENT_DELETE, Permission.ASSIGNMENT_GRADE,
        Permission.REPORT_VIEW_ALL, Permission.REPORT_GENERATE,
        Permission.EVENT_VIEW, Permission.EVENT_CREATE, Permission.EVENT_UPDATE, Permission.EVENT_DELETE,
        Permission.TIMETABLE_VIEW, Permission.TIMETABLE_MANAGE,
        Permission.POST_VIEW, Permission.POST_CREATE, Permission.POST_UPDATE, Permission.POST_DELETE, Permission.POST_PUBLISH,
        Permission.AI_LESSON_PLAN, Permission.AI_QUESTION_GEN, Permission.AI_WORKSHEET_GEN,
        Permission.SUBSCRIPTION_VIEW,
        Permission.AUDIT_VIEW,
        Permission.NOTIFICATION_SEND,
    },
    
    SystemRole.SUB_ADMIN: {
        Permission.TENANT_VIEW,
        Permission.USER_VIEW, Permission.USER_CREATE, Permission.USER_UPDATE,
        Permission.STUDENT_VIEW, Permission.STUDENT_CREATE, Permission.STUDENT_UPDATE,
        Permission.TEACHER_VIEW,
        Permission.CLASS_VIEW, Permission.CLASS_CREATE, Permission.CLASS_UPDATE,
        Permission.SUBJECT_VIEW,
        Permission.SYLLABUS_VIEW,
        Permission.LESSON_VIEW,
        Permission.QUESTION_VIEW,
        Permission.ASSIGNMENT_VIEW,
        Permission.REPORT_VIEW_CLASS,
        Permission.EVENT_VIEW, Permission.EVENT_CREATE, Permission.EVENT_UPDATE,
        Permission.TIMETABLE_VIEW,
        Permission.POST_VIEW, Permission.POST_CREATE,
        Permission.NOTIFICATION_SEND,
    },
    
    SystemRole.TEACHER: {
        Permission.CLASS_VIEW,
        Permission.SUBJECT_VIEW,
        Permission.SYLLABUS_VIEW, Permission.SYLLABUS_UPDATE,
        Permission.LESSON_VIEW, Permission.LESSON_CREATE, Permission.LESSON_UPDATE,
        Permission.QUESTION_VIEW, Permission.QUESTION_CREATE, Permission.QUESTION_UPDATE,
        Permission.ASSIGNMENT_VIEW, Permission.ASSIGNMENT_CREATE, Permission.ASSIGNMENT_UPDATE, Permission.ASSIGNMENT_GRADE,
        Permission.REPORT_VIEW_CLASS, Permission.REPORT_GENERATE,
        Permission.EVENT_VIEW,
        Permission.TIMETABLE_VIEW,
        Permission.POST_VIEW, Permission.POST_CREATE,
        Permission.AI_LESSON_PLAN, Permission.AI_QUESTION_GEN, Permission.AI_WORKSHEET_GEN,
        Permission.STUDENT_VIEW,
    },
    
    SystemRole.STUDENT: {
        Permission.CLASS_VIEW,
        Permission.SUBJECT_VIEW,
        Permission.SYLLABUS_VIEW,
        Permission.LESSON_VIEW,
        Permission.QUESTION_VIEW,
        Permission.ASSIGNMENT_VIEW, Permission.ASSIGNMENT_SUBMIT,
        Permission.REPORT_VIEW_OWN,
        Permission.EVENT_VIEW,
        Permission.TIMETABLE_VIEW,
        Permission.POST_VIEW,
        Permission.AI_DOUBT_SOLVER,
    },
    
    SystemRole.PARENT: {
        Permission.CLASS_VIEW,
        Permission.SUBJECT_VIEW,
        Permission.ASSIGNMENT_VIEW,
        Permission.REPORT_VIEW_OWN,
        Permission.EVENT_VIEW,
        Permission.TIMETABLE_VIEW,
        Permission.POST_VIEW,
    },
}


def check_permission(user_permissions: Set[str], required: Permission) -> bool:
    """Check if user has required permission."""
    return required.value in user_permissions


def check_any_permission(user_permissions: Set[str], required: list[Permission]) -> bool:
    """Check if user has any of the required permissions."""
    return any(p.value in user_permissions for p in required)


def check_all_permissions(user_permissions: Set[str], required: list[Permission]) -> bool:
    """Check if user has all required permissions."""
    return all(p.value in user_permissions for p in required)


def get_role_level(role_code: str) -> int:
    """Get hierarchy level for a role."""
    try:
        role = SystemRole(role_code)
        return ROLE_HIERARCHY.get(role, 0)
    except ValueError:
        return 0


def can_manage_role(manager_roles: list[str], target_role: str) -> bool:
    """Check if manager can manage target role."""
    manager_level = max(get_role_level(r) for r in manager_roles) if manager_roles else 0
    target_level = get_role_level(target_role)
    return manager_level > target_level


def get_default_permissions(role_code: str) -> Set[str]:
    """Get default permissions for a role."""
    try:
        role = SystemRole(role_code)
        return {p.value for p in ROLE_PERMISSIONS.get(role, set())}
    except ValueError:
        return set()
