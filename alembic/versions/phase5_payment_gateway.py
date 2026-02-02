"""Add payment gateway and phase 5 models

Revision ID: phase5_payment_gateway
Revises: (latest)
Create Date: 2026-02-01

This migration adds:
- Payment gateway tables (orders, transactions, refunds, webhooks)
- Attendance tables (student, teacher, summaries, leave requests)
- Announcements/Posts tables
- Calendar events table
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'phase5_payment_gateway'
down_revision = None  # Set to the actual previous revision
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ============================================
    # Payment Gateway Tables
    # ============================================
    
    # Gateway Configurations
    op.create_table(
        'payment_gateway_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('gateway', sa.String(50), nullable=False),
        sa.Column('display_name', sa.String(100), nullable=False),
        sa.Column('api_key', sa.Text, nullable=True),
        sa.Column('api_secret', sa.Text, nullable=True),
        sa.Column('webhook_secret', sa.Text, nullable=True),
        sa.Column('merchant_id', sa.String(100), nullable=True),
        sa.Column('is_live_mode', sa.Boolean, default=False),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('is_default', sa.Boolean, default=False),
        sa.Column('supported_methods', postgresql.JSON, nullable=True),
        sa.Column('settings', postgresql.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_gateway_configs_tenant', 'payment_gateway_configs', ['tenant_id', 'is_active'])
    
    # Payment Orders
    op.create_table(
        'payment_orders',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('order_number', sa.String(50), unique=True, nullable=False),
        sa.Column('invoice_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('fee_invoices.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('amount', sa.Integer, nullable=False),
        sa.Column('currency', sa.String(3), default='INR'),
        sa.Column('gateway', sa.String(50), nullable=False),
        sa.Column('gateway_order_id', sa.String(100), nullable=True),
        sa.Column('status', sa.String(50), default='pending'),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('notes', postgresql.JSON, nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_payment_orders_tenant', 'payment_orders', ['tenant_id', 'status'])
    op.create_index('ix_payment_orders_invoice', 'payment_orders', ['invoice_id'])
    
    # Payment Transactions
    op.create_table(
        'payment_transactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('payment_orders.id', ondelete='CASCADE'), nullable=False),
        sa.Column('transaction_id', sa.String(100), unique=True, nullable=False),
        sa.Column('gateway_transaction_id', sa.String(100), nullable=True),
        sa.Column('gateway_payment_id', sa.String(100), nullable=True),
        sa.Column('amount', sa.Integer, nullable=False),
        sa.Column('currency', sa.String(3), default='INR'),
        sa.Column('status', sa.String(50), default='pending'),
        sa.Column('method', sa.String(50), nullable=True),
        sa.Column('method_details', postgresql.JSON, nullable=True),
        sa.Column('gateway_response', postgresql.JSON, nullable=True),
        sa.Column('error_code', sa.String(50), nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_payment_transactions_order', 'payment_transactions', ['order_id'])
    op.create_index('ix_payment_transactions_status', 'payment_transactions', ['tenant_id', 'status'])
    
    # Payment Refunds
    op.create_table(
        'payment_refunds',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('transaction_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('payment_transactions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('refund_id', sa.String(100), unique=True, nullable=False),
        sa.Column('gateway_refund_id', sa.String(100), nullable=True),
        sa.Column('amount', sa.Integer, nullable=False),
        sa.Column('status', sa.String(50), default='pending'),
        sa.Column('reason', sa.Text, nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('gateway_response', postgresql.JSON, nullable=True),
        sa.Column('initiated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_payment_refunds_transaction', 'payment_refunds', ['transaction_id'])
    
    # Webhook Events
    op.create_table(
        'webhook_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=True),
        sa.Column('gateway', sa.String(50), nullable=False),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('payload', postgresql.JSON, nullable=True),
        sa.Column('signature', sa.Text, nullable=True),
        sa.Column('is_verified', sa.Boolean, default=False),
        sa.Column('is_processed', sa.Boolean, default=False),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('related_order_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('related_transaction_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_webhook_events_gateway', 'webhook_events', ['gateway', 'event_type'])
    
    # ============================================
    # Attendance Tables
    # ============================================
    
    # Student Attendance
    op.create_table(
        'student_attendance',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('class_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('classes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('section_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sections.id', ondelete='SET NULL'), nullable=True),
        sa.Column('attendance_date', sa.Date, nullable=False),
        sa.Column('status', sa.String(50), default='not_marked'),
        sa.Column('check_in_time', sa.Time, nullable=True),
        sa.Column('check_out_time', sa.Time, nullable=True),
        sa.Column('late_minutes', sa.Integer, default=0),
        sa.Column('remarks', sa.String(500), nullable=True),
        sa.Column('marked_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('marked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('academic_year_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('academic_years.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_unique_constraint('uq_student_attendance_date', 'student_attendance', ['tenant_id', 'student_id', 'attendance_date'])
    op.create_index('ix_student_attendance_date', 'student_attendance', ['tenant_id', 'attendance_date'])
    op.create_index('ix_student_attendance_student', 'student_attendance', ['tenant_id', 'student_id'])
    op.create_index('ix_student_attendance_class', 'student_attendance', ['tenant_id', 'class_id', 'attendance_date'])
    
    # Attendance Summary
    op.create_table(
        'attendance_summaries',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('year', sa.Integer, nullable=False),
        sa.Column('month', sa.Integer, nullable=False),
        sa.Column('total_days', sa.Integer, default=0),
        sa.Column('present_days', sa.Integer, default=0),
        sa.Column('absent_days', sa.Integer, default=0),
        sa.Column('late_days', sa.Integer, default=0),
        sa.Column('half_days', sa.Integer, default=0),
        sa.Column('excused_days', sa.Integer, default=0),
        sa.Column('attendance_percentage', sa.Float, default=0.0),
        sa.Column('calculated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_unique_constraint('uq_attendance_summary_month', 'attendance_summaries', ['tenant_id', 'student_id', 'year', 'month'])
    op.create_index('ix_attendance_summary_student', 'attendance_summaries', ['tenant_id', 'student_id'])
    
    # Leave Requests
    op.create_table(
        'leave_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('requested_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('leave_type', sa.String(50), default='casual'),
        sa.Column('start_date', sa.Date, nullable=False),
        sa.Column('end_date', sa.Date, nullable=False),
        sa.Column('reason', sa.Text, nullable=False),
        sa.Column('attachments', postgresql.JSON, nullable=True),
        sa.Column('status', sa.String(50), default='pending'),
        sa.Column('reviewed_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('review_notes', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_leave_request_student', 'leave_requests', ['tenant_id', 'student_id'])
    op.create_index('ix_leave_request_status', 'leave_requests', ['tenant_id', 'status'])
    
    # Teacher Attendance
    op.create_table(
        'teacher_attendance',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('teacher_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('attendance_date', sa.Date, nullable=False),
        sa.Column('status', sa.String(50), default='not_marked'),
        sa.Column('check_in_time', sa.Time, nullable=True),
        sa.Column('check_out_time', sa.Time, nullable=True),
        sa.Column('remarks', sa.String(500), nullable=True),
        sa.Column('marked_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_unique_constraint('uq_teacher_attendance_date', 'teacher_attendance', ['tenant_id', 'teacher_id', 'attendance_date'])
    op.create_index('ix_teacher_attendance_date', 'teacher_attendance', ['tenant_id', 'attendance_date'])
    
    # ============================================
    # Announcements Tables
    # ============================================
    
    # Posts
    op.create_table(
        'posts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('summary', sa.String(500), nullable=True),
        sa.Column('post_type', sa.String(50), default='announcement'),
        sa.Column('priority', sa.String(50), default='normal'),
        sa.Column('audience', sa.String(50), default='all'),
        sa.Column('target_class_ids', postgresql.JSON, nullable=True),
        sa.Column('target_section_ids', postgresql.JSON, nullable=True),
        sa.Column('attachments', postgresql.JSON, nullable=True),
        sa.Column('is_published', sa.Boolean, default=False),
        sa.Column('is_pinned', sa.Boolean, default=False),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('author_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('views_count', sa.Integer, default=0),
        sa.Column('is_deleted', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_posts_tenant', 'posts', ['tenant_id', 'is_published'])
    op.create_index('ix_posts_type', 'posts', ['tenant_id', 'post_type'])
    
    # Post Reads
    op.create_table(
        'post_reads',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('post_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('posts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_post_reads_post', 'post_reads', ['post_id', 'user_id'])
    
    # ============================================
    # Calendar Tables
    # ============================================
    
    # Calendar Events
    op.create_table(
        'calendar_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('event_type', sa.String(50), default='other'),
        sa.Column('scope', sa.String(50), default='school'),
        sa.Column('target_class_ids', postgresql.JSON, nullable=True),
        sa.Column('target_section_ids', postgresql.JSON, nullable=True),
        sa.Column('start_date', sa.Date, nullable=False),
        sa.Column('end_date', sa.Date, nullable=True),
        sa.Column('start_time', sa.Time, nullable=True),
        sa.Column('end_time', sa.Time, nullable=True),
        sa.Column('is_all_day', sa.Boolean, default=True),
        sa.Column('is_holiday', sa.Boolean, default=False),
        sa.Column('location', sa.String(300), nullable=True),
        sa.Column('color', sa.String(20), nullable=True),
        sa.Column('is_recurring', sa.Boolean, default=False),
        sa.Column('recurrence_pattern', postgresql.JSON, nullable=True),
        sa.Column('academic_year_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('academic_years.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_published', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_calendar_events_tenant', 'calendar_events', ['tenant_id', 'start_date'])
    op.create_index('ix_calendar_events_type', 'calendar_events', ['tenant_id', 'event_type'])


def downgrade() -> None:
    # Calendar
    op.drop_table('calendar_events')
    
    # Announcements
    op.drop_table('post_reads')
    op.drop_table('posts')
    
    # Attendance
    op.drop_table('teacher_attendance')
    op.drop_table('leave_requests')
    op.drop_table('attendance_summaries')
    op.drop_table('student_attendance')
    
    # Payment Gateway
    op.drop_table('webhook_events')
    op.drop_table('payment_refunds')
    op.drop_table('payment_transactions')
    op.drop_table('payment_orders')
    op.drop_table('payment_gateway_configs')
