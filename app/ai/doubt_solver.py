"""
CUSTOS Doubt Solver

AI-powered doubt solving for students.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.base import AIPromptBuilder
from app.ai.openai_provider import get_ai_provider
from app.core.config import settings
from app.models.academic import Subject, Topic
from app.models.ai import AISession, AIFeature
from app.schemas.ai import DoubtSolverRequest, DoubtSolverResponse


class DoubtSolver:
    """AI doubt solver for students."""
    
    def __init__(self, session: AsyncSession, tenant_id: UUID, user_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.provider = get_ai_provider()
    
    async def solve(self, request: DoubtSolverRequest) -> DoubtSolverResponse:
        """Solve student doubt using AI."""
        # Get context if provided
        subject_name = None
        topic_name = None
        
        if request.subject_id:
            subject = await self.session.get(Subject, request.subject_id)
            if subject and subject.tenant_id == self.tenant_id:
                subject_name = subject.name
        
        if request.topic_id:
            topic = await self.session.get(Topic, request.topic_id)
            if topic and topic.tenant_id == self.tenant_id:
                topic_name = topic.name
        
        # Build prompt
        prompt = AIPromptBuilder.doubt_solver_prompt(
            question=request.question,
            subject=subject_name,
            topic=topic_name,
            context=request.context,
        )
        
        system_prompt = """You are a patient, encouraging teacher assistant.
Your role is to help students understand concepts, not just give answers.
- Use simple, clear language appropriate for the student's level
- Break down complex concepts into steps
- Use examples and analogies
- Encourage further exploration"""
        
        # Generate response
        result, tokens_used = await self.provider.generate_json(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.7,
        )
        
        # Log session
        await self._log_session(
            prompt=prompt,
            response=str(result),
            tokens=tokens_used,
        )
        
        return DoubtSolverResponse(
            answer=result.get("answer", ""),
            explanation=result.get("explanation"),
            related_topics=result.get("related_topics", []),
            follow_up_questions=result.get("follow_up_questions", []),
            tokens_used=tokens_used,
        )
    
    async def _log_session(
        self,
        prompt: str,
        response: str,
        tokens: int,
    ) -> None:
        """Log AI session."""
        cost = tokens * (settings.ai_cost_per_1k_tokens / 1000)
        
        ai_session = AISession(
            tenant_id=self.tenant_id,
            user_id=self.user_id,
            feature=AIFeature.DOUBT_SOLVER,
            prompt=prompt[:5000],
            response=response[:10000],
            model_used=settings.openai_model,
            total_tokens=tokens,
            cost=cost,
            is_successful=True,
        )
        
        self.session.add(ai_session)
        await self.session.commit()
