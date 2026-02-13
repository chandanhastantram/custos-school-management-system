"""
Database Index Optimization Script

Creates indexes for frequently queried columns.
"""

from alembic import op
import sqlalchemy as sa


def create_performance_indexes():
    """Create indexes for performance optimization."""
    
    # User indexes
    op.create_index(
        'idx_users_email',
        'users',
        ['email'],
        unique=True,
        if_not_exists=True
    )
    op.create_index(
        'idx_users_tenant_id',
        'users',
        ['tenant_id'],
        if_not_exists=True
    )
    op.create_index(
        'idx_users_tenant_email',
        'users',
        ['tenant_id', 'email'],
        if_not_exists=True
    )
    
    # Student indexes
    op.create_index(
        'idx_students_user_id',
        'students',
        ['user_id'],
        if_not_exists=True
    )
    op.create_index(
        'idx_students_tenant_id',
        'students',
        ['tenant_id'],
        if_not_exists=True
    )
    
    # Attendance indexes
    op.create_index(
        'idx_attendance_student_date',
        'attendance',
        ['student_id', 'date'],
        if_not_exists=True
    )
    op.create_index(
        'idx_attendance_class_date',
        'attendance',
        ['class_id', 'date'],
        if_not_exists=True
    )
    
    # Fee indexes
    op.create_index(
        'idx_fees_student_id',
        'fees',
        ['student_id'],
        if_not_exists=True
    )
    op.create_index(
        'idx_fees_status',
        'fees',
        ['status'],
        if_not_exists=True
    )
    op.create_index(
        'idx_fees_due_date',
        'fees',
        ['due_date'],
        if_not_exists=True
    )
    
    # Hostel indexes
    op.create_index(
        'idx_hostel_assignments_student',
        'hostel_assignments',
        ['student_id', 'is_active'],
        if_not_exists=True
    )
    op.create_index(
        'idx_hostel_beds_room',
        'hostel_beds',
        ['room_id', 'is_occupied'],
        if_not_exists=True
    )
    
    # Transport indexes
    op.create_index(
        'idx_transport_assignments_student',
        'transport_assignments',
        ['student_id', 'is_active'],
        if_not_exists=True
    )
    op.create_index(
        'idx_transport_assignments_route',
        'transport_assignments',
        ['route_id'],
        if_not_exists=True
    )
    
    # Exam indexes
    op.create_index(
        'idx_exam_registrations_student',
        'exam_registrations',
        ['student_id', 'exam_id'],
        if_not_exists=True
    )
    op.create_index(
        'idx_exam_results_student',
        'exam_results',
        ['student_id', 'exam_id'],
        if_not_exists=True
    )
    
    # Lesson plan indexes
    op.create_index(
        'idx_lesson_plans_teacher',
        'lesson_plans',
        ['teacher_id', 'subject_id'],
        if_not_exists=True
    )
    op.create_index(
        'idx_lesson_plans_date',
        'lesson_plans',
        ['scheduled_date'],
        if_not_exists=True
    )
    
    # Assignment indexes
    op.create_index(
        'idx_assignments_class_subject',
        'assignments',
        ['class_id', 'subject_id'],
        if_not_exists=True
    )
    op.create_index(
        'idx_assignment_submissions_student',
        'assignment_submissions',
        ['student_id', 'assignment_id'],
        if_not_exists=True
    )
    
    # Notification indexes
    op.create_index(
        'idx_notifications_user_read',
        'notifications',
        ['user_id', 'is_read'],
        if_not_exists=True
    )
    op.create_index(
        'idx_notifications_created',
        'notifications',
        ['created_at'],
        if_not_exists=True
    )
    
    # Audit log indexes
    op.create_index(
        'idx_audit_logs_tenant_action',
        'audit_logs',
        ['tenant_id', 'action'],
        if_not_exists=True
    )
    op.create_index(
        'idx_audit_logs_user',
        'audit_logs',
        ['user_id'],
        if_not_exists=True
    )
    op.create_index(
        'idx_audit_logs_timestamp',
        'audit_logs',
        ['timestamp'],
        if_not_exists=True
    )


def drop_performance_indexes():
    """Drop performance indexes."""
    indexes = [
        'idx_users_email',
        'idx_users_tenant_id',
        'idx_users_tenant_email',
        'idx_students_user_id',
        'idx_students_tenant_id',
        'idx_attendance_student_date',
        'idx_attendance_class_date',
        'idx_fees_student_id',
        'idx_fees_status',
        'idx_fees_due_date',
        'idx_hostel_assignments_student',
        'idx_hostel_beds_room',
        'idx_transport_assignments_student',
        'idx_transport_assignments_route',
        'idx_exam_registrations_student',
        'idx_exam_results_student',
        'idx_lesson_plans_teacher',
        'idx_lesson_plans_date',
        'idx_assignments_class_subject',
        'idx_assignment_submissions_student',
        'idx_notifications_user_read',
        'idx_notifications_created',
        'idx_audit_logs_tenant_action',
        'idx_audit_logs_user',
        'idx_audit_logs_timestamp',
    ]
    
    for index_name in indexes:
        op.drop_index(index_name, if_exists=True)
