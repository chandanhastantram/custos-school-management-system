"""
CUSTOS Daily Learning Loop Service

Business logic for daily loop operations.
"""

from datetime import date
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundError, ValidationError
from app.learning.repositories.daily_loop_repo import DailyLoopRepository
from app.learning.models.daily_loops import (
    DailyLoopSession,
    DailyLoopAttempt,
    StudentTopicMastery,
)
from app.learning.schemas.daily_loops import (
    MasteryLevel,
    DailySessionCreate,
    AttemptSubmit,
    AttemptBulkSubmit,
    QuestionOption,
    QuestionForAttempt,
    StrongWeakQuestion,
    StrongWeakAnalysis,
    StudentMasterySummary,
    MasteryWithDetails,
    TodaySessionInfo,
    DailyLoopStats,
)
from app.scheduling.models.schedule import ScheduleEntry
from app.academics.models.questions import Question


class DailyLoopService:
    """
    Daily Learning Loop Service.
    
    Handles:
    - Session creation from schedule entries
    - Attempt submission and validation
    - Mastery calculation and updates
    - Strong/weak question analysis
    - Question selection for sessions
    """
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
        self.repo = DailyLoopRepository(session, tenant_id)
    
    # ============================================
    # Session Operations
    # ============================================
    
    async def create_daily_session(
        self,
        schedule_entry_id: UUID,
        max_questions: int = 10,
        time_limit_minutes: Optional[int] = None,
    ) -> DailyLoopSession:
        """
        Create a daily loop session from a schedule entry.
        
        This reads the schedule entry to get class, subject, topic, date.
        """
        # Get schedule entry
        schedule_entry = await self._get_schedule_entry(schedule_entry_id)
        if not schedule_entry:
            raise ResourceNotFoundError("ScheduleEntry", schedule_entry_id)
        
        # Create session
        return await self.repo.create_session(
            schedule_entry_id=schedule_entry_id,
            class_id=schedule_entry.class_id,
            section_id=schedule_entry.section_id,
            subject_id=schedule_entry.subject_id,
            topic_id=schedule_entry.topic_id,
            session_date=schedule_entry.date,
            max_questions=max_questions,
            time_limit_minutes=time_limit_minutes,
        )
    
    async def get_session(
        self, 
        session_id: UUID,
    ) -> Optional[DailyLoopSession]:
        """Get session by ID."""
        return await self.repo.get_session(session_id)
    
    async def get_session_with_questions(
        self,
        session_id: UUID,
        student_id: Optional[UUID] = None,
    ) -> Tuple[DailyLoopSession, List[QuestionForAttempt]]:
        """
        Get session with questions for attempting.
        
        If student_id is provided, excludes already-attempted questions.
        """
        session = await self.repo.get_session(session_id)
        if not session:
            raise ResourceNotFoundError("DailyLoopSession", session_id)
        
        # Get questions already attempted by this student
        exclude_ids = []
        if student_id:
            attempts = await self.repo.get_student_attempts_for_session(
                session_id, student_id
            )
            exclude_ids = [a.question_id for a in attempts]
        
        # Get questions for the topic
        questions = await self.repo.get_questions_for_topic(
            topic_id=session.topic_id,
            limit=session.max_questions,
            exclude_ids=exclude_ids if exclude_ids else None,
        )
        
        # Format questions for attempt
        formatted = []
        for q in questions:
            options = []
            if q.options:
                for opt in q.options:
                    if isinstance(opt, dict):
                        options.append(QuestionOption(
                            key=opt.get("key", ""),
                            text=opt.get("text", ""),
                        ))
            
            formatted.append(QuestionForAttempt(
                id=q.id,
                question_type=q.question_type.value,
                question_text=q.question_text,
                question_html=q.question_html,
                options=options,
                marks=q.marks,
                time_limit_seconds=q.time_limit_seconds,
                difficulty=q.difficulty.value if q.difficulty else None,
            ))
        
        return session, formatted
    
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
        return await self.repo.list_sessions(
            class_id=class_id,
            topic_id=topic_id,
            start_date=start_date,
            end_date=end_date,
            page=page,
            size=size,
        )
    
    # ============================================
    # Attempt Operations
    # ============================================
    
    async def submit_attempt(
        self,
        session_id: UUID,
        student_id: UUID,
        attempt: AttemptSubmit,
    ) -> DailyLoopAttempt:
        """
        Submit a single attempt.
        
        1. Validate session exists and is active
        2. Validate question exists
        3. Check answer correctness
        4. Create attempt record
        5. Update mastery
        6. Update session stats
        """
        # Get session
        session = await self.repo.get_session(session_id)
        if not session:
            raise ResourceNotFoundError("DailyLoopSession", session_id)
        
        if not session.is_active:
            raise ValidationError("This session is no longer active")
        
        # Get question
        question = await self._get_question(attempt.question_id)
        if not question:
            raise ResourceNotFoundError("Question", attempt.question_id)
        
        # Check correctness
        is_correct = self._check_answer(question, attempt.selected_option)
        
        # Create attempt
        attempt_record = await self.repo.create_attempt(
            session_id=session_id,
            student_id=student_id,
            question_id=attempt.question_id,
            selected_option=attempt.selected_option,
            is_correct=is_correct,
            time_taken_seconds=attempt.time_taken_seconds,
        )
        
        # Update mastery
        await self.repo.update_mastery(
            student_id=student_id,
            topic_id=session.topic_id,
            is_correct=is_correct,
        )
        
        # Update session stats
        await self.repo.update_session_stats(session_id)
        
        # Increment question usage count
        await self._increment_question_usage(attempt.question_id)
        
        return attempt_record
    
    async def submit_attempts_bulk(
        self,
        student_id: UUID,
        data: AttemptBulkSubmit,
    ) -> List[DailyLoopAttempt]:
        """Submit multiple attempts at once."""
        results = []
        for attempt in data.attempts:
            result = await self.submit_attempt(
                session_id=data.session_id,
                student_id=student_id,
                attempt=attempt,
            )
            results.append(result)
        return results
    
    async def get_student_attempts_for_session(
        self,
        session_id: UUID,
        student_id: UUID,
    ) -> List[DailyLoopAttempt]:
        """Get all attempts by a student for a session."""
        return await self.repo.get_student_attempts_for_session(
            session_id, student_id
        )
    
    # ============================================
    # Mastery Operations
    # ============================================
    
    async def get_student_topic_mastery(
        self,
        student_id: UUID,
        topic_id: UUID,
    ) -> Optional[StudentTopicMastery]:
        """Get mastery for a specific student+topic."""
        return await self.repo.get_student_mastery(student_id, topic_id)
    
    async def get_student_mastery_summary(
        self,
        student_id: UUID,
    ) -> StudentMasterySummary:
        """Get summary of student mastery across all topics."""
        all_mastery = await self.repo.get_student_all_mastery(student_id)
        
        strong = 0
        moderate = 0
        weak = 0
        total_percent = 0.0
        
        topics = []
        for m in all_mastery:
            if m.mastery_percent >= 70:
                strong += 1
                level = MasteryLevel.STRONG
            elif m.mastery_percent >= 40:
                moderate += 1
                level = MasteryLevel.MODERATE
            else:
                weak += 1
                level = MasteryLevel.WEAK
            
            total_percent += m.mastery_percent
            
            topics.append(MasteryWithDetails(
                id=m.id,
                tenant_id=m.tenant_id,
                student_id=m.student_id,
                topic_id=m.topic_id,
                total_attempts=m.total_attempts,
                correct_attempts=m.correct_attempts,
                mastery_percent=m.mastery_percent,
                current_streak=m.current_streak,
                best_streak=m.best_streak,
                last_attempt_date=m.last_attempt_date,
                created_at=m.created_at,
                updated_at=m.updated_at,
                mastery_level=level,
            ))
        
        overall = total_percent / len(all_mastery) if all_mastery else 0.0
        
        return StudentMasterySummary(
            student_id=student_id,
            total_topics_attempted=len(all_mastery),
            strong_topics=strong,
            moderate_topics=moderate,
            weak_topics=weak,
            overall_mastery_percent=round(overall, 2),
            topics=topics,
        )
    
    async def get_strong_weak_questions(
        self,
        student_id: UUID,
        topic_id: UUID,
    ) -> StrongWeakAnalysis:
        """
        Get strong/weak question analysis for a student on a topic.
        
        Strong = accuracy >= 70%
        Weak = accuracy < 40%
        """
        # Get categorized question IDs
        categories = await self.repo.get_strong_weak_question_ids(
            student_id, topic_id
        )
        
        # Get mastery
        mastery = await self.repo.get_student_mastery(student_id, topic_id)
        mastery_percent = mastery.mastery_percent if mastery else 0.0
        
        if mastery_percent >= 70:
            level = MasteryLevel.STRONG
        elif mastery_percent >= 40:
            level = MasteryLevel.MODERATE
        else:
            level = MasteryLevel.WEAK
        
        # Build response with question details
        # (We could fetch question texts here, but keeping it lean for now)
        strong = [
            StrongWeakQuestion(
                question_id=qid,
                total_attempts=0,  # Would need to query per question
                correct_attempts=0,
                accuracy_percent=70.0,  # Simplified
                is_strong=True,
            )
            for qid in categories["strong"]
        ]
        
        weak = [
            StrongWeakQuestion(
                question_id=qid,
                total_attempts=0,
                correct_attempts=0,
                accuracy_percent=30.0,
                is_strong=False,
            )
            for qid in categories["weak"]
        ]
        
        moderate = [
            StrongWeakQuestion(
                question_id=qid,
                total_attempts=0,
                correct_attempts=0,
                accuracy_percent=50.0,
                is_strong=False,
            )
            for qid in categories["moderate"]
        ]
        
        return StrongWeakAnalysis(
            student_id=student_id,
            topic_id=topic_id,
            overall_mastery_percent=mastery_percent,
            mastery_level=level,
            strong_questions=strong,
            weak_questions=weak,
            moderate_questions=moderate,
        )
    
    # ============================================
    # Today's Sessions
    # ============================================
    
    async def get_student_today_info(
        self,
        student_id: UUID,
        class_id: UUID,
    ) -> TodaySessionInfo:
        """Get information about today's sessions for a student."""
        today = date.today()
        
        # Get sessions
        sessions = await self.repo.get_student_sessions_today(
            student_id, class_id, today
        )
        
        # Get today's attempts
        attempts = await self.repo.get_student_attempts_today(student_id, today)
        
        total = len(attempts)
        correct = sum(1 for a in attempts if a.is_correct)
        accuracy = (correct / total * 100) if total > 0 else 0.0
        
        return TodaySessionInfo(
            date=today,
            sessions=[],  # Would need to format with details
            total_questions_attempted=total,
            total_questions_correct=correct,
            accuracy_percent=round(accuracy, 2),
        )
    
    # ============================================
    # Stats
    # ============================================
    
    async def get_stats(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> DailyLoopStats:
        """Get daily loop statistics."""
        stats = await self.repo.get_stats(start_date, end_date)
        return DailyLoopStats(**stats)
    
    # ============================================
    # Helper Methods
    # ============================================
    
    async def _get_schedule_entry(
        self, 
        schedule_entry_id: UUID,
    ) -> Optional[ScheduleEntry]:
        """Get schedule entry by ID."""
        query = select(ScheduleEntry).where(
            ScheduleEntry.id == schedule_entry_id,
            ScheduleEntry.tenant_id == self.tenant_id,
            ScheduleEntry.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def _get_question(self, question_id: UUID) -> Optional[Question]:
        """Get question by ID."""
        query = select(Question).where(
            Question.id == question_id,
            Question.tenant_id == self.tenant_id,
            Question.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    def _check_answer(self, question: Question, selected_option: str) -> bool:
        """Check if the selected option is correct."""
        if not question.correct_answer:
            return False
        
        # Normalize for comparison (case-insensitive, trimmed)
        correct = question.correct_answer.strip().upper()
        selected = selected_option.strip().upper()
        
        return correct == selected
    
    async def _increment_question_usage(self, question_id: UUID) -> None:
        """Increment question usage count."""
        from sqlalchemy import update
        await self.session.execute(
            update(Question)
            .where(Question.id == question_id)
            .values(usage_count=Question.usage_count + 1)
        )
        await self.session.flush()
