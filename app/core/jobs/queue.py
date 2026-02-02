"""
CUSTOS Job Queue

Queue management for background jobs.

FEATURES:
- Redis Queue (RQ) for async execution
- Synchronous fallback if Redis unavailable
- Never silently fail
"""

import logging
from typing import Optional, Any, Type
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.jobs.base import AbstractJob
from app.core.jobs.policies import JobStatus
from app.core.jobs.registry import is_job_allowed, get_job_class

logger = logging.getLogger(__name__)


# Global flag for RQ availability
_RQ_AVAILABLE = False
_redis_conn = None

try:
    from redis import Redis
    from rq import Queue
    _RQ_AVAILABLE = True
except ImportError:
    logger.warning("RQ not installed - jobs will run synchronously")


async def get_queue() -> Optional[Any]:
    """
    Get RQ queue instance.
    
    Returns None if RQ is not available.
    """
    global _redis_conn
    
    if not _RQ_AVAILABLE:
        return None
    
    try:
        from app.core.config import settings
        
        redis_url = getattr(settings, 'redis_url', 'redis://localhost:6379/0')
        
        if _redis_conn is None:
            _redis_conn = Redis.from_url(redis_url)
            # Test connection
            _redis_conn.ping()
        
        return Queue(connection=_redis_conn)
        
    except Exception as e:
        logger.warning(f"Redis queue unavailable: {e}")
        return None


async def enqueue(
    job: AbstractJob,
    session: AsyncSession,
    delay_seconds: int = 0,
) -> dict:
    """
    Enqueue a job for background execution.
    
    If Redis is unavailable, runs synchronously as fallback.
    
    Args:
        job: Job instance to execute
        session: Database session
        delay_seconds: Optional delay before execution
        
    Returns:
        Dict with job_id, status, and execution mode
    """
    job_key = job.get_job_key()
    job_type = job.job_type.value if job.job_type else "unknown"
    
    # Security: Check if job type is allowed
    if not is_job_allowed(type(job)):
        logger.error(f"Unauthorized job type: {type(job).__name__}")
        return {
            "job_key": job_key,
            "status": "rejected",
            "reason": "unauthorized_job_type",
        }
    
    # Try to enqueue to Redis
    queue = await get_queue()
    
    if queue is not None:
        try:
            # RQ available - enqueue for async execution
            rq_job = queue.enqueue(
                _execute_job_sync,
                job.__class__.__name__,
                job.tenant_id,
                job._get_serializable_params(),  # Must implement in job
                job_id=job_key,
                job_timeout=job.policy.timeout_seconds,
                retry=job.policy.max_retries,
            )
            
            logger.info(f"Job enqueued: {job_key} (RQ job ID: {rq_job.id})")
            
            return {
                "job_key": job_key,
                "job_type": job_type,
                "status": JobStatus.QUEUED.value,
                "execution_mode": "async",
                "rq_job_id": rq_job.id,
            }
            
        except Exception as e:
            logger.warning(f"Failed to enqueue job: {e} - falling back to sync")
    
    # Fallback: Run synchronously
    logger.info(f"Running job synchronously: {job_key}")
    
    try:
        result = await job.run(session)
        
        status = JobStatus.COMPLETED.value
        if isinstance(result, dict) and result.get("error"):
            status = JobStatus.FAILED.value
        
        return {
            "job_key": job_key,
            "job_type": job_type,
            "status": status,
            "execution_mode": "sync",
            "result": result,
        }
        
    except Exception as e:
        logger.error(f"Sync job execution failed: {e}")
        
        return {
            "job_key": job_key,
            "job_type": job_type,
            "status": JobStatus.FAILED.value,
            "execution_mode": "sync",
            "error": str(e),
        }


def _execute_job_sync(
    job_class_name: str,
    tenant_id: UUID,
    params: dict,
) -> dict:
    """
    Sync wrapper for RQ worker.
    
    This function is called by RQ worker in a separate process.
    """
    import asyncio
    from app.common.database import get_session
    
    # Get job class from registry
    job_class = get_job_class(job_class_name)
    if not job_class:
        return {"error": f"Unknown job class: {job_class_name}"}
    
    # Create job instance
    job = job_class(tenant_id=tenant_id, **params)
    
    # Run in async context
    async def run_job():
        async with get_session() as session:
            return await job.run(session)
    
    return asyncio.run(run_job())


async def get_job_status(job_key: str, tenant_id: UUID, session: AsyncSession) -> dict:
    """
    Get status of a job by its key.
    """
    from sqlalchemy import select
    from app.core.jobs.models import JobExecution
    
    query = select(JobExecution).where(
        JobExecution.job_key == job_key,
        JobExecution.tenant_id == tenant_id,
    ).order_by(JobExecution.created_at.desc())
    
    result = await session.execute(query)
    execution = result.scalar_one_or_none()
    
    if not execution:
        return {"job_key": job_key, "status": "not_found"}
    
    return {
        "job_key": job_key,
        "job_type": execution.job_type,
        "status": execution.status,
        "attempt": execution.attempt,
        "max_attempts": execution.max_attempts,
        "started_at": execution.started_at.isoformat() if execution.started_at else None,
        "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
        "error_message": execution.error_message,
        "duration_seconds": execution.duration_seconds,
    }


async def cancel_job(job_key: str, tenant_id: UUID, session: AsyncSession) -> bool:
    """
    Cancel a pending/queued job.
    
    Cannot cancel jobs that are already processing or completed.
    """
    from sqlalchemy import select, update
    from app.core.jobs.models import JobExecution
    
    # Find pending jobs
    query = update(JobExecution).where(
        JobExecution.job_key == job_key,
        JobExecution.tenant_id == tenant_id,
        JobExecution.status.in_(["pending", "queued"]),
    ).values(
        status=JobStatus.CANCELLED.value,
        completed_at=datetime.now(timezone.utc),
    )
    
    result = await session.execute(query)
    await session.commit()
    
    if result.rowcount > 0:
        logger.info(f"Job cancelled: {job_key}")
        return True
    
    return False


async def list_jobs(
    tenant_id: UUID,
    session: AsyncSession,
    job_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
) -> list:
    """
    List recent jobs for a tenant.
    """
    from sqlalchemy import select
    from app.core.jobs.models import JobExecution
    
    query = select(JobExecution).where(
        JobExecution.tenant_id == tenant_id,
    )
    
    if job_type:
        query = query.where(JobExecution.job_type == job_type)
    
    if status:
        query = query.where(JobExecution.status == status)
    
    query = query.order_by(JobExecution.created_at.desc()).limit(limit)
    
    result = await session.execute(query)
    executions = result.scalars().all()
    
    return [
        {
            "id": str(ex.id),
            "job_key": ex.job_key,
            "job_type": ex.job_type,
            "status": ex.status,
            "attempt": ex.attempt,
            "created_at": ex.created_at.isoformat() if ex.created_at else None,
            "completed_at": ex.completed_at.isoformat() if ex.completed_at else None,
            "error_message": ex.error_message,
        }
        for ex in executions
    ]
