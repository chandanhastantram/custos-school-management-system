"""
CUSTOS Tenant Modules

Module access control per tenant.
"""

from enum import Enum
from typing import Optional
from uuid import UUID

from sqlalchemy import String, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import TenantBaseModel


class TenantModule(str, Enum):
    """Available modules that can be enabled/disabled per tenant."""
    CORE = "core"                      # Always enabled
    STUDENTS = "students"
    TEACHERS = "teachers"
    ACADEMICS = "academics"
    QUESTION_BANK = "question_bank"
    ASSIGNMENTS = "assignments"
    EXAMS = "exams"
    AI_FEATURES = "ai_features"
    AI_LESSON_PLAN = "ai_lesson_plan"
    AI_QUESTIONS = "ai_questions"
    AI_DOUBT_SOLVER = "ai_doubt_solver"
    LMS = "lms"
    GAMIFICATION = "gamification"
    REPORTS = "reports"
    CALENDAR = "calendar"
    TIMETABLE = "timetable"
    NOTIFICATIONS = "notifications"
    FILE_STORAGE = "file_storage"
    PARENT_PORTAL = "parent_portal"
    BULK_IMPORT = "bulk_import"
    API_ACCESS = "api_access"


class TenantModuleAccess(TenantBaseModel):
    """
    Module access control per tenant.
    
    Allows enabling/disabling features per school.
    """
    __tablename__ = "tenant_module_access"
    
    __table_args__ = (
        UniqueConstraint("tenant_id", "module_name", name="uq_tenant_module"),
    )
    
    module_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Override plan limits for this module
    custom_limit: Mapped[Optional[int]] = mapped_column(nullable=True)
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)


# Default modules enabled for each plan tier
DEFAULT_MODULES_BY_PLAN = {
    "free": [
        TenantModule.CORE,
        TenantModule.STUDENTS,
        TenantModule.TEACHERS,
        TenantModule.ACADEMICS,
        TenantModule.ASSIGNMENTS,
        TenantModule.NOTIFICATIONS,
    ],
    "starter": [
        TenantModule.CORE,
        TenantModule.STUDENTS,
        TenantModule.TEACHERS,
        TenantModule.ACADEMICS,
        TenantModule.QUESTION_BANK,
        TenantModule.ASSIGNMENTS,
        TenantModule.REPORTS,
        TenantModule.CALENDAR,
        TenantModule.NOTIFICATIONS,
        TenantModule.FILE_STORAGE,
    ],
    "professional": [
        TenantModule.CORE,
        TenantModule.STUDENTS,
        TenantModule.TEACHERS,
        TenantModule.ACADEMICS,
        TenantModule.QUESTION_BANK,
        TenantModule.ASSIGNMENTS,
        TenantModule.EXAMS,
        TenantModule.AI_FEATURES,
        TenantModule.AI_LESSON_PLAN,
        TenantModule.AI_QUESTIONS,
        TenantModule.LMS,
        TenantModule.GAMIFICATION,
        TenantModule.REPORTS,
        TenantModule.CALENDAR,
        TenantModule.TIMETABLE,
        TenantModule.NOTIFICATIONS,
        TenantModule.FILE_STORAGE,
        TenantModule.PARENT_PORTAL,
    ],
    "enterprise": list(TenantModule),  # All modules
}
