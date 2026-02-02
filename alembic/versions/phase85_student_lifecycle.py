"""Phase 8.5: Student Lifecycle Events

Revision ID: phase85_student_lifecycle
Revises: phase8_job_executions
Create Date: 2026-02-02

Adds:
- student_lifecycle_events table
- Lifecycle state fields on student_profiles
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'phase85_student_lifecycle'
down_revision = 'phase8_job_executions'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create lifecycle state enum
    lifecycle_state = postgresql.ENUM(
        'active', 'inactive', 'suspended', 
        'transferred_out', 'graduated', 'dropped',
        name='studentlifecyclestate',
        create_type=False,
    )
    lifecycle_state.create(op.get_bind(), checkfirst=True)
    
    # Create student_lifecycle_events table
    op.create_table(
        'student_lifecycle_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('previous_state', sa.Enum(
            'active', 'inactive', 'suspended', 
            'transferred_out', 'graduated', 'dropped',
            name='studentlifecyclestate',
        ), nullable=False),
        sa.Column('new_state', sa.Enum(
            'active', 'inactive', 'suspended', 
            'transferred_out', 'graduated', 'dropped',
            name='studentlifecyclestate',
        ), nullable=False),
        sa.Column('effective_date', sa.Date(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('reference_document', sa.String(500), nullable=True),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), default=False, nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['student_profiles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='SET NULL'),
    )
    
    # Indexes for efficient state resolution
    op.create_index(
        'ix_lifecycle_student_effective',
        'student_lifecycle_events',
        ['student_id', 'effective_date'],
    )
    op.create_index(
        'ix_lifecycle_tenant_effective',
        'student_lifecycle_events',
        ['tenant_id', 'effective_date'],
    )
    op.create_index(
        'ix_lifecycle_events_student_id',
        'student_lifecycle_events',
        ['student_id'],
    )
    
    # Add lifecycle state fields to student_profiles
    op.add_column(
        'student_profiles',
        sa.Column(
            'current_lifecycle_state',
            sa.String(20),
            nullable=False,
            server_default='active',
        ),
    )
    op.add_column(
        'student_profiles',
        sa.Column(
            'current_state_effective_date',
            sa.Date(),
            nullable=True,
        ),
    )
    
    # Index for filtering by state
    op.create_index(
        'ix_student_profiles_lifecycle_state',
        'student_profiles',
        ['current_lifecycle_state'],
    )


def downgrade() -> None:
    # Remove indexes
    op.drop_index('ix_student_profiles_lifecycle_state', table_name='student_profiles')
    op.drop_index('ix_lifecycle_events_student_id', table_name='student_lifecycle_events')
    op.drop_index('ix_lifecycle_tenant_effective', table_name='student_lifecycle_events')
    op.drop_index('ix_lifecycle_student_effective', table_name='student_lifecycle_events')
    
    # Remove columns from student_profiles
    op.drop_column('student_profiles', 'current_state_effective_date')
    op.drop_column('student_profiles', 'current_lifecycle_state')
    
    # Drop table
    op.drop_table('student_lifecycle_events')
    
    # Note: We don't drop the enum as it might be used elsewhere
