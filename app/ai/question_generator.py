"""
CUSTOS Question Generator

AI-powered question generation.
"""

from datetime import datetime, timezone
from typing import Optional, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.base import AIPromptBuilder
from app.ai.openai_provider import get_ai_provider
from app.core.config import settings
from app.core.exceptions import ResourceNotFoundError
from app.models.academic import Topic, Subject, Class
from app.models.question import Question, QuestionType, BloomLevel, Difficulty
from app.models.ai import AISession, AIFeature
from app.schemas.ai import QuestionGenerationRequest, QuestionGenerationResponse


class QuestionGenerator:
    """AI question generator."""
    
    def __init__(self, session: AsyncSession, tenant_id: UUID, user_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.provider = get_ai_provider()
    
    async def generate(self, request: QuestionGenerationRequest) -> QuestionGenerationResponse:
        """Generate questions using AI."""
        # Get topic info
        topic = await self.session.get(Topic, request.topic_id)
        if not topic or topic.tenant_id != self.tenant_id:
            raise ResourceNotFoundError("Topic", str(request.topic_id))
        
        syllabus = topic.syllabus
        subject = await self.session.get(Subject, syllabus.subject_id)
        class_obj = await self.session.get(Class, syllabus.class_id)
        
        # Build prompt
        prompt = AIPromptBuilder.question_generation_prompt(
            subject=subject.name if subject else "Unknown",
            topic=topic.name,
            grade=class_obj.name if class_obj else "Unknown",
            count=request.count,
            question_type=request.question_type,
            difficulty=request.difficulty,
            bloom_level=request.bloom_levels[0] if request.bloom_levels else None,
        )
        
        system_prompt = """You are an expert question paper setter.
Create questions that:
- Are clear and unambiguous
- Test specific learning objectives
- Have distractors that reflect common misconceptions (for MCQ)
- Include detailed explanations
- Follow Bloom's taxonomy guidelines"""
        
        # Generate
        result, tokens_used = await self.provider.generate_json(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.5,
        )
        
        # Log session
        await self._log_session(
            feature=AIFeature.QUESTION_GENERATION,
            prompt=prompt,
            response=str(result),
            tokens=tokens_used,
        )
        
        # Parse and save questions
        questions_data = result if isinstance(result, list) else result.get("questions", [])
        saved_questions = await self._save_questions(topic.id, questions_data)
        
        return QuestionGenerationResponse(
            questions=[self._format_question(q) for q in saved_questions],
            tokens_used=tokens_used,
            saved_count=len(saved_questions),
        )
    
    async def _save_questions(self, topic_id: UUID, questions_data: list) -> List[Question]:
        """Save generated questions to database."""
        saved = []
        
        for q_data in questions_data:
            try:
                # Map question type
                q_type = q_data.get("question_type", "mcq")
                try:
                    question_type = QuestionType(q_type)
                except ValueError:
                    question_type = QuestionType.MCQ
                
                # Map difficulty
                diff = q_data.get("difficulty", "medium")
                try:
                    difficulty = Difficulty(diff)
                except ValueError:
                    difficulty = Difficulty.MEDIUM
                
                # Map bloom level
                bloom = q_data.get("bloom_level", "knowledge")
                try:
                    bloom_level = BloomLevel(bloom)
                except ValueError:
                    bloom_level = BloomLevel.KNOWLEDGE
                
                # Extract options
                options = q_data.get("options", [])
                correct_options = [opt["id"] for opt in options if opt.get("is_correct")]
                
                question = Question(
                    tenant_id=self.tenant_id,
                    topic_id=topic_id,
                    created_by=self.user_id,
                    question_text=q_data.get("question_text", ""),
                    question_type=question_type,
                    bloom_level=bloom_level,
                    difficulty=difficulty,
                    options=options,
                    correct_options=correct_options,
                    correct_answer=q_data.get("correct_answer"),
                    explanation=q_data.get("explanation"),
                    marks=q_data.get("marks", 1.0),
                    is_ai_generated=True,
                    ai_confidence=0.9,  # Could be refined
                    is_reviewed=False,  # Needs human review
                )
                
                self.session.add(question)
                saved.append(question)
                
            except Exception as e:
                # Skip invalid questions
                continue
        
        await self.session.commit()
        
        for q in saved:
            await self.session.refresh(q)
        
        return saved
    
    def _format_question(self, question: Question) -> dict:
        """Format question for response."""
        return {
            "id": str(question.id),
            "question_text": question.question_text,
            "question_type": question.question_type.value,
            "difficulty": question.difficulty.value,
            "bloom_level": question.bloom_level.value,
            "options": question.options,
            "explanation": question.explanation,
            "marks": question.marks,
        }
    
    async def _log_session(
        self,
        feature: AIFeature,
        prompt: str,
        response: str,
        tokens: int,
    ) -> None:
        """Log AI session."""
        cost = tokens * (settings.ai_cost_per_1k_tokens / 1000)
        
        ai_session = AISession(
            tenant_id=self.tenant_id,
            user_id=self.user_id,
            feature=feature,
            prompt=prompt[:5000],
            response=response[:10000],
            model_used=settings.openai_model,
            total_tokens=tokens,
            cost=cost,
            is_successful=True,
        )
        
        self.session.add(ai_session)
