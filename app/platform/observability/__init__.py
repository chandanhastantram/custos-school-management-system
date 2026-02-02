"""
CUSTOS Platform Observability

Lightweight observability for multi-tenant SaaS.

FEATURES:
- Per-tenant metrics collection
- Feature health snapshots
- Alert threshold checking
- Platform admin APIs

USAGE:

1. Record metrics:

    from app.platform.observability import record_request, record_ai_call
    
    # In middleware or endpoint
    record_request(
        tenant_id=request.state.tenant_id,
        endpoint="/api/v1/lesson-plans",
        response_time_ms=response.elapsed_ms,
        is_error=response.status_code >= 400,
    )
    
    # In AI service
    record_ai_call(
        tenant_id=tenant_id,
        tokens_used=response.usage.total_tokens,
        feature="lesson_plan",
    )

2. Get tenant health:

    from app.platform.observability import get_snapshot_service
    
    service = get_snapshot_service()
    snapshot = service.get_tenant_snapshot(tenant_id)
    print(snapshot.status)  # HealthStatus.HEALTHY

3. Check alerts:

    from app.platform.observability import get_alert_checker
    
    alerts = get_alert_checker()
    critical = alerts.get_alerts_by_severity("critical")
"""

# Metrics
from app.platform.observability.metrics import (
    MetricType,
    TenantMetrics,
    MetricsCollector,
    get_metrics_collector,
    record_request,
    record_ai_call,
    record_cache_access,
    record_circuit_open,
)

# Snapshots
from app.platform.observability.snapshots import (
    HealthStatus,
    FeatureStatus,
    FeatureHealth,
    TenantHealthSnapshot,
    HealthSnapshotService,
    get_snapshot_service,
)

# Collectors
from app.platform.observability.collectors import (
    MetricAlert,
    AlertThresholds,
    MetricAggregator,
    AlertChecker,
    ObservabilityCollector,
    get_alert_checker,
    get_observability_collector,
)

# Note: Router is imported separately to avoid circular dependencies
# from app.platform.observability.router import router as observability_router

__all__ = [
    # Metrics
    "MetricType",
    "TenantMetrics",
    "MetricsCollector",
    "get_metrics_collector",
    "record_request",
    "record_ai_call",
    "record_cache_access",
    "record_circuit_open",
    # Snapshots
    "HealthStatus",
    "FeatureStatus",
    "FeatureHealth",
    "TenantHealthSnapshot",
    "HealthSnapshotService",
    "get_snapshot_service",
    # Collectors
    "MetricAlert",
    "AlertThresholds",
    "MetricAggregator",
    "AlertChecker",
    "ObservabilityCollector",
    "get_alert_checker",
    "get_observability_collector",
]
