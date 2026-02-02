"""
CUSTOS Job Framework

Standardized background job infrastructure.

FEATURES:
- Idempotent execution (same job_key = no re-run)
- Retry with backoff
- Timeout enforcement
- Audit integration
- Job registry security

USAGE:

1. Create a job class:

    from app.core.jobs import AbstractJob, JobType, register_job
    
    @register_job
    class MyJob(AbstractJob):
        job_type = JobType.AI_LESSON_PLAN
        
        def __init__(self, tenant_id: UUID, plan_id: UUID):
            super().__init__(tenant_id)
            self.plan_id = plan_id
        
        def get_job_key(self) -> str:
            return f"my_job:{self.plan_id}"
        
        async def execute(self, session: AsyncSession) -> Any:
            # Do the work
            return {"success": True}

2. Enqueue for execution:

    from app.core.jobs import enqueue
    
    job = MyJob(tenant_id=user.tenant_id, plan_id=plan.id)
    result = await enqueue(job, session)

3. Check job status:

    from app.core.jobs import get_job_status
    
    status = await get_job_status(job_key, tenant_id, session)
"""

# Base
from app.core.jobs.base import (
    AbstractJob,
    JobExecutionRecord,
)

# Policies
from app.core.jobs.policies import (
    JobType,
    JobStatus,
    JobPolicy,
    JOB_POLICIES,
    get_policy,
    is_retryable_error,
    RetryableError,
    NonRetryableError,
)

# Queue
from app.core.jobs.queue import (
    enqueue,
    get_job_status,
    cancel_job,
    list_jobs,
    get_queue,
)

# Registry
from app.core.jobs.registry import (
    register_job,
    register_job_class,
    get_job_class,
    is_job_allowed,
    list_registered_jobs,
    get_registry_stats,
    JobCategory,
)

# Models
from app.core.jobs.models import JobExecution

__all__ = [
    # Base
    "AbstractJob",
    "JobExecutionRecord",
    # Policies
    "JobType",
    "JobStatus",
    "JobPolicy",
    "JOB_POLICIES",
    "get_policy",
    "is_retryable_error",
    "RetryableError",
    "NonRetryableError",
    # Queue
    "enqueue",
    "get_job_status",
    "cancel_job",
    "list_jobs",
    "get_queue",
    # Registry
    "register_job",
    "register_job_class",
    "get_job_class",
    "is_job_allowed",
    "list_registered_jobs",
    "get_registry_stats",
    "JobCategory",
    # Models
    "JobExecution",
]
