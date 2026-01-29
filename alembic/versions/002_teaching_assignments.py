"""create teaching_assignments table

Revision ID: 002_teaching_assignments
Revises: 001_initial
Create Date: 2026-01-29

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_teaching_assignments'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create teaching_assignments table
    op.create_table(
        'teaching_assignments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('academic_year_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('academic_years.id', ondelete='CASCADE'), nullable=False),
        sa.Column('teacher_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('class_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('classes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('section_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sections.id', ondelete='SET NULL'), nullable=True),
        sa.Column('subject_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('subjects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('is_primary', sa.Boolean(), default=True, nullable=False),
        sa.Column('notes', sa.String(500), nullable=True),
        sa.Column('periods_per_week', sa.Integer(), default=0, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    
    # Unique constraint: one teacher per class-subject per year (within tenant)
    op.create_unique_constraint(
        'uq_teaching_assignment',
        'teaching_assignments',
        ['tenant_id', 'academic_year_id', 'teacher_id', 'class_id', 'subject_id']
    )
    
    # Indexes for common queries
    op.create_index(
        'ix_teaching_assignment_tenant',
        'teaching_assignments',
        ['tenant_id', 'is_active']
    )
    op.create_index(
        'ix_teaching_assignment_teacher',
        'teaching_assignments',
        ['tenant_id', 'teacher_id', 'is_active']
    )
    op.create_index(
        'ix_teaching_assignment_class',
        'teaching_assignments',
        ['tenant_id', 'class_id', 'is_active']
    )
    op.create_index(
        'ix_teaching_assignment_subject',
        'teaching_assignments',
        ['tenant_id', 'subject_id', 'is_active']
    )
    op.create_index(
        'ix_teaching_assignment_year',
        'teaching_assignments',
        ['tenant_id', 'academic_year_id', 'is_active']
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_teaching_assignment_year', table_name='teaching_assignments')
    op.drop_index('ix_teaching_assignment_subject', table_name='teaching_assignments')
    op.drop_index('ix_teaching_assignment_class', table_name='teaching_assignments')
    op.drop_index('ix_teaching_assignment_teacher', table_name='teaching_assignments')
    op.drop_index('ix_teaching_assignment_tenant', table_name='teaching_assignments')
    
    # Drop unique constraint
    op.drop_constraint('uq_teaching_assignment', 'teaching_assignments', type_='unique')
    
    # Drop table
    op.drop_table('teaching_assignments')
