"""create schedule tables

Revision ID: 004_schedule
Revises: 003_timetables
Create Date: 2026-01-29

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004_schedule'
down_revision = '003_timetables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create CalendarDayType enum
    op.execute("""
        CREATE TYPE calendardaytype AS ENUM (
            'working', 'holiday', 'weekend', 'exam', 'event'
        )
    """)
    
    # Create ScheduleEntryStatus enum
    op.execute("""
        CREATE TYPE scheduleentrystatus AS ENUM (
            'planned', 'completed', 'delayed', 'skipped'
        )
    """)
    
    # Create academic_calendar_days table
    op.create_table(
        'academic_calendar_days',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('academic_year_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('academic_years.id', ondelete='CASCADE'), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('day_type', postgresql.ENUM('working', 'holiday', 'weekend', 'exam', 'event', name='calendardaytype', create_type=False), nullable=False),
        sa.Column('is_working_day', sa.Boolean(), default=True, nullable=False),
        sa.Column('name', sa.String(200), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    
    # Create indexes for academic_calendar_days
    op.create_index(
        'ix_calendar_tenant_date',
        'academic_calendar_days',
        ['tenant_id', 'date']
    )
    op.create_index(
        'ix_calendar_year_date',
        'academic_calendar_days',
        ['academic_year_id', 'date']
    )
    
    # Create schedule_entries table
    op.create_table(
        'schedule_entries',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('timetable_entry_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('timetable_entries.id', ondelete='CASCADE'), nullable=False),
        sa.Column('lesson_plan_unit_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('lesson_plan_units.id', ondelete='CASCADE'), nullable=False),
        sa.Column('lesson_plan_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('lesson_plans.id', ondelete='CASCADE'), nullable=False),
        sa.Column('class_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('classes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('section_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sections.id', ondelete='SET NULL'), nullable=True),
        sa.Column('subject_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('subjects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('teacher_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('topic_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('syllabus_topics.id', ondelete='CASCADE'), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('day_of_week', sa.Integer(), nullable=False),
        sa.Column('period_number', sa.Integer(), nullable=False),
        sa.Column('status', postgresql.ENUM('planned', 'completed', 'delayed', 'skipped', name='scheduleentrystatus', create_type=False), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    
    # Create indexes for schedule_entries
    op.create_index(
        'ix_schedule_tenant_date',
        'schedule_entries',
        ['tenant_id', 'date']
    )
    op.create_index(
        'ix_schedule_class_date',
        'schedule_entries',
        ['tenant_id', 'class_id', 'date']
    )
    op.create_index(
        'ix_schedule_teacher_date',
        'schedule_entries',
        ['tenant_id', 'teacher_id', 'date']
    )
    op.create_index(
        'ix_schedule_lesson_plan',
        'schedule_entries',
        ['lesson_plan_id']
    )


def downgrade() -> None:
    # Drop indexes for schedule_entries
    op.drop_index('ix_schedule_lesson_plan', table_name='schedule_entries')
    op.drop_index('ix_schedule_teacher_date', table_name='schedule_entries')
    op.drop_index('ix_schedule_class_date', table_name='schedule_entries')
    op.drop_index('ix_schedule_tenant_date', table_name='schedule_entries')
    
    # Drop schedule_entries table
    op.drop_table('schedule_entries')
    
    # Drop indexes for academic_calendar_days
    op.drop_index('ix_calendar_year_date', table_name='academic_calendar_days')
    op.drop_index('ix_calendar_tenant_date', table_name='academic_calendar_days')
    
    # Drop academic_calendar_days table
    op.drop_table('academic_calendar_days')
    
    # Drop enums
    op.execute("DROP TYPE scheduleentrystatus")
    op.execute("DROP TYPE calendardaytype")
