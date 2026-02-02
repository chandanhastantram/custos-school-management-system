"""
CUSTOS Circuit State Manager

Tracks failure counts and circuit states per feature.

STORAGE:
- In-memory for speed (resets on restart)
- Could be extended to Redis for multi-instance
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, List
from dataclasses import dataclass, field
from threading import Lock

from app.core.resilience.policies import Feature, CircuitState, get_policy

logger = logging.getLogger(__name__)


@dataclass
class FailureRecord:
    """Record of a single failure."""
    timestamp: datetime
    error_type: str
    error_message: str


@dataclass
class FeatureState:
    """
    State tracking for a single feature's circuit breaker.
    
    Tracks:
    - Current circuit state
    - Recent failures within window
    - State transition timestamps
    - Half-open call attempts
    """
    feature: Feature
    state: CircuitState = CircuitState.CLOSED
    failures: List[FailureRecord] = field(default_factory=list)
    
    # State transitions
    opened_at: Optional[datetime] = None
    half_open_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    
    # Half-open tracking
    half_open_calls: int = 0
    half_open_successes: int = 0
    
    # Stats
    total_failures: int = 0
    total_successes: int = 0
    last_failure_at: Optional[datetime] = None
    last_success_at: Optional[datetime] = None
    
    def get_recent_failures(self, window_seconds: int) -> int:
        """Count failures within the time window."""
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(seconds=window_seconds)
        
        # Clean up old failures
        self.failures = [f for f in self.failures if f.timestamp > cutoff]
        
        return len(self.failures)


class CircuitStateManager:
    """
    Manages circuit breaker states for all features.
    
    Thread-safe singleton for tracking failure counts
    and circuit states across the application.
    """
    
    _instance: Optional["CircuitStateManager"] = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._states: Dict[Feature, FeatureState] = {}
        self._state_lock = Lock()
        self._initialized = True
        
        # Initialize states for all features
        for feature in Feature:
            self._states[feature] = FeatureState(feature=feature)
    
    def get_state(self, feature: Feature) -> FeatureState:
        """Get current state for a feature."""
        if feature not in self._states:
            self._states[feature] = FeatureState(feature=feature)
        return self._states[feature]
    
    def get_circuit_state(self, feature: Feature) -> CircuitState:
        """
        Get current circuit state, checking for automatic transitions.
        
        Transitions:
        - OPEN → HALF_OPEN after open_duration_seconds
        - HALF_OPEN → CLOSED after successful calls
        """
        with self._state_lock:
            state = self.get_state(feature)
            policy = get_policy(feature)
            now = datetime.now(timezone.utc)
            
            if state.state == CircuitState.OPEN:
                # Check if open duration has passed
                if state.opened_at:
                    open_duration = timedelta(seconds=policy.open_duration_seconds)
                    if now > state.opened_at + open_duration:
                        # Transition to HALF_OPEN
                        self._transition_to_half_open(feature)
                        return CircuitState.HALF_OPEN
            
            return state.state
    
    def record_success(self, feature: Feature) -> None:
        """Record a successful call."""
        with self._state_lock:
            state = self.get_state(feature)
            now = datetime.now(timezone.utc)
            
            state.total_successes += 1
            state.last_success_at = now
            
            if state.state == CircuitState.HALF_OPEN:
                state.half_open_successes += 1
                
                # Check if we should close the circuit
                policy = get_policy(feature)
                if state.half_open_successes >= policy.half_open_max_calls:
                    self._transition_to_closed(feature)
    
    def record_failure(
        self,
        feature: Feature,
        error: Exception,
    ) -> CircuitState:
        """
        Record a failure and potentially open the circuit.
        
        Returns the new circuit state.
        """
        with self._state_lock:
            state = self.get_state(feature)
            policy = get_policy(feature)
            now = datetime.now(timezone.utc)
            
            # Record failure
            state.failures.append(FailureRecord(
                timestamp=now,
                error_type=type(error).__name__,
                error_message=str(error)[:500],
            ))
            state.total_failures += 1
            state.last_failure_at = now
            
            if state.state == CircuitState.HALF_OPEN:
                # Any failure in HALF_OPEN reopens the circuit
                self._transition_to_open(feature, reason="half_open_failure")
                return CircuitState.OPEN
            
            elif state.state == CircuitState.CLOSED:
                # Check if we exceeded the threshold
                recent = state.get_recent_failures(policy.window_seconds)
                
                if recent >= policy.failure_threshold:
                    self._transition_to_open(feature, reason="threshold_exceeded")
                    return CircuitState.OPEN
            
            return state.state
    
    def can_execute(self, feature: Feature) -> bool:
        """
        Check if a call can be executed.
        
        Returns False if circuit is OPEN.
        Returns True (with limit) if HALF_OPEN.
        """
        with self._state_lock:
            current_state = self.get_circuit_state(feature)
            
            if current_state == CircuitState.OPEN:
                return False
            
            if current_state == CircuitState.HALF_OPEN:
                state = self.get_state(feature)
                policy = get_policy(feature)
                
                if state.half_open_calls >= policy.half_open_max_calls:
                    return False
                
                state.half_open_calls += 1
            
            return True
    
    def force_open(self, feature: Feature, reason: str = "manual") -> None:
        """Force a circuit to open (for manual intervention)."""
        with self._state_lock:
            self._transition_to_open(feature, reason=reason)
    
    def force_close(self, feature: Feature) -> None:
        """Force a circuit to close (for recovery)."""
        with self._state_lock:
            self._transition_to_closed(feature)
    
    def reset(self, feature: Feature) -> None:
        """Reset all state for a feature."""
        with self._state_lock:
            self._states[feature] = FeatureState(feature=feature)
    
    def reset_all(self) -> None:
        """Reset all feature states."""
        with self._state_lock:
            for feature in Feature:
                self._states[feature] = FeatureState(feature=feature)
    
    def _transition_to_open(self, feature: Feature, reason: str) -> None:
        """Transition circuit to OPEN state."""
        state = self.get_state(feature)
        old_state = state.state
        
        state.state = CircuitState.OPEN
        state.opened_at = datetime.now(timezone.utc)
        state.half_open_calls = 0
        state.half_open_successes = 0
        
        logger.warning(
            f"Circuit OPENED for {feature.value}: {reason} "
            f"({state.get_recent_failures(get_policy(feature).window_seconds)} failures)"
        )
        
        # Trigger audit log (async-safe)
        self._schedule_audit_log(feature, old_state, CircuitState.OPEN, reason)
    
    def _transition_to_half_open(self, feature: Feature) -> None:
        """Transition circuit to HALF_OPEN state."""
        state = self.get_state(feature)
        old_state = state.state
        
        state.state = CircuitState.HALF_OPEN
        state.half_open_at = datetime.now(timezone.utc)
        state.half_open_calls = 0
        state.half_open_successes = 0
        
        logger.info(f"Circuit HALF_OPEN for {feature.value}: testing recovery")
        
        self._schedule_audit_log(feature, old_state, CircuitState.HALF_OPEN, "recovery_test")
    
    def _transition_to_closed(self, feature: Feature) -> None:
        """Transition circuit to CLOSED state."""
        state = self.get_state(feature)
        old_state = state.state
        
        state.state = CircuitState.CLOSED
        state.closed_at = datetime.now(timezone.utc)
        state.failures = []  # Clear failures on close
        state.half_open_calls = 0
        state.half_open_successes = 0
        
        logger.info(f"Circuit CLOSED for {feature.value}: service recovered")
        
        self._schedule_audit_log(feature, old_state, CircuitState.CLOSED, "recovered")
    
    def _schedule_audit_log(
        self,
        feature: Feature,
        old_state: CircuitState,
        new_state: CircuitState,
        reason: str,
    ) -> None:
        """
        Schedule audit log for circuit state change.
        
        Since this may be called from sync context, we just
        store the event. The audit will be written on next
        async opportunity.
        """
        # Store for later audit (could use queue)
        # For now, just log - audit integration in decorator
        pass
    
    def get_all_states(self) -> Dict[str, dict]:
        """Get summary of all circuit states."""
        result = {}
        for feature, state in self._states.items():
            policy = get_policy(feature)
            result[feature.value] = {
                "state": state.state.value,
                "recent_failures": state.get_recent_failures(policy.window_seconds),
                "threshold": policy.failure_threshold,
                "total_failures": state.total_failures,
                "total_successes": state.total_successes,
                "last_failure": state.last_failure_at.isoformat() if state.last_failure_at else None,
                "opened_at": state.opened_at.isoformat() if state.opened_at else None,
            }
        return result
    
    def get_health(self) -> dict:
        """Get overall resilience health status."""
        states = self.get_all_states()
        
        open_circuits = [f for f, s in states.items() if s["state"] == "open"]
        half_open = [f for f, s in states.items() if s["state"] == "half_open"]
        
        return {
            "status": "degraded" if open_circuits else "healthy",
            "open_circuits": open_circuits,
            "half_open_circuits": half_open,
            "total_features": len(Feature),
            "degraded_count": len(open_circuits),
        }


# Global singleton instance
_state_manager: Optional[CircuitStateManager] = None


def get_state_manager() -> CircuitStateManager:
    """Get the global circuit state manager."""
    global _state_manager
    if _state_manager is None:
        _state_manager = CircuitStateManager()
    return _state_manager
