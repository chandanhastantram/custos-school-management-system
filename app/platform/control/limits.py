"""
CUSTOS Usage Limits & Billing Hooks

Track usage against plan limits.

RULES:
1. Soft limits = warning, allow overage
2. Hard limits = block, require upgrade
3. All usage changes are audit-safe
4. No payment processing here (just signals)

USAGE:

    from app.platform.control import check_usage, record_usage, UsageType
    
    # Check before action
    result = await check_usage(tenant_id, UsageType.AI_TOKENS, amount=500)
    if result.blocked:
        return {"error": result.message}
    
    # Record after action
    await record_usage(tenant_id, UsageType.AI_TOKENS, amount=500)
"""

import logging
from enum import Enum
from typing import Dict, Optional, List, Any
from uuid import UUID
from datetime import datetime, timezone, timedelta, date
from dataclasses import dataclass, field
from threading import Lock

logger = logging.getLogger(__name__)


class UsageType(str, Enum):
    """Types of usage that can be limited."""
    # AI Usage
    AI_TOKENS = "ai_tokens"
    AI_CALLS = "ai_calls"
    AI_OCR_PAGES = "ai_ocr_pages"
    
    # Storage
    STORAGE_MB = "storage_mb"
    FILE_UPLOADS = "file_uploads"
    
    # Users
    STUDENTS = "students"
    TEACHERS = "teachers"
    PARENTS = "parents"
    
    # Operations
    SMS_SENT = "sms_sent"
    EMAILS_SENT = "emails_sent"
    API_CALLS = "api_calls"
    
    # Content
    QUESTIONS = "questions"
    ASSIGNMENTS = "assignments"
    REPORTS = "reports"


class LimitType(str, Enum):
    """Types of limits."""
    SOFT = "soft"   # Warning, allow overage
    HARD = "hard"   # Block completely


@dataclass
class UsageLimit:
    """Definition of a usage limit."""
    usage_type: UsageType
    limit: int
    limit_type: LimitType = LimitType.SOFT
    reset_period: str = "monthly"  # monthly, daily, never
    overage_rate: Optional[float] = None  # Cost per unit over limit
    warning_threshold: float = 0.8  # Warn at 80%


# Default limits by plan tier
DEFAULT_LIMITS: Dict[str, Dict[UsageType, UsageLimit]] = {
    "free": {
        UsageType.AI_TOKENS: UsageLimit(UsageType.AI_TOKENS, 1000, LimitType.HARD),
        UsageType.AI_CALLS: UsageLimit(UsageType.AI_CALLS, 10, LimitType.HARD),
        UsageType.STUDENTS: UsageLimit(UsageType.STUDENTS, 50, LimitType.HARD),
        UsageType.TEACHERS: UsageLimit(UsageType.TEACHERS, 5, LimitType.HARD),
        UsageType.STORAGE_MB: UsageLimit(UsageType.STORAGE_MB, 100, LimitType.HARD),
        UsageType.SMS_SENT: UsageLimit(UsageType.SMS_SENT, 0, LimitType.HARD),
    },
    "starter": {
        UsageType.AI_TOKENS: UsageLimit(UsageType.AI_TOKENS, 50000, LimitType.SOFT, overage_rate=0.001),
        UsageType.AI_CALLS: UsageLimit(UsageType.AI_CALLS, 500, LimitType.SOFT),
        UsageType.STUDENTS: UsageLimit(UsageType.STUDENTS, 200, LimitType.HARD),
        UsageType.TEACHERS: UsageLimit(UsageType.TEACHERS, 20, LimitType.HARD),
        UsageType.STORAGE_MB: UsageLimit(UsageType.STORAGE_MB, 1000, LimitType.SOFT),
        UsageType.SMS_SENT: UsageLimit(UsageType.SMS_SENT, 500, LimitType.SOFT, overage_rate=0.05),
    },
    "professional": {
        UsageType.AI_TOKENS: UsageLimit(UsageType.AI_TOKENS, 200000, LimitType.SOFT, overage_rate=0.0008),
        UsageType.AI_CALLS: UsageLimit(UsageType.AI_CALLS, 2000, LimitType.SOFT),
        UsageType.AI_OCR_PAGES: UsageLimit(UsageType.AI_OCR_PAGES, 500, LimitType.SOFT, overage_rate=0.1),
        UsageType.STUDENTS: UsageLimit(UsageType.STUDENTS, 1000, LimitType.HARD),
        UsageType.TEACHERS: UsageLimit(UsageType.TEACHERS, 100, LimitType.HARD),
        UsageType.STORAGE_MB: UsageLimit(UsageType.STORAGE_MB, 10000, LimitType.SOFT),
        UsageType.SMS_SENT: UsageLimit(UsageType.SMS_SENT, 2000, LimitType.SOFT, overage_rate=0.04),
    },
    "enterprise": {
        UsageType.AI_TOKENS: UsageLimit(UsageType.AI_TOKENS, 1000000, LimitType.SOFT, overage_rate=0.0005),
        UsageType.AI_CALLS: UsageLimit(UsageType.AI_CALLS, 10000, LimitType.SOFT),
        UsageType.AI_OCR_PAGES: UsageLimit(UsageType.AI_OCR_PAGES, 5000, LimitType.SOFT, overage_rate=0.08),
        UsageType.STUDENTS: UsageLimit(UsageType.STUDENTS, 10000, LimitType.SOFT),
        UsageType.TEACHERS: UsageLimit(UsageType.TEACHERS, 500, LimitType.SOFT),
        UsageType.STORAGE_MB: UsageLimit(UsageType.STORAGE_MB, 100000, LimitType.SOFT),
        UsageType.SMS_SENT: UsageLimit(UsageType.SMS_SENT, 10000, LimitType.SOFT, overage_rate=0.03),
    },
}


@dataclass
class UsageRecord:
    """Current usage for a tenant."""
    tenant_id: UUID
    usage_type: UsageType
    current_usage: int = 0
    period_start: date = field(default_factory=date.today)
    overage_amount: int = 0
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def reset_if_needed(self, reset_period: str):
        """Reset usage if period has elapsed."""
        today = date.today()
        
        if reset_period == "monthly":
            if self.period_start.month != today.month or self.period_start.year != today.year:
                self.current_usage = 0
                self.overage_amount = 0
                self.period_start = today.replace(day=1)
        elif reset_period == "daily":
            if self.period_start != today:
                self.current_usage = 0
                self.overage_amount = 0
                self.period_start = today


@dataclass
class UsageCheckResult:
    """Result of a usage check."""
    allowed: bool
    blocked: bool
    usage_type: UsageType
    current: int
    limit: int
    remaining: int
    percent_used: float
    is_warning: bool = False
    is_overage: bool = False
    overage_amount: int = 0
    overage_cost: float = 0.0
    message: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "allowed": self.allowed,
            "blocked": self.blocked,
            "usage_type": self.usage_type.value,
            "current": self.current,
            "limit": self.limit,
            "remaining": self.remaining,
            "percent_used": round(self.percent_used, 2),
            "is_warning": self.is_warning,
            "is_overage": self.is_overage,
            "overage_amount": self.overage_amount,
            "overage_cost": round(self.overage_cost, 2),
            "message": self.message,
        }


@dataclass
class BillingSignal:
    """Signal for billing system (no actual charges)."""
    tenant_id: UUID
    signal_type: str  # "overage", "limit_reached", "upgrade_needed"
    usage_type: UsageType
    amount: int
    cost: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> dict:
        return {
            "tenant_id": str(self.tenant_id),
            "signal_type": self.signal_type,
            "usage_type": self.usage_type.value,
            "amount": self.amount,
            "cost": self.cost,
            "timestamp": self.timestamp.isoformat(),
        }


class UsageLimits:
    """
    Usage limit enforcement.
    
    Tracks usage per tenant against plan limits.
    """
    
    _instance: Optional["UsageLimits"] = None
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
        
        self._usage_cache: Dict[str, UsageRecord] = {}  # key: tenant_id:usage_type
        self._billing_signals: List[BillingSignal] = []
        self._signals_lock = Lock()
        self._max_signals = 1000
        self._initialized = True
    
    def _get_cache_key(self, tenant_id: UUID, usage_type: UsageType) -> str:
        return f"{tenant_id}:{usage_type.value}"
    
    def _get_usage_record(self, tenant_id: UUID, usage_type: UsageType) -> UsageRecord:
        """Get or create usage record."""
        key = self._get_cache_key(tenant_id, usage_type)
        
        if key not in self._usage_cache:
            self._usage_cache[key] = UsageRecord(
                tenant_id=tenant_id,
                usage_type=usage_type,
            )
        
        return self._usage_cache[key]
    
    def _get_limit(self, tier: str, usage_type: UsageType) -> Optional[UsageLimit]:
        """Get limit for a tier and usage type."""
        tier_limits = DEFAULT_LIMITS.get(tier, DEFAULT_LIMITS.get("free", {}))
        return tier_limits.get(usage_type)
    
    def check_usage(
        self,
        tenant_id: UUID,
        usage_type: UsageType,
        tier: str,
        amount: int = 1,
    ) -> UsageCheckResult:
        """
        Check if usage is within limits.
        
        Does NOT record usage - just checks.
        """
        with self._lock:
            record = self._get_usage_record(tenant_id, usage_type)
            limit_def = self._get_limit(tier, usage_type)
            
            # No limit defined = unlimited
            if not limit_def:
                return UsageCheckResult(
                    allowed=True,
                    blocked=False,
                    usage_type=usage_type,
                    current=record.current_usage,
                    limit=0,
                    remaining=-1,  # Unlimited
                    percent_used=0,
                )
            
            # Reset if period elapsed
            record.reset_if_needed(limit_def.reset_period)
            
            projected = record.current_usage + amount
            limit = limit_def.limit
            remaining = max(0, limit - record.current_usage)
            percent_used = (record.current_usage / limit * 100) if limit > 0 else 0
            
            # Check if within limits
            if projected <= limit:
                is_warning = percent_used >= (limit_def.warning_threshold * 100)
                return UsageCheckResult(
                    allowed=True,
                    blocked=False,
                    usage_type=usage_type,
                    current=record.current_usage,
                    limit=limit,
                    remaining=remaining,
                    percent_used=percent_used,
                    is_warning=is_warning,
                    message="Approaching limit" if is_warning else None,
                )
            
            # Over limit
            overage = projected - limit
            overage_cost = overage * (limit_def.overage_rate or 0)
            
            if limit_def.limit_type == LimitType.HARD:
                return UsageCheckResult(
                    allowed=False,
                    blocked=True,
                    usage_type=usage_type,
                    current=record.current_usage,
                    limit=limit,
                    remaining=remaining,
                    percent_used=percent_used,
                    message=f"Usage limit reached ({record.current_usage}/{limit}). Upgrade to continue.",
                )
            
            # Soft limit - allowed with overage
            return UsageCheckResult(
                allowed=True,
                blocked=False,
                usage_type=usage_type,
                current=record.current_usage,
                limit=limit,
                remaining=0,
                percent_used=percent_used,
                is_overage=True,
                overage_amount=overage,
                overage_cost=overage_cost,
                message=f"Over limit by {overage}. Overage charges may apply.",
            )
    
    def record_usage(
        self,
        tenant_id: UUID,
        usage_type: UsageType,
        tier: str,
        amount: int = 1,
    ) -> UsageCheckResult:
        """
        Record usage and return updated status.
        
        Also generates billing signals if needed.
        """
        with self._lock:
            record = self._get_usage_record(tenant_id, usage_type)
            limit_def = self._get_limit(tier, usage_type)
            
            if limit_def:
                record.reset_if_needed(limit_def.reset_period)
            
            record.current_usage += amount
            record.last_updated = datetime.now(timezone.utc)
            
            # Calculate status
            result = self.check_usage(tenant_id, usage_type, tier, 0)
            
            # Generate billing signals
            if result.is_overage and limit_def and limit_def.overage_rate:
                self._add_billing_signal(BillingSignal(
                    tenant_id=tenant_id,
                    signal_type="overage",
                    usage_type=usage_type,
                    amount=amount,
                    cost=amount * limit_def.overage_rate,
                ))
            
            if result.blocked:
                self._add_billing_signal(BillingSignal(
                    tenant_id=tenant_id,
                    signal_type="limit_reached",
                    usage_type=usage_type,
                    amount=record.current_usage,
                    cost=0,
                ))
            
            return result
    
    def get_usage_summary(self, tenant_id: UUID, tier: str) -> Dict[str, dict]:
        """Get usage summary for all tracked types."""
        summary = {}
        
        for usage_type in UsageType:
            key = self._get_cache_key(tenant_id, usage_type)
            if key in self._usage_cache:
                result = self.check_usage(tenant_id, usage_type, tier, 0)
                summary[usage_type.value] = result.to_dict()
        
        return summary
    
    def reset_usage(self, tenant_id: UUID, usage_type: Optional[UsageType] = None):
        """Reset usage for a tenant (all types or specific)."""
        with self._lock:
            if usage_type:
                key = self._get_cache_key(tenant_id, usage_type)
                if key in self._usage_cache:
                    del self._usage_cache[key]
            else:
                keys_to_delete = [
                    k for k in self._usage_cache
                    if k.startswith(str(tenant_id))
                ]
                for key in keys_to_delete:
                    del self._usage_cache[key]
    
    def _add_billing_signal(self, signal: BillingSignal):
        """Add a billing signal."""
        with self._signals_lock:
            self._billing_signals.append(signal)
            if len(self._billing_signals) > self._max_signals:
                self._billing_signals.pop(0)
    
    def get_billing_signals(
        self,
        tenant_id: Optional[UUID] = None,
        limit: int = 100,
    ) -> List[dict]:
        """Get recent billing signals."""
        with self._signals_lock:
            signals = self._billing_signals[-limit:]
            if tenant_id:
                signals = [s for s in signals if s.tenant_id == tenant_id]
            return [s.to_dict() for s in signals]
    
    def clear_billing_signals(self):
        """Clear billing signals (after processing)."""
        with self._signals_lock:
            self._billing_signals.clear()


# Global instance
_limits: Optional[UsageLimits] = None


def get_limits() -> UsageLimits:
    """Get the global usage limits instance."""
    global _limits
    if _limits is None:
        _limits = UsageLimits()
    return _limits


async def check_usage(
    tenant_id: UUID,
    usage_type: UsageType,
    amount: int = 1,
    tier: str = "free",
) -> UsageCheckResult:
    """
    Check if usage is within limits.
    
    Does NOT record usage.
    """
    return get_limits().check_usage(tenant_id, usage_type, tier, amount)


async def record_usage(
    tenant_id: UUID,
    usage_type: UsageType,
    amount: int = 1,
    tier: str = "free",
) -> UsageCheckResult:
    """
    Record usage and return updated status.
    
    Also generates billing signals if needed.
    """
    return get_limits().record_usage(tenant_id, usage_type, tier, amount)


async def get_usage_summary(tenant_id: UUID, tier: str = "free") -> Dict[str, dict]:
    """Get usage summary for a tenant."""
    return get_limits().get_usage_summary(tenant_id, tier)
