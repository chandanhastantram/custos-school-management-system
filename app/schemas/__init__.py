"""
CUSTOS Schemas Package
"""

from app.schemas.common import (
    SuccessResponse, ErrorResponse, PaginatedResponse,
    PaginationParams, SearchParams, BulkDeleteRequest,
    BulkActionResponse, HealthResponse,
)

from app.schemas.auth import (
    LoginRequest, LoginResponse, UserInfo,
    RefreshTokenRequest, RefreshTokenResponse,
    PasswordChangeRequest, PasswordResetRequest, PasswordResetConfirm,
    RegisterRequest, VerifyEmailRequest,
)

from app.schemas.tenant import (
    TenantCreate, TenantUpdate, TenantResponse,
    TenantListResponse, TenantStats,
)

from app.schemas.user import (
    UserCreate, UserUpdate, UserResponse, UserListResponse,
    RoleCreate, RoleResponse, PermissionResponse,
    StudentProfileCreate, StudentProfileResponse,
    TeacherProfileCreate, TeacherProfileResponse,
)

from app.schemas.academic import (
    ClassCreate, ClassUpdate, ClassResponse,
    SectionCreate, SectionResponse,
    SubjectCreate, SubjectResponse,
    TopicCreate, TopicResponse,
    SyllabusCreate, SyllabusResponse,
    LessonCreate, LessonResponse,
    AcademicYearCreate, AcademicYearResponse,
)

from app.schemas.question import (
    QuestionCreate, QuestionUpdate, QuestionResponse,
    QuestionListResponse, QuestionFilter,
    QuestionAttemptCreate, QuestionAttemptResponse,
    QuestionGenerateRequest, MCQOption,
)

from app.schemas.assignment import (
    AssignmentCreate, AssignmentUpdate, AssignmentResponse,
    SubmissionCreate, SubmissionResponse, AnswerSubmit,
    WorksheetCreate, WorksheetGenerateRequest, WorksheetResponse,
    CorrectionData, QuestionCorrection, BulkCorrectionRequest,
)

from app.schemas.report import (
    ReportRequest, ReportResponse,
    StudentReportSummary, ClassAnalytics, TeacherEffectivenessReport,
)

from app.schemas.calendar import (
    EventCreate, EventResponse,
    TimetableCreate, TimetableSlotCreate, TimetableResponse,
)

from app.schemas.post import (
    PostCreate, PostUpdate, PostResponse, PostListResponse,
)

from app.schemas.ai import (
    LessonPlanRequest, LessonPlanResponse,
    QuestionGenerationRequest, QuestionGenerationResponse,
    WorksheetGenerationRequest, WorksheetGenerationResponse,
    DoubtSolverRequest, DoubtSolverResponse,
    AIUsageResponse,
)

from app.schemas.billing import (
    PlanResponse, SubscriptionCreate, SubscriptionResponse,
    UsageLimitResponse,
)

from app.schemas.notification import (
    NotificationCreate, NotificationResponse,
    NotificationListResponse, NotificationBulkCreate,
)

__all__ = [
    # Common
    "SuccessResponse", "ErrorResponse", "PaginatedResponse",
    "PaginationParams", "SearchParams", "BulkDeleteRequest",
    "BulkActionResponse", "HealthResponse",
    # Auth
    "LoginRequest", "LoginResponse", "UserInfo",
    "RefreshTokenRequest", "RefreshTokenResponse",
    "PasswordChangeRequest", "PasswordResetRequest", "PasswordResetConfirm",
    "RegisterRequest", "VerifyEmailRequest",
    # Tenant
    "TenantCreate", "TenantUpdate", "TenantResponse",
    "TenantListResponse", "TenantStats",
    # User
    "UserCreate", "UserUpdate", "UserResponse", "UserListResponse",
    "RoleCreate", "RoleResponse", "PermissionResponse",
    "StudentProfileCreate", "StudentProfileResponse",
    "TeacherProfileCreate", "TeacherProfileResponse",
    # Academic
    "ClassCreate", "ClassUpdate", "ClassResponse",
    "SectionCreate", "SectionResponse",
    "SubjectCreate", "SubjectResponse",
    "TopicCreate", "TopicResponse",
    "SyllabusCreate", "SyllabusResponse",
    "LessonCreate", "LessonResponse",
    "AcademicYearCreate", "AcademicYearResponse",
    # Question
    "QuestionCreate", "QuestionUpdate", "QuestionResponse",
    "QuestionListResponse", "QuestionFilter",
    "QuestionAttemptCreate", "QuestionAttemptResponse",
    "QuestionGenerateRequest", "MCQOption",
    # Assignment
    "AssignmentCreate", "AssignmentUpdate", "AssignmentResponse",
    "SubmissionCreate", "SubmissionResponse", "AnswerSubmit",
    "WorksheetCreate", "WorksheetGenerateRequest", "WorksheetResponse",
    "CorrectionData", "QuestionCorrection", "BulkCorrectionRequest",
    # Report
    "ReportRequest", "ReportResponse",
    "StudentReportSummary", "ClassAnalytics", "TeacherEffectivenessReport",
    # Calendar
    "EventCreate", "EventResponse",
    "TimetableCreate", "TimetableSlotCreate", "TimetableResponse",
    # Post
    "PostCreate", "PostUpdate", "PostResponse", "PostListResponse",
    # AI
    "LessonPlanRequest", "LessonPlanResponse",
    "QuestionGenerationRequest", "QuestionGenerationResponse",
    "WorksheetGenerationRequest", "WorksheetGenerationResponse",
    "DoubtSolverRequest", "DoubtSolverResponse",
    "AIUsageResponse",
    # Billing
    "PlanResponse", "SubscriptionCreate", "SubscriptionResponse",
    "UsageLimitResponse",
    # Notification
    "NotificationCreate", "NotificationResponse",
    "NotificationListResponse", "NotificationBulkCreate",
]
