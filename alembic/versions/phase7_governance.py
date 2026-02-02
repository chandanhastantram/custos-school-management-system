"""Add governance and compliance tables

Revision ID: phase7_governance
Revises: phase7_analytics
Create Date: 2026-02-01

This migration adds:
- Audit logs table (IMMUTABLE, append-only)
- Data access logs table
- Consent records table
- Inspection exports table
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'phase7_governance'
down_revision = 'phase7_analytics'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ============================================
    # Audit Logs Table (IMMUTABLE)
    # ============================================
    op.create_table(
        'governance_audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        
        # Actor information
        sa.Column('actor_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('actor_role', sa.String(50), nullable=True),
        sa.Column('actor_email', sa.String(200), nullable=True),
        
        # Action
        sa.Column('action_type', sa.String(30), nullable=False),
        
        # Entity
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('entity_name', sa.String(300), nullable=True),
        
        # Change details
        sa.Column('old_value_json', postgresql.JSONB, nullable=True),
        sa.Column('new_value_json', postgresql.JSONB, nullable=True),
        
        # Context
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('metadata_json', postgresql.JSONB, nullable=True),
        
        # Request context
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('request_id', sa.String(100), nullable=True),
        
        # Timestamp (immutable)
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        
        # Only created_at, NO updated_at (immutable)
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_audit_tenant_timestamp', 'governance_audit_logs', ['tenant_id', 'timestamp'])
    op.create_index('ix_audit_actor', 'governance_audit_logs', ['actor_user_id'])
    op.create_index('ix_audit_entity', 'governance_audit_logs', ['entity_type', 'entity_id'])
    op.create_index('ix_audit_action', 'governance_audit_logs', ['action_type'])
    
    # ============================================
    # Data Access Logs Table
    # ============================================
    op.create_table(
        'governance_data_access_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        
        # Who accessed
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=False),
        sa.Column('user_role', sa.String(50), nullable=True),
        sa.Column('user_email', sa.String(200), nullable=True),
        
        # What was accessed
        sa.Column('accessed_resource', sa.String(300), nullable=False),
        sa.Column('resource_type', sa.String(100), nullable=True),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), nullable=True),
        
        # Access type
        sa.Column('access_type', sa.String(20), nullable=False),
        
        # Context
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('request_path', sa.String(500), nullable=True),
        
        # Result
        sa.Column('success', sa.Boolean, default=True),
        sa.Column('records_accessed', sa.Integer, default=1),
        
        # Timestamp
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_data_access_tenant_timestamp', 'governance_data_access_logs', ['tenant_id', 'timestamp'])
    op.create_index('ix_data_access_user', 'governance_data_access_logs', ['user_id'])
    op.create_index('ix_data_access_resource', 'governance_data_access_logs', ['accessed_resource'])
    
    # ============================================
    # Consent Records Table
    # ============================================
    op.create_table(
        'governance_consent_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        
        # Subject
        sa.Column('subject_type', sa.String(20), nullable=False),
        sa.Column('subject_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('subject_name', sa.String(200), nullable=True),
        
        # Guardian (for minors)
        sa.Column('guardian_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('guardian_name', sa.String(200), nullable=True),
        sa.Column('guardian_relation', sa.String(50), nullable=True),
        
        # Consent details
        sa.Column('consent_type', sa.String(30), nullable=False),
        sa.Column('consent_text', sa.Text, nullable=True),
        sa.Column('consent_version', sa.String(20), nullable=True),
        
        # Status
        sa.Column('granted', sa.Boolean, default=False),
        sa.Column('granted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('granted_ip', sa.String(45), nullable=True),
        
        # Revocation
        sa.Column('revoked', sa.Boolean, default=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoked_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('revocation_reason', sa.Text, nullable=True),
        
        # Expiry
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        
        # Metadata
        sa.Column('metadata_json', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_consent_tenant_subject', 'governance_consent_records', ['tenant_id', 'subject_type', 'subject_id'])
    op.create_index('ix_consent_type', 'governance_consent_records', ['consent_type'])
    
    # ============================================
    # Inspection Exports Table
    # ============================================
    op.create_table(
        'governance_inspection_exports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        
        # Requestor
        sa.Column('requested_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=False),
        sa.Column('requestor_name', sa.String(200), nullable=True),
        sa.Column('requestor_role', sa.String(50), nullable=True),
        
        # Scope
        sa.Column('scope', sa.String(30), nullable=False),
        sa.Column('date_from', sa.DateTime(timezone=True), nullable=True),
        sa.Column('date_to', sa.DateTime(timezone=True), nullable=True),
        sa.Column('filters_json', postgresql.JSONB, nullable=True),
        
        # Status
        sa.Column('status', sa.String(20), default='pending'),
        
        # File
        sa.Column('file_path', sa.String(500), nullable=True),
        sa.Column('file_format', sa.String(20), nullable=True),
        sa.Column('file_size_bytes', sa.Integer, nullable=True),
        sa.Column('file_checksum', sa.String(100), nullable=True),
        
        # Timing
        sa.Column('requested_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('downloaded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        
        # Reference
        sa.Column('reference_number', sa.String(50), nullable=True),
        sa.Column('purpose', sa.Text, nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        
        # Error
        sa.Column('error_message', sa.Text, nullable=True),
        
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_inspection_tenant_status', 'governance_inspection_exports', ['tenant_id', 'status'])


def downgrade() -> None:
    op.drop_table('governance_inspection_exports')
    op.drop_table('governance_consent_records')
    op.drop_table('governance_data_access_logs')
    op.drop_table('governance_audit_logs')
