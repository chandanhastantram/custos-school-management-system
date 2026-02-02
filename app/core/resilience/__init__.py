"""
CUSTOS Resilience Module

Circuit breakers and fail-soft orchestration.

GOAL: Localize failure. Never cascade it.

FEATURES:
- Feature-level circuit breakers
- Automatic degradation with fallback responses
- Error budget tracking
- Audit integration for state changes

USAGE:

1. Decorator (recommended):

    from app.core.resilience import resilient, Feature
    
    @resilient(feature=Feature.AI_OCR)
    async def process_ocr(session, file_id):
        return await ocr_service.process(file_id)

2. Manual circuit breaker:

    from app.core.resilience import CircuitBreaker, Feature
    
    breaker = CircuitBreaker(Feature.PAYMENT_GATEWAY)
    
    if breaker.can_call():
        try:
            result = await payment_service.charge(amount)
            breaker.record_success()
        except Exception as e:
            breaker.record_failure(e)
            raise
    else:
        # Return fallback
        return breaker.get_fallback_response()

3. Context manager:

    from app.core.resilience import ResilientContext, Feature
    
    async with ResilientContext(Feature.AI_INSIGHT) as ctx:
        if ctx.can_proceed:
            result = await generate_insights()
            ctx.record_success()
        else:
            result = ctx.fallback_response

4. Health check:

    from app.core.resilience import get_resilience_health
    
    health = get_resilience_health()
    # {"status": "healthy", "open_circuits": [], ...}
"""

# Policies
from app.core.resilience.policies import (
    Feature,
    CircuitState,
    ResiliencePolicy,
    RESILIENCE_POLICIES,
    get_policy,
)

# State Management
from app.core.resilience.state import (
    FeatureState,
    CircuitStateManager,
    get_state_manager,
)

# Circuit Breaker
from app.core.resilience.circuit import (
    CircuitBreaker,
    CircuitOpenError,
    get_circuit_breaker,
)

# Decorators
from app.core.resilience.decorators import (
    resilient,
    resilient_sync,
    ResilientContext,
    get_feature_status,
    get_all_circuit_status,
    get_resilience_health,
    force_circuit_open,
    force_circuit_close,
    reset_circuit,
)

__all__ = [
    # Policies
    "Feature",
    "CircuitState",
    "ResiliencePolicy",
    "RESILIENCE_POLICIES",
    "get_policy",
    # State
    "FeatureState",
    "CircuitStateManager",
    "get_state_manager",
    # Circuit
    "CircuitBreaker",
    "CircuitOpenError",
    "get_circuit_breaker",
    # Decorators
    "resilient",
    "resilient_sync",
    "ResilientContext",
    "get_feature_status",
    "get_all_circuit_status",
    "get_resilience_health",
    "force_circuit_open",
    "force_circuit_close",
    "reset_circuit",
]
