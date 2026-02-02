"""Add transport management tables

Revision ID: phase6_transport
Revises: phase5_payment_gateway
Create Date: 2026-02-01

This migration adds:
- Transport vehicles table
- Transport drivers table
- Transport routes table
- Route stops table
- Transport assignments table
- Student transport table
- Transport fee links table
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'phase6_transport'
down_revision = 'phase5_payment_gateway'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ============================================
    # Vehicles Table
    # ============================================
    op.create_table(
        'transport_vehicles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('vehicle_number', sa.String(50), nullable=False),
        sa.Column('vehicle_type', sa.String(20), default='bus'),
        sa.Column('make', sa.String(100), nullable=True),
        sa.Column('model', sa.String(100), nullable=True),
        sa.Column('year', sa.Integer, nullable=True),
        sa.Column('capacity', sa.Integer, nullable=False, default=40),
        sa.Column('registration_number', sa.String(100), nullable=True),
        sa.Column('registration_expiry', sa.Date, nullable=True),
        sa.Column('insurance_number', sa.String(100), nullable=True),
        sa.Column('insurance_expiry', sa.Date, nullable=True),
        sa.Column('fitness_certificate', sa.String(100), nullable=True),
        sa.Column('fitness_expiry', sa.Date, nullable=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_unique_constraint('uq_vehicle_number', 'transport_vehicles', ['tenant_id', 'vehicle_number'])
    op.create_index('ix_transport_vehicles_tenant', 'transport_vehicles', ['tenant_id', 'is_active'])
    
    # ============================================
    # Drivers Table
    # ============================================
    op.create_table(
        'transport_drivers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('phone', sa.String(20), nullable=False),
        sa.Column('alternate_phone', sa.String(20), nullable=True),
        sa.Column('email', sa.String(200), nullable=True),
        sa.Column('address', sa.Text, nullable=True),
        sa.Column('license_number', sa.String(50), nullable=False),
        sa.Column('license_type', sa.String(20), nullable=True),
        sa.Column('license_expiry', sa.Date, nullable=True),
        sa.Column('emergency_contact_name', sa.String(200), nullable=True),
        sa.Column('emergency_contact_phone', sa.String(20), nullable=True),
        sa.Column('blood_group', sa.String(10), nullable=True),
        sa.Column('photo_url', sa.String(500), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_unique_constraint('uq_driver_license', 'transport_drivers', ['tenant_id', 'license_number'])
    op.create_index('ix_transport_drivers_tenant', 'transport_drivers', ['tenant_id', 'is_active'])
    
    # ============================================
    # Routes Table
    # ============================================
    op.create_table(
        'transport_routes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('code', sa.String(20), nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('shift', sa.String(20), default='both'),
        sa.Column('distance_km', sa.Numeric(8, 2), nullable=True),
        sa.Column('estimated_duration_minutes', sa.Integer, nullable=True),
        sa.Column('start_location', sa.String(300), nullable=True),
        sa.Column('end_location', sa.String(300), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_unique_constraint('uq_route_name', 'transport_routes', ['tenant_id', 'name'])
    op.create_index('ix_transport_routes_tenant', 'transport_routes', ['tenant_id', 'is_active'])
    
    # ============================================
    # Route Stops Table
    # ============================================
    op.create_table(
        'transport_route_stops',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('route_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('transport_routes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('stop_name', sa.String(200), nullable=False),
        sa.Column('stop_address', sa.Text, nullable=True),
        sa.Column('latitude', sa.Numeric(10, 8), nullable=True),
        sa.Column('longitude', sa.Numeric(11, 8), nullable=True),
        sa.Column('pickup_time', sa.Time, nullable=True),
        sa.Column('drop_time', sa.Time, nullable=True),
        sa.Column('stop_order', sa.Integer, nullable=False),
        sa.Column('landmark', sa.String(300), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_unique_constraint('uq_route_stop_order', 'transport_route_stops', ['route_id', 'stop_order'])
    op.create_index('ix_route_stops_route', 'transport_route_stops', ['route_id'])
    
    # ============================================
    # Transport Assignments Table
    # ============================================
    op.create_table(
        'transport_assignments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('route_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('transport_routes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('vehicle_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('transport_vehicles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('driver_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('transport_drivers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('academic_year_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('academic_years.id', ondelete='CASCADE'), nullable=False),
        sa.Column('shift', sa.String(20), default='both'),
        sa.Column('helper_name', sa.String(200), nullable=True),
        sa.Column('helper_phone', sa.String(20), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_unique_constraint('uq_transport_assignment', 'transport_assignments', ['tenant_id', 'route_id', 'academic_year_id', 'shift'])
    op.create_index('ix_transport_assignments_tenant', 'transport_assignments', ['tenant_id', 'is_active'])
    op.create_index('ix_transport_assignments_route', 'transport_assignments', ['route_id'])
    op.create_index('ix_transport_assignments_vehicle', 'transport_assignments', ['vehicle_id'])
    op.create_index('ix_transport_assignments_driver', 'transport_assignments', ['driver_id'])
    
    # ============================================
    # Student Transport Table
    # ============================================
    op.create_table(
        'student_transport',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('route_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('transport_routes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('pickup_stop_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('transport_route_stops.id', ondelete='SET NULL'), nullable=True),
        sa.Column('drop_stop_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('transport_route_stops.id', ondelete='SET NULL'), nullable=True),
        sa.Column('assigned_from', sa.Date, nullable=False),
        sa.Column('assigned_to', sa.Date, nullable=True),
        sa.Column('academic_year_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('academic_years.id', ondelete='SET NULL'), nullable=True),
        sa.Column('guardian_name', sa.String(200), nullable=True),
        sa.Column('guardian_phone', sa.String(20), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_student_transport_tenant', 'student_transport', ['tenant_id', 'is_active'])
    op.create_index('ix_student_transport_student', 'student_transport', ['student_id'])
    op.create_index('ix_student_transport_route', 'student_transport', ['route_id'])
    
    # ============================================
    # Transport Fee Links Table
    # ============================================
    op.create_table(
        'transport_fee_links',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_transport_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('student_transport.id', ondelete='SET NULL'), nullable=True),
        sa.Column('monthly_fee', sa.Numeric(10, 2), nullable=False),
        sa.Column('linked_invoice_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('fee_invoices.id', ondelete='SET NULL'), nullable=True),
        sa.Column('fee_month', sa.Integer, nullable=False),
        sa.Column('fee_year', sa.Integer, nullable=False),
        sa.Column('is_paid', sa.Boolean, default=False),
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_transport_fee_links_tenant', 'transport_fee_links', ['tenant_id'])
    op.create_index('ix_transport_fee_links_student', 'transport_fee_links', ['student_id'])


def downgrade() -> None:
    op.drop_table('transport_fee_links')
    op.drop_table('student_transport')
    op.drop_table('transport_assignments')
    op.drop_table('transport_route_stops')
    op.drop_table('transport_routes')
    op.drop_table('transport_drivers')
    op.drop_table('transport_vehicles')
