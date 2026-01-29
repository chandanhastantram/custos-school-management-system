"""
CUSTOS Lesson Evaluation Repository

Data access layer for lesson evaluations and adaptive recommendations.
"""

from datetime import datetime, date
from typing import Optional, List, Tuple, Dict
from uuid import UUID
import random

from sqlalchemy import select, func, and_, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundError, ValidationError, DuplicateError
from app.learning.models.lesson_evaluation import (
    LessonEvaluation,
    LessonEvaluationQuestion,
    LessonEvaluationResult,
    LessonMasterySnapshot,
    AdaptiveRecommendation,
    LessonEvaluationStatus,
    RecommendationType,
    RecommendationPriority,
)
from app.learning.models.daily_loops import StudentTopicMastery
from app.learning.models.weekly_tests import WeeklyTestResult, WeeklyStudentPerformance
from app.academics.models.questions import Question, QuestionType, QuestionStatus
from app.academics.models.lesson_plans import LessonPlan, LessonPlanUnit


class LessonEvaluationRepository:
    """Repository for lesson evaluation operations."""
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
    
    # ============================================
    # Lesson Evaluation CRUD
    # ============================================
    
    async def create_evaluation(self, **data) -> LessonEvaluation:
        """Create a lesson evaluation."""
        evaluation = LessonEvaluation(
            tenant_id=self.tenant_id,
            **data
        )
        self.session.add(evaluation)
        await self.session.flush()
        await self.session.refresh(evaluation)
        return evaluation
    
    async def get_evaluation(self, evaluation_id: UUID) -> Optional[LessonEvaluation]:
        """Get lesson evaluation by ID."""
        query = select(LessonEvaluation).where(
            LessonEvaluation.id == evaluation_id,
            LessonEvaluation.tenant_id == self.tenant_id,
            LessonEvaluation.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def list_evaluations(
        self,
        class_id: Optional[UUID] = None,
        lesson_plan_id: Optional[UUID] = None,
        status: Optional[LessonEvaluationStatus] = None,
        page: int = 1,
        size: int = 20,
    ) -> Tuple[List[LessonEvaluation], int]:
        """List lesson evaluations with filters."""
        query = select(LessonEvaluation).where(
            LessonEvaluation.tenant_id == self.tenant_id,
            LessonEvaluation.deleted_at.is_(None),
        )
        
        if class_id:
            query = query.where(LessonEvaluation.class_id == class_id)
        if lesson_plan_id:
            query = query.where(LessonEvaluation.lesson_plan_id == lesson_plan_id)
        if status:
            query = query.where(LessonEvaluation.status == status)
        
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.session.scalar(count_query) or 0
        
        query = query.order_by(LessonEvaluation.created_at.desc())
        query = query.offset((page - 1) * size).limit(size)
        
        result = await self.session.execute(query)
        return list(result.scalars().all()), total
    
    async def update_evaluation(self, evaluation_id: UUID, **data) -> LessonEvaluation:
        """Update a lesson evaluation."""
        evaluation = await self.get_evaluation(evaluation_id)
        if not evaluation:
            raise ResourceNotFoundError("LessonEvaluation", evaluation_id)
        
        for key, value in data.items():
            if value is not None and hasattr(evaluation, key):
                setattr(evaluation, key, value)
        
        await self.session.flush()
        await self.session.refresh(evaluation)
        return evaluation
    
    async def update_evaluation_status(
        self,
        evaluation_id: UUID,
        status: LessonEvaluationStatus,
    ) -> LessonEvaluation:
        """Update evaluation status."""
        evaluation = await self.get_evaluation(evaluation_id)
        if not evaluation:
            raise ResourceNotFoundError("LessonEvaluation", evaluation_id)
        
        evaluation.status = status
        
        if status == LessonEvaluationStatus.CONDUCTED:
            evaluation.conducted_at = datetime.utcnow()
        elif status == LessonEvaluationStatus.EVALUATED:
            evaluation.evaluated_at = datetime.utcnow()
        
        await self.session.flush()
        await self.session.refresh(evaluation)
        return evaluation
    
    async def delete_evaluation(self, evaluation_id: UUID) -> None:
        """Soft delete a lesson evaluation."""
        evaluation = await self.get_evaluation(evaluation_id)
        if not evaluation:
            raise ResourceNotFoundError("LessonEvaluation", evaluation_id)
        await evaluation.soft_delete()
        await self.session.flush()
    
    # ============================================
    # Evaluation Questions
    # ============================================
    
    async def add_question(
        self,
        lesson_evaluation_id: UUID,
        question_id: UUID,
        question_number: int,
        topic_id: Optional[UUID] = None,
        marks: float = 1.0,
    ) -> LessonEvaluationQuestion:
        """Add a question to the evaluation."""
        question = LessonEvaluationQuestion(
            tenant_id=self.tenant_id,
            lesson_evaluation_id=lesson_evaluation_id,
            question_id=question_id,
            question_number=question_number,
            topic_id=topic_id,
            marks=marks,
        )
        self.session.add(question)
        await self.session.flush()
        return question
    
    async def add_questions_bulk(
        self,
        lesson_evaluation_id: UUID,
        questions_data: List[dict],
    ) -> List[LessonEvaluationQuestion]:
        """Add multiple questions to the evaluation."""
        created = []
        for data in questions_data:
            question = LessonEvaluationQuestion(
                tenant_id=self.tenant_id,
                lesson_evaluation_id=lesson_evaluation_id,
                **data
            )
            self.session.add(question)
            created.append(question)
        await self.session.flush()
        return created
    
    async def get_evaluation_questions(
        self,
        lesson_evaluation_id: UUID,
    ) -> List[LessonEvaluationQuestion]:
        """Get all questions for an evaluation."""
        query = select(LessonEvaluationQuestion).where(
            LessonEvaluationQuestion.lesson_evaluation_id == lesson_evaluation_id,
            LessonEvaluationQuestion.tenant_id == self.tenant_id,
            LessonEvaluationQuestion.deleted_at.is_(None),
        ).order_by(LessonEvaluationQuestion.question_number)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def clear_evaluation_questions(self, lesson_evaluation_id: UUID) -> int:
        """Remove all questions from an evaluation."""
        questions = await self.get_evaluation_questions(lesson_evaluation_id)
        count = 0
        for q in questions:
            await q.soft_delete()
            count += 1
        await self.session.flush()
        return count
    
    async def get_questions_for_lesson_plan(
        self,
        lesson_plan_id: UUID,
        limit: int = 50,
    ) -> List[Question]:
        """Get all approved MCQ questions from topics in a lesson plan."""
        # Get topic IDs from lesson plan units
        units_query = select(LessonPlanUnit.topic_id).where(
            LessonPlanUnit.lesson_plan_id == lesson_plan_id,
            LessonPlanUnit.deleted_at.is_(None),
        )
        
        result = await self.session.execute(units_query)
        topic_ids = [row[0] for row in result.all() if row[0]]
        
        if not topic_ids:
            return []
        
        # Get questions for these topics
        query = select(Question).where(
            Question.tenant_id == self.tenant_id,
            Question.topic_id.in_(topic_ids),
            Question.question_type == QuestionType.MCQ,
            Question.status == QuestionStatus.APPROVED,
            Question.deleted_at.is_(None),
        ).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    # ============================================
    # Evaluation Results
    # ============================================
    
    async def submit_result(
        self,
        lesson_evaluation_id: UUID,
        student_id: UUID,
        total_marks: float,
        marks_obtained: float,
        wrong_questions: List[int],
        submitted_by: Optional[UUID] = None,
    ) -> LessonEvaluationResult:
        """Submit a student's result."""
        # Check for duplicate
        existing = await self.get_student_result(lesson_evaluation_id, student_id)
        if existing:
            raise DuplicateError(
                f"Result already exists for student {student_id}"
            )
        
        percentage = (marks_obtained / total_marks * 100) if total_marks > 0 else 0
        
        result = LessonEvaluationResult(
            tenant_id=self.tenant_id,
            lesson_evaluation_id=lesson_evaluation_id,
            student_id=student_id,
            total_marks=total_marks,
            marks_obtained=marks_obtained,
            wrong_questions=wrong_questions,
            percentage=percentage,
            submitted_by=submitted_by,
        )
        self.session.add(result)
        await self.session.flush()
        await self.session.refresh(result)
        return result
    
    async def get_student_result(
        self,
        lesson_evaluation_id: UUID,
        student_id: UUID,
    ) -> Optional[LessonEvaluationResult]:
        """Get a student's result for an evaluation."""
        query = select(LessonEvaluationResult).where(
            LessonEvaluationResult.lesson_evaluation_id == lesson_evaluation_id,
            LessonEvaluationResult.student_id == student_id,
            LessonEvaluationResult.tenant_id == self.tenant_id,
            LessonEvaluationResult.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_evaluation_results(
        self,
        lesson_evaluation_id: UUID,
    ) -> List[LessonEvaluationResult]:
        """Get all results for an evaluation."""
        query = select(LessonEvaluationResult).where(
            LessonEvaluationResult.lesson_evaluation_id == lesson_evaluation_id,
            LessonEvaluationResult.tenant_id == self.tenant_id,
            LessonEvaluationResult.deleted_at.is_(None),
        ).order_by(LessonEvaluationResult.percentage.desc())
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_student_all_results(
        self,
        student_id: UUID,
    ) -> List[LessonEvaluationResult]:
        """Get all lesson evaluation results for a student."""
        query = select(LessonEvaluationResult).where(
            LessonEvaluationResult.student_id == student_id,
            LessonEvaluationResult.tenant_id == self.tenant_id,
            LessonEvaluationResult.deleted_at.is_(None),
        ).order_by(LessonEvaluationResult.created_at.desc())
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def update_evaluation_stats(self, evaluation_id: UUID) -> None:
        """Update evaluation statistics after results are submitted."""
        results = await self.get_evaluation_results(evaluation_id)
        
        if results:
            students_appeared = len(results)
            avg_score = sum(r.percentage for r in results) / students_appeared
            
            await self.session.execute(
                update(LessonEvaluation)
                .where(LessonEvaluation.id == evaluation_id)
                .values(
                    students_appeared=students_appeared,
                    avg_score_percent=round(avg_score, 2),
                )
            )
            await self.session.flush()
    
    # ============================================
    # Mastery Snapshots
    # ============================================
    
    async def create_mastery_snapshot(
        self,
        student_id: UUID,
        chapter_id: UUID,
        lesson_evaluation_id: Optional[UUID],
        mastery_percent: float,
        daily_mastery: float = 0.0,
        weekly_mastery: float = 0.0,
        lesson_mastery: float = 0.0,
    ) -> LessonMasterySnapshot:
        """Create a mastery snapshot."""
        snapshot = LessonMasterySnapshot(
            tenant_id=self.tenant_id,
            student_id=student_id,
            chapter_id=chapter_id,
            lesson_evaluation_id=lesson_evaluation_id,
            mastery_percent=mastery_percent,
            daily_mastery=daily_mastery,
            weekly_mastery=weekly_mastery,
            lesson_mastery=lesson_mastery,
            evaluated_at=datetime.utcnow(),
        )
        self.session.add(snapshot)
        await self.session.flush()
        await self.session.refresh(snapshot)
        return snapshot
    
    async def get_student_mastery_snapshots(
        self,
        student_id: UUID,
        chapter_id: Optional[UUID] = None,
    ) -> List[LessonMasterySnapshot]:
        """Get mastery snapshots for a student."""
        query = select(LessonMasterySnapshot).where(
            LessonMasterySnapshot.student_id == student_id,
            LessonMasterySnapshot.tenant_id == self.tenant_id,
            LessonMasterySnapshot.deleted_at.is_(None),
        )
        
        if chapter_id:
            query = query.where(LessonMasterySnapshot.chapter_id == chapter_id)
        
        query = query.order_by(LessonMasterySnapshot.evaluated_at.desc())
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    # ============================================
    # Adaptive Recommendations
    # ============================================
    
    async def create_recommendation(
        self,
        student_id: UUID,
        topic_id: UUID,
        lesson_evaluation_id: Optional[UUID],
        recommendation_type: RecommendationType,
        priority: RecommendationPriority,
        reason: str,
        current_mastery: float,
    ) -> AdaptiveRecommendation:
        """Create an adaptive recommendation."""
        recommendation = AdaptiveRecommendation(
            tenant_id=self.tenant_id,
            student_id=student_id,
            topic_id=topic_id,
            lesson_evaluation_id=lesson_evaluation_id,
            recommendation_type=recommendation_type,
            priority=priority,
            reason=reason,
            current_mastery=current_mastery,
        )
        self.session.add(recommendation)
        await self.session.flush()
        await self.session.refresh(recommendation)
        return recommendation
    
    async def get_student_recommendations(
        self,
        student_id: UUID,
        include_actioned: bool = False,
    ) -> List[AdaptiveRecommendation]:
        """Get recommendations for a student."""
        query = select(AdaptiveRecommendation).where(
            AdaptiveRecommendation.student_id == student_id,
            AdaptiveRecommendation.tenant_id == self.tenant_id,
            AdaptiveRecommendation.deleted_at.is_(None),
        )
        
        if not include_actioned:
            query = query.where(AdaptiveRecommendation.is_actioned == False)
        
        query = query.order_by(
            AdaptiveRecommendation.priority.desc(),
            AdaptiveRecommendation.created_at.desc(),
        )
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def action_recommendation(
        self,
        recommendation_id: UUID,
        actioned_by: UUID,
    ) -> AdaptiveRecommendation:
        """Mark a recommendation as actioned."""
        query = select(AdaptiveRecommendation).where(
            AdaptiveRecommendation.id == recommendation_id,
            AdaptiveRecommendation.tenant_id == self.tenant_id,
            AdaptiveRecommendation.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        rec = result.scalar_one_or_none()
        
        if not rec:
            raise ResourceNotFoundError("AdaptiveRecommendation", recommendation_id)
        
        rec.is_actioned = True
        rec.actioned_at = datetime.utcnow()
        rec.actioned_by = actioned_by
        
        await self.session.flush()
        await self.session.refresh(rec)
        return rec
    
    # ============================================
    # Mastery Data from Other Sources
    # ============================================
    
    async def get_student_daily_mastery_for_topics(
        self,
        student_id: UUID,
        topic_ids: List[UUID],
    ) -> Dict[UUID, float]:
        """Get daily mastery for topics."""
        query = select(StudentTopicMastery).where(
            StudentTopicMastery.student_id == student_id,
            StudentTopicMastery.topic_id.in_(topic_ids),
            StudentTopicMastery.tenant_id == self.tenant_id,
            StudentTopicMastery.deleted_at.is_(None),
        )
        
        result = await self.session.execute(query)
        
        return {m.topic_id: m.mastery_percent for m in result.scalars().all()}
    
    # ============================================
    # Stats
    # ============================================
    
    async def get_stats(
        self,
        class_id: Optional[UUID] = None,
    ) -> dict:
        """Get lesson evaluation statistics."""
        base_filter = and_(
            LessonEvaluation.tenant_id == self.tenant_id,
            LessonEvaluation.deleted_at.is_(None),
        )
        
        if class_id:
            base_filter = and_(base_filter, LessonEvaluation.class_id == class_id)
        
        total = await self.session.scalar(
            select(func.count(LessonEvaluation.id)).where(base_filter)
        ) or 0
        
        created = await self.session.scalar(
            select(func.count(LessonEvaluation.id)).where(
                base_filter,
                LessonEvaluation.status == LessonEvaluationStatus.CREATED,
            )
        ) or 0
        
        conducted = await self.session.scalar(
            select(func.count(LessonEvaluation.id)).where(
                base_filter,
                LessonEvaluation.status == LessonEvaluationStatus.CONDUCTED,
            )
        ) or 0
        
        evaluated = await self.session.scalar(
            select(func.count(LessonEvaluation.id)).where(
                base_filter,
                LessonEvaluation.status == LessonEvaluationStatus.EVALUATED,
            )
        ) or 0
        
        students_evaluated = await self.session.scalar(
            select(func.count(LessonEvaluationResult.id)).join(
                LessonEvaluation,
                LessonEvaluationResult.lesson_evaluation_id == LessonEvaluation.id,
            ).where(base_filter)
        ) or 0
        
        avg_score = await self.session.scalar(
            select(func.avg(LessonEvaluationResult.percentage)).join(
                LessonEvaluation,
                LessonEvaluationResult.lesson_evaluation_id == LessonEvaluation.id,
            ).where(base_filter)
        )
        
        # Recommendation counts
        rec_filter = and_(
            AdaptiveRecommendation.tenant_id == self.tenant_id,
            AdaptiveRecommendation.deleted_at.is_(None),
        )
        
        total_recs = await self.session.scalar(
            select(func.count(AdaptiveRecommendation.id)).where(rec_filter)
        ) or 0
        
        high_priority_recs = await self.session.scalar(
            select(func.count(AdaptiveRecommendation.id)).where(
                rec_filter,
                AdaptiveRecommendation.priority == RecommendationPriority.HIGH,
                AdaptiveRecommendation.is_actioned == False,
            )
        ) or 0
        
        return {
            "total_evaluations": total,
            "evaluations_created": created,
            "evaluations_conducted": conducted,
            "evaluations_evaluated": evaluated,
            "total_students_evaluated": students_evaluated,
            "avg_score_percent": round(float(avg_score), 2) if avg_score else 0.0,
            "total_recommendations": total_recs,
            "high_priority_recommendations": high_priority_recs,
        }
