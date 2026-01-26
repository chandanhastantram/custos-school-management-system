"""
CUSTOS Models Package

All SQLAlchemy models.
"""

from app.models.base import (
    Base,
    BaseModel,
    TenantBaseModel,
    TenantSoftDeleteModel,
    TimestampMixin,
    SoftDeleteMixin,
    TenantMixin,
)

from app.models.tenant import (
    Tenant,
    TenantStatus,
    TenantType,
    TenantDomain,
    TenantInvitation,
)

from app.models.user import (
    User,
    UserStatus,
    Gender,
    Role,
    Permission,
    StudentProfile,
    TeacherProfile,
    ParentProfile,
    user_roles,
    role_permissions,
    parent_student_relations,
)

from app.models.academic import (
    AcademicYear,
    Class,
    Section,
    Subject,
    ClassSubject,
    Syllabus,
    SyllabusStatus,
    Topic,
    TopicStatus,
    Lesson,
    LessonStatus,
)

from app.models.question import (
    Question,
    QuestionType,
    BloomLevel,
    Difficulty,
    QuestionAttempt,
)

from app.models.assignment import (
    Assignment,
    AssignmentType,
    AssignmentStatus,
    AssignmentQuestion,
    AssignmentSubmission,
    SubmissionStatus,
    Worksheet,
    WorksheetQuestion,
    Correction,
    CorrectionStatus,
)

from app.models.report import (
    Report,
    ReportType,
    ReportPeriod,
    StudentPerformance,
    TeacherEffectiveness,
)

from app.models.calendar import (
    Event,
    EventType,
    RecurrenceType,
    Timetable,
    TimetableSlot,
    DayOfWeek,
)

from app.models.post import (
    Post,
    PostType,
    PostPriority,
    PostView,
)

from app.models.ai import (
    AISession,
    AIFeature,
    AIUsage,
)

from app.models.billing import (
    Plan,
    PlanType,
    Subscription,
    SubscriptionStatus,
    BillingCycle,
    UsageLimit,
)

from app.models.audit import (
    AuditLog,
    AuditAction,
    Notification,
    NotificationType,
    NotificationChannel,
    Reward,
    Badge,
    UserBadge,
)

__all__ = [
    # Base
    "Base", "BaseModel", "TenantBaseModel", "TenantSoftDeleteModel",
    "TimestampMixin", "SoftDeleteMixin", "TenantMixin",
    # Tenant
    "Tenant", "TenantStatus", "TenantType", "TenantDomain", "TenantInvitation",
    # User
    "User", "UserStatus", "Gender", "Role", "Permission",
    "StudentProfile", "TeacherProfile", "ParentProfile",
    "user_roles", "role_permissions", "parent_student_relations",
    # Academic
    "AcademicYear", "Class", "Section", "Subject", "ClassSubject",
    "Syllabus", "SyllabusStatus", "Topic", "TopicStatus", "Lesson", "LessonStatus",
    # Question
    "Question", "QuestionType", "BloomLevel", "Difficulty", "QuestionAttempt",
    # Assignment
    "Assignment", "AssignmentType", "AssignmentStatus", "AssignmentQuestion",
    "AssignmentSubmission", "SubmissionStatus", "Worksheet", "WorksheetQuestion",
    "Correction", "CorrectionStatus",
    # Report
    "Report", "ReportType", "ReportPeriod", "StudentPerformance", "TeacherEffectiveness",
    # Calendar
    "Event", "EventType", "RecurrenceType", "Timetable", "TimetableSlot", "DayOfWeek",
    # Post
    "Post", "PostType", "PostPriority", "PostView",
    # AI
    "AISession", "AIFeature", "AIUsage",
    # Billing
    "Plan", "PlanType", "Subscription", "SubscriptionStatus", "BillingCycle", "UsageLimit",
    # Audit
    "AuditLog", "AuditAction", "Notification", "NotificationType", "NotificationChannel",
    "Reward", "Badge", "UserBadge",
]
