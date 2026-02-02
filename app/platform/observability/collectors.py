"""
CUSTOS Observability Collectors

Periodic aggregation and storage of metrics.

Handles:
- Metric window rotation
- Historical aggregation
- Alert threshold checks
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID
from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession

from app.platform.observability.metrics import get_metrics_collector, TenantMetrics
from app.platform.observability.snapshots import (
    get_snapshot_service,
    HealthStatus,
)

logger = logging.getLogger(__name__)


@dataclass
class MetricAlert:
    """Alert generated from metric threshold breach."""
    alert_type: str
    tenant_id: Optional[UUID]
    severity: str  # info, warning, critical
    message: str
    metric_name: str
    current_value: float
    threshold: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> dict:
        return {
            "alert_type": self.alert_type,
            "tenant_id": str(self.tenant_id) if self.tenant_id else "platform",
            "severity": self.severity,
            "message": self.message,
            "metric_name": self.metric_name,
            "current_value": self.current_value,
            "threshold": self.threshold,
            "timestamp": self.timestamp.isoformat(),
        }


class AlertThresholds:
    """Alert threshold configuration."""
    
    # Error rate thresholds
    ERROR_RATE_WARNING = 0.05      # 5%
    ERROR_RATE_CRITICAL = 0.15    # 15%
    
    # Response time thresholds (ms)
    RESPONSE_TIME_WARNING = 500
    RESPONSE_TIME_CRITICAL = 2000
    
    # AI usage thresholds (% of quota)
    AI_QUOTA_WARNING = 80
    AI_QUOTA_CRITICAL = 95
    
    # Circuit breaker thresholds
    CIRCUIT_OPENS_WARNING = 3
    CIRCUIT_OPENS_CRITICAL = 5


class MetricAggregator:
    """
    Aggregates metrics for historical storage.
    
    Compacts 5-minute windows into hourly/daily summaries.
    """
    
    def __init__(self):
        self._hourly_aggregates: Dict[str, Dict] = {}
        self._daily_aggregates: Dict[str, Dict] = {}
    
    def aggregate_window(self, tenant_id: UUID, metrics: TenantMetrics) -> dict:
        """
        Aggregate a metrics window into a storable summary.
        
        Called at the end of each metric window.
        """
        return {
            "tenant_id": str(tenant_id),
            "window_start": metrics.window_start.isoformat(),
            "window_end": datetime.now(timezone.utc).isoformat(),
            "request_count": metrics.request_count,
            "error_count": metrics.error_count,
            "error_rate": metrics.error_rate,
            "ai_calls": metrics.ai_call_count,
            "ai_tokens": metrics.ai_tokens_used,
            "cache_hit_ratio": metrics.cache_hit_ratio,
            "avg_response_time_ms": metrics.avg_response_time_ms,
            "p95_response_time_ms": metrics.p95_response_time_ms,
        }
    
    def get_hourly_summary(self, tenant_id: UUID, hour: datetime) -> Optional[dict]:
        """Get hourly summary for a tenant."""
        key = f"{tenant_id}:{hour.strftime('%Y%m%d%H')}"
        return self._hourly_aggregates.get(key)


class AlertChecker:
    """
    Checks metrics against thresholds and generates alerts.
    """
    
    def __init__(self):
        self._recent_alerts: List[MetricAlert] = []
        self._max_alerts = 100
    
    def check_tenant_metrics(self, tenant_id: UUID, metrics: dict) -> List[MetricAlert]:
        """
        Check tenant metrics against thresholds.
        
        Returns list of generated alerts.
        """
        alerts = []
        counters = metrics.get("counters", {})
        rates = metrics.get("rates", {})
        response_times = metrics.get("response_times", {})
        
        # Error rate check
        error_rate = rates.get("error_rate", 0)
        if error_rate >= AlertThresholds.ERROR_RATE_CRITICAL:
            alerts.append(MetricAlert(
                alert_type="error_rate",
                tenant_id=tenant_id,
                severity="critical",
                message=f"Critical error rate: {error_rate:.1%}",
                metric_name="error_rate",
                current_value=error_rate,
                threshold=AlertThresholds.ERROR_RATE_CRITICAL,
            ))
        elif error_rate >= AlertThresholds.ERROR_RATE_WARNING:
            alerts.append(MetricAlert(
                alert_type="error_rate",
                tenant_id=tenant_id,
                severity="warning",
                message=f"High error rate: {error_rate:.1%}",
                metric_name="error_rate",
                current_value=error_rate,
                threshold=AlertThresholds.ERROR_RATE_WARNING,
            ))
        
        # Response time check
        p95_rt = response_times.get("p95_ms", 0)
        if p95_rt >= AlertThresholds.RESPONSE_TIME_CRITICAL:
            alerts.append(MetricAlert(
                alert_type="response_time",
                tenant_id=tenant_id,
                severity="critical",
                message=f"Critical response time: {p95_rt:.0f}ms (p95)",
                metric_name="p95_response_time_ms",
                current_value=p95_rt,
                threshold=AlertThresholds.RESPONSE_TIME_CRITICAL,
            ))
        elif p95_rt >= AlertThresholds.RESPONSE_TIME_WARNING:
            alerts.append(MetricAlert(
                alert_type="response_time",
                tenant_id=tenant_id,
                severity="warning",
                message=f"Slow response time: {p95_rt:.0f}ms (p95)",
                metric_name="p95_response_time_ms",
                current_value=p95_rt,
                threshold=AlertThresholds.RESPONSE_TIME_WARNING,
            ))
        
        # Circuit opens check
        circuit_opens = counters.get("circuit_opens", 0)
        if circuit_opens >= AlertThresholds.CIRCUIT_OPENS_CRITICAL:
            alerts.append(MetricAlert(
                alert_type="circuit_opens",
                tenant_id=tenant_id,
                severity="critical",
                message=f"Multiple circuit breakers opened: {circuit_opens}",
                metric_name="circuit_opens",
                current_value=circuit_opens,
                threshold=AlertThresholds.CIRCUIT_OPENS_CRITICAL,
            ))
        
        # Store alerts
        for alert in alerts:
            self._add_alert(alert)
        
        return alerts
    
    def check_platform_health(self, snapshot: dict) -> List[MetricAlert]:
        """Check platform-wide health."""
        alerts = []
        
        tenant_health = snapshot.get("tenant_health", {})
        unhealthy = tenant_health.get("unhealthy", 0)
        total = tenant_health.get("total", 1)
        
        if total > 0 and unhealthy / total > 0.1:  # >10% unhealthy
            alerts.append(MetricAlert(
                alert_type="platform_health",
                tenant_id=None,
                severity="critical",
                message=f"High proportion of unhealthy tenants: {unhealthy}/{total}",
                metric_name="unhealthy_tenant_ratio",
                current_value=unhealthy / total,
                threshold=0.1,
            ))
        
        for alert in alerts:
            self._add_alert(alert)
        
        return alerts
    
    def _add_alert(self, alert: MetricAlert):
        """Add alert to recent list."""
        self._recent_alerts.append(alert)
        if len(self._recent_alerts) > self._max_alerts:
            self._recent_alerts.pop(0)
    
    def get_recent_alerts(self, limit: int = 50) -> List[dict]:
        """Get recent alerts."""
        return [a.to_dict() for a in self._recent_alerts[-limit:]]
    
    def get_alerts_by_severity(self, severity: str) -> List[dict]:
        """Get alerts filtered by severity."""
        return [
            a.to_dict() for a in self._recent_alerts
            if a.severity == severity
        ]


class ObservabilityCollector:
    """
    Main collector that orchestrates metric collection.
    
    Can be run as a background task or called periodically.
    """
    
    def __init__(self):
        self._metrics = get_metrics_collector()
        self._snapshots = get_snapshot_service()
        self._aggregator = MetricAggregator()
        self._alerts = AlertChecker()
    
    async def collect_and_check(self) -> dict:
        """
        Perform a collection cycle.
        
        1. Get current metrics
        2. Check thresholds
        3. Generate alerts if needed
        
        Returns summary of collection.
        """
        now = datetime.now(timezone.utc)
        
        # Get all tenant metrics
        all_metrics = self._metrics.get_all_tenant_metrics()
        
        alerts_generated = []
        
        # Check each tenant
        for tm in all_metrics:
            tenant_id = UUID(tm["tenant_id"]) if tm.get("tenant_id") else None
            if tenant_id:
                tenant_alerts = self._alerts.check_tenant_metrics(tenant_id, tm)
                alerts_generated.extend(tenant_alerts)
        
        # Check platform health
        platform_snapshot = self._snapshots.get_platform_snapshot()
        platform_alerts = self._alerts.check_platform_health(platform_snapshot)
        alerts_generated.extend(platform_alerts)
        
        return {
            "timestamp": now.isoformat(),
            "tenants_checked": len(all_metrics),
            "alerts_generated": len(alerts_generated),
            "alerts": [a.to_dict() for a in alerts_generated],
        }
    
    def get_collection_status(self) -> dict:
        """Get status of the collector."""
        return {
            "platform_metrics": self._metrics.get_platform_metrics(),
            "recent_alerts": self._alerts.get_recent_alerts(20),
            "feature_health": self._snapshots.get_feature_health_summary(),
        }


# Global instances
_aggregator: Optional[MetricAggregator] = None
_alert_checker: Optional[AlertChecker] = None
_collector: Optional[ObservabilityCollector] = None


def get_alert_checker() -> AlertChecker:
    """Get the global alert checker."""
    global _alert_checker
    if _alert_checker is None:
        _alert_checker = AlertChecker()
    return _alert_checker


def get_observability_collector() -> ObservabilityCollector:
    """Get the global observability collector."""
    global _collector
    if _collector is None:
        _collector = ObservabilityCollector()
    return _collector
