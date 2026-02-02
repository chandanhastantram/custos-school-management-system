"""Add analytics snapshot tables

Revision ID: phase7_analytics
Revises: phase6_hr_payroll
Create Date: 2026-02-01

This migration adds:
- Student analytics snapshots table
- Teacher analytics snapshots table
- Class analytics snapshots table
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'phase7_analytics'
down_revision = 'phase6_hr_payroll'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ============================================
    # Student Analytics Snapshots Table
    # ============================================
    op.create_table(
        'analytics_student_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('class_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('classes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('subject_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('subjects.id', ondelete='SET NULL'), nullable=True),
        sa.Column('academic_year_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('academic_years.id', ondelete='SET NULL'), nullable=True),
        sa.Column('period_type', sa.String(20), default='weekly'),
        sa.Column('period_start', sa.Date, nullable=False),
        sa.Column('period_end', sa.Date, nullable=False),
        
        # Activity Score (visible to students)
        sa.Column('activity_score', sa.Numeric(5, 2), default=0),
        sa.Column('daily_loop_participation_pct', sa.Numeric(5, 2), default=0),
        sa.Column('weekly_test_participation_pct', sa.Numeric(5, 2), default=0),
        sa.Column('lesson_eval_participation_pct', sa.Numeric(5, 2), default=0),
        sa.Column('attendance_pct', sa.Numeric(5, 2), default=0),
        
        # Actual Score (hidden from students)
        sa.Column('actual_score', sa.Numeric(5, 2), default=0),
        sa.Column('daily_mastery_pct', sa.Numeric(5, 2), default=0),
        sa.Column('weekly_test_mastery_pct', sa.Numeric(5, 2), default=0),
        sa.Column('lesson_eval_mastery_pct', sa.Numeric(5, 2), default=0),
        sa.Column('overall_mastery_pct', sa.Numeric(5, 2), default=0),
        
        # Raw counts
        sa.Column('daily_loops_total', sa.Integer, default=0),
        sa.Column('daily_loops_completed', sa.Integer, default=0),
        sa.Column('weekly_tests_total', sa.Integer, default=0),
        sa.Column('weekly_tests_completed', sa.Integer, default=0),
        sa.Column('lesson_evals_total', sa.Integer, default=0),
        sa.Column('lesson_evals_completed', sa.Integer, default=0),
        sa.Column('school_days_total', sa.Integer, default=0),
        sa.Column('school_days_present', sa.Integer, default=0),
        
        # Concepts
        sa.Column('weak_concepts_json', postgresql.JSONB, nullable=True),
        sa.Column('strong_concepts_json', postgresql.JSONB, nullable=True),
        
        # Metadata
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('generated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_analytics_student_tenant', 'analytics_student_snapshots', ['tenant_id', 'student_id'])
    op.create_index('ix_analytics_student_class', 'analytics_student_snapshots', ['class_id'])
    op.create_index('ix_analytics_student_period', 'analytics_student_snapshots', ['period_start', 'period_end'])
    
    # ============================================
    # Teacher Analytics Snapshots Table
    # ============================================
    op.create_table(
        'analytics_teacher_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('teacher_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('subject_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('subjects.id', ondelete='SET NULL'), nullable=True),
        sa.Column('class_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('classes.id', ondelete='SET NULL'), nullable=True),
        sa.Column('academic_year_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('academic_years.id', ondelete='SET NULL'), nullable=True),
        sa.Column('period_type', sa.String(20), default='weekly'),
        sa.Column('period_start', sa.Date, nullable=False),
        sa.Column('period_end', sa.Date, nullable=False),
        
        # Teaching metrics
        sa.Column('syllabus_coverage_pct', sa.Numeric(5, 2), default=0),
        sa.Column('lessons_planned', sa.Integer, default=0),
        sa.Column('lessons_completed', sa.Integer, default=0),
        sa.Column('schedule_adherence_pct', sa.Numeric(5, 2), default=0),
        sa.Column('periods_scheduled', sa.Integer, default=0),
        sa.Column('periods_conducted', sa.Integer, default=0),
        
        # Student engagement
        sa.Column('student_participation_pct', sa.Numeric(5, 2), default=0),
        sa.Column('class_mastery_avg', sa.Numeric(5, 2), default=0),
        
        # Assessment activity
        sa.Column('daily_loops_created', sa.Integer, default=0),
        sa.Column('weekly_tests_created', sa.Integer, default=0),
        sa.Column('lesson_evals_created', sa.Integer, default=0),
        
        # Overall
        sa.Column('engagement_score', sa.Numeric(5, 2), default=0),
        
        # Metadata
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('generated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_analytics_teacher_tenant', 'analytics_teacher_snapshots', ['tenant_id', 'teacher_id'])
    op.create_index('ix_analytics_teacher_period', 'analytics_teacher_snapshots', ['period_start', 'period_end'])
    
    # ============================================
    # Class Analytics Snapshots Table
    # ============================================
    op.create_table(
        'analytics_class_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('class_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('classes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('subject_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('subjects.id', ondelete='SET NULL'), nullable=True),
        sa.Column('academic_year_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('academic_years.id', ondelete='SET NULL'), nullable=True),
        sa.Column('period_type', sa.String(20), default='weekly'),
        sa.Column('period_start', sa.Date, nullable=False),
        sa.Column('period_end', sa.Date, nullable=False),
        
        # Class size
        sa.Column('total_students', sa.Integer, default=0),
        
        # Aggregates
        sa.Column('avg_mastery_pct', sa.Numeric(5, 2), default=0),
        sa.Column('avg_activity_score', sa.Numeric(5, 2), default=0),
        sa.Column('avg_attendance_pct', sa.Numeric(5, 2), default=0),
        
        # Participation
        sa.Column('daily_loop_participation_avg', sa.Numeric(5, 2), default=0),
        sa.Column('weekly_test_participation_avg', sa.Numeric(5, 2), default=0),
        sa.Column('lesson_eval_participation_avg', sa.Numeric(5, 2), default=0),
        
        # Topics
        sa.Column('common_weak_topics_json', postgresql.JSONB, nullable=True),
        sa.Column('common_strong_topics_json', postgresql.JSONB, nullable=True),
        sa.Column('weak_topic_count', sa.Integer, default=0),
        sa.Column('strong_topic_count', sa.Integer, default=0),
        
        # Progress
        sa.Column('syllabus_coverage_pct', sa.Numeric(5, 2), default=0),
        
        # Metadata
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('generated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_analytics_class_tenant', 'analytics_class_snapshots', ['tenant_id', 'class_id'])
    op.create_index('ix_analytics_class_period', 'analytics_class_snapshots', ['period_start', 'period_end'])


def downgrade() -> None:
    op.drop_table('analytics_class_snapshots')
    op.drop_table('analytics_teacher_snapshots')
    op.drop_table('analytics_student_snapshots')
