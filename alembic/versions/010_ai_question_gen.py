"""ai question gen and usage quotas

Revision ID: 010_ai_question_gen
Revises: 009_ocr_engine
Create Date: 2026-01-29

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '010_ai_question_gen'
down_revision = '009_ocr_engine'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enums for question generation
    op.execute("""
        CREATE TYPE questiongendifficulty AS ENUM (
            'easy', 'medium', 'hard', 'mixed'
        )
    """)
    
    op.execute("""
        CREATE TYPE questiongentype AS ENUM (
            'mcq', 'true_false', 'short_answer', 'long_answer',
            'numerical', 'fill_blank', 'mixed'
        )
    """)
    
    # Create ai_question_gen_jobs table
    op.create_table(
        'ai_question_gen_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('requested_by', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('topic_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('syllabus_topics.id', ondelete='CASCADE'), nullable=False),
        sa.Column('subject_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('subjects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('class_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('classes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('difficulty', postgresql.ENUM('easy', 'medium', 'hard', 'mixed', 
                  name='questiongendifficulty', create_type=False), 
                  nullable=False, default='mixed'),
        sa.Column('question_type', postgresql.ENUM('mcq', 'true_false', 'short_answer', 
                  'long_answer', 'numerical', 'fill_blank', 'mixed',
                  name='questiongentype', create_type=False), 
                  nullable=False, default='mcq'),
        sa.Column('count', sa.Integer(), default=10, nullable=False),
        sa.Column('status', postgresql.ENUM('pending', 'running', 'completed', 'failed', 
                  name='aijobstatus', create_type=False), 
                  nullable=False, default='pending'),
        sa.Column('ai_provider', sa.String(50), default='openai', nullable=False),
        sa.Column('input_snapshot', postgresql.JSON(), nullable=False, default={}),
        sa.Column('output_snapshot', postgresql.JSON(), nullable=True),
        sa.Column('created_question_ids', postgresql.JSON(), nullable=True),
        sa.Column('questions_created', sa.Integer(), default=0, nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tokens_used', sa.Integer(), default=0, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), default=False, nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    
    # Create indexes
    op.create_index('ix_ai_qgen_tenant_teacher', 'ai_question_gen_jobs', ['tenant_id', 'requested_by'])
    op.create_index('ix_ai_qgen_status', 'ai_question_gen_jobs', ['tenant_id', 'status'])
    op.create_index('ix_ai_qgen_topic', 'ai_question_gen_jobs', ['topic_id'])
    
    # Add tier column to subscriptions
    op.add_column('subscriptions', sa.Column(
        'tier', 
        postgresql.ENUM('free', 'starter', 'professional', 'enterprise', 
                        name='plantier', create_type=False),
        nullable=True,
        default='starter'
    ))
    
    # Add new AI usage columns to usage_limits
    op.add_column('usage_limits', sa.Column('ocr_requests_used', sa.Integer(), default=0, nullable=True))
    op.add_column('usage_limits', sa.Column('lesson_plan_gen_used', sa.Integer(), default=0, nullable=True))
    op.add_column('usage_limits', sa.Column('question_gen_used', sa.Integer(), default=0, nullable=True))
    op.add_column('usage_limits', sa.Column('doubt_solver_used', sa.Integer(), default=0, nullable=True))
    op.add_column('usage_limits', sa.Column('total_tokens_used', sa.Integer(), default=0, nullable=True))
    
    # Create index on usage_limits
    op.create_index('ix_usage_tenant_period', 'usage_limits', ['tenant_id', 'year', 'month'])
    
    # Set default values for existing rows
    op.execute("""
        UPDATE usage_limits 
        SET ocr_requests_used = 0,
            lesson_plan_gen_used = 0,
            question_gen_used = 0,
            doubt_solver_used = 0,
            total_tokens_used = 0
        WHERE ocr_requests_used IS NULL
    """)
    
    op.execute("""
        UPDATE subscriptions SET tier = 'starter' WHERE tier IS NULL
    """)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_usage_tenant_period', table_name='usage_limits')
    op.drop_index('ix_ai_qgen_topic', table_name='ai_question_gen_jobs')
    op.drop_index('ix_ai_qgen_status', table_name='ai_question_gen_jobs')
    op.drop_index('ix_ai_qgen_tenant_teacher', table_name='ai_question_gen_jobs')
    
    # Drop columns from usage_limits
    op.drop_column('usage_limits', 'total_tokens_used')
    op.drop_column('usage_limits', 'doubt_solver_used')
    op.drop_column('usage_limits', 'question_gen_used')
    op.drop_column('usage_limits', 'lesson_plan_gen_used')
    op.drop_column('usage_limits', 'ocr_requests_used')
    
    # Drop tier from subscriptions
    op.drop_column('subscriptions', 'tier')
    
    # Drop table
    op.drop_table('ai_question_gen_jobs')
    
    # Drop enums
    op.execute("DROP TYPE questiongentype")
    op.execute("DROP TYPE questiongendifficulty")
