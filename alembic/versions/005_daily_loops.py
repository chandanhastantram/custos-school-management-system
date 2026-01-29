"""create daily learning loop tables

Revision ID: 005_daily_loops
Revises: 004_schedule
Create Date: 2026-01-29

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005_daily_loops'
down_revision = '004_schedule'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create daily_loop_sessions table
    op.create_table(
        'daily_loop_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('schedule_entry_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('schedule_entries.id', ondelete='CASCADE'), nullable=False),
        sa.Column('class_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('classes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('section_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sections.id', ondelete='SET NULL'), nullable=True),
        sa.Column('subject_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('subjects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('topic_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('syllabus_topics.id', ondelete='CASCADE'), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('max_questions', sa.Integer(), default=10, nullable=False),
        sa.Column('time_limit_minutes', sa.Integer(), nullable=True),
        sa.Column('total_attempts', sa.Integer(), default=0, nullable=False),
        sa.Column('unique_students', sa.Integer(), default=0, nullable=False),
        sa.Column('avg_score_percent', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    
    # Create indexes for daily_loop_sessions
    op.create_index(
        'ix_daily_session_tenant_date',
        'daily_loop_sessions',
        ['tenant_id', 'date']
    )
    op.create_index(
        'ix_daily_session_schedule',
        'daily_loop_sessions',
        ['schedule_entry_id']
    )
    op.create_index(
        'ix_daily_session_class',
        'daily_loop_sessions',
        ['tenant_id', 'class_id', 'date']
    )
    op.create_index(
        'ix_daily_session_topic',
        'daily_loop_sessions',
        ['tenant_id', 'topic_id', 'date']
    )
    
    # Create daily_loop_attempts table
    op.create_table(
        'daily_loop_attempts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('daily_loop_sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('question_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('questions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('selected_option', sa.String(500), nullable=False),
        sa.Column('is_correct', sa.Boolean(), nullable=False),
        sa.Column('time_taken_seconds', sa.Integer(), default=0, nullable=False),
        sa.Column('attempt_number', sa.Integer(), default=1, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
    )
    
    # Create indexes for daily_loop_attempts
    op.create_index(
        'ix_daily_attempt_session',
        'daily_loop_attempts',
        ['session_id']
    )
    op.create_index(
        'ix_daily_attempt_student',
        'daily_loop_attempts',
        ['student_id']
    )
    op.create_index(
        'ix_daily_attempt_question',
        'daily_loop_attempts',
        ['question_id']
    )
    
    # Create student_topic_mastery table
    op.create_table(
        'student_topic_mastery',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('topic_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('syllabus_topics.id', ondelete='CASCADE'), nullable=False),
        sa.Column('total_attempts', sa.Integer(), default=0, nullable=False),
        sa.Column('correct_attempts', sa.Integer(), default=0, nullable=False),
        sa.Column('mastery_percent', sa.Float(), default=0.0, nullable=False),
        sa.Column('current_streak', sa.Integer(), default=0, nullable=False),
        sa.Column('best_streak', sa.Integer(), default=0, nullable=False),
        sa.Column('last_attempt_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    
    # Create indexes for student_topic_mastery
    op.create_index(
        'ix_mastery_student',
        'student_topic_mastery',
        ['tenant_id', 'student_id']
    )
    op.create_index(
        'ix_mastery_topic',
        'student_topic_mastery',
        ['tenant_id', 'topic_id']
    )
    
    # Unique constraint on student+topic
    op.create_unique_constraint(
        'uq_mastery_student_topic',
        'student_topic_mastery',
        ['student_id', 'topic_id']
    )


def downgrade() -> None:
    # Drop student_topic_mastery
    op.drop_constraint('uq_mastery_student_topic', 'student_topic_mastery', type_='unique')
    op.drop_index('ix_mastery_topic', table_name='student_topic_mastery')
    op.drop_index('ix_mastery_student', table_name='student_topic_mastery')
    op.drop_table('student_topic_mastery')
    
    # Drop daily_loop_attempts
    op.drop_index('ix_daily_attempt_question', table_name='daily_loop_attempts')
    op.drop_index('ix_daily_attempt_student', table_name='daily_loop_attempts')
    op.drop_index('ix_daily_attempt_session', table_name='daily_loop_attempts')
    op.drop_table('daily_loop_attempts')
    
    # Drop daily_loop_sessions
    op.drop_index('ix_daily_session_topic', table_name='daily_loop_sessions')
    op.drop_index('ix_daily_session_class', table_name='daily_loop_sessions')
    op.drop_index('ix_daily_session_schedule', table_name='daily_loop_sessions')
    op.drop_index('ix_daily_session_tenant_date', table_name='daily_loop_sessions')
    op.drop_table('daily_loop_sessions')
