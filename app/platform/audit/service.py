"""
CUSTOS Audit Service
"""

from typing import Optional, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.platform.audit.models import AuditLog, AuditAction


class AuditService:
    """Audit logging service."""
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
    
    async def log(
        self,
        action: AuditAction,
        resource_type: str,
        description: str,
        user_id: Optional[UUID] = None,
        resource_id: Optional[str] = None,
        old_values: Optional[dict] = None,
        new_values: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """Create audit log entry."""
        log = AuditLog(
            tenant_id=self.tenant_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            description=description,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.session.add(log)
        await self.session.commit()
        return log
    
    async def get_logs(
        self,
        resource_type: Optional[str] = None,
        user_id: Optional[UUID] = None,
        action: Optional[AuditAction] = None,
        limit: int = 100,
    ) -> List[AuditLog]:
        """Get audit logs."""
        query = select(AuditLog).where(AuditLog.tenant_id == self.tenant_id)
        
        if resource_type:
            query = query.where(AuditLog.resource_type == resource_type)
        if user_id:
            query = query.where(AuditLog.user_id == user_id)
        if action:
            query = query.where(AuditLog.action == action)
        
        query = query.order_by(AuditLog.created_at.desc()).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())
