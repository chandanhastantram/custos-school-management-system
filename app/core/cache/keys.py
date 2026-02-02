"""
CUSTOS Cache Keys

Canonical cache key generation.

RULES:
- All keys MUST include tenant_id
- Keys must be deterministic
- Keys must be human-readable for debugging
"""

from uuid import UUID
from typing import Optional
from datetime import date


# Key prefixes by domain
class CachePrefix:
    """Cache key prefixes by domain."""
    SYLLABUS = "syllabus"
    TIMETABLE = "timetable"
    CALENDAR = "calendar"
    FEE = "fee"
    ANALYTICS = "analytics"
    QUOTA = "quota"
    CLASS = "class"
    SUBJECT = "subject"


class CacheKeys:
    """
    Canonical cache key builders.
    
    All keys follow pattern: custos:{tenant}:{domain}:{specific}
    """
    
    @staticmethod
    def _base(tenant_id: UUID, prefix: str) -> str:
        """Base key with tenant."""
        return f"custos:{tenant_id}:{prefix}"
    
    # ============================================
    # Syllabus Keys (TTL: 24h)
    # ============================================
    
    @staticmethod
    def syllabus_tree(tenant_id: UUID, board_id: UUID) -> str:
        """
        Full syllabus tree for a board.
        
        TTL: 24 hours
        Invalidate on: syllabus create/update/delete
        """
        return f"custos:{tenant_id}:{CachePrefix.SYLLABUS}:tree:{board_id}"
    
    @staticmethod
    def syllabus_by_class(tenant_id: UUID, class_id: UUID, subject_id: UUID) -> str:
        """
        Syllabus for specific class + subject.
        
        TTL: 24 hours
        Invalidate on: syllabus update for this class/subject
        """
        return f"custos:{tenant_id}:{CachePrefix.SYLLABUS}:class:{class_id}:subject:{subject_id}"
    
    @staticmethod
    def syllabus_topics(tenant_id: UUID, syllabus_id: UUID) -> str:
        """
        Topics for a specific syllabus.
        
        TTL: 24 hours
        """
        return f"custos:{tenant_id}:{CachePrefix.SYLLABUS}:topics:{syllabus_id}"
    
    @staticmethod
    def syllabus_pattern(tenant_id: UUID) -> str:
        """Pattern to invalidate all syllabus cache for tenant."""
        return f"custos:{tenant_id}:{CachePrefix.SYLLABUS}:*"
    
    # ============================================
    # Timetable Keys (TTL: 6h)
    # ============================================
    
    @staticmethod
    def timetable_class_week(
        tenant_id: UUID,
        class_id: UUID,
        week_start: date,
    ) -> str:
        """
        Timetable for a class for a specific week.
        
        TTL: 6 hours
        Invalidate on: timetable/schedule changes
        """
        return f"custos:{tenant_id}:{CachePrefix.TIMETABLE}:class:{class_id}:week:{week_start.isoformat()}"
    
    @staticmethod
    def timetable_teacher_week(
        tenant_id: UUID,
        teacher_id: UUID,
        week_start: date,
    ) -> str:
        """
        Timetable for a teacher for a specific week.
        
        TTL: 6 hours
        """
        return f"custos:{tenant_id}:{CachePrefix.TIMETABLE}:teacher:{teacher_id}:week:{week_start.isoformat()}"
    
    @staticmethod
    def timetable_pattern(tenant_id: UUID) -> str:
        """Pattern to invalidate all timetable cache for tenant."""
        return f"custos:{tenant_id}:{CachePrefix.TIMETABLE}:*"
    
    @staticmethod
    def timetable_class_pattern(tenant_id: UUID, class_id: UUID) -> str:
        """Pattern to invalidate all timetable cache for a class."""
        return f"custos:{tenant_id}:{CachePrefix.TIMETABLE}:class:{class_id}:*"
    
    # ============================================
    # Calendar Keys (TTL: 12h)
    # ============================================
    
    @staticmethod
    def calendar_academic_year(tenant_id: UUID, year_id: UUID) -> str:
        """
        Academic calendar for a year.
        
        TTL: 12 hours
        """
        return f"custos:{tenant_id}:{CachePrefix.CALENDAR}:year:{year_id}"
    
    @staticmethod
    def calendar_events_month(
        tenant_id: UUID,
        year: int,
        month: int,
    ) -> str:
        """
        Calendar events for a month.
        
        TTL: 12 hours
        """
        return f"custos:{tenant_id}:{CachePrefix.CALENDAR}:events:{year}:{month:02d}"
    
    @staticmethod
    def calendar_pattern(tenant_id: UUID) -> str:
        """Pattern to invalidate all calendar cache for tenant."""
        return f"custos:{tenant_id}:{CachePrefix.CALENDAR}:*"
    
    # ============================================
    # Fee Structure Keys (TTL: 6h)
    # ============================================
    
    @staticmethod
    def fee_structure(tenant_id: UUID, class_id: UUID, year_id: UUID) -> str:
        """
        Fee structure for a class/year.
        
        TTL: 6 hours
        """
        return f"custos:{tenant_id}:{CachePrefix.FEE}:structure:{class_id}:{year_id}"
    
    @staticmethod
    def fee_components(tenant_id: UUID) -> str:
        """
        All fee components for tenant.
        
        TTL: 6 hours
        """
        return f"custos:{tenant_id}:{CachePrefix.FEE}:components"
    
    @staticmethod
    def fee_pattern(tenant_id: UUID) -> str:
        """Pattern to invalidate all fee cache for tenant."""
        return f"custos:{tenant_id}:{CachePrefix.FEE}:*"
    
    # ============================================
    # Analytics Snapshot Keys (TTL: 1h)
    # ============================================
    
    @staticmethod
    def analytics_snapshot(tenant_id: UUID, snapshot_id: UUID) -> str:
        """
        Individual analytics snapshot.
        
        TTL: 1 hour
        """
        return f"custos:{tenant_id}:{CachePrefix.ANALYTICS}:snapshot:{snapshot_id}"
    
    @staticmethod
    def analytics_class_latest(tenant_id: UUID, class_id: UUID) -> str:
        """
        Latest analytics for a class.
        
        TTL: 1 hour
        """
        return f"custos:{tenant_id}:{CachePrefix.ANALYTICS}:class:{class_id}:latest"
    
    @staticmethod
    def analytics_pattern(tenant_id: UUID) -> str:
        """Pattern to invalidate all analytics cache for tenant."""
        return f"custos:{tenant_id}:{CachePrefix.ANALYTICS}:*"
    
    # ============================================
    # Quota Keys (TTL: 5min)
    # ============================================
    
    @staticmethod
    def ai_quota(tenant_id: UUID) -> str:
        """
        AI quota status for tenant.
        
        TTL: 5 minutes
        """
        return f"custos:{tenant_id}:{CachePrefix.QUOTA}:ai"
    
    @staticmethod
    def insights_quota(tenant_id: UUID) -> str:
        """
        Insights quota for tenant.
        
        TTL: 5 minutes
        """
        return f"custos:{tenant_id}:{CachePrefix.QUOTA}:insights"
    
    # ============================================
    # Class/Subject Keys (TTL: 1h)
    # ============================================
    
    @staticmethod
    def class_list(tenant_id: UUID) -> str:
        """
        List of all classes for tenant.
        
        TTL: 1 hour
        """
        return f"custos:{tenant_id}:{CachePrefix.CLASS}:list"
    
    @staticmethod
    def class_detail(tenant_id: UUID, class_id: UUID) -> str:
        """
        Class detail.
        
        TTL: 1 hour
        """
        return f"custos:{tenant_id}:{CachePrefix.CLASS}:detail:{class_id}"
    
    @staticmethod
    def subject_list(tenant_id: UUID) -> str:
        """
        List of all subjects for tenant.
        
        TTL: 1 hour
        """
        return f"custos:{tenant_id}:{CachePrefix.SUBJECT}:list"


# TTL Constants (in seconds)
class CacheTTL:
    """Cache TTL values in seconds."""
    SYLLABUS = 86400      # 24 hours
    TIMETABLE = 21600     # 6 hours
    CALENDAR = 43200      # 12 hours
    FEE = 21600           # 6 hours
    ANALYTICS = 3600      # 1 hour
    QUOTA = 300           # 5 minutes
    CLASS_SUBJECT = 3600  # 1 hour
    SHORT = 300           # 5 minutes
    MEDIUM = 3600         # 1 hour
    LONG = 86400          # 24 hours
