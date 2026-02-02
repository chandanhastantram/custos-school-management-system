"""
CUSTOS Resilience Decorators

Easy-to-use decorators for circuit breaker protection.

Usage:

    @resilient(feature=Feature.AI_OCR)
    async def process_exam_ocr(session, exam_id):
        # This will be protected by circuit breaker
        return await ai_service.process_ocr(exam_id)
"""

import functools
import logging
from typing import Callable, Any, Optional, Union
from uuid import UUID

from app.core.resilience.policies import Feature, CircuitState, get_policy
from app.core.resilience.state import get_state_manager
from app.core.resilience.circuit import CircuitBreaker, CircuitOpenError

logger = logging.getLogger(__name__)


def resilient(
    feature: Union[Feature, str],
    fallback: Optional[Callable] = None,
    reraise: bool = False,
):
    """
    Decorator to protect a function with circuit breaker.
    
    Args:
        feature: Feature enum or string name
        fallback: Optional custom fallback function
        reraise: If True, reraise exception after recording failure
        
    Example:
    
        @resilient(feature=Feature.AI_OCR)
        async def process_ocr(session, file_id):
            return await ocr_service.process(file_id)
        
        # With custom fallback:
        @resilient(
            feature=Feature.AI_INSIGHT,
            fallback=lambda *a, **k: {"insights": [], "degraded": True}
        )
        async def get_insights(session, class_id):
            return await insight_service.generate(class_id)
    """
    # Convert string to Feature enum if needed
    if isinstance(feature, str):
        try:
            feature = Feature(feature)
        except ValueError:
            logger.warning(f"Unknown feature: {feature}, using default policy")
            feature = Feature.CACHE  # Safe default
    
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            breaker = CircuitBreaker(feature)
            
            # Check if we can make the call
            if not breaker.can_call():
                logger.warning(
                    f"Circuit OPEN for {feature.value} - returning fallback"
                )
                
                # Return custom fallback or default
                if fallback:
                    return fallback(*args, **kwargs)
                return breaker.get_fallback_response()
            
            try:
                # Execute the function
                result = await func(*args, **kwargs)
                
                # Record success
                breaker.record_success()
                
                return result
                
            except Exception as e:
                # Record failure
                new_state = breaker.record_failure(e)
                
                if new_state == CircuitState.OPEN:
                    logger.warning(
                        f"Circuit OPENED for {feature.value} after failure: {e}"
                    )
                
                if reraise:
                    raise
                
                # Return fallback on error
                if fallback:
                    return fallback(*args, **kwargs)
                
                return {
                    **breaker.get_fallback_response(),
                    "error": str(e)[:200],
                }
        
        # Attach circuit breaker info to function
        wrapper._circuit_feature = feature
        wrapper._circuit_breaker = CircuitBreaker(feature)
        
        return wrapper
    
    return decorator


def resilient_sync(
    feature: Union[Feature, str],
    fallback: Optional[Callable] = None,
    reraise: bool = False,
):
    """
    Synchronous version of resilient decorator.
    
    For non-async functions.
    """
    if isinstance(feature, str):
        try:
            feature = Feature(feature)
        except ValueError:
            feature = Feature.CACHE
    
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            breaker = CircuitBreaker(feature)
            
            if not breaker.can_call():
                if fallback:
                    return fallback(*args, **kwargs)
                return breaker.get_fallback_response()
            
            try:
                result = func(*args, **kwargs)
                breaker.record_success()
                return result
                
            except Exception as e:
                breaker.record_failure(e)
                
                if reraise:
                    raise
                
                if fallback:
                    return fallback(*args, **kwargs)
                
                return {
                    **breaker.get_fallback_response(),
                    "error": str(e)[:200],
                }
        
        wrapper._circuit_feature = feature
        return wrapper
    
    return decorator


class ResilientContext:
    """
    Context manager for circuit breaker protection.
    
    For when you need more control than decorators provide.
    
    Usage:
    
        async with ResilientContext(Feature.AI_OCR) as ctx:
            if ctx.can_proceed:
                result = await do_something()
                ctx.record_success()
            else:
                result = ctx.fallback_response
    """
    
    def __init__(self, feature: Feature):
        self.feature = feature
        self.breaker = CircuitBreaker(feature)
        self.can_proceed = False
        self.fallback_response = None
    
    async def __aenter__(self):
        self.can_proceed = self.breaker.can_call()
        if not self.can_proceed:
            self.fallback_response = self.breaker.get_fallback_response()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None and self.can_proceed:
            # Record failure if an exception occurred
            self.breaker.record_failure(exc_val)
        return False  # Don't suppress exceptions
    
    def record_success(self):
        """Record successful execution."""
        if self.can_proceed:
            self.breaker.record_success()
    
    def record_failure(self, error: Exception):
        """Record failed execution."""
        self.breaker.record_failure(error)


def get_feature_status(feature: Feature) -> dict:
    """Get status of a specific feature's circuit breaker."""
    return CircuitBreaker(feature).get_status()


def get_all_circuit_status() -> dict:
    """Get status of all circuit breakers."""
    manager = get_state_manager()
    return manager.get_all_states()


def get_resilience_health() -> dict:
    """Get overall resilience health."""
    manager = get_state_manager()
    return manager.get_health()


def force_circuit_open(feature: Feature, reason: str = "manual") -> None:
    """Manually open a circuit (for testing or emergency)."""
    manager = get_state_manager()
    manager.force_open(feature, reason)
    logger.warning(f"Circuit manually OPENED: {feature.value} - {reason}")


def force_circuit_close(feature: Feature) -> None:
    """Manually close a circuit (for recovery)."""
    manager = get_state_manager()
    manager.force_close(feature)
    logger.info(f"Circuit manually CLOSED: {feature.value}")


def reset_circuit(feature: Feature) -> None:
    """Reset a circuit to initial state."""
    manager = get_state_manager()
    manager.reset(feature)
    logger.info(f"Circuit reset: {feature.value}")
