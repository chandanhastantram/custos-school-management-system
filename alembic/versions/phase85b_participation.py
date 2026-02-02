"""Phase 8.5b: Academic Fairness - Participation Status

Revision ID: phase85b_participation
Revises: phase85_student_lifecycle
Create Date: 2026-02-02

Adds participation_status to attendance, test results, and analytics.
Ensures fair mastery calculation (excused absences excluded from denominator).
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'phase85b_participation'
down_revision = 'phase85_student_lifecycle'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # =============================================
    # Student Attendance - Participation tracking
    # =============================================
    op.add_column('student_attendance', 
        sa.Column('participation_status', sa.String(20), nullable=False, server_default='participated'))
    op.add_column('student_attendance', 
        sa.Column('absence_reason', sa.String(50), nullable=True))
    op.add_column('student_attendance', 
        sa.Column('absence_reason_detail', sa.String(500), nullable=True))
    op.add_column('student_attendance', 
        sa.Column('reference_document_id', sa.String(100), nullable=True))
    
    # =============================================
    # Attendance Summary - Excused/Unexcused breakdown
    # =============================================
    op.add_column('attendance_summaries', 
        sa.Column('unexcused_days', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('attendance_summaries', 
        sa.Column('participation_rate', sa.Float(), nullable=False, server_default='0'))
    
    # =============================================
    # Weekly Test Results - Participation status
    # =============================================
    op.add_column('weekly_test_results', 
        sa.Column('participation_status', sa.String(20), nullable=False, server_default='participated'))
    op.add_column('weekly_test_results', 
        sa.Column('absence_reason', sa.String(50), nullable=True))
    
    # Make marks_obtained nullable for excused absences
    op.alter_column('weekly_test_results', 'marks_obtained',
        existing_type=sa.Float(),
        nullable=True)
    op.alter_column('weekly_test_results', 'percentage',
        existing_type=sa.Float(),
        nullable=True)
    
    # =============================================
    # Lesson Evaluation Results - Participation status
    # =============================================
    op.add_column('lesson_evaluation_results', 
        sa.Column('participation_status', sa.String(20), nullable=False, server_default='participated'))
    op.add_column('lesson_evaluation_results', 
        sa.Column('absence_reason', sa.String(50), nullable=True))
    
    # Make marks_obtained nullable for excused absences
    op.alter_column('lesson_evaluation_results', 'marks_obtained',
        existing_type=sa.Float(),
        nullable=True)
    op.alter_column('lesson_evaluation_results', 'percentage',
        existing_type=sa.Float(),
        nullable=True)
    
    # =============================================
    # Student Topic Mastery - Participation tracking
    # =============================================
    op.add_column('student_topic_mastery', 
        sa.Column('total_sessions', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('student_topic_mastery', 
        sa.Column('participated_sessions', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('student_topic_mastery', 
        sa.Column('excused_absence_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('student_topic_mastery', 
        sa.Column('unexcused_absence_count', sa.Integer(), nullable=False, server_default='0'))
    
    # =============================================
    # Student Analytics Snapshot - Fair scoring
    # =============================================
    op.add_column('analytics_student_snapshots', 
        sa.Column('excused_absence_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('analytics_student_snapshots', 
        sa.Column('unexcused_absence_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('analytics_student_snapshots', 
        sa.Column('participation_rate', sa.Numeric(5, 2), nullable=False, server_default='0'))


def downgrade() -> None:
    # Analytics
    op.drop_column('analytics_student_snapshots', 'participation_rate')
    op.drop_column('analytics_student_snapshots', 'unexcused_absence_count')
    op.drop_column('analytics_student_snapshots', 'excused_absence_count')
    
    # Mastery
    op.drop_column('student_topic_mastery', 'unexcused_absence_count')
    op.drop_column('student_topic_mastery', 'excused_absence_count')
    op.drop_column('student_topic_mastery', 'participated_sessions')
    op.drop_column('student_topic_mastery', 'total_sessions')
    
    # Lesson evaluation results
    op.alter_column('lesson_evaluation_results', 'percentage',
        existing_type=sa.Float(),
        nullable=False)
    op.alter_column('lesson_evaluation_results', 'marks_obtained',
        existing_type=sa.Float(),
        nullable=False)
    op.drop_column('lesson_evaluation_results', 'absence_reason')
    op.drop_column('lesson_evaluation_results', 'participation_status')
    
    # Weekly test results
    op.alter_column('weekly_test_results', 'percentage',
        existing_type=sa.Float(),
        nullable=False)
    op.alter_column('weekly_test_results', 'marks_obtained',
        existing_type=sa.Float(),
        nullable=False)
    op.drop_column('weekly_test_results', 'absence_reason')
    op.drop_column('weekly_test_results', 'participation_status')
    
    # Attendance summary
    op.drop_column('attendance_summaries', 'participation_rate')
    op.drop_column('attendance_summaries', 'unexcused_days')
    
    # Student attendance
    op.drop_column('student_attendance', 'reference_document_id')
    op.drop_column('student_attendance', 'absence_reason_detail')
    op.drop_column('student_attendance', 'absence_reason')
    op.drop_column('student_attendance', 'participation_status')
