"""
CUSTOS Question Repository
"""

from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.question import Question, QuestionType, BloomLevel, Difficulty, QuestionAttempt
from app.repositories.base import BaseRepository


class QuestionRepository(BaseRepository[Question]):
    """Question repository."""
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        super().__init__(Question, session, tenant_id)
    
    async def get_by_topic(
        self,
        topic_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Question]:
        """Get questions by topic."""
        query = self._base_query().where(
            Question.topic_id == topic_id,
            Question.is_active == True
        ).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def search(
        self,
        topic_id: Optional[UUID] = None,
        question_type: Optional[QuestionType] = None,
        difficulty: Optional[Difficulty] = None,
        bloom_level: Optional[BloomLevel] = None,
        is_reviewed: Optional[bool] = None,
        search_text: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Question]:
        """Search questions with filters."""
        query = self._base_query().where(Question.is_active == True)
        
        if topic_id:
            query = query.where(Question.topic_id == topic_id)
        if question_type:
            query = query.where(Question.question_type == question_type)
        if difficulty:
            query = query.where(Question.difficulty == difficulty)
        if bloom_level:
            query = query.where(Question.bloom_level == bloom_level)
        if is_reviewed is not None:
            query = query.where(Question.is_reviewed == is_reviewed)
        if search_text:
            search = f"%{search_text}%"
            query = query.where(Question.question_text.ilike(search))
        
        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def count_by_topic(self, topic_id: UUID) -> int:
        """Count questions by topic."""
        query = select(func.count()).select_from(Question).where(
            Question.tenant_id == self.tenant_id,
            Question.topic_id == topic_id,
            Question.is_active == True
        )
        result = await self.session.execute(query)
        return result.scalar() or 0
    
    async def get_random(
        self,
        topic_id: UUID,
        count: int,
        difficulty: Optional[Difficulty] = None,
        question_type: Optional[QuestionType] = None,
        exclude_ids: Optional[List[UUID]] = None,
    ) -> List[Question]:
        """Get random questions for worksheet/assignment."""
        query = self._base_query().where(
            Question.topic_id == topic_id,
            Question.is_active == True,
            Question.is_reviewed == True
        )
        
        if difficulty:
            query = query.where(Question.difficulty == difficulty)
        if question_type:
            query = query.where(Question.question_type == question_type)
        if exclude_ids:
            query = query.where(~Question.id.in_(exclude_ids))
        
        query = query.order_by(func.random()).limit(count)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def increment_usage(self, question_id: UUID) -> None:
        """Increment question usage count."""
        question = await self.get_by_id(question_id)
        if question:
            question.times_used += 1
            await self.session.flush()


class QuestionAttemptRepository(BaseRepository[QuestionAttempt]):
    """Question attempt repository."""
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        super().__init__(QuestionAttempt, session, tenant_id)
    
    async def get_by_student(
        self,
        student_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[QuestionAttempt]:
        """Get attempts by student."""
        query = self._base_query().where(
            QuestionAttempt.student_id == student_id
        ).order_by(QuestionAttempt.attempted_at.desc()).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_by_assignment(
        self,
        assignment_id: UUID,
        student_id: Optional[UUID] = None,
    ) -> List[QuestionAttempt]:
        """Get attempts for an assignment."""
        query = self._base_query().where(
            QuestionAttempt.assignment_id == assignment_id
        )
        if student_id:
            query = query.where(QuestionAttempt.student_id == student_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_student_stats(self, student_id: UUID) -> dict:
        """Get student attempt statistics."""
        total = await self.session.execute(
            select(func.count()).select_from(QuestionAttempt).where(
                QuestionAttempt.tenant_id == self.tenant_id,
                QuestionAttempt.student_id == student_id
            )
        )
        correct = await self.session.execute(
            select(func.count()).select_from(QuestionAttempt).where(
                QuestionAttempt.tenant_id == self.tenant_id,
                QuestionAttempt.student_id == student_id,
                QuestionAttempt.is_correct == True
            )
        )
        
        total_count = total.scalar() or 0
        correct_count = correct.scalar() or 0
        
        return {
            "total_attempts": total_count,
            "correct_attempts": correct_count,
            "accuracy": (correct_count / total_count * 100) if total_count > 0 else 0
        }
