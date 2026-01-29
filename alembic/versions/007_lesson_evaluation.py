"""create lesson evaluation and adaptive tables

Revision ID: 007_lesson_evaluation
Revises: 006_weekly_tests
Create Date: 2026-01-29

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '007_lesson_evaluation'
down_revision = '006_weekly_tests'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create LessonEvaluationStatus enum
    op.execute("""
        CREATE TYPE lessonevaluationstatus AS ENUM (
            'created', 'conducted', 'evaluated'
        )
    """)
    
    # Create RecommendationType enum
    op.execute("""
        CREATE TYPE recommendationtype AS ENUM (
            'revision', 'extra_daily_loop', 'remedial_class'
        )
    """)
    
    # Create RecommendationPriority enum
    op.execute("""
        CREATE TYPE recommendationpriority AS ENUM (
            'low', 'medium', 'high'
        )
    """)
    
    # Create lesson_evaluations table
    op.create_table(
        'lesson_evaluations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('lesson_plan_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('lesson_plans.id', ondelete='CASCADE'), nullable=False),
        sa.Column('class_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('classes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('section_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sections.id', ondelete='SET NULL'), nullable=True),
        sa.Column('subject_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('subjects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('chapter_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('syllabus_units.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('test_date', sa.Date(), nullable=True),
        sa.Column('status', postgresql.ENUM('created', 'conducted', 'evaluated', name='lessonevaluationstatus', create_type=False), nullable=False, default='created'),
        sa.Column('total_questions', sa.Integer(), default=25, nullable=False),
        sa.Column('total_marks', sa.Float(), default=25.0, nullable=False),
        sa.Column('duration_minutes', sa.Integer(), default=45, nullable=False),
        sa.Column('students_appeared', sa.Integer(), default=0, nullable=False),
        sa.Column('avg_score_percent', sa.Float(), nullable=True),
        sa.Column('conducted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('evaluated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    
    # Create indexes for lesson_evaluations
    op.create_index(
        'ix_lesson_eval_tenant_class',
        'lesson_evaluations',
        ['tenant_id', 'class_id']
    )
    op.create_index(
        'ix_lesson_eval_lesson_plan',
        'lesson_evaluations',
        ['lesson_plan_id']
    )
    op.create_index(
        'ix_lesson_eval_status',
        'lesson_evaluations',
        ['tenant_id', 'status']
    )
    
    # Create lesson_evaluation_questions table
    op.create_table(
        'lesson_evaluation_questions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('lesson_evaluation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('lesson_evaluations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('question_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('questions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('question_number', sa.Integer(), nullable=False),
        sa.Column('marks', sa.Float(), default=1.0, nullable=False),
        sa.Column('topic_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('syllabus_topics.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    
    op.create_index(
        'ix_lesson_eval_question',
        'lesson_evaluation_questions',
        ['lesson_evaluation_id', 'question_number']
    )
    
    # Create lesson_evaluation_results table
    op.create_table(
        'lesson_evaluation_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('lesson_evaluation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('lesson_evaluations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('total_marks', sa.Float(), nullable=False),
        sa.Column('marks_obtained', sa.Float(), nullable=False),
        sa.Column('wrong_questions', postgresql.JSON(), default=[], nullable=False),
        sa.Column('percentage', sa.Float(), default=0.0, nullable=False),
        sa.Column('submitted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    
    op.create_index(
        'ix_lesson_eval_result_test',
        'lesson_evaluation_results',
        ['lesson_evaluation_id']
    )
    op.create_index(
        'ix_lesson_eval_result_student',
        'lesson_evaluation_results',
        ['student_id']
    )
    
    # Create lesson_mastery_snapshots table
    op.create_table(
        'lesson_mastery_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('chapter_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('syllabus_units.id', ondelete='CASCADE'), nullable=False),
        sa.Column('lesson_evaluation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('lesson_evaluations.id', ondelete='SET NULL'), nullable=True),
        sa.Column('mastery_percent', sa.Float(), nullable=False),
        sa.Column('daily_mastery', sa.Float(), default=0.0, nullable=False),
        sa.Column('weekly_mastery', sa.Float(), default=0.0, nullable=False),
        sa.Column('lesson_mastery', sa.Float(), default=0.0, nullable=False),
        sa.Column('evaluated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    
    op.create_index(
        'ix_lesson_mastery_student',
        'lesson_mastery_snapshots',
        ['tenant_id', 'student_id']
    )
    op.create_index(
        'ix_lesson_mastery_chapter',
        'lesson_mastery_snapshots',
        ['tenant_id', 'chapter_id']
    )
    
    # Create adaptive_recommendations table
    op.create_table(
        'adaptive_recommendations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('topic_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('syllabus_topics.id', ondelete='CASCADE'), nullable=False),
        sa.Column('lesson_evaluation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('lesson_evaluations.id', ondelete='SET NULL'), nullable=True),
        sa.Column('recommendation_type', postgresql.ENUM('revision', 'extra_daily_loop', 'remedial_class', name='recommendationtype', create_type=False), nullable=False),
        sa.Column('priority', postgresql.ENUM('low', 'medium', 'high', name='recommendationpriority', create_type=False), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('current_mastery', sa.Float(), nullable=False),
        sa.Column('is_actioned', sa.Boolean(), default=False, nullable=False),
        sa.Column('actioned_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('actioned_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    
    op.create_index(
        'ix_adaptive_rec_student',
        'adaptive_recommendations',
        ['tenant_id', 'student_id']
    )
    op.create_index(
        'ix_adaptive_rec_topic',
        'adaptive_recommendations',
        ['tenant_id', 'topic_id']
    )
    op.create_index(
        'ix_adaptive_rec_priority',
        'adaptive_recommendations',
        ['tenant_id', 'priority']
    )


def downgrade() -> None:
    # Drop adaptive_recommendations
    op.drop_index('ix_adaptive_rec_priority', table_name='adaptive_recommendations')
    op.drop_index('ix_adaptive_rec_topic', table_name='adaptive_recommendations')
    op.drop_index('ix_adaptive_rec_student', table_name='adaptive_recommendations')
    op.drop_table('adaptive_recommendations')
    
    # Drop lesson_mastery_snapshots
    op.drop_index('ix_lesson_mastery_chapter', table_name='lesson_mastery_snapshots')
    op.drop_index('ix_lesson_mastery_student', table_name='lesson_mastery_snapshots')
    op.drop_table('lesson_mastery_snapshots')
    
    # Drop lesson_evaluation_results
    op.drop_index('ix_lesson_eval_result_student', table_name='lesson_evaluation_results')
    op.drop_index('ix_lesson_eval_result_test', table_name='lesson_evaluation_results')
    op.drop_table('lesson_evaluation_results')
    
    # Drop lesson_evaluation_questions
    op.drop_index('ix_lesson_eval_question', table_name='lesson_evaluation_questions')
    op.drop_table('lesson_evaluation_questions')
    
    # Drop lesson_evaluations
    op.drop_index('ix_lesson_eval_status', table_name='lesson_evaluations')
    op.drop_index('ix_lesson_eval_lesson_plan', table_name='lesson_evaluations')
    op.drop_index('ix_lesson_eval_tenant_class', table_name='lesson_evaluations')
    op.drop_table('lesson_evaluations')
    
    # Drop enums
    op.execute("DROP TYPE recommendationpriority")
    op.execute("DROP TYPE recommendationtype")
    op.execute("DROP TYPE lessonevaluationstatus")
