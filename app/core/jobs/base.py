"""
CUSTOS Abstract Job Base

Base class for all background jobs.

RULES:
1. Every job must have a unique job_key
2. Jobs must be idempotent (same key = no re-execution if completed)
3. Jobs must be audited
4. Jobs must handle timeout and retries
"""

import asyncio
import logging
import traceback
from abc import ABC, abstractmethod
from datetime import datetime, timezone, timedelta
from typing import Optional, Any, Dict
from uuid import UUID, uuid4

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.jobs.policies import (
    JobType,
    JobStatus,
    JobPolicy,
    get_policy,
    is_retryable_error,
    RetryableError,
    NonRetryableError,
)

logger = logging.getLogger(__name__)


class JobExecutionRecord:
    """
    In-memory representation of job execution.
    
    For persistent storage, use the JobExecution model.
    """
    
    def __init__(
        self,
        job_key: str,
        job_type: JobType,
        tenant_id: UUID,
        status: JobStatus = JobStatus.PENDING,
    ):
        self.id = uuid4()
        self.job_key = job_key
        self.job_type = job_type
        self.tenant_id = tenant_id
        self.status = status
        self.attempt = 0
        self.max_attempts = 1
        self.created_at = datetime.now(timezone.utc)
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.error_message: Optional[str] = None
        self.result_data: Optional[Dict] = None
        self.metadata: Dict = {}


class AbstractJob(ABC):
    """
    Abstract base class for all background jobs.
    
    MANDATORY FEATURES:
    1. Unique job_key for idempotency
    2. Audit logging on start/success/failure
    3. Timeout enforcement
    4. Retry with backoff
    
    USAGE:
    
    class MyJob(AbstractJob):
        job_type = JobType.AI_LESSON_PLAN
        
        def __init__(self, tenant_id: UUID, lesson_plan_id: UUID):
            super().__init__(tenant_id)
            self.lesson_plan_id = lesson_plan_id
        
        def get_job_key(self) -> str:
            return f"ai_lesson_plan:{self.lesson_plan_id}"
        
        async def execute(self, session: AsyncSession) -> Any:
            # Do the work
            return {"success": True}
    """
    
    # MUST be overridden in subclass
    job_type: JobType = None
    
    def __init__(self, tenant_id: UUID):
        self.tenant_id = tenant_id
        self.policy = get_policy(self.job_type) if self.job_type else JobPolicy(
            timeout_seconds=120,
            max_retries=1,
            retry_delay_seconds=15,
        )
        self._execution: Optional[JobExecutionRecord] = None
        self._actor_user_id: Optional[UUID] = None
        self._request_id: Optional[str] = None
        self._ip_address: Optional[str] = None
    
    @abstractmethod
    def get_job_key(self) -> str:
        """
        Return unique key for this job instance.
        
        The key must be deterministic based on job parameters.
        Same parameters = same key.
        
        Examples:
        - "ai_lesson_plan:123e4567-e89b-12d3-a456-426614174000"
        - "ocr_process:file_abc123"
        - "analytics_snapshot:2026-02-01:class_123"
        """
        pass
    
    @abstractmethod
    async def execute(self, session: AsyncSession) -> Any:
        """
        Execute the job logic.
        
        Args:
            session: Database session
            
        Returns:
            Result data (will be stored in execution record)
            
        Raises:
            RetryableError: For errors that should trigger retry
            NonRetryableError: For errors that should not retry
            Any other exception: Will be evaluated for retry
        """
        pass
    
    def get_entity_type(self) -> str:
        """
        Return entity type for audit logging.
        Override in subclass if needed.
        """
        return "SYSTEM"
    
    def get_entity_id(self) -> Optional[UUID]:
        """
        Return entity ID for audit logging.
        Override in subclass if needed.
        """
        return None
    
    def get_entity_name(self) -> Optional[str]:
        """
        Return entity name for audit logging.
        Override in subclass if needed.
        """
        return self.get_job_key()
    
    def set_context(
        self,
        actor_user_id: Optional[UUID] = None,
        request_id: Optional[str] = None,
        ip_address: Optional[str] = None,
    ):
        """Set request context for audit logging."""
        self._actor_user_id = actor_user_id
        self._request_id = request_id
        self._ip_address = ip_address
    
    async def on_success(self, session: AsyncSession, result: Any) -> None:
        """
        Called after successful execution.
        Override in subclass for custom success handling.
        """
        pass
    
    async def on_failure(self, session: AsyncSession, error: Exception) -> None:
        """
        Called after final failure (all retries exhausted).
        Override in subclass for custom failure handling.
        """
        pass
    
    async def on_retry(self, session: AsyncSession, error: Exception, attempt: int) -> None:
        """
        Called before a retry attempt.
        Override in subclass for custom retry handling.
        """
        pass
    
    # ============================================
    # Internal Execution Logic (DO NOT OVERRIDE)
    # ============================================
    
    async def _check_idempotency(self, session: AsyncSession) -> bool:
        """
        Check if job with same key has already completed.
        
        Returns True if job should run, False if already completed.
        """
        from app.core.jobs.models import JobExecution
        
        try:
            query = select(JobExecution).where(
                and_(
                    JobExecution.job_key == self.get_job_key(),
                    JobExecution.tenant_id == self.tenant_id,
                    JobExecution.status == JobStatus.COMPLETED.value,
                )
            )
            result = await session.execute(query)
            existing = result.scalar_one_or_none()
            
            if existing:
                logger.info(
                    f"Job already completed: {self.get_job_key()} "
                    f"(completed at {existing.completed_at})"
                )
                return False
            
            return True
            
        except Exception as e:
            # If we can't check (table doesn't exist yet), proceed with job
            logger.warning(f"Idempotency check failed: {e}")
            return True
    
    async def _create_execution_record(self, session: AsyncSession) -> None:
        """Create execution record in database."""
        from app.core.jobs.models import JobExecution
        
        try:
            self._execution = JobExecution(
                id=uuid4(),
                tenant_id=self.tenant_id,
                job_key=self.get_job_key(),
                job_type=self.job_type.value if self.job_type else "unknown",
                status=JobStatus.PROCESSING.value,
                attempt=1,
                max_attempts=self.policy.max_retries + 1,
                started_at=datetime.now(timezone.utc),
                actor_user_id=self._actor_user_id,
                request_id=self._request_id,
            )
            session.add(self._execution)
            await session.commit()
            
        except Exception as e:
            logger.warning(f"Failed to create execution record: {e}")
            # Create in-memory record as fallback
            self._execution = JobExecutionRecord(
                job_key=self.get_job_key(),
                job_type=self.job_type,
                tenant_id=self.tenant_id,
                status=JobStatus.PROCESSING,
            )
    
    async def _update_execution_status(
        self,
        session: AsyncSession,
        status: JobStatus,
        error_message: Optional[str] = None,
        result_data: Optional[Dict] = None,
    ) -> None:
        """Update execution record status."""
        from app.core.jobs.models import JobExecution
        
        try:
            if hasattr(self._execution, 'id') and isinstance(self._execution, JobExecution):
                self._execution.status = status.value
                self._execution.error_message = error_message
                if result_data:
                    self._execution.result_json = result_data
                if status in [JobStatus.COMPLETED, JobStatus.FAILED]:
                    self._execution.completed_at = datetime.now(timezone.utc)
                await session.commit()
        except Exception as e:
            logger.warning(f"Failed to update execution status: {e}")
    
    async def _audit_log(
        self,
        session: AsyncSession,
        action: str,
        description: str,
        success: bool = True,
    ) -> None:
        """Write to governance audit log."""
        try:
            from app.governance.service import GovernanceService
            from app.governance.models import ActionType, EntityType
            
            governance = GovernanceService(session, self.tenant_id)
            
            # Map action string to ActionType
            action_type_map = {
                "GENERATE": ActionType.GENERATE,
                "PROCESS": ActionType.PROCESS,
                "EXPORT": ActionType.EXPORT,
                "IMPORT": ActionType.IMPORT,
            }
            action_type = action_type_map.get(action, ActionType.PROCESS)
            
            # Map entity type
            entity_type_map = {
                "LESSON_PLAN": EntityType.LESSON_PLAN,
                "ANALYTICS": EntityType.ANALYTICS,
                "EXPORT": EntityType.EXPORT,
                "PAYROLL": EntityType.PAYROLL,
                "SALARY_SLIP": EntityType.SALARY_SLIP,
                "SYSTEM": EntityType.SYSTEM,
            }
            entity_type = entity_type_map.get(
                self.get_entity_type(), EntityType.SYSTEM
            )
            
            await governance.log_action(
                action_type=action_type,
                entity_type=entity_type,
                entity_id=self.get_entity_id(),
                entity_name=self.get_entity_name(),
                actor_user_id=self._actor_user_id,
                description=description,
                ip_address=self._ip_address,
                metadata={
                    "job_key": self.get_job_key(),
                    "job_type": self.job_type.value if self.job_type else "unknown",
                    "success": success,
                    "request_id": self._request_id,
                },
            )
            
        except Exception as e:
            logger.warning(f"Audit log failed: {e}")
    
    async def run(self, session: AsyncSession) -> Any:
        """
        Run the job with full lifecycle management.
        
        DO NOT OVERRIDE THIS METHOD.
        
        Lifecycle:
        1. Check idempotency
        2. Create execution record
        3. Audit start
        4. Execute with timeout
        5. Handle success/failure
        6. Retry if applicable
        7. Audit completion
        """
        job_key = self.get_job_key()
        
        # 1. Check idempotency
        should_run = await self._check_idempotency(session)
        if not should_run:
            logger.info(f"Skipping duplicate job: {job_key}")
            return {"skipped": True, "reason": "already_completed"}
        
        # 2. Create execution record
        await self._create_execution_record(session)
        
        # 3. Audit start
        await self._audit_log(
            session,
            self.policy.audit_action,
            f"Job started: {job_key}",
        )
        
        last_error: Optional[Exception] = None
        result: Any = None
        attempt = 0
        max_attempts = self.policy.max_retries + 1
        
        while attempt < max_attempts:
            attempt += 1
            
            try:
                logger.info(f"Job {job_key} attempt {attempt}/{max_attempts}")
                
                # 4. Execute with timeout
                result = await asyncio.wait_for(
                    self.execute(session),
                    timeout=self.policy.timeout_seconds,
                )
                
                # 5. Success!
                await self._update_execution_status(
                    session,
                    JobStatus.COMPLETED,
                    result_data={"result": str(result)[:500]} if result else None,
                )
                
                await self.on_success(session, result)
                
                # 7. Audit success
                await self._audit_log(
                    session,
                    self.policy.audit_action,
                    f"Job completed: {job_key}",
                    success=True,
                )
                
                logger.info(f"Job {job_key} completed successfully")
                return result
                
            except asyncio.TimeoutError as e:
                last_error = RetryableError(f"Job timed out after {self.policy.timeout_seconds}s")
                logger.warning(f"Job {job_key} timed out on attempt {attempt}")
                
            except Exception as e:
                last_error = e
                logger.warning(f"Job {job_key} failed on attempt {attempt}: {e}")
            
            # Check if we should retry
            if attempt < max_attempts and is_retryable_error(last_error):
                await self._update_execution_status(
                    session,
                    JobStatus.RETRYING,
                    error_message=str(last_error),
                )
                await self.on_retry(session, last_error, attempt)
                
                # Wait before retry
                if self.policy.retry_delay_seconds > 0:
                    await asyncio.sleep(self.policy.retry_delay_seconds)
            else:
                # No more retries
                break
        
        # 6. Final failure
        error_msg = str(last_error) if last_error else "Unknown error"
        
        await self._update_execution_status(
            session,
            JobStatus.FAILED,
            error_message=error_msg,
        )
        
        await self.on_failure(session, last_error)
        
        # 7. Audit failure
        await self._audit_log(
            session,
            self.policy.audit_action,
            f"Job failed: {job_key} - {error_msg}",
            success=False,
        )
        
        logger.error(f"Job {job_key} failed after {attempt} attempts: {error_msg}")
        
        return {"error": error_msg, "attempts": attempt}
