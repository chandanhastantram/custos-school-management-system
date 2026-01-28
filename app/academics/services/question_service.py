"""
CUSTOS Question Service
"""

from datetime import datetime, timezone
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundError, ValidationError
from app.academics.models.questions import (
    Question, QuestionType, DifficultyLevel, BloomLevel, QuestionStatus,
)


class QuestionService:
    """Question bank management."""
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
    
    async def create_question(
        self,
        subject_id: UUID,
        question_type: QuestionType,
        question_text: str,
        created_by: UUID,
        topic_id: Optional[UUID] = None,
        difficulty: DifficultyLevel = DifficultyLevel.MEDIUM,
        bloom_level: BloomLevel = BloomLevel.UNDERSTAND,
        options: Optional[List[dict]] = None,
        correct_answer: Optional[str] = None,
        answer_explanation: Optional[str] = None,
        marks: float = 1.0,
        tags: Optional[List[str]] = None,
    ) -> Question:
        """Create question."""
        # Validate MCQ options
        if question_type == QuestionType.MCQ:
            if not options or len(options) < 2:
                raise ValidationError("MCQ must have at least 2 options")
            if not correct_answer:
                raise ValidationError("MCQ must have correct answer")
        
        question = Question(
            tenant_id=self.tenant_id,
            subject_id=subject_id,
            topic_id=topic_id,
            created_by=created_by,
            question_type=question_type,
            difficulty=difficulty,
            bloom_level=bloom_level,
            question_text=question_text,
            options=options,
            correct_answer=correct_answer,
            answer_explanation=answer_explanation,
            marks=marks,
            tags=tags,
            status=QuestionStatus.DRAFT,
        )
        
        self.session.add(question)
        await self.session.commit()
        await self.session.refresh(question)
        return question
    
    async def get_questions(
        self,
        subject_id: Optional[UUID] = None,
        topic_id: Optional[UUID] = None,
        question_type: Optional[QuestionType] = None,
        difficulty: Optional[DifficultyLevel] = None,
        status: Optional[QuestionStatus] = None,
        page: int = 1,
        size: int = 20,
    ) -> Tuple[List[Question], int]:
        """Get questions with filters."""
        query = select(Question).where(
            Question.tenant_id == self.tenant_id,
            Question.is_deleted == False,
        )
        
        if subject_id:
            query = query.where(Question.subject_id == subject_id)
        if topic_id:
            query = query.where(Question.topic_id == topic_id)
        if question_type:
            query = query.where(Question.question_type == question_type)
        if difficulty:
            query = query.where(Question.difficulty == difficulty)
        if status:
            query = query.where(Question.status == status)
        
        # Count
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0
        
        # Paginate
        skip = (page - 1) * size
        query = query.order_by(Question.created_at.desc()).offset(skip).limit(size)
        result = await self.session.execute(query)
        
        return list(result.scalars().all()), total
    
    async def get_question(self, question_id: UUID) -> Question:
        """Get question by ID."""
        query = select(Question).where(
            Question.tenant_id == self.tenant_id,
            Question.id == question_id,
        )
        result = await self.session.execute(query)
        question = result.scalar_one_or_none()
        if not question:
            raise ResourceNotFoundError("Question", str(question_id))
        return question
    
    async def approve_question(
        self,
        question_id: UUID,
        reviewed_by: UUID,
    ) -> Question:
        """Approve question."""
        question = await self.get_question(question_id)
        question.status = QuestionStatus.APPROVED
        question.reviewed_by = reviewed_by
        question.reviewed_at = datetime.now(timezone.utc)
        await self.session.commit()
        return question
    
    async def reject_question(
        self,
        question_id: UUID,
        reviewed_by: UUID,
        reason: Optional[str] = None,
    ) -> Question:
        """Reject question."""
        question = await self.get_question(question_id)
        question.status = QuestionStatus.REJECTED
        question.reviewed_by = reviewed_by
        question.reviewed_at = datetime.now(timezone.utc)
        await self.session.commit()
        return question
    
    async def get_random_questions(
        self,
        subject_id: UUID,
        count: int,
        difficulty: Optional[DifficultyLevel] = None,
        question_type: Optional[QuestionType] = None,
    ) -> List[Question]:
        """Get random questions for assignment."""
        query = select(Question).where(
            Question.tenant_id == self.tenant_id,
            Question.subject_id == subject_id,
            Question.status == QuestionStatus.APPROVED,
        )
        
        if difficulty:
            query = query.where(Question.difficulty == difficulty)
        if question_type:
            query = query.where(Question.question_type == question_type)
        
        query = query.order_by(func.random()).limit(count)
        result = await self.session.execute(query)
        return list(result.scalars().all())
