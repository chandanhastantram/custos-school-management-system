"""
CUSTOS Lesson Evaluation & Adaptive Service

Business logic for lesson evaluations and rule-based adaptive recommendations.
"""

from datetime import datetime
from typing import Optional, List, Tuple, Dict
from uuid import UUID
import random

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundError, ValidationError
from app.learning.repositories.lesson_eval_repo import LessonEvaluationRepository
from app.learning.repositories.daily_loop_repo import DailyLoopRepository
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
from app.learning.schemas.lesson_evaluation import (
    LessonEvaluationCreate,
    LessonEvaluationUpdate,
    LessonResultSubmit,
    BulkLessonResultSubmit,
    GenerateLessonPaperRequest,
    GenerateLessonPaperResult,
    LessonEvaluationPaper,
    LessonQuestionWithContent,
    CalculateMasteryResult,
    AdaptiveRecommendationsForStudent,
    AdaptiveRecommendationWithDetails,
    LessonEvaluationStats,
)
from app.academics.models.questions import Question
from app.academics.models.lesson_plans import LessonPlan, LessonPlanUnit


class LessonEvaluationService:
    """
    Lesson Evaluation & Adaptive Learning Service.
    
    Handles:
    - End-of-lesson/chapter evaluations
    - Paper generation from lesson plan topics
    - Result submission and processing
    - Mastery calculation (combining daily, weekly, lesson data)
    - Adaptive recommendations based on mastery thresholds
    
    Adaptive Rules:
    - mastery < 40%  → REMEDIAL_CLASS + HIGH priority
    - mastery 40-60% → EXTRA_DAILY_LOOP + MEDIUM priority  
    - mastery 60-75% → REVISION + LOW priority
    - mastery >= 75% → No recommendation (mastered)
    """
    
    # Mastery thresholds for adaptive recommendations
    THRESHOLD_REMEDIAL = 40      # Below this → REMEDIAL_CLASS
    THRESHOLD_EXTRA_LOOP = 60    # 40-60 → EXTRA_DAILY_LOOP
    THRESHOLD_REVISION = 75      # 60-75 → REVISION
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
        self.repo = LessonEvaluationRepository(session, tenant_id)
        self.daily_repo = DailyLoopRepository(session, tenant_id)
    
    # ============================================
    # Lesson Evaluation CRUD
    # ============================================
    
    async def create_lesson_evaluation(
        self,
        data: LessonEvaluationCreate,
        created_by: UUID,
    ) -> LessonEvaluation:
        """Create a lesson evaluation from a lesson plan."""
        return await self.repo.create_evaluation(
            lesson_plan_id=data.lesson_plan_id,
            class_id=data.class_id,
            section_id=data.section_id,
            subject_id=data.subject_id,
            chapter_id=data.chapter_id,
            created_by=created_by,
            title=data.title,
            description=data.description,
            test_date=data.test_date,
            total_questions=data.total_questions,
            total_marks=data.total_marks,
            duration_minutes=data.duration_minutes,
        )
    
    async def get_evaluation(self, evaluation_id: UUID) -> Optional[LessonEvaluation]:
        """Get lesson evaluation by ID."""
        return await self.repo.get_evaluation(evaluation_id)
    
    async def list_evaluations(
        self,
        class_id: Optional[UUID] = None,
        lesson_plan_id: Optional[UUID] = None,
        status: Optional[LessonEvaluationStatus] = None,
        page: int = 1,
        size: int = 20,
    ) -> Tuple[List[LessonEvaluation], int]:
        """List lesson evaluations with filters."""
        return await self.repo.list_evaluations(
            class_id=class_id,
            lesson_plan_id=lesson_plan_id,
            status=status,
            page=page,
            size=size,
        )
    
    async def update_evaluation(
        self,
        evaluation_id: UUID,
        data: LessonEvaluationUpdate,
    ) -> LessonEvaluation:
        """Update a lesson evaluation."""
        update_data = data.model_dump(exclude_unset=True)
        return await self.repo.update_evaluation(evaluation_id, **update_data)
    
    async def delete_evaluation(self, evaluation_id: UUID) -> None:
        """Delete a lesson evaluation."""
        await self.repo.delete_evaluation(evaluation_id)
    
    # ============================================
    # Paper Generation
    # ============================================
    
    async def generate_lesson_paper(
        self,
        lesson_evaluation_id: UUID,
        request: GenerateLessonPaperRequest,
    ) -> GenerateLessonPaperResult:
        """
        Generate lesson evaluation paper.
        
        Selects questions from all topics in the lesson plan.
        """
        warnings = []
        
        evaluation = await self.repo.get_evaluation(lesson_evaluation_id)
        if not evaluation:
            raise ResourceNotFoundError("LessonEvaluation", lesson_evaluation_id)
        
        if evaluation.status != LessonEvaluationStatus.CREATED:
            raise ValidationError(
                f"Cannot regenerate paper for evaluation in {evaluation.status} status"
            )
        
        # Clear existing questions
        cleared = await self.repo.clear_evaluation_questions(lesson_evaluation_id)
        if cleared > 0:
            warnings.append(f"Cleared {cleared} existing questions")
        
        # Get questions from lesson plan topics
        questions = await self.repo.get_questions_for_lesson_plan(
            lesson_plan_id=evaluation.lesson_plan_id,
            limit=evaluation.total_questions * 2,
        )
        
        if len(questions) < evaluation.total_questions:
            warnings.append(
                f"Only {len(questions)} questions available (need {evaluation.total_questions})"
            )
        
        # Select needed number of questions
        selected = questions[:evaluation.total_questions]
        
        if request.shuffle_questions:
            random.shuffle(selected)
        
        # Get unique topics covered
        topics_covered = set()
        
        # Create question records
        marks_per_question = (
            evaluation.total_marks / evaluation.total_questions
            if evaluation.total_questions > 0 else 1.0
        )
        
        questions_data = []
        for i, q in enumerate(selected):
            if q.topic_id:
                topics_covered.add(q.topic_id)
            
            questions_data.append({
                "question_id": q.id,
                "question_number": i + 1,
                "topic_id": q.topic_id,
                "marks": marks_per_question,
            })
        
        await self.repo.add_questions_bulk(lesson_evaluation_id, questions_data)
        
        return GenerateLessonPaperResult(
            lesson_evaluation_id=lesson_evaluation_id,
            total_questions_generated=len(questions_data),
            topics_covered=len(topics_covered),
            warnings=warnings,
        )
    
    async def get_evaluation_paper(
        self,
        lesson_evaluation_id: UUID,
        include_answers: bool = False,
    ) -> LessonEvaluationPaper:
        """Get the evaluation paper with questions."""
        evaluation = await self.repo.get_evaluation(lesson_evaluation_id)
        if not evaluation:
            raise ResourceNotFoundError("LessonEvaluation", lesson_evaluation_id)
        
        eval_questions = await self.repo.get_evaluation_questions(lesson_evaluation_id)
        
        question_ids = [q.question_id for q in eval_questions]
        questions_map = await self._get_questions_by_ids(question_ids)
        
        formatted = []
        for eq in eval_questions:
            q = questions_map.get(eq.question_id)
            
            formatted.append(LessonQuestionWithContent(
                id=eq.id,
                lesson_evaluation_id=lesson_evaluation_id,
                question_id=eq.question_id,
                question_number=eq.question_number,
                marks=eq.marks,
                topic_id=eq.topic_id,
                question_text=q.question_text if q else None,
                question_html=q.question_html if q else None,
                options=q.options if q else None,
                correct_answer=q.correct_answer if include_answers else None,
            ))
        
        return LessonEvaluationPaper(
            evaluation_id=lesson_evaluation_id,
            title=evaluation.title,
            test_date=evaluation.test_date,
            total_marks=evaluation.total_marks,
            duration_minutes=evaluation.duration_minutes,
            questions=formatted,
        )
    
    async def get_answer_key(
        self,
        lesson_evaluation_id: UUID,
    ) -> LessonEvaluationPaper:
        """Get the answer key."""
        return await self.get_evaluation_paper(lesson_evaluation_id, include_answers=True)
    
    # ============================================
    # Result Submission
    # ============================================
    
    async def submit_result(
        self,
        lesson_evaluation_id: UUID,
        result_data: LessonResultSubmit,
        submitted_by: UUID,
    ) -> LessonEvaluationResult:
        """
        Submit a single student's result.
        
        Also triggers:
        - Mastery calculation
        - Adaptive recommendation generation
        """
        evaluation = await self.repo.get_evaluation(lesson_evaluation_id)
        if not evaluation:
            raise ResourceNotFoundError("LessonEvaluation", lesson_evaluation_id)
        
        # Submit result
        result = await self.repo.submit_result(
            lesson_evaluation_id=lesson_evaluation_id,
            student_id=result_data.student_id,
            total_marks=evaluation.total_marks,
            marks_obtained=result_data.marks_obtained,
            wrong_questions=result_data.wrong_questions,
            submitted_by=submitted_by,
        )
        
        # Calculate mastery and generate recommendations
        if evaluation.chapter_id:
            await self.calculate_lesson_mastery(
                student_id=result_data.student_id,
                chapter_id=evaluation.chapter_id,
                lesson_evaluation_id=lesson_evaluation_id,
            )
        
        # Update evaluation stats
        await self.repo.update_evaluation_stats(lesson_evaluation_id)
        
        return result
    
    async def submit_results_bulk(
        self,
        lesson_evaluation_id: UUID,
        data: BulkLessonResultSubmit,
        submitted_by: UUID,
    ) -> List[LessonEvaluationResult]:
        """Submit multiple student results at once."""
        results = []
        for result_data in data.results:
            try:
                result = await self.submit_result(
                    lesson_evaluation_id=lesson_evaluation_id,
                    result_data=result_data,
                    submitted_by=submitted_by,
                )
                results.append(result)
            except Exception:
                pass  # Continue with other results
        
        # Mark as evaluated
        if results:
            await self.repo.update_evaluation_status(
                lesson_evaluation_id,
                LessonEvaluationStatus.EVALUATED,
            )
        
        return results
    
    async def get_evaluation_results(
        self,
        lesson_evaluation_id: UUID,
    ) -> List[LessonEvaluationResult]:
        """Get all results for an evaluation."""
        return await self.repo.get_evaluation_results(lesson_evaluation_id)
    
    async def get_student_results(
        self,
        student_id: UUID,
    ) -> List[LessonEvaluationResult]:
        """Get all lesson evaluation results for a student."""
        return await self.repo.get_student_all_results(student_id)
    
    # ============================================
    # Mastery Calculation
    # ============================================
    
    async def calculate_lesson_mastery(
        self,
        student_id: UUID,
        chapter_id: UUID,
        lesson_evaluation_id: Optional[UUID] = None,
    ) -> CalculateMasteryResult:
        """
        Calculate combined mastery for a chapter.
        
        Combines:
        - Daily mastery (from daily loop attempts)
        - Weekly mastery (from weekly test results)
        - Lesson mastery (from this lesson evaluation)
        
        Weights: Daily 30%, Weekly 30%, Lesson 40%
        """
        # Get topics for this chapter
        topic_ids = await self._get_topics_for_chapter(chapter_id)
        
        # Get daily mastery
        daily_mastery_map = await self.repo.get_student_daily_mastery_for_topics(
            student_id, topic_ids
        )
        daily_avg = (
            sum(daily_mastery_map.values()) / len(daily_mastery_map)
            if daily_mastery_map else 0.0
        )
        
        # Get weekly mastery (average from weekly test results)
        # Simplified: use daily mastery as proxy for now
        weekly_avg = daily_avg  # TODO: Implement proper weekly mastery calculation
        
        # Get lesson mastery
        lesson_mastery = 0.0
        if lesson_evaluation_id:
            result = await self.repo.get_student_result(
                lesson_evaluation_id, student_id
            )
            if result:
                lesson_mastery = result.percentage
        
        # Combined mastery (weighted)
        combined = (
            daily_avg * 0.30 +
            weekly_avg * 0.30 +
            lesson_mastery * 0.40
        )
        
        # Create mastery snapshot
        await self.repo.create_mastery_snapshot(
            student_id=student_id,
            chapter_id=chapter_id,
            lesson_evaluation_id=lesson_evaluation_id,
            mastery_percent=combined,
            daily_mastery=daily_avg,
            weekly_mastery=weekly_avg,
            lesson_mastery=lesson_mastery,
        )
        
        # Generate adaptive recommendations for weak topics
        recs_generated = await self.generate_adaptive_recommendations(
            student_id=student_id,
            chapter_id=chapter_id,
            lesson_evaluation_id=lesson_evaluation_id,
        )
        
        return CalculateMasteryResult(
            student_id=student_id,
            chapter_id=chapter_id,
            daily_mastery=round(daily_avg, 2),
            weekly_mastery=round(weekly_avg, 2),
            lesson_mastery=round(lesson_mastery, 2),
            combined_mastery=round(combined, 2),
            recommendations_generated=recs_generated,
        )
    
    # ============================================
    # Adaptive Recommendations
    # ============================================
    
    async def generate_adaptive_recommendations(
        self,
        student_id: UUID,
        chapter_id: UUID,
        lesson_evaluation_id: Optional[UUID] = None,
    ) -> int:
        """
        Generate adaptive recommendations based on mastery.
        
        Rules:
        - mastery < 40%  → REMEDIAL_CLASS + HIGH
        - mastery 40-60% → EXTRA_DAILY_LOOP + MEDIUM
        - mastery 60-75% → REVISION + LOW
        - mastery >= 75% → No action (mastered)
        """
        topic_ids = await self._get_topics_for_chapter(chapter_id)
        mastery_map = await self.repo.get_student_daily_mastery_for_topics(
            student_id, topic_ids
        )
        
        recommendations_created = 0
        
        for topic_id in topic_ids:
            mastery = mastery_map.get(topic_id, 0.0)
            
            rec_type = None
            priority = None
            reason = ""
            
            if mastery < self.THRESHOLD_REMEDIAL:
                rec_type = RecommendationType.REMEDIAL_CLASS
                priority = RecommendationPriority.HIGH
                reason = f"Mastery at {mastery:.1f}% is critically low. Remedial class recommended."
            
            elif mastery < self.THRESHOLD_EXTRA_LOOP:
                rec_type = RecommendationType.EXTRA_DAILY_LOOP
                priority = RecommendationPriority.MEDIUM
                reason = f"Mastery at {mastery:.1f}% needs improvement. Extra daily practice recommended."
            
            elif mastery < self.THRESHOLD_REVISION:
                rec_type = RecommendationType.REVISION
                priority = RecommendationPriority.LOW
                reason = f"Mastery at {mastery:.1f}% is moderate. Quick revision recommended."
            
            # Create recommendation if needed
            if rec_type and priority:
                await self.repo.create_recommendation(
                    student_id=student_id,
                    topic_id=topic_id,
                    lesson_evaluation_id=lesson_evaluation_id,
                    recommendation_type=rec_type,
                    priority=priority,
                    reason=reason,
                    current_mastery=mastery,
                )
                recommendations_created += 1
        
        return recommendations_created
    
    async def get_student_recommendations(
        self,
        student_id: UUID,
        include_actioned: bool = False,
    ) -> AdaptiveRecommendationsForStudent:
        """Get all recommendations for a student."""
        recommendations = await self.repo.get_student_recommendations(
            student_id, include_actioned
        )
        
        high = sum(1 for r in recommendations if r.priority == RecommendationPriority.HIGH)
        medium = sum(1 for r in recommendations if r.priority == RecommendationPriority.MEDIUM)
        low = sum(1 for r in recommendations if r.priority == RecommendationPriority.LOW)
        
        formatted = [
            AdaptiveRecommendationWithDetails(
                id=r.id,
                tenant_id=r.tenant_id,
                student_id=r.student_id,
                topic_id=r.topic_id,
                lesson_evaluation_id=r.lesson_evaluation_id,
                recommendation_type=r.recommendation_type,
                priority=r.priority,
                reason=r.reason,
                current_mastery=r.current_mastery,
                is_actioned=r.is_actioned,
                actioned_at=r.actioned_at,
                actioned_by=r.actioned_by,
                created_at=r.created_at,
            )
            for r in recommendations
        ]
        
        return AdaptiveRecommendationsForStudent(
            student_id=student_id,
            total_recommendations=len(recommendations),
            high_priority=high,
            medium_priority=medium,
            low_priority=low,
            recommendations=formatted,
        )
    
    async def action_recommendation(
        self,
        recommendation_id: UUID,
        actioned_by: UUID,
    ) -> AdaptiveRecommendation:
        """Mark a recommendation as actioned."""
        return await self.repo.action_recommendation(recommendation_id, actioned_by)
    
    # ============================================
    # Stats
    # ============================================
    
    async def get_stats(
        self,
        class_id: Optional[UUID] = None,
    ) -> LessonEvaluationStats:
        """Get lesson evaluation statistics."""
        stats = await self.repo.get_stats(class_id)
        return LessonEvaluationStats(**stats)
    
    # ============================================
    # Helpers
    # ============================================
    
    async def _get_questions_by_ids(
        self,
        question_ids: List[UUID],
    ) -> Dict[UUID, Question]:
        """Get questions by IDs as a map."""
        if not question_ids:
            return {}
        
        query = select(Question).where(
            Question.id.in_(question_ids),
            Question.tenant_id == self.tenant_id,
            Question.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        questions = result.scalars().all()
        
        return {q.id: q for q in questions}
    
    async def _get_topics_for_chapter(self, chapter_id: UUID) -> List[UUID]:
        """Get topic IDs for a chapter."""
        from app.academics.models.syllabus import SyllabusTopic
        
        query = select(SyllabusTopic.id).where(
            SyllabusTopic.unit_id == chapter_id,
            SyllabusTopic.tenant_id == self.tenant_id,
            SyllabusTopic.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        return [row[0] for row in result.all()]
