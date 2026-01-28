"""
CUSTOS Feature Usage Tracking

Track module/feature usage per tenant.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import String, Integer, DateTime, Date, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_model import TenantBaseModel


class FeatureUsage(TenantBaseModel):
    """
    Track feature/module usage per tenant per day.
    
    Allows:
    - Usage analytics
    - Billing based on usage
    - Quota enforcement
    """
    __tablename__ = "feature_usage"
    
    __table_args__ = (
        UniqueConstraint("tenant_id", "feature", "date", name="uq_tenant_feature_date"),
    )
    
    feature: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    date: Mapped[datetime] = mapped_column(Date, nullable=False, index=True)
    
    count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Optional: track by user
    last_used_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )


class FeatureUsageService:
    """Service for tracking feature usage."""
    
    # Feature codes
    ASSIGNMENT_CREATE = "assignment:create"
    ASSIGNMENT_SUBMIT = "assignment:submit"
    QUESTION_CREATE = "question:create"
    QUESTION_AI_GENERATE = "question:ai_generate"
    LESSON_AI_GENERATE = "lesson:ai_generate"
    DOUBT_AI_SOLVE = "doubt:ai_solve"
    FILE_UPLOAD = "file:upload"
    NOTIFICATION_SEND = "notification:send"
    REPORT_GENERATE = "report:generate"
    USER_LOGIN = "user:login"
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
    
    async def increment(
        self, 
        feature: str, 
        user_id: Optional[UUID] = None,
        amount: int = 1,
    ) -> FeatureUsage:
        """Increment usage counter for a feature."""
        today = datetime.now().date()
        
        # Try to get existing record
        query = select(FeatureUsage).where(
            FeatureUsage.tenant_id == self.tenant_id,
            FeatureUsage.feature == feature,
            FeatureUsage.date == today,
        )
        result = await self.session.execute(query)
        usage = result.scalar_one_or_none()
        
        if usage:
            usage.count += amount
            if user_id:
                usage.last_used_by = user_id
        else:
            usage = FeatureUsage(
                tenant_id=self.tenant_id,
                feature=feature,
                date=today,
                count=amount,
                last_used_by=user_id,
            )
            self.session.add(usage)
        
        await self.session.commit()
        return usage
    
    async def get_daily_usage(
        self, 
        feature: str, 
        date: Optional[datetime] = None,
    ) -> int:
        """Get usage count for a feature on a specific day."""
        target_date = date or datetime.now().date()
        
        query = select(FeatureUsage.count).where(
            FeatureUsage.tenant_id == self.tenant_id,
            FeatureUsage.feature == feature,
            FeatureUsage.date == target_date,
        )
        result = await self.session.execute(query)
        return result.scalar() or 0
    
    async def get_monthly_usage(
        self, 
        feature: str, 
        year: int, 
        month: int,
    ) -> int:
        """Get total usage for a feature in a month."""
        from datetime import date
        
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)
        
        query = select(func.sum(FeatureUsage.count)).where(
            FeatureUsage.tenant_id == self.tenant_id,
            FeatureUsage.feature == feature,
            FeatureUsage.date >= start_date,
            FeatureUsage.date < end_date,
        )
        result = await self.session.execute(query)
        return result.scalar() or 0
    
    async def get_all_monthly_usage(
        self, 
        year: int, 
        month: int,
    ) -> dict:
        """Get all feature usage for a month."""
        from datetime import date
        
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)
        
        query = select(
            FeatureUsage.feature,
            func.sum(FeatureUsage.count).label("total")
        ).where(
            FeatureUsage.tenant_id == self.tenant_id,
            FeatureUsage.date >= start_date,
            FeatureUsage.date < end_date,
        ).group_by(FeatureUsage.feature)
        
        result = await self.session.execute(query)
        return {row.feature: row.total for row in result.all()}
    
    async def get_usage_trend(
        self, 
        feature: str, 
        days: int = 30,
    ) -> list:
        """Get usage trend for the last N days."""
        from datetime import timedelta
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        query = select(
            FeatureUsage.date,
            FeatureUsage.count
        ).where(
            FeatureUsage.tenant_id == self.tenant_id,
            FeatureUsage.feature == feature,
            FeatureUsage.date >= start_date,
        ).order_by(FeatureUsage.date)
        
        result = await self.session.execute(query)
        return [{"date": str(row.date), "count": row.count} for row in result.all()]
