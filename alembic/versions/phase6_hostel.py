"""Add hostel management tables

Revision ID: phase6_hostel
Revises: phase6_transport
Create Date: 2026-02-01

This migration adds:
- Hostels table
- Hostel rooms table
- Hostel beds table
- Hostel wardens table
- Student hostel assignments table
- Hostel fee links table
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'phase6_hostel'
down_revision = 'phase6_transport'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ============================================
    # Hostels Table
    # ============================================
    op.create_table(
        'hostels',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('code', sa.String(20), nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('gender', sa.String(20), default='mixed'),
        sa.Column('address', sa.Text, nullable=True),
        sa.Column('building_name', sa.String(200), nullable=True),
        sa.Column('total_capacity', sa.Integer, default=0),
        sa.Column('floor_count', sa.Integer, default=1),
        sa.Column('contact_phone', sa.String(20), nullable=True),
        sa.Column('contact_email', sa.String(200), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_unique_constraint('uq_hostel_name', 'hostels', ['tenant_id', 'name'])
    op.create_index('ix_hostels_tenant', 'hostels', ['tenant_id', 'is_active'])
    
    # ============================================
    # Hostel Rooms Table
    # ============================================
    op.create_table(
        'hostel_rooms',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('hostel_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('hostels.id', ondelete='CASCADE'), nullable=False),
        sa.Column('room_number', sa.String(20), nullable=False),
        sa.Column('room_type', sa.String(50), nullable=True),
        sa.Column('floor', sa.Integer, default=0),
        sa.Column('capacity', sa.Integer, default=1),
        sa.Column('has_attached_bathroom', sa.Boolean, default=False),
        sa.Column('has_ac', sa.Boolean, default=False),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_unique_constraint('uq_room_number', 'hostel_rooms', ['hostel_id', 'room_number'])
    op.create_index('ix_hostel_rooms_hostel', 'hostel_rooms', ['hostel_id', 'is_active'])
    
    # ============================================
    # Hostel Beds Table
    # ============================================
    op.create_table(
        'hostel_beds',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('room_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('hostel_rooms.id', ondelete='CASCADE'), nullable=False),
        sa.Column('bed_number', sa.String(20), nullable=False),
        sa.Column('bed_type', sa.String(50), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('is_occupied', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_unique_constraint('uq_bed_number', 'hostel_beds', ['room_id', 'bed_number'])
    op.create_index('ix_hostel_beds_room', 'hostel_beds', ['room_id', 'is_active'])
    
    # ============================================
    # Hostel Wardens Table
    # ============================================
    op.create_table(
        'hostel_wardens',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('phone', sa.String(20), nullable=False),
        sa.Column('alternate_phone', sa.String(20), nullable=True),
        sa.Column('email', sa.String(200), nullable=True),
        sa.Column('address', sa.Text, nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('assigned_hostel_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('hostels.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_chief_warden', sa.Boolean, default=False),
        sa.Column('assigned_from', sa.Date, nullable=True),
        sa.Column('assigned_to', sa.Date, nullable=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_hostel_wardens_tenant', 'hostel_wardens', ['tenant_id', 'is_active'])
    op.create_index('ix_hostel_wardens_hostel', 'hostel_wardens', ['assigned_hostel_id'])
    
    # ============================================
    # Student Hostel Assignments Table
    # ============================================
    op.create_table(
        'student_hostel_assignments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('hostel_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('hostels.id', ondelete='CASCADE'), nullable=False),
        sa.Column('room_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('hostel_rooms.id', ondelete='CASCADE'), nullable=False),
        sa.Column('bed_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('hostel_beds.id', ondelete='CASCADE'), nullable=False),
        sa.Column('academic_year_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('academic_years.id', ondelete='SET NULL'), nullable=True),
        sa.Column('assigned_from', sa.Date, nullable=False),
        sa.Column('assigned_to', sa.Date, nullable=True),
        sa.Column('checked_in_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('checked_out_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('guardian_name', sa.String(200), nullable=True),
        sa.Column('guardian_phone', sa.String(20), nullable=True),
        sa.Column('guardian_relation', sa.String(50), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_student_hostel_tenant', 'student_hostel_assignments', ['tenant_id', 'is_active'])
    op.create_index('ix_student_hostel_student', 'student_hostel_assignments', ['student_id'])
    op.create_index('ix_student_hostel_hostel', 'student_hostel_assignments', ['hostel_id'])
    op.create_index('ix_student_hostel_room', 'student_hostel_assignments', ['room_id'])
    op.create_index('ix_student_hostel_bed', 'student_hostel_assignments', ['bed_id'])
    
    # ============================================
    # Hostel Fee Links Table
    # ============================================
    op.create_table(
        'hostel_fee_links',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('assignment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('student_hostel_assignments.id', ondelete='SET NULL'), nullable=True),
        sa.Column('monthly_fee', sa.Numeric(10, 2), nullable=False),
        sa.Column('fee_month', sa.Integer, nullable=False),
        sa.Column('fee_year', sa.Integer, nullable=False),
        sa.Column('linked_invoice_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('fee_invoices.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_paid', sa.Boolean, default=False),
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_hostel_fee_links_tenant', 'hostel_fee_links', ['tenant_id'])
    op.create_index('ix_hostel_fee_links_student', 'hostel_fee_links', ['student_id'])


def downgrade() -> None:
    op.drop_table('hostel_fee_links')
    op.drop_table('student_hostel_assignments')
    op.drop_table('hostel_wardens')
    op.drop_table('hostel_beds')
    op.drop_table('hostel_rooms')
    op.drop_table('hostels')
