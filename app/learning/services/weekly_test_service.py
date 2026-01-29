"""
CUSTOS Weekly Evaluation Service

Business logic for weekly offline tests with 40/60 question split.
"""

from datetime import date, datetime
from typing import Optional, List, Tuple, Dict
from uuid import UUID
import random

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundError, ValidationError
from app.learning.repositories.weekly_test_repo import WeeklyTestRepository
from app.learning.repositories.daily_loop_repo import DailyLoopRepository
from app.learning.models.weekly_tests import (
    WeeklyTest,
    WeeklyTestQuestion,
    WeeklyTestResult,
    WeeklyStudentPerformance,
    WeeklyTestStatus,
    QuestionStrengthType,
)
from app.learning.models.daily_loops import StudentTopicMastery
from app.learning.schemas.weekly_tests import (
    WeeklyTestCreate,
    WeeklyTestUpdate,
    StudentResultSubmit,
    BulkResultSubmit,
    GeneratePaperRequest,
    GeneratePaperResult,
    WeeklyTestPaper,
    WeeklyTestQuestionWithContent,
    WeeklyTestStats,
)
from app.academics.models.questions import Question


class WeeklyTestService:
    """
    Weekly Evaluation Service.
    
    Implements the 40/60 rule:
    - 40% questions from strong pool (student accuracy >= 70%)
    - 60% questions from weak pool (student accuracy < 40%)
    
    Handles:
    - Test creation
    - Paper generation with 40/60 split
    - Manual result submission
    - Mastery updates from weekly results
    """
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
        self.repo = WeeklyTestRepository(session, tenant_id)
        self.daily_repo = DailyLoopRepository(session, tenant_id)
    
    # ============================================
    # Weekly Test CRUD
    # ============================================
    
    async def create_weekly_test(
        self,
        data: WeeklyTestCreate,
        created_by: UUID,
    ) -> WeeklyTest:
        """Create a new weekly test."""
        # Validate strong + weak = 100
        if data.strong_percent + data.weak_percent != 100:
            raise ValidationError(
                f"Strong ({data.strong_percent}%) + Weak ({data.weak_percent}%) must equal 100%"
            )
        
        # Convert topic_ids to string list for JSON storage
        topic_ids_str = [str(t) for t in data.topic_ids]
        
        return await self.repo.create_test(
            class_id=data.class_id,
            section_id=data.section_id,
            subject_id=data.subject_id,
            topic_ids=topic_ids_str,
            created_by=created_by,
            title=data.title,
            description=data.description,
            start_date=data.start_date,
            end_date=data.end_date,
            test_date=data.test_date,
            total_questions=data.total_questions,
            total_marks=data.total_marks,
            duration_minutes=data.duration_minutes,
            strong_percent=data.strong_percent,
            weak_percent=data.weak_percent,
        )
    
    async def get_test(self, test_id: UUID) -> Optional[WeeklyTest]:
        """Get weekly test by ID."""
        return await self.repo.get_test(test_id)
    
    async def list_tests(
        self,
        class_id: Optional[UUID] = None,
        subject_id: Optional[UUID] = None,
        status: Optional[WeeklyTestStatus] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        page: int = 1,
        size: int = 20,
    ) -> Tuple[List[WeeklyTest], int]:
        """List weekly tests with filters."""
        return await self.repo.list_tests(
            class_id=class_id,
            subject_id=subject_id,
            status=status,
            start_date=start_date,
            end_date=end_date,
            page=page,
            size=size,
        )
    
    async def update_test(
        self,
        test_id: UUID,
        data: WeeklyTestUpdate,
    ) -> WeeklyTest:
        """Update a weekly test."""
        update_data = data.model_dump(exclude_unset=True)
        return await self.repo.update_test(test_id, **update_data)
    
    async def delete_test(self, test_id: UUID) -> None:
        """Delete a weekly test."""
        await self.repo.delete_test(test_id)
    
    # ============================================
    # Paper Generation (40/60 Rule)
    # ============================================
    
    async def generate_weekly_paper(
        self,
        weekly_test_id: UUID,
        request: GeneratePaperRequest,
    ) -> GeneratePaperResult:
        """
        Generate weekly test paper using 40/60 rule.
        
        Algorithm:
        1. Get test configuration (class, subject, topics, date range)
        2. Analyze daily loop data to categorize questions as strong/weak
        3. Select 40% from strong pool, 60% from weak pool
        4. If not enough questions, fill from moderate or available
        5. Assign sequential question numbers
        6. Store mapping in WeeklyTestQuestion
        """
        warnings = []
        
        # 1. Get test
        test = await self.repo.get_test(weekly_test_id)
        if not test:
            raise ResourceNotFoundError("WeeklyTest", weekly_test_id)
        
        if test.status != WeeklyTestStatus.CREATED:
            raise ValidationError(
                f"Cannot regenerate paper for test in {test.status} status"
            )
        
        # 2. Clear existing questions (if regenerating)
        cleared = await self.repo.clear_test_questions(weekly_test_id)
        if cleared > 0:
            warnings.append(f"Cleared {cleared} existing questions")
        
        # 3. Get strong/weak question categorization
        topic_ids = [UUID(t) for t in test.topic_ids]
        
        categories = await self.repo.get_strong_weak_question_ids(
            topic_ids=topic_ids,
            class_id=test.class_id,
            start_date=test.start_date,
            end_date=test.end_date,
        )
        
        strong_pool = categories["strong"]
        weak_pool = categories["weak"]
        moderate_pool = categories["moderate"]
        
        # 4. Calculate how many to select from each
        total_needed = test.total_questions
        strong_needed = int(total_needed * test.strong_percent / 100)
        weak_needed = total_needed - strong_needed  # Remaining goes to weak
        
        # 5. Select questions
        selected_strong = []
        selected_weak = []
        selected_moderate = []
        
        # Select from strong pool
        if len(strong_pool) >= strong_needed:
            selected_strong = random.sample(strong_pool, strong_needed)
        else:
            selected_strong = strong_pool.copy()
            shortfall = strong_needed - len(selected_strong)
            warnings.append(f"Only {len(strong_pool)} strong questions available (needed {strong_needed})")
            
            # Fill from moderate if allowed
            if request.include_moderate and moderate_pool:
                fill_count = min(shortfall, len(moderate_pool))
                selected_moderate.extend(random.sample(moderate_pool, fill_count))
        
        # Select from weak pool
        if len(weak_pool) >= weak_needed:
            selected_weak = random.sample(weak_pool, weak_needed)
        else:
            selected_weak = weak_pool.copy()
            shortfall = weak_needed - len(selected_weak)
            warnings.append(f"Only {len(weak_pool)} weak questions available (needed {weak_needed})")
            
            # Fill from moderate if allowed
            if request.include_moderate:
                available_moderate = [q for q in moderate_pool if q not in selected_moderate]
                fill_count = min(shortfall, len(available_moderate))
                if available_moderate:
                    selected_moderate.extend(random.sample(available_moderate, fill_count))
        
        # 6. If still not enough, get from question bank directly
        all_selected = selected_strong + selected_weak + selected_moderate
        if len(all_selected) < total_needed:
            # Get more questions from topic pool
            existing_ids = all_selected
            questions = await self.repo.get_questions_for_topics(
                topic_ids=topic_ids,
                limit=total_needed * 2,  # Get more to filter
            )
            
            additional = [q.id for q in questions if q.id not in existing_ids]
            fill_count = total_needed - len(all_selected)
            
            if additional:
                selected_moderate.extend(additional[:fill_count])
                warnings.append(f"Added {min(fill_count, len(additional))} questions from question bank")
        
        # 7. Combine and shuffle if requested
        all_questions = []
        for qid in selected_strong:
            all_questions.append((qid, QuestionStrengthType.STRONG))
        for qid in selected_weak:
            all_questions.append((qid, QuestionStrengthType.WEAK))
        for qid in selected_moderate:
            all_questions.append((qid, QuestionStrengthType.MODERATE))
        
        if request.shuffle_questions:
            random.shuffle(all_questions)
        
        # 8. Create WeeklyTestQuestion records
        marks_per_question = test.total_marks / test.total_questions if test.total_questions > 0 else 1.0
        
        questions_data = []
        for i, (qid, strength) in enumerate(all_questions):
            questions_data.append({
                "question_id": qid,
                "question_number": i + 1,
                "strength_type": strength,
                "marks": marks_per_question,
            })
        
        await self.repo.add_test_questions_bulk(weekly_test_id, questions_data)
        
        return GeneratePaperResult(
            weekly_test_id=weekly_test_id,
            total_questions_generated=len(questions_data),
            strong_questions=len(selected_strong),
            weak_questions=len(selected_weak),
            moderate_questions=len(selected_moderate),
            warnings=warnings,
        )
    
    async def get_test_paper(
        self,
        weekly_test_id: UUID,
        include_answers: bool = False,
    ) -> WeeklyTestPaper:
        """Get the test paper with questions."""
        test = await self.repo.get_test(weekly_test_id)
        if not test:
            raise ResourceNotFoundError("WeeklyTest", weekly_test_id)
        
        test_questions = await self.repo.get_test_questions(weekly_test_id)
        
        # Get full question content
        question_ids = [q.question_id for q in test_questions]
        questions_map = await self._get_questions_by_ids(question_ids)
        
        formatted_questions = []
        strong_count = 0
        weak_count = 0
        
        for tq in test_questions:
            q = questions_map.get(tq.question_id)
            
            if tq.strength_type == QuestionStrengthType.STRONG:
                strong_count += 1
            elif tq.strength_type == QuestionStrengthType.WEAK:
                weak_count += 1
            
            formatted_questions.append(WeeklyTestQuestionWithContent(
                id=tq.id,
                weekly_test_id=weekly_test_id,
                question_id=tq.question_id,
                question_number=tq.question_number,
                strength_type=tq.strength_type,
                marks=tq.marks,
                question_text=q.question_text if q else None,
                question_html=q.question_html if q else None,
                options=q.options if q else None,
                correct_answer=q.correct_answer if include_answers else None,
            ))
        
        return WeeklyTestPaper(
            test_id=weekly_test_id,
            title=test.title,
            test_date=test.test_date,
            total_marks=test.total_marks,
            duration_minutes=test.duration_minutes,
            questions=formatted_questions,
            strong_count=strong_count,
            weak_count=weak_count,
        )
    
    async def get_answer_key(
        self,
        weekly_test_id: UUID,
    ) -> WeeklyTestPaper:
        """Get the answer key (paper with answers)."""
        return await self.get_test_paper(weekly_test_id, include_answers=True)
    
    # ============================================
    # Result Submission
    # ============================================
    
    async def submit_result(
        self,
        weekly_test_id: UUID,
        result_data: StudentResultSubmit,
        submitted_by: UUID,
    ) -> WeeklyTestResult:
        """
        Submit a single student's result.
        
        Also:
        - Calculates strong/weak performance breakdown
        - Updates mastery from weekly results
        """
        test = await self.repo.get_test(weekly_test_id)
        if not test:
            raise ResourceNotFoundError("WeeklyTest", weekly_test_id)
        
        # Submit result
        result = await self.repo.submit_result(
            weekly_test_id=weekly_test_id,
            student_id=result_data.student_id,
            total_marks=test.total_marks,
            marks_obtained=result_data.marks_obtained,
            attempted_questions=result_data.attempted_questions,
            wrong_questions=result_data.wrong_questions,
            submitted_by=submitted_by,
        )
        
        # Calculate strong/weak breakdown
        await self._calculate_performance_breakdown(
            weekly_test_id=weekly_test_id,
            student_id=result_data.student_id,
            wrong_questions=result_data.wrong_questions,
        )
        
        # Update mastery
        await self._update_mastery_from_weekly(
            student_id=result_data.student_id,
            weekly_test_id=weekly_test_id,
        )
        
        # Update test stats
        await self.repo.update_test_stats(weekly_test_id)
        
        return result
    
    async def submit_results_bulk(
        self,
        weekly_test_id: UUID,
        data: BulkResultSubmit,
        submitted_by: UUID,
    ) -> List[WeeklyTestResult]:
        """Submit multiple student results at once."""
        results = []
        for result_data in data.results:
            try:
                result = await self.submit_result(
                    weekly_test_id=weekly_test_id,
                    result_data=result_data,
                    submitted_by=submitted_by,
                )
                results.append(result)
            except Exception as e:
                # Log error but continue with other results
                pass
        
        # Mark test as evaluated if results were submitted
        if results:
            await self.repo.update_test_status(
                weekly_test_id,
                WeeklyTestStatus.EVALUATED,
            )
        
        return results
    
    async def get_test_results(
        self,
        weekly_test_id: UUID,
    ) -> List[WeeklyTestResult]:
        """Get all results for a test."""
        return await self.repo.get_test_results(weekly_test_id)
    
    async def get_student_results(
        self,
        student_id: UUID,
    ) -> List[WeeklyTestResult]:
        """Get all test results for a student."""
        return await self.repo.get_student_all_results(student_id)
    
    # ============================================
    # Performance & Mastery
    # ============================================
    
    async def _calculate_performance_breakdown(
        self,
        weekly_test_id: UUID,
        student_id: UUID,
        wrong_questions: List[int],
    ) -> WeeklyStudentPerformance:
        """Calculate strong/weak performance from result."""
        test_questions = await self.repo.get_test_questions(weekly_test_id)
        
        strong_total = 0
        strong_correct = 0
        weak_total = 0
        weak_correct = 0
        
        wrong_set = set(wrong_questions)
        
        for tq in test_questions:
            is_correct = tq.question_number not in wrong_set
            
            if tq.strength_type == QuestionStrengthType.STRONG:
                strong_total += 1
                if is_correct:
                    strong_correct += 1
            elif tq.strength_type == QuestionStrengthType.WEAK:
                weak_total += 1
                if is_correct:
                    weak_correct += 1
        
        return await self.repo.create_or_update_performance(
            weekly_test_id=weekly_test_id,
            student_id=student_id,
            strong_total=strong_total,
            strong_correct=strong_correct,
            weak_total=weak_total,
            weak_correct=weak_correct,
        )
    
    async def _update_mastery_from_weekly(
        self,
        student_id: UUID,
        weekly_test_id: UUID,
    ) -> None:
        """Update topic mastery based on weekly test performance."""
        test = await self.repo.get_test(weekly_test_id)
        if not test:
            return
        
        # Get the test questions to know which topics were covered
        test_questions = await self.repo.get_test_questions(weekly_test_id)
        
        # Get the result to know which were wrong
        result = await self.repo.get_student_result(weekly_test_id, student_id)
        if not result:
            return
        
        wrong_set = set(result.wrong_questions)
        
        # Group by topic (need to get question topics)
        question_ids = [tq.question_id for tq in test_questions]
        questions_map = await self._get_questions_by_ids(question_ids)
        
        # Count correct/wrong per topic
        topic_results: Dict[UUID, Dict[str, int]] = {}
        
        for tq in test_questions:
            q = questions_map.get(tq.question_id)
            if not q or not q.topic_id:
                continue
            
            topic_id = q.topic_id
            if topic_id not in topic_results:
                topic_results[topic_id] = {"total": 0, "correct": 0}
            
            topic_results[topic_id]["total"] += 1
            if tq.question_number not in wrong_set:
                topic_results[topic_id]["correct"] += 1
        
        # Update mastery for each topic
        for topic_id, counts in topic_results.items():
            # Get or create mastery
            mastery = await self.daily_repo.get_or_create_mastery(student_id, topic_id)
            
            # Add weekly results to mastery
            mastery.total_attempts += counts["total"]
            mastery.correct_attempts += counts["correct"]
            
            # Recalculate percentage
            mastery.mastery_percent = (
                (mastery.correct_attempts / mastery.total_attempts) * 100
                if mastery.total_attempts > 0 else 0.0
            )
            
            await self.session.flush()
    
    async def get_student_performance(
        self,
        weekly_test_id: UUID,
        student_id: UUID,
    ) -> Optional[WeeklyStudentPerformance]:
        """Get student's performance breakdown."""
        return await self.repo.get_student_performance(weekly_test_id, student_id)
    
    # ============================================
    # Stats
    # ============================================
    
    async def get_stats(
        self,
        class_id: Optional[UUID] = None,
    ) -> WeeklyTestStats:
        """Get weekly test statistics."""
        stats = await self.repo.get_stats(class_id)
        return WeeklyTestStats(**stats)
    
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
