"""
CUSTOS Job Registry

Explicit allowlist of job classes.

SECURITY:
- Only registered jobs can be executed
- Prevents arbitrary job injection
- Centralized job management
"""

import logging
from typing import Dict, Type, Optional, Set

logger = logging.getLogger(__name__)


# ============================================
# JOB REGISTRY (EXPLICIT ALLOWLIST)
# ============================================

# Maps job class name -> job class
_JOB_REGISTRY: Dict[str, Type] = {}

# Set of allowed job class names
_ALLOWED_JOBS: Set[str] = set()


def register_job(job_class: Type) -> Type:
    """
    Decorator to register a job class.
    
    Usage:
    
    @register_job
    class MyJob(AbstractJob):
        ...
    """
    class_name = job_class.__name__
    
    if class_name in _JOB_REGISTRY:
        logger.warning(f"Job class already registered: {class_name}")
    else:
        _JOB_REGISTRY[class_name] = job_class
        _ALLOWED_JOBS.add(class_name)
        logger.debug(f"Registered job: {class_name}")
    
    return job_class


def register_job_class(job_class: Type) -> None:
    """
    Explicitly register a job class.
    
    Usage:
    
    from app.ai.jobs import AILessonPlanJob
    register_job_class(AILessonPlanJob)
    """
    register_job(job_class)


def unregister_job(job_class_name: str) -> None:
    """Remove a job from the registry."""
    if job_class_name in _JOB_REGISTRY:
        del _JOB_REGISTRY[job_class_name]
        _ALLOWED_JOBS.discard(job_class_name)
        logger.info(f"Unregistered job: {job_class_name}")


def get_job_class(class_name: str) -> Optional[Type]:
    """
    Get job class by name.
    
    Returns None if not registered.
    """
    if class_name not in _JOB_REGISTRY:
        logger.warning(f"Unknown job class requested: {class_name}")
        return None
    return _JOB_REGISTRY[class_name]


def is_job_allowed(job_class: Type) -> bool:
    """
    Check if a job class is allowed to execute.
    
    Returns True only if the job is explicitly registered.
    """
    class_name = job_class.__name__
    is_allowed = class_name in _ALLOWED_JOBS
    
    if not is_allowed:
        logger.warning(f"Unauthorized job class: {class_name}")
    
    return is_allowed


def list_registered_jobs() -> list:
    """List all registered job classes."""
    return list(_JOB_REGISTRY.keys())


def get_registry_stats() -> dict:
    """Get registry statistics."""
    return {
        "total_registered": len(_JOB_REGISTRY),
        "job_classes": list(_JOB_REGISTRY.keys()),
    }


# ============================================
# PRE-REGISTERED JOBS
# ============================================
# These will be populated by importing job modules

def _auto_register_jobs():
    """
    Auto-register known job classes.
    
    This is called during module initialization to register
    all standard CUSTOS job classes.
    """
    # Note: The actual job classes will import this module
    # and use @register_job decorator or call register_job_class()
    #
    # Example jobs that should be registered:
    # - AILessonPlanJob
    # - AIWorksheetJob
    # - AIInsightJob
    # - OCRProcessJob
    # - AnalyticsSnapshotJob
    # - PayrollProcessJob
    # - ExportInspectionJob
    pass


# ============================================
# JOB CATEGORIES
# ============================================

class JobCategory:
    """Categories for grouping jobs."""
    AI = "ai"
    OCR = "ocr"
    ANALYTICS = "analytics"
    PAYROLL = "payroll"
    EXPORT = "export"
    NOTIFICATION = "notification"


# Map job types to categories for filtering
JOB_CATEGORIES = {
    JobCategory.AI: [
        "AILessonPlanJob",
        "AIWorksheetJob",
        "AIDoubtSolverJob",
        "AIMCQGenerateJob",
        "AIInsightJob",
    ],
    JobCategory.OCR: [
        "OCRProcessJob",
        "OCRImportJob",
    ],
    JobCategory.ANALYTICS: [
        "AnalyticsSnapshotJob",
        "AnalyticsAggregateJob",
    ],
    JobCategory.PAYROLL: [
        "PayrollProcessJob",
        "PayrollGenerateJob",
    ],
    JobCategory.EXPORT: [
        "ExportInspectionJob",
        "ExportReportJob",
        "ExportAnalyticsJob",
    ],
    JobCategory.NOTIFICATION: [
        "NotificationSendJob",
        "NotificationBulkJob",
    ],
}


def get_jobs_by_category(category: str) -> list:
    """Get list of job class names by category."""
    return JOB_CATEGORIES.get(category, [])


def get_job_category(job_class_name: str) -> Optional[str]:
    """Get category for a job class."""
    for category, jobs in JOB_CATEGORIES.items():
        if job_class_name in jobs:
            return category
    return None
