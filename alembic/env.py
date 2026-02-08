"""
Alembic Environment Configuration

Updated for app_new structure.
"""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy import CHAR

from alembic import context

# Register UUID type for SQLite (which doesn't support UUID natively)
# This makes migrations work on SQLite by converting UUID to CHAR(36)
import sqlalchemy
from sqlalchemy.dialects import sqlite
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID, JSON as PostgresJSON
from sqlalchemy.ext.compiler import compiles

# SQLite foreign key pragma - only for SQLite connections
@sqlalchemy.event.listens_for(sqlalchemy.engine.Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Enable foreign keys for SQLite only."""
    # Check if this is a SQLite connection
    if 'sqlite' in type(dbapi_connection).__module__:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

# Register type compiler for PostgreSQL UUID -> SQLite CHAR(36)
@compiles(PostgresUUID, "sqlite")
def compile_uuid_sqlite(type_, compiler_obj, **kw):
    """Compile PostgreSQL UUID as CHAR(36) for SQLite."""
    return "CHAR(36)"

# Register type compiler for PostgreSQL JSON -> SQLite TEXT
@compiles(PostgresJSON, "sqlite")
def compile_json_sqlite(type_, compiler_obj, **kw):
    """Compile PostgreSQL JSON as TEXT for SQLite."""
    return "TEXT"


# Import base and all models for new structure
from app.core.base_model import BaseModel

# Import all models to register them with Base.metadata
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

# Syllabus Engine (Phase 2)
from app.academics.models.syllabus import (
    Board, ClassLevel, SyllabusSubject, Chapter, SyllabusTopic, TopicWeightage
)

# Lesson Planning (Phase 2)
from app.academics.models.lesson_plans import (
    LessonPlan, LessonPlanUnit, TeachingProgress
)

# Teaching Assignments (Phase 2)
from app.academics.models.teaching_assignments import TeachingAssignment

# Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add your model's MetaData object here
target_metadata = BaseModel.metadata


def get_url():
    """Get database URL from environment."""
    from app.core.config import settings
    return settings.database_url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with connection."""
    # Use render_as_batch for SQLite to support constraint operations
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_as_batch=True,  # Required for SQLite ALTER TABLE operations
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run async migrations."""
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
