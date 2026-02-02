"""Add job executions table

Revision ID: phase8_job_executions
Revises: phase7_insights
Create Date: 2026-02-02

This migration adds:
- Job executions table for idempotency and tracking
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'phase8_job_executions'
down_revision = 'phase7_insights'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ============================================
    # Job Executions Table
    # ============================================
    op.create_table(
        'job_executions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        
        # Job identification
        sa.Column('job_key', sa.String(500), nullable=False),
        sa.Column('job_type', sa.String(50), nullable=False),
        
        # Status
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('attempt', sa.Integer, default=1),
        sa.Column('max_attempts', sa.Integer, default=1),
        
        # Timing
        sa.Column('queued_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        
        # Result/Error
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('result_json', postgresql.JSONB, nullable=True),
        
        # Context
        sa.Column('actor_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('request_id', sa.String(100), nullable=True),
        sa.Column('input_json', postgresql.JSONB, nullable=True),
        
        # Base model fields
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    
    # Indexes for performance
    op.create_index('ix_job_exec_job_key', 'job_executions', ['job_key'])
    op.create_index('ix_job_exec_job_type', 'job_executions', ['job_type'])
    op.create_index('ix_job_exec_status', 'job_executions', ['status'])
    
    # Composite indexes
    op.create_index('ix_job_exec_idempotency', 'job_executions', ['tenant_id', 'job_key', 'status'])
    op.create_index('ix_job_exec_type_status', 'job_executions', ['tenant_id', 'job_type', 'status'])
    op.create_index('ix_job_exec_recent', 'job_executions', ['tenant_id', 'created_at'])


def downgrade() -> None:
    op.drop_table('job_executions')
