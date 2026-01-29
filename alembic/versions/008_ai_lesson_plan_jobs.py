"""create ai lesson plan jobs table

Revision ID: 008_ai_lesson_plan_jobs
Revises: 007_lesson_evaluation
Create Date: 2026-01-29

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '008_ai_lesson_plan_jobs'
down_revision = '007_lesson_evaluation'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create AIJobStatus enum
    op.execute("""
        CREATE TYPE aijobstatus AS ENUM (
            'pending', 'running', 'completed', 'failed'
        )
    """)
    
    # Create ai_lesson_plan_jobs table
    op.create_table(
        'ai_lesson_plan_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('teacher_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('class_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('classes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('subject_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('subjects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('syllabus_subject_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('syllabus_subjects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', postgresql.ENUM('pending', 'running', 'completed', 'failed', name='aijobstatus', create_type=False), nullable=False, default='pending'),
        sa.Column('ai_provider', sa.String(50), default='openai', nullable=False),
        sa.Column('input_snapshot', postgresql.JSON(), nullable=False, default={}),
        sa.Column('output_snapshot', postgresql.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('lesson_plan_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('lesson_plans.id', ondelete='SET NULL'), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tokens_used', sa.Integer(), default=0, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    
    # Create indexes
    op.create_index(
        'ix_ai_job_tenant_teacher',
        'ai_lesson_plan_jobs',
        ['tenant_id', 'teacher_id']
    )
    op.create_index(
        'ix_ai_job_status',
        'ai_lesson_plan_jobs',
        ['tenant_id', 'status']
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_ai_job_status', table_name='ai_lesson_plan_jobs')
    op.drop_index('ix_ai_job_tenant_teacher', table_name='ai_lesson_plan_jobs')
    
    # Drop table
    op.drop_table('ai_lesson_plan_jobs')
    
    # Drop enum
    op.execute("DROP TYPE aijobstatus")
