"""Add AI insights tables

Revision ID: phase7_insights
Revises: phase7_governance
Create Date: 2026-02-01

This migration adds:
- Insight jobs table
- Generated insights table
- Insight quotas table
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'phase7_insights'
down_revision = 'phase7_governance'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ============================================
    # Insight Jobs Table
    # ============================================
    op.create_table(
        'insights_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        
        # Requestor info
        sa.Column('requested_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=False),
        sa.Column('requestor_role', sa.String(20), nullable=False),
        sa.Column('requestor_email', sa.String(200), nullable=True),
        
        # Insight type and target
        sa.Column('insight_type', sa.String(20), nullable=False),
        sa.Column('target_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('target_name', sa.String(200), nullable=True),
        
        # Period
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        
        # Snapshot references
        sa.Column('snapshot_ids_json', postgresql.JSONB, nullable=True),
        
        # Status
        sa.Column('status', sa.String(20), default='pending'),
        
        # AI usage tracking
        sa.Column('tokens_used', sa.Integer, default=0),
        sa.Column('prompt_version', sa.String(20), nullable=True),
        sa.Column('model_used', sa.String(50), nullable=True),
        
        # Timing
        sa.Column('processing_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        
        # Error tracking
        sa.Column('error_message', sa.Text, nullable=True),
        
        # Request context
        sa.Column('ip_address', sa.String(45), nullable=True),
        
        # Base model fields
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_insight_job_tenant_status', 'insights_jobs', ['tenant_id', 'status'])
    op.create_index('ix_insight_job_requestor', 'insights_jobs', ['requested_by'])
    
    # ============================================
    # Generated Insights Table
    # ============================================
    op.create_table(
        'insights_generated',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        
        # Parent job
        sa.Column('insight_job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('insights_jobs.id', ondelete='CASCADE'), nullable=False),
        
        # Category and severity
        sa.Column('category', sa.String(30), nullable=False),
        sa.Column('severity', sa.String(10), default='info'),
        
        # Content
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('explanation_text', sa.Text, nullable=False),
        
        # Evidence (references only)
        sa.Column('evidence_json', postgresql.JSONB, nullable=True),
        
        # Suggested actions
        sa.Column('suggested_actions', postgresql.JSONB, nullable=True),
        
        # Confidence
        sa.Column('confidence_score', sa.Numeric(3, 2), default=0.5),
        
        # Metadata
        sa.Column('display_order', sa.Integer, default=0),
        sa.Column('is_actionable', sa.Boolean, default=True),
        
        # Base model fields
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_insight_job', 'insights_generated', ['insight_job_id'])
    op.create_index('ix_insight_category', 'insights_generated', ['category'])
    op.create_index('ix_insight_severity', 'insights_generated', ['severity'])
    
    # ============================================
    # Insight Quotas Table
    # ============================================
    op.create_table(
        'insights_quotas',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        
        # Period
        sa.Column('month', sa.Integer, nullable=False),
        sa.Column('year', sa.Integer, nullable=False),
        
        # Limits
        sa.Column('max_requests', sa.Integer, default=100),
        sa.Column('max_tokens', sa.Integer, default=100000),
        
        # Usage
        sa.Column('requests_used', sa.Integer, default=0),
        sa.Column('tokens_used', sa.Integer, default=0),
        
        # Last request
        sa.Column('last_request_at', sa.DateTime(timezone=True), nullable=True),
        
        # Base model fields
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_insight_quota_tenant_month', 'insights_quotas', ['tenant_id', 'month', 'year'])


def downgrade() -> None:
    op.drop_table('insights_quotas')
    op.drop_table('insights_generated')
    op.drop_table('insights_jobs')
