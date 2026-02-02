"""
CUSTOS Cache Invalidation

Event-based cache invalidation.

RULES:
- Soft delete → invalidate
- Updates → invalidate
- No silent stale reads
"""

import logging
from typing import Optional
from uuid import UUID
from enum import Enum

from app.core.cache.backend import get_cache
from app.core.cache.keys import CacheKeys

logger = logging.getLogger(__name__)


class CacheEvent(str, Enum):
    """Events that trigger cache invalidation."""
    # Syllabus
    SYLLABUS_CREATED = "syllabus_created"
    SYLLABUS_UPDATED = "syllabus_updated"
    SYLLABUS_DELETED = "syllabus_deleted"
    TOPIC_CREATED = "topic_created"
    TOPIC_UPDATED = "topic_updated"
    TOPIC_DELETED = "topic_deleted"
    
    # Timetable
    TIMETABLE_CREATED = "timetable_created"
    TIMETABLE_UPDATED = "timetable_updated"
    TIMETABLE_DELETED = "timetable_deleted"
    SCHEDULE_UPDATED = "schedule_updated"
    
    # Calendar
    CALENDAR_EVENT_CREATED = "calendar_event_created"
    CALENDAR_EVENT_UPDATED = "calendar_event_updated"
    CALENDAR_EVENT_DELETED = "calendar_event_deleted"
    
    # Fee
    FEE_STRUCTURE_UPDATED = "fee_structure_updated"
    FEE_COMPONENT_UPDATED = "fee_component_updated"
    
    # Analytics
    ANALYTICS_SNAPSHOT_GENERATED = "analytics_snapshot_generated"
    
    # Class/Subject
    CLASS_CREATED = "class_created"
    CLASS_UPDATED = "class_updated"
    CLASS_DELETED = "class_deleted"
    SUBJECT_CREATED = "subject_created"
    SUBJECT_UPDATED = "subject_updated"
    SUBJECT_DELETED = "subject_deleted"


class CacheInvalidator:
    """
    Cache invalidation handler.
    
    Call when data changes to ensure cache consistency.
    """
    
    @staticmethod
    async def invalidate(
        event: CacheEvent,
        tenant_id: UUID,
        entity_id: Optional[UUID] = None,
        class_id: Optional[UUID] = None,
        subject_id: Optional[UUID] = None,
        **kwargs,
    ) -> int:
        """
        Invalidate cache based on event.
        
        Returns count of invalidated keys.
        """
        cache = await get_cache()
        if not cache.is_connected:
            return 0
        
        total_invalidated = 0
        
        # Route to appropriate handler
        if event in [
            CacheEvent.SYLLABUS_CREATED,
            CacheEvent.SYLLABUS_UPDATED,
            CacheEvent.SYLLABUS_DELETED,
            CacheEvent.TOPIC_CREATED,
            CacheEvent.TOPIC_UPDATED,
            CacheEvent.TOPIC_DELETED,
        ]:
            total_invalidated += await CacheInvalidator._invalidate_syllabus(
                tenant_id, entity_id, class_id, subject_id
            )
        
        elif event in [
            CacheEvent.TIMETABLE_CREATED,
            CacheEvent.TIMETABLE_UPDATED,
            CacheEvent.TIMETABLE_DELETED,
            CacheEvent.SCHEDULE_UPDATED,
        ]:
            total_invalidated += await CacheInvalidator._invalidate_timetable(
                tenant_id, class_id
            )
        
        elif event in [
            CacheEvent.CALENDAR_EVENT_CREATED,
            CacheEvent.CALENDAR_EVENT_UPDATED,
            CacheEvent.CALENDAR_EVENT_DELETED,
        ]:
            total_invalidated += await CacheInvalidator._invalidate_calendar(
                tenant_id
            )
        
        elif event in [
            CacheEvent.FEE_STRUCTURE_UPDATED,
            CacheEvent.FEE_COMPONENT_UPDATED,
        ]:
            total_invalidated += await CacheInvalidator._invalidate_fee(
                tenant_id
            )
        
        elif event == CacheEvent.ANALYTICS_SNAPSHOT_GENERATED:
            total_invalidated += await CacheInvalidator._invalidate_analytics(
                tenant_id, class_id
            )
        
        elif event in [
            CacheEvent.CLASS_CREATED,
            CacheEvent.CLASS_UPDATED,
            CacheEvent.CLASS_DELETED,
        ]:
            total_invalidated += await CacheInvalidator._invalidate_class(
                tenant_id
            )
        
        elif event in [
            CacheEvent.SUBJECT_CREATED,
            CacheEvent.SUBJECT_UPDATED,
            CacheEvent.SUBJECT_DELETED,
        ]:
            total_invalidated += await CacheInvalidator._invalidate_subject(
                tenant_id
            )
        
        if total_invalidated > 0:
            logger.info(f"Cache invalidated: {event.value} - {total_invalidated} keys")
        
        return total_invalidated
    
    @staticmethod
    async def _invalidate_syllabus(
        tenant_id: UUID,
        syllabus_id: Optional[UUID],
        class_id: Optional[UUID],
        subject_id: Optional[UUID],
    ) -> int:
        """Invalidate syllabus-related cache."""
        cache = await get_cache()
        count = 0
        
        # If specific syllabus, invalidate specific keys
        if syllabus_id:
            key = CacheKeys.syllabus_topics(tenant_id, syllabus_id)
            if await cache.delete(key):
                count += 1
        
        if class_id and subject_id:
            key = CacheKeys.syllabus_by_class(tenant_id, class_id, subject_id)
            if await cache.delete(key):
                count += 1
        
        # Always invalidate pattern to be safe
        pattern = CacheKeys.syllabus_pattern(tenant_id)
        count += await cache.delete_pattern(pattern)
        
        return count
    
    @staticmethod
    async def _invalidate_timetable(
        tenant_id: UUID,
        class_id: Optional[UUID],
    ) -> int:
        """Invalidate timetable-related cache."""
        cache = await get_cache()
        
        if class_id:
            pattern = CacheKeys.timetable_class_pattern(tenant_id, class_id)
        else:
            pattern = CacheKeys.timetable_pattern(tenant_id)
        
        return await cache.delete_pattern(pattern)
    
    @staticmethod
    async def _invalidate_calendar(tenant_id: UUID) -> int:
        """Invalidate calendar-related cache."""
        cache = await get_cache()
        pattern = CacheKeys.calendar_pattern(tenant_id)
        return await cache.delete_pattern(pattern)
    
    @staticmethod
    async def _invalidate_fee(tenant_id: UUID) -> int:
        """Invalidate fee-related cache."""
        cache = await get_cache()
        pattern = CacheKeys.fee_pattern(tenant_id)
        return await cache.delete_pattern(pattern)
    
    @staticmethod
    async def _invalidate_analytics(
        tenant_id: UUID,
        class_id: Optional[UUID],
    ) -> int:
        """Invalidate analytics-related cache."""
        cache = await get_cache()
        
        if class_id:
            # Invalidate specific class analytics
            key = CacheKeys.analytics_class_latest(tenant_id, class_id)
            return 1 if await cache.delete(key) else 0
        else:
            # Invalidate all analytics
            pattern = CacheKeys.analytics_pattern(tenant_id)
            return await cache.delete_pattern(pattern)
    
    @staticmethod
    async def _invalidate_class(tenant_id: UUID) -> int:
        """Invalidate class list cache."""
        cache = await get_cache()
        key = CacheKeys.class_list(tenant_id)
        return 1 if await cache.delete(key) else 0
    
    @staticmethod
    async def _invalidate_subject(tenant_id: UUID) -> int:
        """Invalidate subject list cache."""
        cache = await get_cache()
        key = CacheKeys.subject_list(tenant_id)
        return 1 if await cache.delete(key) else 0


# Convenience function
async def invalidate_cache(
    event: CacheEvent,
    tenant_id: UUID,
    **kwargs,
) -> int:
    """
    Invalidate cache for an event.
    
    This should be called after any data mutation.
    
    Example:
        await invalidate_cache(
            CacheEvent.SYLLABUS_UPDATED,
            tenant_id=user.tenant_id,
            entity_id=syllabus.id,
        )
    """
    return await CacheInvalidator.invalidate(event, tenant_id, **kwargs)
