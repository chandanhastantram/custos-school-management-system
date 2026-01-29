"""
CUSTOS Weekly Evaluation Repository

Data access layer for weekly tests and results.
"""

from datetime import date, datetime
from typing import Optional, List, Tuple, Dict
from uuid import UUID
import random

from sqlalchemy import select, func, and_, or_, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundError, ValidationError, DuplicateError
from app.learning.models.weekly_tests import (
    WeeklyTest,
    WeeklyTestQuestion,
    WeeklyTestResult,
    WeeklyStudentPerformance,
    WeeklyTestStatus,
    QuestionStrengthType,
)
from app.learning.models.daily_loops import (
    DailyLoopSession,
    DailyLoopAttempt,
    StudentTopicMastery,
)
from app.academics.models.questions import Question, QuestionType, QuestionStatus


class WeeklyTestRepository:
    """Repository for weekly test operations."""
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
    
    # ============================================
    # Weekly Test CRUD
    # ============================================
    
    async def create_test(self, **data) -> WeeklyTest:
        """Create a weekly test."""
        test = WeeklyTest(
            tenant_id=self.tenant_id,
            **data
        )
        self.session.add(test)
        await self.session.flush()
        await self.session.refresh(test)
        return test
    
    async def get_test(self, test_id: UUID) -> Optional[WeeklyTest]:
        """Get weekly test by ID."""
        query = select(WeeklyTest).where(
            WeeklyTest.id == test_id,
            WeeklyTest.tenant_id == self.tenant_id,
            WeeklyTest.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
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
        query = select(WeeklyTest).where(
            WeeklyTest.tenant_id == self.tenant_id,
            WeeklyTest.deleted_at.is_(None),
        )
        
        if class_id:
            query = query.where(WeeklyTest.class_id == class_id)
        if subject_id:
            query = query.where(WeeklyTest.subject_id == subject_id)
        if status:
            query = query.where(WeeklyTest.status == status)
        if start_date:
            query = query.where(WeeklyTest.start_date >= start_date)
        if end_date:
            query = query.where(WeeklyTest.end_date <= end_date)
        
        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.session.scalar(count_query) or 0
        
        # Paginate
        query = query.order_by(WeeklyTest.created_at.desc())
        query = query.offset((page - 1) * size).limit(size)
        
        result = await self.session.execute(query)
        return list(result.scalars().all()), total
    
    async def update_test(self, test_id: UUID, **data) -> WeeklyTest:
        """Update a weekly test."""
        test = await self.get_test(test_id)
        if not test:
            raise ResourceNotFoundError("WeeklyTest", test_id)
        
        for key, value in data.items():
            if value is not None and hasattr(test, key):
                setattr(test, key, value)
        
        await self.session.flush()
        await self.session.refresh(test)
        return test
    
    async def update_test_status(
        self,
        test_id: UUID,
        status: WeeklyTestStatus,
    ) -> WeeklyTest:
        """Update test status."""
        test = await self.get_test(test_id)
        if not test:
            raise ResourceNotFoundError("WeeklyTest", test_id)
        
        test.status = status
        
        if status == WeeklyTestStatus.CONDUCTED:
            test.conducted_at = datetime.utcnow()
        elif status == WeeklyTestStatus.EVALUATED:
            test.evaluated_at = datetime.utcnow()
        
        await self.session.flush()
        await self.session.refresh(test)
        return test
    
    async def delete_test(self, test_id: UUID) -> None:
        """Soft delete a weekly test."""
        test = await self.get_test(test_id)
        if not test:
            raise ResourceNotFoundError("WeeklyTest", test_id)
        await test.soft_delete()
        await self.session.flush()
    
    # ============================================
    # Question Selection for Paper Generation
    # ============================================
    
    async def get_strong_weak_question_ids(
        self,
        topic_ids: List[UUID],
        class_id: UUID,
        start_date: date,
        end_date: date,
    ) -> Dict[str, List[UUID]]:
        """
        Get question IDs categorized by class-wide performance.
        
        Analyzes daily loop attempts for the date range to find:
        - Strong: class-wide accuracy >= 70%
        - Weak: class-wide accuracy < 40%
        - Moderate: 40-69%
        """
        # Get session IDs for the date range
        session_query = select(DailyLoopSession.id).where(
            DailyLoopSession.tenant_id == self.tenant_id,
            DailyLoopSession.class_id == class_id,
            DailyLoopSession.date >= start_date,
            DailyLoopSession.date <= end_date,
            DailyLoopSession.topic_id.in_([str(t) for t in topic_ids] if topic_ids else []),
            DailyLoopSession.deleted_at.is_(None),
        )
        
        # Get question performance from attempts
        perf_query = select(
            DailyLoopAttempt.question_id,
            func.count(DailyLoopAttempt.id).label("total"),
            func.sum(func.cast(DailyLoopAttempt.is_correct, Integer)).label("correct"),
        ).where(
            DailyLoopAttempt.session_id.in_(session_query),
        ).group_by(
            DailyLoopAttempt.question_id,
        )
        
        result = await self.session.execute(perf_query)
        
        strong = []
        moderate = []
        weak = []
        
        for row in result.all():
            accuracy = (row.correct / row.total * 100) if row.total > 0 else 0
            question_id = row.question_id
            
            if accuracy >= 70:
                strong.append(question_id)
            elif accuracy >= 40:
                moderate.append(question_id)
            else:
                weak.append(question_id)
        
        return {
            "strong": strong,
            "moderate": moderate,
            "weak": weak,
        }
    
    async def get_questions_for_topics(
        self,
        topic_ids: List[UUID],
        limit: int = 50,
    ) -> List[Question]:
        """Get all approved MCQ questions for topics."""
        # Convert topic_ids to proper format
        topic_id_values = [t if isinstance(t, UUID) else UUID(str(t)) for t in topic_ids]
        
        query = select(Question).where(
            Question.tenant_id == self.tenant_id,
            Question.topic_id.in_(topic_id_values),
            Question.question_type == QuestionType.MCQ,
            Question.status == QuestionStatus.APPROVED,
            Question.deleted_at.is_(None),
        ).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    # ============================================
    # Weekly Test Questions
    # ============================================
    
    async def add_test_question(
        self,
        weekly_test_id: UUID,
        question_id: UUID,
        question_number: int,
        strength_type: QuestionStrengthType,
        marks: float = 1.0,
    ) -> WeeklyTestQuestion:
        """Add a question to the weekly test."""
        question = WeeklyTestQuestion(
            tenant_id=self.tenant_id,
            weekly_test_id=weekly_test_id,
            question_id=question_id,
            question_number=question_number,
            strength_type=strength_type,
            marks=marks,
        )
        self.session.add(question)
        await self.session.flush()
        return question
    
    async def add_test_questions_bulk(
        self,
        weekly_test_id: UUID,
        questions_data: List[dict],
    ) -> List[WeeklyTestQuestion]:
        """Add multiple questions to the weekly test."""
        created = []
        for data in questions_data:
            question = WeeklyTestQuestion(
                tenant_id=self.tenant_id,
                weekly_test_id=weekly_test_id,
                **data
            )
            self.session.add(question)
            created.append(question)
        await self.session.flush()
        return created
    
    async def get_test_questions(
        self,
        weekly_test_id: UUID,
    ) -> List[WeeklyTestQuestion]:
        """Get all questions for a weekly test."""
        query = select(WeeklyTestQuestion).where(
            WeeklyTestQuestion.weekly_test_id == weekly_test_id,
            WeeklyTestQuestion.tenant_id == self.tenant_id,
            WeeklyTestQuestion.deleted_at.is_(None),
        ).order_by(WeeklyTestQuestion.question_number)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_question_by_number(
        self,
        weekly_test_id: UUID,
        question_number: int,
    ) -> Optional[WeeklyTestQuestion]:
        """Get a specific question by its number on the test."""
        query = select(WeeklyTestQuestion).where(
            WeeklyTestQuestion.weekly_test_id == weekly_test_id,
            WeeklyTestQuestion.question_number == question_number,
            WeeklyTestQuestion.tenant_id == self.tenant_id,
            WeeklyTestQuestion.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def clear_test_questions(self, weekly_test_id: UUID) -> int:
        """Remove all questions from a test (for regeneration)."""
        questions = await self.get_test_questions(weekly_test_id)
        count = 0
        for q in questions:
            await q.soft_delete()
            count += 1
        await self.session.flush()
        return count
    
    # ============================================
    # Weekly Test Results
    # ============================================
    
    async def submit_result(
        self,
        weekly_test_id: UUID,
        student_id: UUID,
        total_marks: float,
        marks_obtained: float,
        attempted_questions: List[int],
        wrong_questions: List[int],
        submitted_by: Optional[UUID] = None,
    ) -> WeeklyTestResult:
        """Submit a student's result."""
        # Check for duplicate
        existing = await self.get_student_result(weekly_test_id, student_id)
        if existing:
            raise DuplicateError(
                f"Result already exists for student {student_id} on test {weekly_test_id}"
            )
        
        percentage = (marks_obtained / total_marks * 100) if total_marks > 0 else 0
        
        result = WeeklyTestResult(
            tenant_id=self.tenant_id,
            weekly_test_id=weekly_test_id,
            student_id=student_id,
            total_marks=total_marks,
            marks_obtained=marks_obtained,
            attempted_questions=attempted_questions,
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
        weekly_test_id: UUID,
        student_id: UUID,
    ) -> Optional[WeeklyTestResult]:
        """Get a student's result for a test."""
        query = select(WeeklyTestResult).where(
            WeeklyTestResult.weekly_test_id == weekly_test_id,
            WeeklyTestResult.student_id == student_id,
            WeeklyTestResult.tenant_id == self.tenant_id,
            WeeklyTestResult.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_test_results(
        self,
        weekly_test_id: UUID,
    ) -> List[WeeklyTestResult]:
        """Get all results for a test."""
        query = select(WeeklyTestResult).where(
            WeeklyTestResult.weekly_test_id == weekly_test_id,
            WeeklyTestResult.tenant_id == self.tenant_id,
            WeeklyTestResult.deleted_at.is_(None),
        ).order_by(WeeklyTestResult.percentage.desc())
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_student_all_results(
        self,
        student_id: UUID,
    ) -> List[WeeklyTestResult]:
        """Get all test results for a student."""
        query = select(WeeklyTestResult).where(
            WeeklyTestResult.student_id == student_id,
            WeeklyTestResult.tenant_id == self.tenant_id,
            WeeklyTestResult.deleted_at.is_(None),
        ).order_by(WeeklyTestResult.created_at.desc())
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    # ============================================
    # Performance Tracking
    # ============================================
    
    async def create_or_update_performance(
        self,
        weekly_test_id: UUID,
        student_id: UUID,
        strong_total: int,
        strong_correct: int,
        weak_total: int,
        weak_correct: int,
        mastery_delta: float = 0.0,
    ) -> WeeklyStudentPerformance:
        """Create or update student performance record."""
        # Check existing
        query = select(WeeklyStudentPerformance).where(
            WeeklyStudentPerformance.weekly_test_id == weekly_test_id,
            WeeklyStudentPerformance.student_id == student_id,
            WeeklyStudentPerformance.tenant_id == self.tenant_id,
            WeeklyStudentPerformance.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        perf = result.scalar_one_or_none()
        
        strong_accuracy = (strong_correct / strong_total * 100) if strong_total > 0 else 0
        weak_accuracy = (weak_correct / weak_total * 100) if weak_total > 0 else 0
        total = strong_total + weak_total
        correct = strong_correct + weak_correct
        overall_accuracy = (correct / total * 100) if total > 0 else 0
        
        if perf:
            perf.strong_total = strong_total
            perf.strong_correct = strong_correct
            perf.strong_accuracy = strong_accuracy
            perf.weak_total = weak_total
            perf.weak_correct = weak_correct
            perf.weak_accuracy = weak_accuracy
            perf.mastery_delta = mastery_delta
            perf.overall_accuracy = overall_accuracy
        else:
            perf = WeeklyStudentPerformance(
                tenant_id=self.tenant_id,
                weekly_test_id=weekly_test_id,
                student_id=student_id,
                strong_total=strong_total,
                strong_correct=strong_correct,
                strong_accuracy=strong_accuracy,
                weak_total=weak_total,
                weak_correct=weak_correct,
                weak_accuracy=weak_accuracy,
                mastery_delta=mastery_delta,
                overall_accuracy=overall_accuracy,
            )
            self.session.add(perf)
        
        await self.session.flush()
        await self.session.refresh(perf)
        return perf
    
    async def get_student_performance(
        self,
        weekly_test_id: UUID,
        student_id: UUID,
    ) -> Optional[WeeklyStudentPerformance]:
        """Get student's performance breakdown."""
        query = select(WeeklyStudentPerformance).where(
            WeeklyStudentPerformance.weekly_test_id == weekly_test_id,
            WeeklyStudentPerformance.student_id == student_id,
            WeeklyStudentPerformance.tenant_id == self.tenant_id,
            WeeklyStudentPerformance.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    # ============================================
    # Stats
    # ============================================
    
    async def get_stats(
        self,
        class_id: Optional[UUID] = None,
    ) -> dict:
        """Get weekly test statistics."""
        base_filter = and_(
            WeeklyTest.tenant_id == self.tenant_id,
            WeeklyTest.deleted_at.is_(None),
        )
        
        if class_id:
            base_filter = and_(base_filter, WeeklyTest.class_id == class_id)
        
        # Total tests
        total = await self.session.scalar(
            select(func.count(WeeklyTest.id)).where(base_filter)
        ) or 0
        
        # By status
        created = await self.session.scalar(
            select(func.count(WeeklyTest.id)).where(
                base_filter,
                WeeklyTest.status == WeeklyTestStatus.CREATED,
            )
        ) or 0
        
        conducted = await self.session.scalar(
            select(func.count(WeeklyTest.id)).where(
                base_filter,
                WeeklyTest.status == WeeklyTestStatus.CONDUCTED,
            )
        ) or 0
        
        evaluated = await self.session.scalar(
            select(func.count(WeeklyTest.id)).where(
                base_filter,
                WeeklyTest.status == WeeklyTestStatus.EVALUATED,
            )
        ) or 0
        
        # Total students evaluated
        students_evaluated = await self.session.scalar(
            select(func.count(WeeklyTestResult.id)).join(
                WeeklyTest,
                WeeklyTestResult.weekly_test_id == WeeklyTest.id,
            ).where(base_filter)
        ) or 0
        
        # Average score
        avg_score = await self.session.scalar(
            select(func.avg(WeeklyTestResult.percentage)).join(
                WeeklyTest,
                WeeklyTestResult.weekly_test_id == WeeklyTest.id,
            ).where(base_filter)
        )
        
        return {
            "total_tests": total,
            "tests_created": created,
            "tests_conducted": conducted,
            "tests_evaluated": evaluated,
            "total_students_evaluated": students_evaluated,
            "avg_score_percent": round(float(avg_score), 2) if avg_score else 0.0,
        }
    
    async def update_test_stats(self, test_id: UUID) -> None:
        """Update test statistics after results are submitted."""
        results = await self.get_test_results(test_id)
        
        if results:
            students_appeared = len(results)
            avg_score = sum(r.percentage for r in results) / students_appeared
            
            await self.session.execute(
                update(WeeklyTest)
                .where(WeeklyTest.id == test_id)
                .values(
                    students_appeared=students_appeared,
                    avg_score_percent=round(avg_score, 2),
                )
            )
            await self.session.flush()
