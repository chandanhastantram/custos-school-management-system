"""
CUSTOS Job Policies

Retry, timeout, and idempotency rules for background jobs.

RULES:
- Every job has defined timeout and retry limits
- Retry only on safe failures (network, timeout)
- Idempotency is MANDATORY for all jobs
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional


class JobType(str, Enum):
    """Allowed background job types."""
    # AI Jobs
    AI_LESSON_PLAN = "ai_lesson_plan"
    AI_WORKSHEET = "ai_worksheet"
    AI_DOUBT_SOLVER = "ai_doubt_solver"
    AI_MCQ_GENERATE = "ai_mcq_generate"
    AI_INSIGHT = "ai_insight"
    
    # OCR Jobs
    OCR_PROCESS = "ocr_process"
    OCR_IMPORT = "ocr_import"
    
    # Analytics Jobs
    ANALYTICS_SNAPSHOT = "analytics_snapshot"
    ANALYTICS_AGGREGATE = "analytics_aggregate"
    
    # Payroll Jobs
    PAYROLL_PROCESS = "payroll_process"
    PAYROLL_GENERATE = "payroll_generate"
    
    # Export Jobs
    EXPORT_INSPECTION = "export_inspection"
    EXPORT_REPORT = "export_report"
    EXPORT_ANALYTICS = "export_analytics"
    
    # Notification Jobs
    NOTIFICATION_SEND = "notification_send"
    NOTIFICATION_BULK = "notification_bulk"


class JobStatus(str, Enum):
    """Job execution status."""
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


class RetryableError(Exception):
    """
    Exception that indicates a job can be retried.
    
    Use for:
    - Network timeouts
    - Temporary service unavailable
    - Rate limits
    
    Do NOT use for:
    - Validation errors
    - Not found errors
    - Permission errors
    """
    pass


class NonRetryableError(Exception):
    """
    Exception that should NOT trigger a retry.
    
    Use for:
    - Validation errors
    - Business logic failures
    - Permanent failures
    """
    pass


@dataclass
class JobPolicy:
    """Policy configuration for a job type."""
    timeout_seconds: int
    max_retries: int
    retry_delay_seconds: int
    idempotent: bool = True  # All jobs MUST be idempotent
    audit_action: str = "PROCESS"  # Default audit action


# ============================================
# JOB POLICIES TABLE
# ============================================

JOB_POLICIES: dict[JobType, JobPolicy] = {
    # AI Jobs - Longer timeout, limited retries
    JobType.AI_LESSON_PLAN: JobPolicy(
        timeout_seconds=600,
        max_retries=2,
        retry_delay_seconds=30,
        audit_action="GENERATE",
    ),
    JobType.AI_WORKSHEET: JobPolicy(
        timeout_seconds=600,
        max_retries=2,
        retry_delay_seconds=30,
        audit_action="GENERATE",
    ),
    JobType.AI_DOUBT_SOLVER: JobPolicy(
        timeout_seconds=300,
        max_retries=2,
        retry_delay_seconds=15,
        audit_action="GENERATE",
    ),
    JobType.AI_MCQ_GENERATE: JobPolicy(
        timeout_seconds=600,
        max_retries=2,
        retry_delay_seconds=30,
        audit_action="GENERATE",
    ),
    JobType.AI_INSIGHT: JobPolicy(
        timeout_seconds=600,
        max_retries=2,
        retry_delay_seconds=30,
        audit_action="GENERATE",
    ),
    
    # OCR Jobs - Medium timeout, more retries
    JobType.OCR_PROCESS: JobPolicy(
        timeout_seconds=300,
        max_retries=3,
        retry_delay_seconds=20,
        audit_action="PROCESS",
    ),
    JobType.OCR_IMPORT: JobPolicy(
        timeout_seconds=300,
        max_retries=3,
        retry_delay_seconds=20,
        audit_action="IMPORT",
    ),
    
    # Analytics Jobs - Fast, single attempt
    JobType.ANALYTICS_SNAPSHOT: JobPolicy(
        timeout_seconds=120,
        max_retries=1,
        retry_delay_seconds=10,
        audit_action="GENERATE",
    ),
    JobType.ANALYTICS_AGGREGATE: JobPolicy(
        timeout_seconds=120,
        max_retries=1,
        retry_delay_seconds=10,
        audit_action="GENERATE",
    ),
    
    # Payroll Jobs - Critical, no retry (human review needed)
    JobType.PAYROLL_PROCESS: JobPolicy(
        timeout_seconds=300,
        max_retries=0,  # NO automatic retry for payroll
        retry_delay_seconds=0,
        audit_action="PROCESS",
    ),
    JobType.PAYROLL_GENERATE: JobPolicy(
        timeout_seconds=300,
        max_retries=0,  # NO automatic retry
        retry_delay_seconds=0,
        audit_action="GENERATE",
    ),
    
    # Export Jobs
    JobType.EXPORT_INSPECTION: JobPolicy(
        timeout_seconds=180,
        max_retries=2,
        retry_delay_seconds=30,
        audit_action="EXPORT",
    ),
    JobType.EXPORT_REPORT: JobPolicy(
        timeout_seconds=180,
        max_retries=2,
        retry_delay_seconds=30,
        audit_action="EXPORT",
    ),
    JobType.EXPORT_ANALYTICS: JobPolicy(
        timeout_seconds=180,
        max_retries=2,
        retry_delay_seconds=30,
        audit_action="EXPORT",
    ),
    
    # Notification Jobs
    JobType.NOTIFICATION_SEND: JobPolicy(
        timeout_seconds=60,
        max_retries=3,
        retry_delay_seconds=10,
        audit_action="PROCESS",
    ),
    JobType.NOTIFICATION_BULK: JobPolicy(
        timeout_seconds=180,
        max_retries=2,
        retry_delay_seconds=30,
        audit_action="PROCESS",
    ),
}


def get_policy(job_type: JobType) -> JobPolicy:
    """Get policy for a job type."""
    if job_type not in JOB_POLICIES:
        # Default policy for unknown types (should not happen with registry)
        return JobPolicy(
            timeout_seconds=120,
            max_retries=1,
            retry_delay_seconds=15,
        )
    return JOB_POLICIES[job_type]


def is_retryable_error(error: Exception) -> bool:
    """
    Determine if an error is retryable.
    
    Retryable errors:
    - Network timeouts
    - Connection refused
    - Rate limits (429)
    - Service unavailable (503)
    
    Non-retryable:
    - Validation errors
    - Not found
    - Permission denied
    - Business logic errors
    """
    if isinstance(error, RetryableError):
        return True
    
    if isinstance(error, NonRetryableError):
        return False
    
    error_str = str(error).lower()
    
    # Retryable patterns
    retryable_patterns = [
        "timeout",
        "connection refused",
        "connection reset",
        "rate limit",
        "too many requests",
        "service unavailable",
        "temporary",
        "retry",
    ]
    
    for pattern in retryable_patterns:
        if pattern in error_str:
            return True
    
    # Non-retryable patterns
    non_retryable_patterns = [
        "not found",
        "validation",
        "invalid",
        "permission",
        "forbidden",
        "unauthorized",
        "already exists",
        "duplicate",
    ]
    
    for pattern in non_retryable_patterns:
        if pattern in error_str:
            return False
    
    # Default: retry for unknown errors (safe)
    return True
