"""
CUSTOS Question Service

Question bank management.
"""

from datetime import datetime, timezone
from typing import Optional, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundError, ValidationError
from app.models.question import Question, QuestionType, BloomLevel, Difficulty, QuestionAttempt
from app.repositories.question_repo import QuestionRepository, QuestionAttemptRepository
from app.schemas.question import QuestionCreate, QuestionUpdate, QuestionFilter


class QuestionService:
    """Question management service."""
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
        self.question_repo = QuestionRepository(session, tenant_id)
        self.attempt_repo = QuestionAttemptRepository(session, tenant_id)
    
    async def create_question(
        self,
        data: QuestionCreate,
        created_by: UUID,
    ) -> Question:
        """Create new question."""
        # Validate MCQ options
        if data.question_type in [QuestionType.MCQ, QuestionType.MCQ_MULTIPLE]:
            if not data.options or len(data.options) < 2:
                raise ValidationError("MCQ questions require at least 2 options")
            
            correct_count = sum(1 for opt in data.options if opt.is_correct)
            if correct_count == 0:
                raise ValidationError("At least one option must be correct")
        
        # Prepare options data
        options_data = None
        correct_options = None
        if data.options:
            options_data = [opt.model_dump() for opt in data.options]
            correct_options = [opt.id for opt in data.options if opt.is_correct]
        
        question = await self.question_repo.create(
            topic_id=data.topic_id,
            created_by=created_by,
            question_text=data.question_text,
            question_html=data.question_html,
            question_type=data.question_type,
            bloom_level=data.bloom_level,
            difficulty=data.difficulty,
            options=options_data,
            correct_answer=data.correct_answer,
            correct_options=correct_options,
            explanation=data.explanation,
            solution_steps=data.solution_steps,
            marks=data.marks,
            negative_marks=data.negative_marks,
            time_limit_seconds=data.time_limit_seconds,
            subtopic=data.subtopic,
            tags=data.tags,
        )
        
        await self.session.commit()
        return question
    
    async def get_question(self, question_id: UUID) -> Question:
        """Get question by ID."""
        question = await self.question_repo.get_by_id(question_id)
        if not question:
            raise ResourceNotFoundError("Question", str(question_id))
        return question
    
    async def update_question(
        self,
        question_id: UUID,
        data: QuestionUpdate,
    ) -> Question:
        """Update question."""
        question = await self.question_repo.get_by_id(question_id)
        if not question:
            raise ResourceNotFoundError("Question", str(question_id))
        
        update_data = data.model_dump(exclude_unset=True)
        
        # Handle options update
        if "options" in update_data and update_data["options"]:
            options_data = [opt.model_dump() for opt in data.options]
            correct_options = [opt.id for opt in data.options if opt.is_correct]
            update_data["options"] = options_data
            update_data["correct_options"] = correct_options
        
        for key, value in update_data.items():
            if hasattr(question, key):
                setattr(question, key, value)
        
        # Mark as needing review if content changed
        if any(k in update_data for k in ["question_text", "options", "correct_answer"]):
            question.is_reviewed = False
        
        await self.session.commit()
        await self.session.refresh(question)
        return question
    
    async def delete_question(self, question_id: UUID, deleted_by: UUID) -> bool:
        """Soft delete question."""
        return await self.question_repo.soft_delete(question_id, deleted_by)
    
    async def list_questions(
        self,
        filters: QuestionFilter,
        page: int = 1,
        size: int = 20,
    ) -> tuple[List[Question], int]:
        """List questions with filters."""
        skip = (page - 1) * size
        
        questions = await self.question_repo.search(
            topic_id=filters.topic_id,
            question_type=filters.question_type,
            difficulty=filters.difficulty,
            bloom_level=filters.bloom_level,
            is_reviewed=filters.is_reviewed,
            search_text=filters.search,
            skip=skip,
            limit=size,
        )
        
        total = await self.question_repo.count()
        
        return questions, total
    
    async def review_question(
        self,
        question_id: UUID,
        reviewer_id: UUID,
        approved: bool,
    ) -> Question:
        """Review and approve/reject question."""
        question = await self.question_repo.get_by_id(question_id)
        if not question:
            raise ResourceNotFoundError("Question", str(question_id))
        
        question.is_reviewed = approved
        question.reviewed_by = reviewer_id
        question.reviewed_at = datetime.now(timezone.utc)
        
        await self.session.commit()
        return question
    
    async def bulk_create_questions(
        self,
        questions_data: List[QuestionCreate],
        created_by: UUID,
    ) -> List[Question]:
        """Bulk create questions."""
        questions = []
        for data in questions_data:
            question = await self.create_question(data, created_by)
            questions.append(question)
        return questions
    
    async def get_questions_for_worksheet(
        self,
        topic_id: UUID,
        count: int,
        difficulty_distribution: Optional[dict] = None,
    ) -> List[Question]:
        """Get random questions for worksheet generation."""
        questions = []
        
        if difficulty_distribution:
            for difficulty, num in difficulty_distribution.items():
                diff_questions = await self.question_repo.get_random(
                    topic_id=topic_id,
                    count=num,
                    difficulty=Difficulty(difficulty),
                    exclude_ids=[q.id for q in questions],
                )
                questions.extend(diff_questions)
        else:
            questions = await self.question_repo.get_random(
                topic_id=topic_id,
                count=count,
            )
        
        return questions
    
    async def record_attempt(
        self,
        question_id: UUID,
        student_id: UUID,
        answer: Optional[str] = None,
        selected_options: Optional[List[str]] = None,
        assignment_id: Optional[UUID] = None,
        time_taken: Optional[int] = None,
    ) -> QuestionAttempt:
        """Record student's question attempt."""
        question = await self.question_repo.get_by_id(question_id)
        if not question:
            raise ResourceNotFoundError("Question", str(question_id))
        
        # Evaluate answer
        is_correct = None
        marks_obtained = 0.0
        needs_manual = False
        
        if question.question_type in [QuestionType.MCQ, QuestionType.MCQ_MULTIPLE, QuestionType.TRUE_FALSE]:
            if selected_options and question.correct_options:
                is_correct = set(selected_options) == set(question.correct_options)
                marks_obtained = question.marks if is_correct else -question.negative_marks
        elif question.question_type == QuestionType.FILL_BLANK:
            if answer and question.correct_answer:
                is_correct = answer.strip().lower() == question.correct_answer.strip().lower()
                marks_obtained = question.marks if is_correct else 0
        else:
            needs_manual = True
        
        attempt = await self.attempt_repo.create(
            question_id=question_id,
            student_id=student_id,
            assignment_id=assignment_id,
            answer=answer,
            selected_options=selected_options,
            is_correct=is_correct,
            marks_obtained=marks_obtained,
            time_taken_seconds=time_taken,
            attempted_at=datetime.now(timezone.utc),
            needs_manual_grading=needs_manual,
        )
        
        # Update question usage
        await self.question_repo.increment_usage(question_id)
        
        await self.session.commit()
        return attempt
