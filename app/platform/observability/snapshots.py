"""
CUSTOS Tenant Health Snapshots

Point-in-time health status per tenant.

Combines:
- Circuit breaker states
- Error rates
- Resource usage
- Capacity limits
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from uuid import UUID
from dataclasses import dataclass, field
from enum import Enum
from threading import Lock

from app.core.resilience import (
    Feature,
    CircuitState,
    get_state_manager,
    get_resilience_health,
)
from app.platform.observability.metrics import get_metrics_collector

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Overall health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"


class FeatureStatus(str, Enum):
    """Per-feature status."""
    AVAILABLE = "available"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


@dataclass
class FeatureHealth:
    """Health status for a single feature."""
    feature: str
    status: FeatureStatus
    circuit_state: str
    recent_failures: int
    threshold: int
    last_failure: Optional[str] = None


@dataclass
class TenantHealthSnapshot:
    """
    Point-in-time health snapshot for a tenant.
    
    Provides a complete view of:
    - Overall health status
    - Per-feature availability
    - Resource usage
    - Limit warnings
    """
    tenant_id: UUID
    timestamp: datetime
    
    # Overall status
    status: HealthStatus
    status_message: str
    
    # Feature health
    features: List[FeatureHealth] = field(default_factory=list)
    degraded_features: List[str] = field(default_factory=list)
    unavailable_features: List[str] = field(default_factory=list)
    
    # Metrics summary
    request_count: int = 0
    error_count: int = 0
    error_rate: float = 0.0
    ai_tokens_used: int = 0
    cache_hit_ratio: float = 0.0
    avg_response_time_ms: float = 0.0
    
    # Capacity/limits
    ai_quota_used_pct: float = 0.0
    approaching_limits: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "tenant_id": str(self.tenant_id),
            "timestamp": self.timestamp.isoformat(),
            "status": self.status.value,
            "status_message": self.status_message,
            "features": {
                "total": len(self.features),
                "degraded": self.degraded_features,
                "unavailable": self.unavailable_features,
                "details": [
                    {
                        "feature": f.feature,
                        "status": f.status.value,
                        "circuit_state": f.circuit_state,
                        "recent_failures": f.recent_failures,
                        "threshold": f.threshold,
                    }
                    for f in self.features
                ],
            },
            "metrics": {
                "request_count": self.request_count,
                "error_count": self.error_count,
                "error_rate": round(self.error_rate, 4),
                "ai_tokens_used": self.ai_tokens_used,
                "cache_hit_ratio": round(self.cache_hit_ratio, 3),
                "avg_response_time_ms": round(self.avg_response_time_ms, 2),
            },
            "capacity": {
                "ai_quota_used_pct": round(self.ai_quota_used_pct, 2),
                "approaching_limits": self.approaching_limits,
            },
        }


class HealthSnapshotService:
    """
    Service for generating tenant health snapshots.
    
    Aggregates data from:
    - Circuit breakers
    - Metrics collector
    - Quota tracking
    """
    
    def __init__(self):
        self._state_manager = get_state_manager()
        self._metrics = get_metrics_collector()
    
    def get_tenant_snapshot(self, tenant_id: UUID) -> TenantHealthSnapshot:
        """
        Generate health snapshot for a specific tenant.
        
        Combines circuit breaker state and metrics for complete picture.
        """
        now = datetime.now(timezone.utc)
        
        # Get circuit breaker states
        circuit_states = self._state_manager.get_all_states()
        features = []
        degraded = []
        unavailable = []
        
        for feature_name, state in circuit_states.items():
            circuit_state = state["state"]
            
            if circuit_state == "open":
                status = FeatureStatus.UNAVAILABLE
                unavailable.append(feature_name)
            elif circuit_state == "half_open":
                status = FeatureStatus.DEGRADED
                degraded.append(feature_name)
            else:
                status = FeatureStatus.AVAILABLE
            
            features.append(FeatureHealth(
                feature=feature_name,
                status=status,
                circuit_state=circuit_state,
                recent_failures=state.get("recent_failures", 0),
                threshold=state.get("threshold", 5),
                last_failure=state.get("last_failure"),
            ))
        
        # Get metrics
        metrics = self._metrics.get_tenant_metrics(tenant_id)
        
        counters = metrics.get("counters", {})
        rates = metrics.get("rates", {})
        response_times = metrics.get("response_times", {})
        
        # Calculate overall status
        status, status_message = self._calculate_overall_status(
            unavailable_count=len(unavailable),
            degraded_count=len(degraded),
            error_rate=rates.get("error_rate", 0),
        )
        
        # Check limits
        approaching_limits = []
        ai_quota_pct = 0.0
        
        # Could add actual quota checking here
        if counters.get("ai_tokens", 0) > 80000:  # 80% of 100k default
            approaching_limits.append("ai_token_quota")
            ai_quota_pct = min(counters.get("ai_tokens", 0) / 100000 * 100, 100)
        
        return TenantHealthSnapshot(
            tenant_id=tenant_id,
            timestamp=now,
            status=status,
            status_message=status_message,
            features=features,
            degraded_features=degraded,
            unavailable_features=unavailable,
            request_count=counters.get("requests", 0),
            error_count=counters.get("errors", 0),
            error_rate=rates.get("error_rate", 0),
            ai_tokens_used=counters.get("ai_tokens", 0),
            cache_hit_ratio=rates.get("cache_hit_ratio", 0),
            avg_response_time_ms=response_times.get("avg_ms", 0),
            ai_quota_used_pct=ai_quota_pct,
            approaching_limits=approaching_limits,
        )
    
    def _calculate_overall_status(
        self,
        unavailable_count: int,
        degraded_count: int,
        error_rate: float,
    ) -> tuple:
        """Calculate overall health status."""
        if unavailable_count >= 3 or error_rate > 0.3:
            return HealthStatus.CRITICAL, "Multiple features unavailable or very high error rate"
        
        if unavailable_count > 0:
            return HealthStatus.UNHEALTHY, f"{unavailable_count} feature(s) unavailable"
        
        if degraded_count > 0 or error_rate > 0.1:
            return HealthStatus.DEGRADED, f"{degraded_count} feature(s) degraded"
        
        return HealthStatus.HEALTHY, "All systems operational"
    
    def get_platform_snapshot(self) -> dict:
        """
        Generate platform-wide health snapshot.
        
        Aggregates across all tenants for admin view.
        """
        now = datetime.now(timezone.utc)
        
        # Get resilience health
        resilience = get_resilience_health()
        
        # Get platform metrics
        platform_metrics = self._metrics.get_platform_metrics()
        
        # Get tenant breakdown
        all_tenant_metrics = self._metrics.get_all_tenant_metrics()
        
        # Count tenants by health
        healthy_tenants = 0
        degraded_tenants = 0
        unhealthy_tenants = 0
        
        for tm in all_tenant_metrics:
            error_rate = tm.get("rates", {}).get("error_rate", 0)
            if error_rate > 0.2:
                unhealthy_tenants += 1
            elif error_rate > 0.05:
                degraded_tenants += 1
            else:
                healthy_tenants += 1
        
        # Overall platform status
        if resilience.get("degraded_count", 0) > 3:
            status = HealthStatus.CRITICAL
        elif resilience.get("degraded_count", 0) > 0:
            status = HealthStatus.DEGRADED
        elif unhealthy_tenants > 0:
            status = HealthStatus.DEGRADED
        else:
            status = HealthStatus.HEALTHY
        
        return {
            "timestamp": now.isoformat(),
            "status": status.value,
            "resilience": resilience,
            "platform_metrics": platform_metrics,
            "tenant_health": {
                "total": len(all_tenant_metrics),
                "healthy": healthy_tenants,
                "degraded": degraded_tenants,
                "unhealthy": unhealthy_tenants,
            },
        }
    
    def get_degraded_tenants(self) -> List[dict]:
        """Get list of tenants currently experiencing issues."""
        all_metrics = self._metrics.get_all_tenant_metrics()
        
        degraded = []
        for tm in all_metrics:
            error_rate = tm.get("rates", {}).get("error_rate", 0)
            if error_rate > 0.05:  # >5% error rate
                degraded.append({
                    "tenant_id": tm.get("tenant_id"),
                    "error_rate": error_rate,
                    "error_count": tm.get("counters", {}).get("errors", 0),
                    "request_count": tm.get("counters", {}).get("requests", 0),
                    "top_errors": tm.get("top_errors", {}),
                })
        
        return sorted(degraded, key=lambda x: x["error_rate"], reverse=True)
    
    def get_feature_health_summary(self) -> dict:
        """Get summary of feature health across platform."""
        circuit_states = self._state_manager.get_all_states()
        
        summary = {
            "total_features": len(circuit_states),
            "available": 0,
            "degraded": 0,
            "unavailable": 0,
            "features": {},
        }
        
        for feature_name, state in circuit_states.items():
            circuit_state = state["state"]
            
            if circuit_state == "open":
                summary["unavailable"] += 1
                status = "unavailable"
            elif circuit_state == "half_open":
                summary["degraded"] += 1
                status = "degraded"
            else:
                summary["available"] += 1
                status = "available"
            
            summary["features"][feature_name] = {
                "status": status,
                "circuit_state": circuit_state,
                "recent_failures": state.get("recent_failures", 0),
            }
        
        return summary


# Global service instance
_snapshot_service: Optional[HealthSnapshotService] = None


def get_snapshot_service() -> HealthSnapshotService:
    """Get the global health snapshot service."""
    global _snapshot_service
    if _snapshot_service is None:
        _snapshot_service = HealthSnapshotService()
    return _snapshot_service
