"""Phase 8.5c: Safe Correction Framework

Revision ID: phase85c_corrections
Revises: phase85b_participation
Create Date: 2026-02-02

Adds correction request and record tables for controlled reversals.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'phase85c_corrections'
down_revision = 'phase85b_participation'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create EntityType enum
    entity_type_enum = sa.Enum(
        'attendance', 'weekly_test', 'lesson_eval', 'daily_loop',
        'fee_invoice', 'payment', 'payroll', 'schedule', 'student_lifecycle',
        name='entitytype'
    )
    entity_type_enum.create(op.get_bind(), checkfirst=True)
    
    # Create CorrectionType enum
    correction_type_enum = sa.Enum(
        'value_change', 'void', 'reinstate', 'backdate', 'merge',
        name='correctiontype'
    )
    correction_type_enum.create(op.get_bind(), checkfirst=True)
    
    # Create CorrectionStatus enum
    correction_status_enum = sa.Enum(
        'pending', 'approved', 'rejected', 'applied', 'failed',
        name='correctionstatus'
    )
    correction_status_enum.create(op.get_bind(), checkfirst=True)
    
    # Create ImpactLevel enum
    impact_level_enum = sa.Enum(
        'none', 'low', 'medium', 'high', 'critical',
        name='impactlevel'
    )
    impact_level_enum.create(op.get_bind(), checkfirst=True)
    
    # =============================================
    # Correction Requests Table
    # =============================================
    op.create_table(
        'correction_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        
        # What is being corrected
        sa.Column('entity_type', entity_type_enum, nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        
        # What kind of correction
        sa.Column('correction_type', correction_type_enum, nullable=False),
        
        # Record date for time-lock check
        sa.Column('record_date', sa.Date(), nullable=False),
        
        # Values
        sa.Column('current_value', postgresql.JSONB(), nullable=False),
        sa.Column('corrected_value', postgresql.JSONB(), nullable=False),
        
        # Reason
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('reference_document', sa.String(500), nullable=True),
        
        # Impact
        sa.Column('impact_level', impact_level_enum, nullable=False, server_default='low'),
        sa.Column('affected_entities', postgresql.JSONB(), nullable=True),
        
        # Status
        sa.Column('status', correction_status_enum, nullable=False, server_default='pending'),
        
        # Requester
        sa.Column('requested_by', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('requested_at', sa.DateTime(timezone=True), nullable=False),
        
        # Review
        sa.Column('reviewed_by', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('review_notes', sa.Text(), nullable=True),
        
        # Application
        sa.Column('applied_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('application_result', postgresql.JSONB(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
    )
    
    op.create_index('ix_correction_tenant_status', 'correction_requests',
                    ['tenant_id', 'status'])
    op.create_index('ix_correction_entity', 'correction_requests',
                    ['entity_type', 'entity_id'])
    op.create_index('ix_correction_date', 'correction_requests',
                    ['tenant_id', 'requested_at'])
    
    # =============================================
    # Correction Records Table (Immutable Audit)
    # =============================================
    op.create_table(
        'correction_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        
        # Link to request
        sa.Column('request_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('correction_requests.id', ondelete='CASCADE'), nullable=False),
        
        # What was corrected
        sa.Column('entity_type', entity_type_enum, nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        
        # Before/After snapshots
        sa.Column('before_snapshot', postgresql.JSONB(), nullable=False),
        sa.Column('after_snapshot', postgresql.JSONB(), nullable=False),
        
        # Correction details
        sa.Column('correction_type', correction_type_enum, nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        
        # Who and when
        sa.Column('corrected_by', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('corrected_at', sa.DateTime(timezone=True), nullable=False),
        
        # Downstream
        sa.Column('downstream_updates', postgresql.JSONB(), nullable=True),
    )
    
    op.create_index('ix_correction_record_entity', 'correction_records',
                    ['entity_type', 'entity_id'])
    op.create_index('ix_correction_record_date', 'correction_records',
                    ['tenant_id', 'corrected_at'])
    
    # =============================================
    # Time Lock Overrides Table
    # =============================================
    op.create_table(
        'time_lock_overrides',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        
        sa.Column('entity_type', entity_type_enum, nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('authorized_by', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        
        sa.Column('is_permanent', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('used', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('time_lock_overrides')
    op.drop_table('correction_records')
    op.drop_table('correction_requests')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS impactlevel')
    op.execute('DROP TYPE IF EXISTS correctionstatus')
    op.execute('DROP TYPE IF EXISTS correctiontype')
    op.execute('DROP TYPE IF EXISTS entitytype')
