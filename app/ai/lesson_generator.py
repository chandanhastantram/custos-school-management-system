"""
CUSTOS Lesson Generator

AI-powered lesson plan generation.
"""

from datetime import datetime, timezone
from typing import Optional, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.base import AIPromptBuilder
from app.ai.openai_provider import get_ai_provider
from app.core.exceptions import ResourceNotFoundError, AIServiceError
from app.models.academic import Lesson, Topic, Subject, Class, LessonStatus
from app.models.ai import AISession, AIFeature
from app.schemas.ai import LessonPlanRequest, LessonPlanResponse


class LessonGenerator:
    """AI lesson plan generator."""
    
    def __init__(self, session: AsyncSession, tenant_id: UUID, user_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.provider = get_ai_provider()
    
    async def generate(self, request: LessonPlanRequest) -> LessonPlanResponse:
        """Generate lesson plan using AI."""
        # Get topic and related info
        topic = await self.session.get(Topic, request.topic_id)
        if not topic or topic.tenant_id != self.tenant_id:
            raise ResourceNotFoundError("Topic", str(request.topic_id))
        
        syllabus = topic.syllabus
        
        # Get subject and class
        from sqlalchemy import select
        from app.models.academic import Syllabus
        
        subject = await self.session.get(Subject, syllabus.subject_id)
        class_obj = await self.session.get(Class, syllabus.class_id)
        
        # Build prompt
        prompt = AIPromptBuilder.lesson_plan_prompt(
            subject=subject.name if subject else "Unknown",
            topic=topic.name,
            grade=class_obj.name if class_obj else "Unknown",
            duration=request.duration_minutes,
            objectives=topic.learning_objectives,
        )
        
        system_prompt = """You are an experienced teacher and curriculum designer. 
Create engaging, age-appropriate lesson plans that follow best pedagogical practices.
Include interactive elements, formative assessments, and differentiated instruction strategies."""
        
        # Generate
        try:
            result, tokens_used = await self.provider.generate_json(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.7,
            )
        except Exception as e:
            await self._log_session(
                feature=AIFeature.LESSON_PLAN,
                prompt=prompt,
                response=None,
                tokens=0,
                success=False,
                error=str(e),
            )
            raise
        
        # Log session
        await self._log_session(
            feature=AIFeature.LESSON_PLAN,
            prompt=prompt,
            response=str(result),
            tokens=tokens_used,
            success=True,
        )
        
        # Optionally save the lesson
        lesson = await self._save_lesson(topic.id, result, request.duration_minutes)
        
        return LessonPlanResponse(
            title=result.get("title", topic.name),
            objectives=result.get("objectives", []),
            content=result,
            activities=result.get("main_content", []),
            assessment_plan=result.get("assessment", {}),
            homework=result.get("conclusion", {}).get("homework"),
            resources=result.get("resources", []),
            tokens_used=tokens_used,
            lesson_id=lesson.id if lesson else None,
        )
    
    async def _save_lesson(
        self,
        topic_id: UUID,
        content: dict,
        duration: int,
    ) -> Lesson:
        """Save generated lesson to database."""
        lesson = Lesson(
            tenant_id=self.tenant_id,
            topic_id=topic_id,
            teacher_id=self.user_id,
            title=content.get("title", "AI Generated Lesson"),
            description=content.get("introduction", {}).get("activity"),
            objectives=content.get("objectives", []),
            duration_minutes=duration,
            content=content,
            resources=content.get("resources", []),
            activities=content.get("main_content", []),
            assessment_plan=content.get("assessment"),
            homework=content.get("conclusion", {}).get("homework"),
            status=LessonStatus.DRAFT,
            is_ai_generated=True,
            ai_generation_params={"duration": duration},
        )
        
        self.session.add(lesson)
        await self.session.commit()
        await self.session.refresh(lesson)
        
        return lesson
    
    async def _log_session(
        self,
        feature: AIFeature,
        prompt: str,
        response: Optional[str],
        tokens: int,
        success: bool,
        error: Optional[str] = None,
    ) -> None:
        """Log AI session for usage tracking."""
        # Estimate cost
        cost = tokens * (settings.ai_cost_per_1k_tokens / 1000) if tokens else 0
        
        from app.core.config import settings
        
        ai_session = AISession(
            tenant_id=self.tenant_id,
            user_id=self.user_id,
            feature=feature,
            prompt=prompt[:5000],  # Truncate for storage
            response=response[:10000] if response else None,
            model_used=settings.openai_model,
            input_tokens=0,  # Would need to track separately
            output_tokens=0,
            total_tokens=tokens,
            cost=cost,
            is_successful=success,
            error_message=error,
        )
        
        self.session.add(ai_session)
        await self.session.commit()
