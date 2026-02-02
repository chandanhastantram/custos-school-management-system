"""Add HR and payroll management tables

Revision ID: phase6_hr_payroll
Revises: phase6_hostel
Create Date: 2026-02-01

This migration adds:
- HR departments table
- HR designations table
- HR employees table
- Employment contracts table
- Salary components table
- Payroll structures table
- Payroll runs table
- Salary slips table
- Leave types table
- Leave balances table
- Leave applications table
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'phase6_hr_payroll'
down_revision = 'phase6_hostel'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ============================================
    # Departments Table
    # ============================================
    op.create_table(
        'hr_departments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('code', sa.String(20), nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('head_employee_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_unique_constraint('uq_department_name', 'hr_departments', ['tenant_id', 'name'])
    op.create_index('ix_hr_departments_tenant', 'hr_departments', ['tenant_id', 'is_active'])
    
    # ============================================
    # Designations Table
    # ============================================
    op.create_table(
        'hr_designations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('code', sa.String(20), nullable=True),
        sa.Column('level', sa.Integer, default=1),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_unique_constraint('uq_designation_name', 'hr_designations', ['tenant_id', 'name'])
    op.create_index('ix_hr_designations_tenant', 'hr_designations', ['tenant_id', 'is_active'])
    
    # ============================================
    # Employees Table
    # ============================================
    op.create_table(
        'hr_employees',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('employee_code', sa.String(50), nullable=False),
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=True),
        sa.Column('gender', sa.String(20), nullable=True),
        sa.Column('date_of_birth', sa.Date, nullable=True),
        sa.Column('email', sa.String(200), nullable=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('alternate_phone', sa.String(20), nullable=True),
        sa.Column('address', sa.Text, nullable=True),
        sa.Column('role', sa.String(30), default='other'),
        sa.Column('department_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('hr_departments.id', ondelete='SET NULL'), nullable=True),
        sa.Column('designation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('hr_designations.id', ondelete='SET NULL'), nullable=True),
        sa.Column('employment_type', sa.String(20), default='full_time'),
        sa.Column('date_of_joining', sa.Date, nullable=False),
        sa.Column('date_of_leaving', sa.Date, nullable=True),
        sa.Column('qualifications', sa.Text, nullable=True),
        sa.Column('experience_years', sa.Integer, nullable=True),
        sa.Column('photo_url', sa.String(500), nullable=True),
        sa.Column('documents_json', postgresql.JSONB, nullable=True),
        sa.Column('bank_name', sa.String(200), nullable=True),
        sa.Column('bank_account_number', sa.String(50), nullable=True),
        sa.Column('bank_ifsc', sa.String(20), nullable=True),
        sa.Column('emergency_contact_name', sa.String(200), nullable=True),
        sa.Column('emergency_contact_phone', sa.String(20), nullable=True),
        sa.Column('emergency_contact_relation', sa.String(50), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_unique_constraint('uq_employee_code', 'hr_employees', ['tenant_id', 'employee_code'])
    op.create_index('ix_hr_employees_tenant', 'hr_employees', ['tenant_id', 'is_active'])
    op.create_index('ix_hr_employees_department', 'hr_employees', ['department_id'])
    op.create_index('ix_hr_employees_designation', 'hr_employees', ['designation_id'])
    
    # ============================================
    # Salary Components Table
    # ============================================
    op.create_table(
        'hr_salary_components',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('code', sa.String(20), nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('component_type', sa.String(20), default='earning'),
        sa.Column('is_percentage', sa.Boolean, default=False),
        sa.Column('percentage_of', sa.String(50), nullable=True),
        sa.Column('default_value', sa.Numeric(12, 2), default=0),
        sa.Column('is_taxable', sa.Boolean, default=True),
        sa.Column('display_order', sa.Integer, default=0),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_unique_constraint('uq_salary_component_name', 'hr_salary_components', ['tenant_id', 'name'])
    op.create_index('ix_hr_salary_components_tenant', 'hr_salary_components', ['tenant_id', 'is_active'])
    
    # ============================================
    # Payroll Structures Table
    # ============================================
    op.create_table(
        'hr_payroll_structures',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('code', sa.String(20), nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('components_json', postgresql.JSONB, nullable=True),
        sa.Column('base_salary', sa.Numeric(12, 2), default=0),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_unique_constraint('uq_payroll_structure_name', 'hr_payroll_structures', ['tenant_id', 'name'])
    op.create_index('ix_hr_payroll_structures_tenant', 'hr_payroll_structures', ['tenant_id', 'is_active'])
    
    # ============================================
    # Employment Contracts Table
    # ============================================
    op.create_table(
        'hr_employment_contracts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('employee_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('hr_employees.id', ondelete='CASCADE'), nullable=False),
        sa.Column('salary_structure_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('hr_payroll_structures.id', ondelete='SET NULL'), nullable=True),
        sa.Column('start_date', sa.Date, nullable=False),
        sa.Column('end_date', sa.Date, nullable=True),
        sa.Column('base_salary', sa.Numeric(12, 2), nullable=True),
        sa.Column('probation_end_date', sa.Date, nullable=True),
        sa.Column('notice_period_days', sa.Integer, default=30),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_hr_contracts_employee', 'hr_employment_contracts', ['employee_id', 'is_active'])
    
    # ============================================
    # Payroll Runs Table
    # ============================================
    op.create_table(
        'hr_payroll_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('month', sa.Integer, nullable=False),
        sa.Column('year', sa.Integer, nullable=False),
        sa.Column('status', sa.String(20), default='draft'),
        sa.Column('processed_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('total_employees', sa.Integer, default=0),
        sa.Column('total_gross', sa.Numeric(14, 2), default=0),
        sa.Column('total_deductions', sa.Numeric(14, 2), default=0),
        sa.Column('total_net', sa.Numeric(14, 2), default=0),
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('payment_reference', sa.String(100), nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_unique_constraint('uq_payroll_run_month', 'hr_payroll_runs', ['tenant_id', 'month', 'year'])
    op.create_index('ix_hr_payroll_runs_tenant', 'hr_payroll_runs', ['tenant_id', 'status'])
    
    # ============================================
    # Salary Slips Table
    # ============================================
    op.create_table(
        'hr_salary_slips',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('payroll_run_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('hr_payroll_runs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('employee_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('hr_employees.id', ondelete='CASCADE'), nullable=False),
        sa.Column('basic_salary', sa.Numeric(12, 2), default=0),
        sa.Column('gross_salary', sa.Numeric(12, 2), default=0),
        sa.Column('total_deductions', sa.Numeric(12, 2), default=0),
        sa.Column('net_salary', sa.Numeric(12, 2), default=0),
        sa.Column('breakdown_json', postgresql.JSONB, nullable=True),
        sa.Column('working_days', sa.Integer, default=0),
        sa.Column('present_days', sa.Integer, default=0),
        sa.Column('leave_days', sa.Integer, default=0),
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_paid', sa.Boolean, default=False),
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_unique_constraint('uq_salary_slip_employee', 'hr_salary_slips', ['payroll_run_id', 'employee_id'])
    op.create_index('ix_hr_salary_slips_payroll', 'hr_salary_slips', ['payroll_run_id'])
    op.create_index('ix_hr_salary_slips_employee', 'hr_salary_slips', ['employee_id'])
    
    # ============================================
    # Leave Types Table
    # ============================================
    op.create_table(
        'hr_leave_types',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('code', sa.String(10), nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('annual_quota', sa.Integer, default=0),
        sa.Column('can_carry_forward', sa.Boolean, default=False),
        sa.Column('max_carry_forward', sa.Integer, default=0),
        sa.Column('is_encashable', sa.Boolean, default=False),
        sa.Column('requires_approval', sa.Boolean, default=True),
        sa.Column('min_days_notice', sa.Integer, default=0),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_unique_constraint('uq_leave_type_name', 'hr_leave_types', ['tenant_id', 'name'])
    op.create_index('ix_hr_leave_types_tenant', 'hr_leave_types', ['tenant_id', 'is_active'])
    
    # ============================================
    # Leave Balances Table
    # ============================================
    op.create_table(
        'hr_leave_balances',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('employee_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('hr_employees.id', ondelete='CASCADE'), nullable=False),
        sa.Column('leave_type_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('hr_leave_types.id', ondelete='CASCADE'), nullable=False),
        sa.Column('year', sa.Integer, nullable=False),
        sa.Column('total_allocated', sa.Integer, default=0),
        sa.Column('used_days', sa.Integer, default=0),
        sa.Column('remaining_days', sa.Integer, default=0),
        sa.Column('carried_forward', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_unique_constraint('uq_leave_balance', 'hr_leave_balances', ['employee_id', 'leave_type_id', 'year'])
    op.create_index('ix_hr_leave_balances_employee', 'hr_leave_balances', ['employee_id'])
    
    # ============================================
    # Leave Applications Table
    # ============================================
    op.create_table(
        'hr_leave_applications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('employee_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('hr_employees.id', ondelete='CASCADE'), nullable=False),
        sa.Column('leave_type_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('hr_leave_types.id', ondelete='CASCADE'), nullable=False),
        sa.Column('from_date', sa.Date, nullable=False),
        sa.Column('to_date', sa.Date, nullable=False),
        sa.Column('total_days', sa.Integer, nullable=False),
        sa.Column('is_half_day', sa.Boolean, default=False),
        sa.Column('half_day_type', sa.String(20), nullable=True),
        sa.Column('reason', sa.Text, nullable=False),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejection_reason', sa.Text, nullable=True),
        sa.Column('attachments_json', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_hr_leave_applications_employee', 'hr_leave_applications', ['employee_id'])
    op.create_index('ix_hr_leave_applications_status', 'hr_leave_applications', ['tenant_id', 'status'])


def downgrade() -> None:
    op.drop_table('hr_leave_applications')
    op.drop_table('hr_leave_balances')
    op.drop_table('hr_leave_types')
    op.drop_table('hr_salary_slips')
    op.drop_table('hr_payroll_runs')
    op.drop_table('hr_employment_contracts')
    op.drop_table('hr_payroll_structures')
    op.drop_table('hr_salary_components')
    op.drop_table('hr_employees')
    op.drop_table('hr_designations')
    op.drop_table('hr_departments')
