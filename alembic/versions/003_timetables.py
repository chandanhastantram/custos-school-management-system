"""create timetable tables

Revision ID: 003_timetables
Revises: 002_teaching_assignments
Create Date: 2026-01-29

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_timetables'
down_revision = '002_teaching_assignments'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create timetables table
    op.create_table(
        'timetables',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('academic_year_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('academic_years.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    
    # Create indexes for timetables
    op.create_index(
        'ix_timetable_tenant',
        'timetables',
        ['tenant_id', 'is_active']
    )
    op.create_index(
        'ix_timetable_year',
        'timetables',
        ['tenant_id', 'academic_year_id', 'is_active']
    )
    
    # Create timetable_entries table
    op.create_table(
        'timetable_entries',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('timetable_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('timetables.id', ondelete='CASCADE'), nullable=False),
        sa.Column('class_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('classes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('section_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sections.id', ondelete='SET NULL'), nullable=True),
        sa.Column('subject_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('subjects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('teacher_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('day_of_week', sa.Integer(), nullable=False),
        sa.Column('period_number', sa.Integer(), nullable=False),
        sa.Column('room', sa.String(100), nullable=True),
        sa.Column('notes', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    
    # Unique constraint: one subject per class slot (day+period)
    op.create_unique_constraint(
        'uq_timetable_class_slot',
        'timetable_entries',
        ['timetable_id', 'class_id', 'day_of_week', 'period_number']
    )
    
    # Check constraints
    op.create_check_constraint(
        'ck_timetable_day_of_week',
        'timetable_entries',
        'day_of_week >= 0 AND day_of_week <= 6'
    )
    op.create_check_constraint(
        'ck_timetable_period_number',
        'timetable_entries',
        'period_number >= 1 AND period_number <= 12'
    )
    
    # Create indexes for timetable_entries
    op.create_index(
        'ix_timetable_entry_timetable',
        'timetable_entries',
        ['timetable_id']
    )
    op.create_index(
        'ix_timetable_entry_class',
        'timetable_entries',
        ['class_id', 'day_of_week', 'period_number']
    )
    op.create_index(
        'ix_timetable_entry_teacher',
        'timetable_entries',
        ['teacher_id', 'day_of_week', 'period_number']
    )
    op.create_index(
        'ix_timetable_entry_subject',
        'timetable_entries',
        ['subject_id']
    )


def downgrade() -> None:
    # Drop indexes for timetable_entries
    op.drop_index('ix_timetable_entry_subject', table_name='timetable_entries')
    op.drop_index('ix_timetable_entry_teacher', table_name='timetable_entries')
    op.drop_index('ix_timetable_entry_class', table_name='timetable_entries')
    op.drop_index('ix_timetable_entry_timetable', table_name='timetable_entries')
    
    # Drop constraints for timetable_entries
    op.drop_constraint('ck_timetable_period_number', 'timetable_entries', type_='check')
    op.drop_constraint('ck_timetable_day_of_week', 'timetable_entries', type_='check')
    op.drop_constraint('uq_timetable_class_slot', 'timetable_entries', type_='unique')
    
    # Drop timetable_entries table
    op.drop_table('timetable_entries')
    
    # Drop indexes for timetables
    op.drop_index('ix_timetable_year', table_name='timetables')
    op.drop_index('ix_timetable_tenant', table_name='timetables')
    
    # Drop timetables table
    op.drop_table('timetables')
