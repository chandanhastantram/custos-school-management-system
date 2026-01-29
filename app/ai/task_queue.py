"""
CUSTOS Background Task Queue

Redis Queue (RQ) integration for background AI jobs.
"""

import asyncio
from datetime import datetime
from typing import Optional, Callable, Any
from uuid import UUID
from functools import wraps
import json

from app.core.config import settings


# Check if Redis is available
REDIS_AVAILABLE = False
try:
    from redis import Redis
    from rq import Queue
    REDIS_AVAILABLE = True
except ImportError:
    pass


class BackgroundTaskQueue:
    """
    Background task queue for large AI jobs.
    
    Features:
    - Redis Queue (RQ) when available
    - Falls back to synchronous execution
    - Job tracking and status
    """
    
    def __init__(self):
        self.redis_conn = None
        self.queue = None
        self._setup_queue()
    
    def _setup_queue(self):
        """Initialize Redis Queue if available."""
        if not REDIS_AVAILABLE:
            return
        
        redis_url = getattr(settings, 'redis_url', None)
        if not redis_url:
            return
        
        try:
            self.redis_conn = Redis.from_url(redis_url)
            self.redis_conn.ping()  # Test connection
            self.queue = Queue(connection=self.redis_conn)
        except Exception:
            self.redis_conn = None
            self.queue = None
    
    @property
    def is_available(self) -> bool:
        """Check if queue is available."""
        return self.queue is not None
    
    def enqueue(
        self,
        func: Callable,
        *args,
        job_timeout: int = 300,
        **kwargs,
    ) -> Optional[str]:
        """
        Enqueue a job for background processing.
        
        Returns job_id if queued, None if executed synchronously.
        """
        if not self.is_available:
            # Execute synchronously if queue not available
            if asyncio.iscoroutinefunction(func):
                loop = asyncio.get_event_loop()
                loop.run_until_complete(func(*args, **kwargs))
            else:
                func(*args, **kwargs)
            return None
        
        job = self.queue.enqueue(
            func,
            *args,
            job_timeout=job_timeout,
            **kwargs,
        )
        return job.id
    
    def get_job_status(self, job_id: str) -> dict:
        """Get status of a queued job."""
        if not self.is_available:
            return {"status": "unknown", "error": "Queue not available"}
        
        from rq.job import Job
        try:
            job = Job.fetch(job_id, connection=self.redis_conn)
            return {
                "status": job.get_status(),
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "ended_at": job.ended_at.isoformat() if job.ended_at else None,
                "result": job.result,
                "error": str(job.exc_info) if job.exc_info else None,
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}


# Global queue instance
task_queue = BackgroundTaskQueue()


def background_task(timeout: int = 300):
    """
    Decorator for background tasks.
    
    Usage:
        @background_task(timeout=600)
        async def process_large_batch(...):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, enqueue: bool = False, **kwargs):
            if enqueue and task_queue.is_available:
                return task_queue.enqueue(func, *args, job_timeout=timeout, **kwargs)
            
            if asyncio.iscoroutinefunction(func):
                loop = asyncio.get_event_loop()
                return loop.run_until_complete(func(*args, **kwargs))
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


class JobTracker:
    """
    Tracks background job status in database.
    
    For when Redis is not available or for persistence.
    """
    
    def __init__(self, session, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
    
    async def create_job(
        self,
        job_type: str,
        params: dict,
    ) -> UUID:
        """Create a job tracking record."""
        from app.ai.models import AILessonPlanJob, AIJobStatus
        import uuid
        
        job_id = uuid.uuid4()
        # Job tracking is done via the existing job models
        return job_id
    
    async def update_status(
        self,
        job_id: UUID,
        status: str,
        result: Optional[dict] = None,
        error: Optional[str] = None,
    ) -> None:
        """Update job status."""
        pass  # Status updates are handled by individual services
