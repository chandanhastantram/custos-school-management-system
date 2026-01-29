"""create ocr tables

Revision ID: 009_ocr_engine
Revises: 008_ai_lesson_plan_jobs
Create Date: 2026-01-29

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '009_ocr_engine'
down_revision = '008_ai_lesson_plan_jobs'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ExamType enum
    op.execute("""
        CREATE TYPE examtype AS ENUM (
            'weekly', 'lesson'
        )
    """)
    
    # Create OCRJobStatus enum
    op.execute("""
        CREATE TYPE ocrjobstatus AS ENUM (
            'pending', 'processing', 'completed', 'failed'
        )
    """)
    
    # Create ocr_jobs table
    op.create_table(
        'ocr_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('uploaded_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('exam_type', postgresql.ENUM('weekly', 'lesson', name='examtype', create_type=False), nullable=False),
        sa.Column('exam_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', postgresql.ENUM('pending', 'processing', 'completed', 'failed', name='ocrjobstatus', create_type=False), nullable=False, default='pending'),
        sa.Column('image_path', sa.String(500), nullable=False),
        sa.Column('original_filename', sa.String(255), nullable=True),
        sa.Column('ai_provider', sa.String(50), default='openai', nullable=False),
        sa.Column('input_snapshot', postgresql.JSON(), nullable=False, default={}),
        sa.Column('output_snapshot', postgresql.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tokens_used', sa.Integer(), default=0, nullable=False),
        sa.Column('results_extracted', sa.Integer(), default=0, nullable=False),
        sa.Column('results_imported', sa.Integer(), default=0, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    
    # Create indexes for ocr_jobs
    op.create_index(
        'ix_ocr_job_tenant_teacher',
        'ocr_jobs',
        ['tenant_id', 'uploaded_by']
    )
    op.create_index(
        'ix_ocr_job_status',
        'ocr_jobs',
        ['tenant_id', 'status']
    )
    op.create_index(
        'ix_ocr_job_exam',
        'ocr_jobs',
        ['exam_type', 'exam_id']
    )
    
    # Create ocr_parsed_results table
    op.create_table(
        'ocr_parsed_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('ocr_job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('ocr_jobs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_identifier', sa.String(100), nullable=False),
        sa.Column('matched_student_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('total_marks', sa.Float(), nullable=False),
        sa.Column('marks_obtained', sa.Float(), nullable=False),
        sa.Column('attempted_questions', postgresql.JSON(), nullable=False, default=[]),
        sa.Column('wrong_questions', postgresql.JSON(), nullable=False, default=[]),
        sa.Column('percentage', sa.Float(), default=0.0, nullable=False),
        sa.Column('is_imported', sa.Boolean(), default=False, nullable=False),
        sa.Column('imported_result_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('confidence_score', sa.Float(), default=0.0, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    
    # Create index for ocr_parsed_results
    op.create_index(
        'ix_ocr_result_job',
        'ocr_parsed_results',
        ['ocr_job_id']
    )


def downgrade() -> None:
    # Drop ocr_parsed_results
    op.drop_index('ix_ocr_result_job', table_name='ocr_parsed_results')
    op.drop_table('ocr_parsed_results')
    
    # Drop ocr_jobs
    op.drop_index('ix_ocr_job_exam', table_name='ocr_jobs')
    op.drop_index('ix_ocr_job_status', table_name='ocr_jobs')
    op.drop_index('ix_ocr_job_tenant_teacher', table_name='ocr_jobs')
    op.drop_table('ocr_jobs')
    
    # Drop enums
    op.execute("DROP TYPE ocrjobstatus")
    op.execute("DROP TYPE examtype")
