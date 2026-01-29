"""
CUSTOS Daily Learning Loop Repository

Data access layer for daily loop sessions, attempts, and mastery.
"""

from datetime import date, datetime
from typing import Optional, List, Tuple, Dict
from uuid import UUID

from sqlalchemy import select, func, and_, or_, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundError, ValidationError, DuplicateError
from app.learning.models.daily_loops import (
    DailyLoopSession,
    DailyLoopAttempt,
    StudentTopicMastery,
)
from app.scheduling.models.schedule import ScheduleEntry
from app.academics.models.questions import Question, QuestionType, QuestionStatus


class DailyLoopRepository:
    """Repository for daily loop operations."""
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
    
    # ============================================
    # Session Operations
    # ============================================
    
    async def create_session(
        self,
        schedule_entry_id: UUID,
        class_id: UUID,
        section_id: Optional[UUID],
        subject_id: UUID,
        topic_id: UUID,
        session_date: date,
        max_questions: int = 10,
        time_limit_minutes: Optional[int] = None,
    ) -> DailyLoopSession:
        """Create a daily loop session."""
        # Check if session already exists for this schedule entry
        existing = await self.get_session_by_schedule_entry(schedule_entry_id)
        if existing:
            raise DuplicateError(
                f"Session already exists for schedule entry {schedule_entry_id}"
            )
        
        session = DailyLoopSession(
            tenant_id=self.tenant_id,
            schedule_entry_id=schedule_entry_id,
            class_id=class_id,
            section_id=section_id,
            subject_id=subject_id,
            topic_id=topic_id,
            date=session_date,
            max_questions=max_questions,
            time_limit_minutes=time_limit_minutes,
        )
        self.session.add(session)
        await self.session.flush()
        await self.session.refresh(session)
        return session
    
    async def get_session(self, session_id: UUID) -> Optional[DailyLoopSession]:
        """Get session by ID."""
        query = select(DailyLoopSession).where(
            DailyLoopSession.id == session_id,
            DailyLoopSession.tenant_id == self.tenant_id,
            DailyLoopSession.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_session_by_schedule_entry(
        self, 
        schedule_entry_id: UUID,
    ) -> Optional[DailyLoopSession]:
        """Get session by schedule entry ID."""
        query = select(DailyLoopSession).where(
            DailyLoopSession.schedule_entry_id == schedule_entry_id,
            DailyLoopSession.tenant_id == self.tenant_id,
            DailyLoopSession.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_sessions_by_date(
        self,
        session_date: date,
        class_id: Optional[UUID] = None,
    ) -> List[DailyLoopSession]:
        """Get all sessions for a date."""
        query = select(DailyLoopSession).where(
            DailyLoopSession.tenant_id == self.tenant_id,
            DailyLoopSession.date == session_date,
            DailyLoopSession.deleted_at.is_(None),
        )
        
        if class_id:
            query = query.where(DailyLoopSession.class_id == class_id)
        
        query = query.order_by(DailyLoopSession.created_at)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_student_sessions_today(
        self,
        student_id: UUID,
        class_id: UUID,
        today: date,
    ) -> List[DailyLoopSession]:
        """Get today's sessions for a student's class."""
        query = select(DailyLoopSession).where(
            DailyLoopSession.tenant_id == self.tenant_id,
            DailyLoopSession.class_id == class_id,
            DailyLoopSession.date == today,
            DailyLoopSession.is_active == True,
            DailyLoopSession.deleted_at.is_(None),
        )
        query = query.order_by(DailyLoopSession.created_at)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def update_session_stats(self, session_id: UUID) -> None:
        """Update session statistics based on attempts."""
        # Get attempt stats
        stats_query = select(
            func.count(DailyLoopAttempt.id).label("total"),
            func.count(func.distinct(DailyLoopAttempt.student_id)).label("unique_students"),
            func.avg(
                func.cast(DailyLoopAttempt.is_correct, Integer) * 100
            ).label("avg_score"),
        ).where(
            DailyLoopAttempt.session_id == session_id,
        )
        
        result = await self.session.execute(stats_query)
        row = result.one()
        
        # Update session
        await self.session.execute(
            update(DailyLoopSession)
            .where(DailyLoopSession.id == session_id)
            .values(
                total_attempts=row.total or 0,
                unique_students=row.unique_students or 0,
                avg_score_percent=float(row.avg_score) if row.avg_score else None,
            )
        )
        await self.session.flush()
    
    async def list_sessions(
        self,
        class_id: Optional[UUID] = None,
        topic_id: Optional[UUID] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        page: int = 1,
        size: int = 20,
    ) -> Tuple[List[DailyLoopSession], int]:
        """List sessions with filters."""
        query = select(DailyLoopSession).where(
            DailyLoopSession.tenant_id == self.tenant_id,
            DailyLoopSession.deleted_at.is_(None),
        )
        
        if class_id:
            query = query.where(DailyLoopSession.class_id == class_id)
        if topic_id:
            query = query.where(DailyLoopSession.topic_id == topic_id)
        if start_date:
            query = query.where(DailyLoopSession.date >= start_date)
        if end_date:
            query = query.where(DailyLoopSession.date <= end_date)
        
        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.session.scalar(count_query) or 0
        
        # Paginate
        query = query.order_by(DailyLoopSession.date.desc())
        query = query.offset((page - 1) * size).limit(size)
        
        result = await self.session.execute(query)
        return list(result.scalars().all()), total
    
    # ============================================
    # Attempt Operations
    # ============================================
    
    async def create_attempt(
        self,
        session_id: UUID,
        student_id: UUID,
        question_id: UUID,
        selected_option: str,
        is_correct: bool,
        time_taken_seconds: int = 0,
    ) -> DailyLoopAttempt:
        """Create a single attempt."""
        # Check attempt number (how many times has this student attempted this question?)
        count_query = select(func.count(DailyLoopAttempt.id)).where(
            DailyLoopAttempt.session_id == session_id,
            DailyLoopAttempt.student_id == student_id,
            DailyLoopAttempt.question_id == question_id,
        )
        attempt_count = await self.session.scalar(count_query) or 0
        
        attempt = DailyLoopAttempt(
            session_id=session_id,
            student_id=student_id,
            question_id=question_id,
            selected_option=selected_option,
            is_correct=is_correct,
            time_taken_seconds=time_taken_seconds,
            attempt_number=attempt_count + 1,
        )
        self.session.add(attempt)
        await self.session.flush()
        await self.session.refresh(attempt)
        return attempt
    
    async def get_attempt(self, attempt_id: UUID) -> Optional[DailyLoopAttempt]:
        """Get attempt by ID."""
        query = select(DailyLoopAttempt).where(
            DailyLoopAttempt.id == attempt_id,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_student_attempts_for_session(
        self,
        session_id: UUID,
        student_id: UUID,
    ) -> List[DailyLoopAttempt]:
        """Get all attempts by a student for a session."""
        query = select(DailyLoopAttempt).where(
            DailyLoopAttempt.session_id == session_id,
            DailyLoopAttempt.student_id == student_id,
        ).order_by(DailyLoopAttempt.created_at)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_student_attempts_today(
        self,
        student_id: UUID,
        today: date,
    ) -> List[DailyLoopAttempt]:
        """Get all attempts by a student today."""
        # Get session IDs for today
        session_query = select(DailyLoopSession.id).where(
            DailyLoopSession.tenant_id == self.tenant_id,
            DailyLoopSession.date == today,
            DailyLoopSession.deleted_at.is_(None),
        )
        
        query = select(DailyLoopAttempt).where(
            DailyLoopAttempt.session_id.in_(session_query),
            DailyLoopAttempt.student_id == student_id,
        ).order_by(DailyLoopAttempt.created_at)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    # ============================================
    # Mastery Operations
    # ============================================
    
    async def get_or_create_mastery(
        self,
        student_id: UUID,
        topic_id: UUID,
    ) -> StudentTopicMastery:
        """Get or create mastery record for student+topic."""
        query = select(StudentTopicMastery).where(
            StudentTopicMastery.student_id == student_id,
            StudentTopicMastery.topic_id == topic_id,
            StudentTopicMastery.tenant_id == self.tenant_id,
            StudentTopicMastery.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        mastery = result.scalar_one_or_none()
        
        if not mastery:
            mastery = StudentTopicMastery(
                tenant_id=self.tenant_id,
                student_id=student_id,
                topic_id=topic_id,
            )
            self.session.add(mastery)
            await self.session.flush()
            await self.session.refresh(mastery)
        
        return mastery
    
    async def update_mastery(
        self,
        student_id: UUID,
        topic_id: UUID,
        is_correct: bool,
    ) -> StudentTopicMastery:
        """Update mastery record after an attempt."""
        mastery = await self.get_or_create_mastery(student_id, topic_id)
        
        # Update counts
        mastery.total_attempts += 1
        if is_correct:
            mastery.correct_attempts += 1
            mastery.current_streak += 1
            if mastery.current_streak > mastery.best_streak:
                mastery.best_streak = mastery.current_streak
        else:
            mastery.current_streak = 0
        
        # Recalculate mastery percent
        mastery.mastery_percent = (
            (mastery.correct_attempts / mastery.total_attempts) * 100
            if mastery.total_attempts > 0 else 0.0
        )
        
        mastery.last_attempt_date = date.today()
        
        await self.session.flush()
        await self.session.refresh(mastery)
        return mastery
    
    async def get_student_mastery(
        self,
        student_id: UUID,
        topic_id: UUID,
    ) -> Optional[StudentTopicMastery]:
        """Get mastery for a specific student+topic."""
        query = select(StudentTopicMastery).where(
            StudentTopicMastery.student_id == student_id,
            StudentTopicMastery.topic_id == topic_id,
            StudentTopicMastery.tenant_id == self.tenant_id,
            StudentTopicMastery.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_student_all_mastery(
        self,
        student_id: UUID,
    ) -> List[StudentTopicMastery]:
        """Get all mastery records for a student."""
        query = select(StudentTopicMastery).where(
            StudentTopicMastery.student_id == student_id,
            StudentTopicMastery.tenant_id == self.tenant_id,
            StudentTopicMastery.deleted_at.is_(None),
        ).order_by(StudentTopicMastery.mastery_percent.desc())
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_strong_weak_question_ids(
        self,
        student_id: UUID,
        topic_id: UUID,
    ) -> Dict[str, List[UUID]]:
        """
        Get question IDs categorized by student performance.
        
        Returns dict with:
        - strong: questions with >= 70% accuracy
        - weak: questions with < 40% accuracy
        - moderate: questions with 40-69% accuracy
        """
        # Get all attempts for this student on questions for this topic
        query = select(
            DailyLoopAttempt.question_id,
            func.count(DailyLoopAttempt.id).label("total"),
            func.sum(func.cast(DailyLoopAttempt.is_correct, Integer)).label("correct"),
        ).join(
            DailyLoopSession,
            DailyLoopAttempt.session_id == DailyLoopSession.id,
        ).where(
            DailyLoopSession.topic_id == topic_id,
            DailyLoopSession.tenant_id == self.tenant_id,
            DailyLoopAttempt.student_id == student_id,
        ).group_by(
            DailyLoopAttempt.question_id,
        )
        
        result = await self.session.execute(query)
        
        strong = []
        moderate = []
        weak = []
        
        for row in result.all():
            accuracy = (row.correct / row.total * 100) if row.total > 0 else 0
            if accuracy >= 70:
                strong.append(row.question_id)
            elif accuracy >= 40:
                moderate.append(row.question_id)
            else:
                weak.append(row.question_id)
        
        return {
            "strong": strong,
            "moderate": moderate,
            "weak": weak,
        }
    
    # ============================================
    # Question Selection
    # ============================================
    
    async def get_questions_for_topic(
        self,
        topic_id: UUID,
        limit: int = 10,
        exclude_ids: Optional[List[UUID]] = None,
    ) -> List[Question]:
        """Get approved MCQ questions for a topic."""
        query = select(Question).where(
            Question.tenant_id == self.tenant_id,
            Question.topic_id == topic_id,
            Question.question_type == QuestionType.MCQ,
            Question.status == QuestionStatus.APPROVED,
            Question.deleted_at.is_(None),
        )
        
        if exclude_ids:
            query = query.where(Question.id.notin_(exclude_ids))
        
        # Order by usage count (prefer less-used questions)
        query = query.order_by(Question.usage_count.asc())
        query = query.limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    # ============================================
    # Stats
    # ============================================
    
    async def get_stats(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> dict:
        """Get daily loop statistics."""
        session_filter = and_(
            DailyLoopSession.tenant_id == self.tenant_id,
            DailyLoopSession.deleted_at.is_(None),
        )
        
        if start_date:
            session_filter = and_(session_filter, DailyLoopSession.date >= start_date)
        if end_date:
            session_filter = and_(session_filter, DailyLoopSession.date <= end_date)
        
        # Total sessions
        total_sessions = await self.session.scalar(
            select(func.count(DailyLoopSession.id)).where(session_filter)
        ) or 0
        
        # Sessions today
        today = date.today()
        sessions_today = await self.session.scalar(
            select(func.count(DailyLoopSession.id)).where(
                session_filter,
                DailyLoopSession.date == today,
            )
        ) or 0
        
        # Total attempts (need to join with sessions for tenant filtering)
        attempt_query = select(func.count(DailyLoopAttempt.id)).join(
            DailyLoopSession,
            DailyLoopAttempt.session_id == DailyLoopSession.id,
        ).where(session_filter)
        total_attempts = await self.session.scalar(attempt_query) or 0
        
        # Attempts today
        attempts_today_query = select(func.count(DailyLoopAttempt.id)).join(
            DailyLoopSession,
            DailyLoopAttempt.session_id == DailyLoopSession.id,
        ).where(
            session_filter,
            DailyLoopSession.date == today,
        )
        attempts_today = await self.session.scalar(attempts_today_query) or 0
        
        # Unique students
        unique_students = await self.session.scalar(
            select(func.count(func.distinct(DailyLoopAttempt.student_id))).join(
                DailyLoopSession,
                DailyLoopAttempt.session_id == DailyLoopSession.id,
            ).where(session_filter)
        ) or 0
        
        # Average accuracy
        avg_accuracy = await self.session.scalar(
            select(func.avg(func.cast(DailyLoopAttempt.is_correct, Integer) * 100)).join(
                DailyLoopSession,
                DailyLoopAttempt.session_id == DailyLoopSession.id,
            ).where(session_filter)
        )
        
        return {
            "total_sessions": total_sessions,
            "total_attempts": total_attempts,
            "unique_students": unique_students,
            "avg_accuracy_percent": round(float(avg_accuracy), 2) if avg_accuracy else 0.0,
            "sessions_today": sessions_today,
            "attempts_today": attempts_today,
        }
