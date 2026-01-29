"""fees and finance tables

Revision ID: 011_fees_finance
Revises: 010_ai_question_gen
Create Date: 2026-01-29

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '011_fees_finance'
down_revision = '010_ai_question_gen'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enums
    op.execute("""
        CREATE TYPE invoicestatus AS ENUM (
            'pending', 'partial', 'paid', 'overdue', 'cancelled'
        )
    """)
    
    op.execute("""
        CREATE TYPE paymentmethod AS ENUM (
            'cash', 'upi', 'card', 'bank_transfer', 'cheque', 'dd', 'online', 'other'
        )
    """)
    
    # Fee Components
    op.create_table(
        'fee_components',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('code', sa.String(20), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_mandatory', sa.Boolean(), default=True, nullable=False),
        sa.Column('is_refundable', sa.Boolean(), default=False, nullable=False),
        sa.Column('allow_partial', sa.Boolean(), default=True, nullable=False),
        sa.Column('category', sa.String(50), nullable=True),
        sa.Column('is_taxable', sa.Boolean(), default=False, nullable=False),
        sa.Column('tax_percentage', sa.Float(), default=0.0, nullable=False),
        sa.Column('display_order', sa.Integer(), default=0, nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint('tenant_id', 'code', name='uq_fee_component_code'),
    )
    op.create_index('ix_fee_comp_tenant', 'fee_components', ['tenant_id'])
    
    # Fee Structures
    op.create_table(
        'fee_structures',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('class_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('classes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('academic_year_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('academic_years.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('total_amount', sa.Numeric(12, 2), default=0.0, nullable=False),
        sa.Column('installment_count', sa.Integer(), default=1, nullable=False),
        sa.Column('installment_schedule', postgresql.JSON(), nullable=True),
        sa.Column('is_published', sa.Boolean(), default=False, nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint('tenant_id', 'class_id', 'academic_year_id', name='uq_fee_structure_class_year'),
    )
    op.create_index('ix_fee_struct_tenant', 'fee_structures', ['tenant_id'])
    op.create_index('ix_fee_struct_class', 'fee_structures', ['class_id'])
    
    # Fee Structure Items
    op.create_table(
        'fee_structure_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('fee_structure_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('fee_structures.id', ondelete='CASCADE'), nullable=False),
        sa.Column('fee_component_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('fee_components.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('discount_percentage', sa.Float(), default=0.0, nullable=False),
        sa.Column('discounted_amount', sa.Numeric(12, 2), default=0.0, nullable=False),
        sa.Column('display_order', sa.Integer(), default=0, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint('fee_structure_id', 'fee_component_id', name='uq_fee_item_structure_component'),
    )
    op.create_index('ix_fee_item_structure', 'fee_structure_items', ['fee_structure_id'])
    
    # Student Fee Accounts
    op.create_table(
        'student_fee_accounts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('academic_year_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('academic_years.id', ondelete='CASCADE'), nullable=False),
        sa.Column('fee_structure_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('fee_structures.id', ondelete='SET NULL'), nullable=True),
        sa.Column('total_due', sa.Numeric(12, 2), default=0.0, nullable=False),
        sa.Column('total_paid', sa.Numeric(12, 2), default=0.0, nullable=False),
        sa.Column('total_discount', sa.Numeric(12, 2), default=0.0, nullable=False),
        sa.Column('total_fine', sa.Numeric(12, 2), default=0.0, nullable=False),
        sa.Column('balance', sa.Numeric(12, 2), default=0.0, nullable=False),
        sa.Column('is_cleared', sa.Boolean(), default=False, nullable=False),
        sa.Column('has_overdue', sa.Boolean(), default=False, nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint('tenant_id', 'student_id', 'academic_year_id', name='uq_student_fee_account'),
    )
    op.create_index('ix_fee_account_student', 'student_fee_accounts', ['student_id'])
    op.create_index('ix_fee_account_year', 'student_fee_accounts', ['academic_year_id'])
    
    # Fee Invoices
    op.create_table(
        'fee_invoices',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('invoice_number', sa.String(50), nullable=False),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('student_fee_accounts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('structure_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('fee_structures.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('installment_no', sa.Integer(), default=1, nullable=False),
        sa.Column('total_installments', sa.Integer(), default=1, nullable=False),
        sa.Column('invoice_date', sa.Date(), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('subtotal', sa.Numeric(12, 2), default=0.0, nullable=False),
        sa.Column('discount_amount', sa.Numeric(12, 2), default=0.0, nullable=False),
        sa.Column('fine_amount', sa.Numeric(12, 2), default=0.0, nullable=False),
        sa.Column('tax_amount', sa.Numeric(12, 2), default=0.0, nullable=False),
        sa.Column('total_amount', sa.Numeric(12, 2), default=0.0, nullable=False),
        sa.Column('amount_paid', sa.Numeric(12, 2), default=0.0, nullable=False),
        sa.Column('balance_due', sa.Numeric(12, 2), default=0.0, nullable=False),
        sa.Column('status', postgresql.ENUM('pending', 'partial', 'paid', 'overdue', 'cancelled',
                  name='invoicestatus', create_type=False), nullable=False, default='pending'),
        sa.Column('line_items', postgresql.JSON(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint('tenant_id', 'invoice_number', name='uq_fee_invoice_number'),
    )
    op.create_index('ix_invoice_account', 'fee_invoices', ['account_id'])
    op.create_index('ix_invoice_student', 'fee_invoices', ['student_id'])
    op.create_index('ix_invoice_status', 'fee_invoices', ['tenant_id', 'status'])
    op.create_index('ix_invoice_due_date', 'fee_invoices', ['tenant_id', 'due_date'])
    
    # Fee Payments
    op.create_table(
        'fee_payments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('invoice_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('fee_invoices.id', ondelete='CASCADE'), nullable=False),
        sa.Column('amount_paid', sa.Numeric(12, 2), nullable=False),
        sa.Column('payment_date', sa.Date(), nullable=False),
        sa.Column('payment_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('method', postgresql.ENUM('cash', 'upi', 'card', 'bank_transfer', 'cheque', 'dd', 'online', 'other',
                  name='paymentmethod', create_type=False), nullable=False, default='cash'),
        sa.Column('reference_no', sa.String(100), nullable=True),
        sa.Column('transaction_id', sa.String(100), nullable=True),
        sa.Column('bank_name', sa.String(100), nullable=True),
        sa.Column('cheque_number', sa.String(50), nullable=True),
        sa.Column('cheque_date', sa.Date(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), default=True, nullable=False),
        sa.Column('is_reversed', sa.Boolean(), default=False, nullable=False),
        sa.Column('reversed_reason', sa.Text(), nullable=True),
        sa.Column('recorded_by', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_payment_invoice', 'fee_payments', ['invoice_id'])
    op.create_index('ix_payment_date', 'fee_payments', ['tenant_id', 'payment_date'])
    
    # Fee Receipts
    op.create_table(
        'fee_receipts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('payment_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('fee_payments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('receipt_number', sa.String(50), nullable=False),
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('generated_by', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('print_count', sa.Integer(), default=0, nullable=False),
        sa.Column('last_printed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint('tenant_id', 'receipt_number', name='uq_fee_receipt_number'),
    )
    op.create_index('ix_receipt_payment', 'fee_receipts', ['payment_id'])
    
    # Fee Discounts
    op.create_table(
        'fee_discounts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('academic_year_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('academic_years.id', ondelete='CASCADE'), nullable=False),
        sa.Column('discount_type', sa.String(50), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('is_percentage', sa.Boolean(), default=False, nullable=False),
        sa.Column('discount_value', sa.Numeric(12, 2), nullable=False),
        sa.Column('applies_to_components', postgresql.JSON(), nullable=True),
        sa.Column('is_approved', sa.Boolean(), default=False, nullable=False),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_discount_student', 'fee_discounts', ['student_id'])
    op.create_index('ix_discount_type', 'fee_discounts', ['tenant_id', 'discount_type'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index('ix_discount_type', table_name='fee_discounts')
    op.drop_index('ix_discount_student', table_name='fee_discounts')
    op.drop_table('fee_discounts')
    
    op.drop_index('ix_receipt_payment', table_name='fee_receipts')
    op.drop_table('fee_receipts')
    
    op.drop_index('ix_payment_date', table_name='fee_payments')
    op.drop_index('ix_payment_invoice', table_name='fee_payments')
    op.drop_table('fee_payments')
    
    op.drop_index('ix_invoice_due_date', table_name='fee_invoices')
    op.drop_index('ix_invoice_status', table_name='fee_invoices')
    op.drop_index('ix_invoice_student', table_name='fee_invoices')
    op.drop_index('ix_invoice_account', table_name='fee_invoices')
    op.drop_table('fee_invoices')
    
    op.drop_index('ix_fee_account_year', table_name='student_fee_accounts')
    op.drop_index('ix_fee_account_student', table_name='student_fee_accounts')
    op.drop_table('student_fee_accounts')
    
    op.drop_index('ix_fee_item_structure', table_name='fee_structure_items')
    op.drop_table('fee_structure_items')
    
    op.drop_index('ix_fee_struct_class', table_name='fee_structures')
    op.drop_index('ix_fee_struct_tenant', table_name='fee_structures')
    op.drop_table('fee_structures')
    
    op.drop_index('ix_fee_comp_tenant', table_name='fee_components')
    op.drop_table('fee_components')
    
    # Drop enums
    op.execute("DROP TYPE paymentmethod")
    op.execute("DROP TYPE invoicestatus")
