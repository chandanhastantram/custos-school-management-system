"""
CUSTOS Circuit Breaker

Core circuit breaker implementation.

STATES:
- CLOSED: Normal operation, all calls pass through
- OPEN: All calls blocked, fallback returned
- HALF_OPEN: Limited calls allowed to test recovery
"""

import logging
from datetime import datetime, timezone
from typing import Optional, Any, Callable
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.resilience.policies import Feature, CircuitState, get_policy
from app.core.resilience.state import get_state_manager

logger = logging.getLogger(__name__)


class CircuitOpenError(Exception):
    """Raised when circuit is open and call is blocked."""
    
    def __init__(self, feature: Feature, message: str, fallback_response: Any = None):
        self.feature = feature
        self.message = message
        self.fallback_response = fallback_response
        super().__init__(message)


class CircuitBreaker:
    """
    Circuit breaker for a specific feature.
    
    Usage:
    
        breaker = CircuitBreaker(Feature.AI_OCR)
        
        if breaker.can_call():
            try:
                result = await do_ocr()
                breaker.record_success()
                return result
            except Exception as e:
                breaker.record_failure(e)
                raise
        else:
            return breaker.get_fallback_response()
    """
    
    def __init__(self, feature: Feature):
        self.feature = feature
        self.policy = get_policy(feature)
        self._state_manager = get_state_manager()
    
    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        return self._state_manager.get_circuit_state(self.feature)
    
    @property
    def is_open(self) -> bool:
        """Check if circuit is open (blocking calls)."""
        return self.state == CircuitState.OPEN
    
    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed (normal operation)."""
        return self.state == CircuitState.CLOSED
    
    @property
    def is_half_open(self) -> bool:
        """Check if circuit is half-open (testing recovery)."""
        return self.state == CircuitState.HALF_OPEN
    
    def can_call(self) -> bool:
        """
        Check if a call can be made.
        
        Returns False if circuit is OPEN.
        May return False in HALF_OPEN if max calls reached.
        """
        return self._state_manager.can_execute(self.feature)
    
    def record_success(self) -> None:
        """Record a successful call."""
        self._state_manager.record_success(self.feature)
    
    def record_failure(self, error: Exception) -> CircuitState:
        """
        Record a failed call.
        
        May open the circuit if threshold exceeded.
        Returns the new circuit state.
        """
        return self._state_manager.record_failure(self.feature, error)
    
    def get_fallback_response(self) -> dict:
        """
        Get fallback response for when circuit is open.
        
        Returns a structured response with:
        - status: "degraded"
        - message: User-friendly message
        - feature: The affected feature
        - fallback_data: Any fallback data from policy
        """
        return {
            "status": "degraded",
            "message": self.policy.fallback_message,
            "feature": self.feature.value,
            "circuit_state": self.state.value,
            "fallback_data": self.policy.fallback_response,
        }
    
    def get_status(self) -> dict:
        """Get detailed status of this circuit breaker."""
        feature_state = self._state_manager.get_state(self.feature)
        
        return {
            "feature": self.feature.value,
            "state": self.state.value,
            "recent_failures": feature_state.get_recent_failures(
                self.policy.window_seconds
            ),
            "threshold": self.policy.failure_threshold,
            "window_seconds": self.policy.window_seconds,
            "total_failures": feature_state.total_failures,
            "total_successes": feature_state.total_successes,
            "last_failure": (
                feature_state.last_failure_at.isoformat()
                if feature_state.last_failure_at else None
            ),
            "opened_at": (
                feature_state.opened_at.isoformat()
                if feature_state.opened_at else None
            ),
        }
    
    async def execute(
        self,
        func: Callable,
        *args,
        session: Optional[AsyncSession] = None,
        actor_user_id: Optional[UUID] = None,
        **kwargs,
    ) -> Any:
        """
        Execute a function with circuit breaker protection.
        
        If circuit is open, returns fallback response.
        If call fails, records failure and may open circuit.
        
        Args:
            func: Async function to execute
            *args: Function arguments
            session: Optional DB session for audit
            actor_user_id: Optional user ID for audit
            **kwargs: Function keyword arguments
            
        Returns:
            Function result or fallback response
        """
        if not self.can_call():
            # Circuit is open - return fallback
            fallback = self.get_fallback_response()
            
            # Log the blocked call
            await self._audit_blocked_call(session, actor_user_id)
            
            return fallback
        
        try:
            # Execute the function
            result = await func(*args, **kwargs)
            
            # Record success
            self.record_success()
            
            return result
            
        except Exception as e:
            # Record failure
            new_state = self.record_failure(e)
            
            # Audit if circuit opened
            if new_state == CircuitState.OPEN:
                await self._audit_circuit_open(session, actor_user_id, e)
            
            # Re-raise the exception
            raise
    
    async def _audit_blocked_call(
        self,
        session: Optional[AsyncSession],
        actor_user_id: Optional[UUID],
    ) -> None:
        """Audit a blocked call due to open circuit."""
        if not session:
            return
        
        try:
            from app.governance.service import GovernanceService
            from app.governance.models import ActionType, EntityType
            
            # Get tenant from session context or skip
            tenant_id = getattr(session, '_tenant_id', None)
            if not tenant_id:
                return
            
            governance = GovernanceService(session, tenant_id)
            
            await governance.log_action(
                action_type=ActionType.PROCESS,
                entity_type=EntityType.SYSTEM,
                entity_id=None,
                entity_name=f"circuit_breaker:{self.feature.value}",
                actor_user_id=actor_user_id,
                description=f"Call blocked - circuit OPEN for {self.feature.value}",
                metadata={
                    "feature": self.feature.value,
                    "circuit_state": "open",
                    "action": "blocked",
                },
            )
        except Exception as e:
            logger.warning(f"Failed to audit blocked call: {e}")
    
    async def _audit_circuit_open(
        self,
        session: Optional[AsyncSession],
        actor_user_id: Optional[UUID],
        error: Exception,
    ) -> None:
        """Audit circuit state change to OPEN."""
        if not session:
            return
        
        try:
            from app.governance.service import GovernanceService
            from app.governance.models import ActionType, EntityType
            
            tenant_id = getattr(session, '_tenant_id', None)
            if not tenant_id:
                return
            
            governance = GovernanceService(session, tenant_id)
            
            await governance.log_action(
                action_type=ActionType.PROCESS,
                entity_type=EntityType.SYSTEM,
                entity_id=None,
                entity_name=f"circuit_breaker:{self.feature.value}",
                actor_user_id=actor_user_id,
                description=f"Circuit OPENED for {self.feature.value} - threshold exceeded",
                metadata={
                    "feature": self.feature.value,
                    "circuit_state": "open",
                    "action": "state_change",
                    "trigger_error": str(error)[:200],
                },
            )
        except Exception as e:
            logger.warning(f"Failed to audit circuit open: {e}")


def get_circuit_breaker(feature: Feature) -> CircuitBreaker:
    """Get a circuit breaker for a feature."""
    return CircuitBreaker(feature)
