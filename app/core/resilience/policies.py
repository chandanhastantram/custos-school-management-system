"""
CUSTOS Resilience Policies

Error thresholds and fallback definitions per feature.

GOAL: Localize failure. Never cascade it.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Any, Dict


class Feature(str, Enum):
    """Protected features with circuit breakers."""
    # AI Features
    AI_LESSON_PLAN = "ai_lesson_plan"
    AI_WORKSHEET = "ai_worksheet"
    AI_MCQ_GENERATE = "ai_mcq_generate"
    AI_DOUBT_SOLVER = "ai_doubt_solver"
    AI_INSIGHT = "ai_insight"
    AI_OCR = "ai_ocr"
    
    # External Services
    PAYMENT_GATEWAY = "payment_gateway"
    SMS_PROVIDER = "sms_provider"
    EMAIL_PROVIDER = "email_provider"
    NOTIFICATION = "notification"
    
    # Internal Critical
    ANALYTICS = "analytics"
    OCR_PROCESS = "ocr_process"
    EXPORT = "export"
    
    # Database Operations (for read replicas if any)
    DB_READ = "db_read"
    CACHE = "cache"


class CircuitState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Blocked, fallback only
    HALF_OPEN = "half_open"  # Limited retry


@dataclass
class ResiliencePolicy:
    """
    Policy configuration for a feature's circuit breaker.
    
    Attributes:
        failure_threshold: Max failures before opening circuit
        window_seconds: Time window for counting failures
        open_duration_seconds: How long to stay in OPEN state
        half_open_max_calls: Max calls allowed in HALF_OPEN
        fallback_response: Default response when circuit is OPEN
        fallback_message: User-friendly message
    """
    failure_threshold: int
    window_seconds: int
    open_duration_seconds: int
    half_open_max_calls: int = 3
    fallback_response: Optional[Any] = None
    fallback_message: str = "Service temporarily unavailable"
    is_critical: bool = False  # If True, log at ERROR level


# ============================================
# RESILIENCE POLICIES TABLE
# ============================================

RESILIENCE_POLICIES: Dict[Feature, ResiliencePolicy] = {
    # AI Features - High threshold, long recovery
    Feature.AI_LESSON_PLAN: ResiliencePolicy(
        failure_threshold=5,
        window_seconds=600,  # 10 min
        open_duration_seconds=300,  # 5 min
        half_open_max_calls=2,
        fallback_message="AI lesson plan generation temporarily unavailable. Please use manual planning.",
        fallback_response={"status": "degraded", "manual_mode": True},
    ),
    
    Feature.AI_WORKSHEET: ResiliencePolicy(
        failure_threshold=5,
        window_seconds=600,
        open_duration_seconds=300,
        half_open_max_calls=2,
        fallback_message="AI worksheet generation temporarily unavailable. Please create manually.",
        fallback_response={"status": "degraded", "manual_mode": True},
    ),
    
    Feature.AI_MCQ_GENERATE: ResiliencePolicy(
        failure_threshold=5,
        window_seconds=600,
        open_duration_seconds=300,
        half_open_max_calls=2,
        fallback_message="AI MCQ generation temporarily unavailable.",
        fallback_response={"status": "degraded", "manual_mode": True},
    ),
    
    Feature.AI_DOUBT_SOLVER: ResiliencePolicy(
        failure_threshold=5,
        window_seconds=600,
        open_duration_seconds=300,
        half_open_max_calls=2,
        fallback_message="AI doubt solver temporarily unavailable. Please contact your teacher.",
        fallback_response={"status": "degraded", "contact_teacher": True},
    ),
    
    Feature.AI_INSIGHT: ResiliencePolicy(
        failure_threshold=5,
        window_seconds=600,
        open_duration_seconds=300,
        half_open_max_calls=2,
        fallback_message="AI insights temporarily unavailable. Analytics data is still accessible.",
        fallback_response={"status": "degraded", "insights": []},
    ),
    
    Feature.AI_OCR: ResiliencePolicy(
        failure_threshold=5,
        window_seconds=600,
        open_duration_seconds=300,
        half_open_max_calls=2,
        fallback_message="AI OCR temporarily unavailable. Please enter scores manually.",
        fallback_response={"status": "degraded", "manual_entry_required": True},
    ),
    
    # External Payment - Critical, lower threshold
    Feature.PAYMENT_GATEWAY: ResiliencePolicy(
        failure_threshold=3,
        window_seconds=300,  # 5 min
        open_duration_seconds=180,  # 3 min
        half_open_max_calls=1,
        fallback_message="Payment processing temporarily unavailable. Please record payment manually or try again later.",
        fallback_response={"status": "degraded", "manual_record": True},
        is_critical=True,
    ),
    
    # Notifications - Can retry later
    Feature.SMS_PROVIDER: ResiliencePolicy(
        failure_threshold=10,
        window_seconds=600,
        open_duration_seconds=300,
        half_open_max_calls=3,
        fallback_message="SMS delivery delayed. Message will be sent when service recovers.",
        fallback_response={"status": "queued", "retry_later": True},
    ),
    
    Feature.EMAIL_PROVIDER: ResiliencePolicy(
        failure_threshold=10,
        window_seconds=600,
        open_duration_seconds=300,
        half_open_max_calls=3,
        fallback_message="Email delivery delayed. Will be sent when service recovers.",
        fallback_response={"status": "queued", "retry_later": True},
    ),
    
    Feature.NOTIFICATION: ResiliencePolicy(
        failure_threshold=10,
        window_seconds=600,
        open_duration_seconds=300,
        half_open_max_calls=3,
        fallback_message="Notification delivery delayed.",
        fallback_response={"status": "queued"},
    ),
    
    # Analytics - Return last good data
    Feature.ANALYTICS: ResiliencePolicy(
        failure_threshold=5,
        window_seconds=300,
        open_duration_seconds=120,
        half_open_max_calls=3,
        fallback_message="Live analytics temporarily unavailable. Showing last available data.",
        fallback_response={"status": "degraded", "use_cache": True},
    ),
    
    # OCR Processing
    Feature.OCR_PROCESS: ResiliencePolicy(
        failure_threshold=5,
        window_seconds=600,
        open_duration_seconds=300,
        half_open_max_calls=2,
        fallback_message="OCR processing temporarily unavailable. Please enter results manually.",
        fallback_response={"status": "degraded", "manual_entry_required": True},
    ),
    
    # Export
    Feature.EXPORT: ResiliencePolicy(
        failure_threshold=5,
        window_seconds=300,
        open_duration_seconds=180,
        half_open_max_calls=2,
        fallback_message="Export generation temporarily unavailable. Please try again later.",
        fallback_response={"status": "unavailable", "retry_after_seconds": 180},
    ),
    
    # Infrastructure - Higher tolerance
    Feature.DB_READ: ResiliencePolicy(
        failure_threshold=10,
        window_seconds=60,
        open_duration_seconds=30,
        half_open_max_calls=5,
        fallback_message="Data temporarily unavailable.",
        fallback_response=None,
        is_critical=True,
    ),
    
    Feature.CACHE: ResiliencePolicy(
        failure_threshold=20,  # High tolerance
        window_seconds=60,
        open_duration_seconds=10,  # Quick recovery
        half_open_max_calls=10,
        fallback_message=None,  # Silent fallback
        fallback_response=None,  # Just bypass cache
    ),
}


def get_policy(feature: Feature) -> ResiliencePolicy:
    """Get resilience policy for a feature."""
    return RESILIENCE_POLICIES.get(feature, ResiliencePolicy(
        failure_threshold=5,
        window_seconds=300,
        open_duration_seconds=120,
        half_open_max_calls=3,
        fallback_message="Service temporarily unavailable.",
    ))
