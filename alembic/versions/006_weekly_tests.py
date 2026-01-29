"""create weekly evaluation tables

Revision ID: 006_weekly_tests
Revises: 005_daily_loops
Create Date: 2026-01-29

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '006_weekly_tests'
down_revision = '005_daily_loops'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create WeeklyTestStatus enum
    op.execute("""
        CREATE TYPE weeklyteststatus AS ENUM (
            'created', 'conducted', 'evaluated'
        )
    """)
    
    # Create QuestionStrengthType enum
    op.execute("""
        CREATE TYPE questionstrengthtype AS ENUM (
            'strong', 'weak', 'moderate'
        )
    """)
    
    # Create weekly_tests table
    op.create_table(
        'weekly_tests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('class_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('classes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('section_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sections.id', ondelete='SET NULL'), nullable=True),
        sa.Column('subject_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('subjects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('topic_ids', postgresql.JSON(), nullable=False, default=[]),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('test_date', sa.Date(), nullable=True),
        sa.Column('status', postgresql.ENUM('created', 'conducted', 'evaluated', name='weeklyteststatus', create_type=False), nullable=False, default='created'),
        sa.Column('total_questions', sa.Integer(), default=20, nullable=False),
        sa.Column('total_marks', sa.Float(), default=20.0, nullable=False),
        sa.Column('duration_minutes', sa.Integer(), default=30, nullable=False),
        sa.Column('strong_percent', sa.Integer(), default=40, nullable=False),
        sa.Column('weak_percent', sa.Integer(), default=60, nullable=False),
        sa.Column('students_appeared', sa.Integer(), default=0, nullable=False),
        sa.Column('avg_score_percent', sa.Float(), nullable=True),
        sa.Column('conducted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('evaluated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    
    # Create indexes for weekly_tests
    op.create_index(
        'ix_weekly_test_tenant_class',
        'weekly_tests',
        ['tenant_id', 'class_id']
    )
    op.create_index(
        'ix_weekly_test_status',
        'weekly_tests',
        ['tenant_id', 'status']
    )
    op.create_index(
        'ix_weekly_test_date',
        'weekly_tests',
        ['tenant_id', 'start_date', 'end_date']
    )
    
    # Create weekly_test_questions table
    op.create_table(
        'weekly_test_questions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('weekly_test_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('weekly_tests.id', ondelete='CASCADE'), nullable=False),
        sa.Column('question_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('questions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('question_number', sa.Integer(), nullable=False),
        sa.Column('strength_type', postgresql.ENUM('strong', 'weak', 'moderate', name='questionstrengthtype', create_type=False), nullable=False),
        sa.Column('marks', sa.Float(), default=1.0, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    
    # Create index for weekly_test_questions
    op.create_index(
        'ix_weekly_question_test',
        'weekly_test_questions',
        ['weekly_test_id', 'question_number']
    )
    
    # Create weekly_test_results table
    op.create_table(
        'weekly_test_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('weekly_test_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('weekly_tests.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('total_marks', sa.Float(), nullable=False),
        sa.Column('marks_obtained', sa.Float(), nullable=False),
        sa.Column('attempted_questions', postgresql.JSON(), default=[], nullable=False),
        sa.Column('wrong_questions', postgresql.JSON(), default=[], nullable=False),
        sa.Column('percentage', sa.Float(), default=0.0, nullable=False),
        sa.Column('submitted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    
    # Create indexes for weekly_test_results
    op.create_index(
        'ix_weekly_result_test',
        'weekly_test_results',
        ['weekly_test_id']
    )
    op.create_index(
        'ix_weekly_result_student',
        'weekly_test_results',
        ['student_id']
    )
    
    # Create weekly_student_performance table
    op.create_table(
        'weekly_student_performance',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('weekly_test_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('weekly_tests.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('strong_total', sa.Integer(), default=0, nullable=False),
        sa.Column('strong_correct', sa.Integer(), default=0, nullable=False),
        sa.Column('strong_accuracy', sa.Float(), default=0.0, nullable=False),
        sa.Column('weak_total', sa.Integer(), default=0, nullable=False),
        sa.Column('weak_correct', sa.Integer(), default=0, nullable=False),
        sa.Column('weak_accuracy', sa.Float(), default=0.0, nullable=False),
        sa.Column('mastery_delta', sa.Float(), default=0.0, nullable=False),
        sa.Column('overall_accuracy', sa.Float(), default=0.0, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    
    # Create indexes for weekly_student_performance
    op.create_index(
        'ix_weekly_perf_student',
        'weekly_student_performance',
        ['tenant_id', 'student_id']
    )
    op.create_index(
        'ix_weekly_perf_test',
        'weekly_student_performance',
        ['weekly_test_id']
    )


def downgrade() -> None:
    # Drop weekly_student_performance
    op.drop_index('ix_weekly_perf_test', table_name='weekly_student_performance')
    op.drop_index('ix_weekly_perf_student', table_name='weekly_student_performance')
    op.drop_table('weekly_student_performance')
    
    # Drop weekly_test_results
    op.drop_index('ix_weekly_result_student', table_name='weekly_test_results')
    op.drop_index('ix_weekly_result_test', table_name='weekly_test_results')
    op.drop_table('weekly_test_results')
    
    # Drop weekly_test_questions
    op.drop_index('ix_weekly_question_test', table_name='weekly_test_questions')
    op.drop_table('weekly_test_questions')
    
    # Drop weekly_tests
    op.drop_index('ix_weekly_test_date', table_name='weekly_tests')
    op.drop_index('ix_weekly_test_status', table_name='weekly_tests')
    op.drop_index('ix_weekly_test_tenant_class', table_name='weekly_tests')
    op.drop_table('weekly_tests')
    
    # Drop enums
    op.execute("DROP TYPE questionstrengthtype")
    op.execute("DROP TYPE weeklyteststatus")
