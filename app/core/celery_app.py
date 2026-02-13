"""
Celery Configuration for Background Tasks

Handles async tasks like email sending, report generation, etc.
"""

from celery import Celery
from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "custos",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
)

# Task routes
celery_app.conf.task_routes = {
    "app.tasks.email.*": {"queue": "email"},
    "app.tasks.reports.*": {"queue": "reports"},
    "app.tasks.notifications.*": {"queue": "notifications"},
    "app.tasks.ai.*": {"queue": "ai"},
}

# Periodic tasks
celery_app.conf.beat_schedule = {
    "send-pending-notifications": {
        "task": "app.tasks.notifications.send_pending_notifications",
        "schedule": 60.0,  # Every minute
    },
    "generate-daily-reports": {
        "task": "app.tasks.reports.generate_daily_reports",
        "schedule": 86400.0,  # Daily
    },
    "cleanup-old-sessions": {
        "task": "app.tasks.cleanup.cleanup_old_sessions",
        "schedule": 3600.0,  # Hourly
    },
}


# Example tasks
@celery_app.task(name="app.tasks.email.send_email")
def send_email_task(to: str, subject: str, body: str):
    """Send email asynchronously."""
    from app.platform.notifications.email import send_email
    return send_email(to, subject, body)


@celery_app.task(name="app.tasks.reports.generate_report")
def generate_report_task(report_type: str, tenant_id: str, **kwargs):
    """Generate report asynchronously."""
    from app.platform.reports.service import ReportService
    service = ReportService()
    return service.generate_report(report_type, tenant_id, **kwargs)


@celery_app.task(name="app.tasks.notifications.send_pending_notifications")
def send_pending_notifications():
    """Send pending notifications."""
    from app.platform.notifications.service import NotificationService
    service = NotificationService()
    return service.send_pending()


@celery_app.task(name="app.tasks.ai.generate_lesson_plan")
def generate_lesson_plan_task(subject: str, topic: str, grade: int, **kwargs):
    """Generate lesson plan using AI."""
    from app.ai.lesson_plan_generator import LessonPlanGenerator
    generator = LessonPlanGenerator()
    return generator.generate(subject, topic, grade, **kwargs)


@celery_app.task(name="app.tasks.cleanup.cleanup_old_sessions")
def cleanup_old_sessions():
    """Cleanup old sessions."""
    # Implement session cleanup logic
    pass
