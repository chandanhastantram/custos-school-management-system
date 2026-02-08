"""Initialize database tables - Minimal approach."""
import asyncio
from app.core.database import engine
from app.core.base_model import BaseModel

# Core models only - these are the essentials
from app.tenants.models import Tenant, TenantSettings
from app.tenants.modules import TenantModuleAccess
from app.users.models import User, Role, Permission, StudentProfile, TeacherProfile, ParentProfile
from app.users.pre_registration import PreRegisteredUser
from app.auth.models import RefreshToken, PasswordResetToken, LoginAttempt
from app.academics.models.structure import AcademicYear, Class, Section
from app.academics.models.curriculum import Subject, Syllabus, Topic, Lesson
from app.academics.models.questions import Question
from app.academics.models.assignments import Assignment, AssignmentQuestion, Submission, SubmissionAnswer
from app.billing.models import Plan, Subscription, UsageLimit
from app.platform.notifications.models import Notification
from app.platform.gamification.models import Points, Badge, UserBadge
from app.platform.audit.models import AuditLog
from app.platform.admin.models import PlatformAdmin, PlatformSettings
from app.platform.usage.tracking import FeatureUsage
from app.academics.models.syllabus import Board, ClassLevel, SyllabusSubject, Chapter, SyllabusTopic, TopicWeightage
from app.academics.models.lesson_plans import LessonPlan, LessonPlanUnit, TeachingProgress
from app.academics.models.teaching_assignments import TeachingAssignment

# Finance models
from app.finance.models import (
    FeeComponent, FeeStructure, FeeStructureItem, StudentFeeAccount,
    FeeInvoice, FeePayment, FeeReceipt, FeeDiscount, FeeChallan
)

# Payment Gateway models
from app.payments.models import GatewayConfig, PaymentOrder, PaymentTransaction, PaymentRefund, WebhookEvent

# Attendance models
from app.attendance.models import StudentAttendance, AttendanceSummary, LeaveRequest, TeacherAttendance

# Calendar
from app.calendar.models import CalendarEvent

print("✓ Core models imported")


async def init_db():
    """Create all tables."""
    print("🔄 Creating all database tables on PostgreSQL...")
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)
    print("✅ All tables created successfully!")


if __name__ == "__main__":
    asyncio.run(init_db())
