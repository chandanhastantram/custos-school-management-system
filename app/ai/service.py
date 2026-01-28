"""
CUSTOS AI Service
"""

from typing import Optional, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.providers.openai import OpenAIProvider
from app.core.exceptions import UsageLimitExceededError


class AIService:
    """AI service for lesson plans, questions, doubt solving."""
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
        self.provider = OpenAIProvider()
    
    async def _check_usage(self) -> None:
        """Check if tenant has AI credits."""
        from app.billing.models import UsageLimit
        from sqlalchemy import select
        from datetime import datetime
        
        now = datetime.now()
        query = select(UsageLimit).where(
            UsageLimit.tenant_id == self.tenant_id,
            UsageLimit.year == now.year,
            UsageLimit.month == now.month,
        )
        result = await self.session.execute(query)
        usage = result.scalar_one_or_none()
        
        if usage:
            # Check limit (would get from subscription plan)
            max_requests = 100  # Default
            if usage.ai_requests_used >= max_requests:
                raise UsageLimitExceededError(
                    "AI requests", usage.ai_requests_used, max_requests
                )
    
    async def _increment_usage(self) -> None:
        """Increment AI usage counter."""
        from app.billing.models import UsageLimit
        from sqlalchemy import select
        from datetime import datetime
        
        now = datetime.now()
        query = select(UsageLimit).where(
            UsageLimit.tenant_id == self.tenant_id,
            UsageLimit.year == now.year,
            UsageLimit.month == now.month,
        )
        result = await self.session.execute(query)
        usage = result.scalar_one_or_none()
        
        if usage:
            usage.ai_requests_used += 1
            await self.session.commit()
    
    async def generate_lesson_plan(
        self,
        subject: str,
        topic: str,
        grade_level: int,
        duration_minutes: int = 45,
    ) -> dict:
        """Generate AI lesson plan."""
        await self._check_usage()
        
        result = await self.provider.generate_lesson_plan(
            subject=subject,
            topic=topic,
            grade_level=grade_level,
            duration_minutes=duration_minutes,
        )
        
        await self._increment_usage()
        return result
    
    async def generate_questions(
        self,
        subject: str,
        topic: str,
        question_type: str,
        count: int = 5,
        difficulty: str = "medium",
    ) -> List[dict]:
        """Generate AI questions."""
        await self._check_usage()
        
        result = await self.provider.generate_questions(
            subject=subject,
            topic=topic,
            question_type=question_type,
            count=count,
            difficulty=difficulty,
        )
        
        await self._increment_usage()
        return result
    
    async def solve_doubt(
        self,
        question: str,
        subject: str,
        context: Optional[str] = None,
    ) -> dict:
        """AI doubt solver."""
        await self._check_usage()
        
        result = await self.provider.solve_doubt(
            question=question,
            subject=subject,
            context=context,
        )
        
        await self._increment_usage()
        return result
    
    async def get_usage(self) -> dict:
        """Get AI usage for current month."""
        from app.billing.models import UsageLimit
        from sqlalchemy import select
        from datetime import datetime
        
        now = datetime.now()
        query = select(UsageLimit).where(
            UsageLimit.tenant_id == self.tenant_id,
            UsageLimit.year == now.year,
            UsageLimit.month == now.month,
        )
        result = await self.session.execute(query)
        usage = result.scalar_one_or_none()
        
        return {
            "month": now.month,
            "year": now.year,
            "ai_requests_used": usage.ai_requests_used if usage else 0,
            "ai_requests_limit": 100,  # Would get from plan
        }
