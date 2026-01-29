"""
CUSTOS Background Task Queue

RQ-based background task processing for long-running AI operations.
"""

import os
import logging
from typing import Optional, Callable, Any
from functools import wraps

from redis import Redis
from rq import Queue, Worker
from rq.job import Job

from app.core.config import settings

logger = logging.getLogger("custos.tasks")


# Redis connection
def get_redis_connection() -> Redis:
    """Get Redis connection for task queue."""
    redis_url = getattr(settings, 'redis_url', 'redis://localhost:6379/0')
    return Redis.from_url(redis_url)


# Task queues with different priorities
class TaskQueues:
    """Named queues for different task types."""
    HIGH = "custos_high"      # Critical operations
    DEFAULT = "custos"        # Normal AI operations  
    LOW = "custos_low"        # Bulk/batch operations
    AI_BATCH = "custos_ai"    # Large AI batches only


# Queue instances (lazy loaded)
_queues: dict[str, Queue] = {}


def get_queue(name: str = TaskQueues.DEFAULT) -> Queue:
    """Get or create a queue by name."""
    if name not in _queues:
        _queues[name] = Queue(name, connection=get_redis_connection())
    return _queues[name]


def enqueue_task(
    func: Callable,
    *args,
    queue_name: str = TaskQueues.DEFAULT,
    job_timeout: int = 600,  # 10 minutes default
    retry_count: int = 1,
    job_id: Optional[str] = None,
    **kwargs,
) -> Job:
    """
    Enqueue a task for background processing.
    
    Args:
        func: The function to execute
        *args: Positional arguments for the function
        queue_name: Which queue to use
        job_timeout: Max execution time in seconds
        retry_count: Number of retries on failure
        job_id: Optional custom job ID
        **kwargs: Keyword arguments for the function
    
    Returns:
        RQ Job object
    """
    queue = get_queue(queue_name)
    job = queue.enqueue(
        func,
        *args,
        job_timeout=job_timeout,
        retry=retry_count if retry_count > 0 else None,
        job_id=job_id,
        **kwargs,
    )
    logger.info(f"Enqueued task {func.__name__} with job_id={job.id}")
    return job


def get_job(job_id: str) -> Optional[Job]:
    """Get a job by ID."""
    try:
        return Job.fetch(job_id, connection=get_redis_connection())
    except Exception:
        return None


def get_job_status(job_id: str) -> dict:
    """Get detailed job status."""
    job = get_job(job_id)
    if not job:
        return {"status": "not_found", "job_id": job_id}
    
    return {
        "job_id": job.id,
        "status": job.get_status(),
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "ended_at": job.ended_at.isoformat() if job.ended_at else None,
        "result": job.result if job.is_finished else None,
        "error": str(job.exc_info) if job.is_failed else None,
        "progress": getattr(job, 'meta', {}).get('progress', None),
    }


def update_job_progress(job_id: str, progress: int, message: str = None):
    """Update job progress metadata."""
    job = get_job(job_id)
    if job:
        job.meta['progress'] = progress
        if message:
            job.meta['message'] = message
        job.save_meta()


def cancel_job(job_id: str) -> bool:
    """Cancel a queued or running job."""
    job = get_job(job_id)
    if job:
        job.cancel()
        return True
    return False


# Decorator for background tasks
def background_task(
    queue_name: str = TaskQueues.DEFAULT,
    timeout: int = 600,
):
    """
    Decorator to mark a function as a background task.
    
    When called with .delay(), the function runs in background.
    When called normally, runs synchronously.
    
    Usage:
        @background_task(queue_name=TaskQueues.AI_BATCH, timeout=1800)
        def process_large_batch(tenant_id, data):
            ...
        
        # Run in background
        job = process_large_batch.delay(tenant_id, data)
        
        # Run synchronously
        result = process_large_batch(tenant_id, data)
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        def delay(*args, **kwargs):
            return enqueue_task(
                func,
                *args,
                queue_name=queue_name,
                job_timeout=timeout,
                **kwargs,
            )
        
        wrapper.delay = delay
        wrapper.queue_name = queue_name
        wrapper.timeout = timeout
        return wrapper
    
    return decorator


# Task status enum-like class
class TaskStatus:
    QUEUED = "queued"
    STARTED = "started"
    FINISHED = "finished"
    FAILED = "failed"
    CANCELED = "canceled"


def is_redis_available() -> bool:
    """Check if Redis is available for task queue."""
    try:
        redis = get_redis_connection()
        redis.ping()
        return True
    except Exception as e:
        logger.warning(f"Redis not available: {e}")
        return False
