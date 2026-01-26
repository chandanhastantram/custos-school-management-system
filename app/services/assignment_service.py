"""
CUSTOS Assignment Service

Assignment and worksheet management.
"""

from datetime import datetime, timezone
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ResourceNotFoundError, ValidationError
from app.models.assignment import (
    Assignment, AssignmentSubmission, AssignmentQuestion, Worksheet,
    AssignmentType, AssignmentStatus, SubmissionStatus
)
from app.models.question import Question, QuestionAttempt
from app.schemas.assignment import (
    AssignmentCreate, AssignmentUpdate, SubmissionCreate, AnswerSubmit,
    WorksheetCreate,
)


class AssignmentService:
    """Assignment management service."""
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
    
    # ==================== Assignments ====================
    
    async def create_assignment(
        self,
        data: AssignmentCreate,
        created_by: UUID,
    ) -> Assignment:
        """Create assignment."""
        assignment = Assignment(
            tenant_id=self.tenant_id,
            section_id=data.section_id,
            subject_id=data.subject_id,
            topic_id=data.topic_id,
            created_by=created_by,
            title=data.title,
            description=data.description,
            instructions=data.instructions,
            assignment_type=data.assignment_type,
            status=AssignmentStatus.DRAFT,
            total_marks=data.total_marks,
            passing_marks=data.passing_marks,
            start_date=data.start_date,
            due_date=data.due_date,
            late_submission_allowed=data.late_submission_allowed,
            late_penalty_percent=data.late_penalty_percent,
            time_limit_minutes=data.time_limit_minutes,
            max_attempts=data.max_attempts,
            shuffle_questions=data.shuffle_questions,
            show_answers_after=data.show_answers_after,
        )
        self.session.add(assignment)
        await self.session.flush()
        
        # Add questions
        if data.question_ids:
            total_marks = 0.0
            for order, qid in enumerate(data.question_ids):
                question = await self.session.get(Question, qid)
                if question and question.tenant_id == self.tenant_id:
                    aq = AssignmentQuestion(
                        tenant_id=self.tenant_id,
                        assignment_id=assignment.id,
                        question_id=qid,
                        order=order,
                        marks=question.marks,
                    )
                    self.session.add(aq)
                    total_marks += question.marks
            
            assignment.total_marks = total_marks
            assignment.question_count = len(data.question_ids)
        
        await self.session.commit()
        await self.session.refresh(assignment)
        return assignment
    
    async def get_assignments(
        self,
        section_id: Optional[UUID] = None,
        subject_id: Optional[UUID] = None,
        teacher_id: Optional[UUID] = None,
        status: Optional[AssignmentStatus] = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[List[Assignment], int]:
        """Get assignments with filters."""
        query = select(Assignment).where(Assignment.tenant_id == self.tenant_id)
        
        if section_id:
            query = query.where(Assignment.section_id == section_id)
        if subject_id:
            query = query.where(Assignment.subject_id == subject_id)
        if teacher_id:
            query = query.where(Assignment.created_by == teacher_id)
        if status:
            query = query.where(Assignment.status == status)
        
        # Count
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0
        
        # Paginate
        skip = (page - 1) * size
        query = query.order_by(Assignment.due_date.desc()).offset(skip).limit(size)
        result = await self.session.execute(query)
        
        return list(result.scalars().all()), total
    
    async def get_assignment(self, assignment_id: UUID) -> Assignment:
        """Get assignment by ID."""
        query = select(Assignment).where(
            Assignment.tenant_id == self.tenant_id,
            Assignment.id == assignment_id
        ).options(selectinload(Assignment.questions))
        result = await self.session.execute(query)
        assignment = result.scalar_one_or_none()
        if not assignment:
            raise ResourceNotFoundError("Assignment", str(assignment_id))
        return assignment
    
    async def update_assignment(
        self,
        assignment_id: UUID,
        data: AssignmentUpdate,
    ) -> Assignment:
        """Update assignment."""
        assignment = await self.get_assignment(assignment_id)
        
        if assignment.status == AssignmentStatus.COMPLETED:
            raise ValidationError("Cannot update completed assignment")
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(assignment, key, value)
        
        await self.session.commit()
        await self.session.refresh(assignment)
        return assignment
    
    async def publish_assignment(self, assignment_id: UUID) -> Assignment:
        """Publish assignment."""
        assignment = await self.get_assignment(assignment_id)
        assignment.status = AssignmentStatus.PUBLISHED
        assignment.published_at = datetime.now(timezone.utc)
        await self.session.commit()
        return assignment
    
    async def delete_assignment(self, assignment_id: UUID) -> bool:
        """Delete assignment."""
        assignment = await self.get_assignment(assignment_id)
        if assignment.status != AssignmentStatus.DRAFT:
            raise ValidationError("Can only delete draft assignments")
        await self.session.delete(assignment)
        await self.session.commit()
        return True
    
    async def get_assignment_questions(self, assignment_id: UUID) -> List[Question]:
        """Get questions for assignment."""
        query = select(Question).join(AssignmentQuestion).where(
            AssignmentQuestion.assignment_id == assignment_id
        ).order_by(AssignmentQuestion.order)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    # ==================== Submissions ====================
    
    async def start_submission(
        self,
        assignment_id: UUID,
        student_id: UUID,
    ) -> AssignmentSubmission:
        """Start assignment attempt."""
        assignment = await self.get_assignment(assignment_id)
        
        # Check if already submitted max attempts
        existing = await self.session.execute(
            select(func.count()).select_from(AssignmentSubmission).where(
                AssignmentSubmission.assignment_id == assignment_id,
                AssignmentSubmission.student_id == student_id,
            )
        )
        attempt_count = existing.scalar() or 0
        
        if attempt_count >= assignment.max_attempts:
            raise ValidationError(f"Maximum attempts ({assignment.max_attempts}) reached")
        
        # Check if assignment is active
        now = datetime.now(timezone.utc)
        if assignment.start_date and now < assignment.start_date:
            raise ValidationError("Assignment not yet started")
        if assignment.due_date and now > assignment.due_date:
            if not assignment.late_submission_allowed:
                raise ValidationError("Assignment past due date")
        
        submission = AssignmentSubmission(
            tenant_id=self.tenant_id,
            assignment_id=assignment_id,
            student_id=student_id,
            status=SubmissionStatus.IN_PROGRESS,
            attempt_number=attempt_count + 1,
            started_at=now,
            total_marks=assignment.total_marks,
        )
        self.session.add(submission)
        await self.session.commit()
        await self.session.refresh(submission)
        return submission
    
    async def submit_answers(
        self,
        submission_id: UUID,
        answers: List[AnswerSubmit],
    ) -> AssignmentSubmission:
        """Submit answers for assignment."""
        submission = await self.session.get(AssignmentSubmission, submission_id)
        if not submission or submission.tenant_id != self.tenant_id:
            raise ResourceNotFoundError("Submission", str(submission_id))
        
        if submission.status == SubmissionStatus.GRADED:
            raise ValidationError("Submission already graded")
        
        assignment = await self.get_assignment(submission.assignment_id)
        now = datetime.now(timezone.utc)
        
        marks_obtained = 0.0
        auto_graded_count = 0
        needs_manual = 0
        
        for ans in answers:
            question = await self.session.get(Question, ans.question_id)
            if not question:
                continue
            
            # Create attempt
            attempt = QuestionAttempt(
                tenant_id=self.tenant_id,
                question_id=ans.question_id,
                student_id=submission.student_id,
                assignment_id=submission.assignment_id,
                answer=ans.answer,
                selected_options=ans.selected_options,
                attempted_at=now,
            )
            
            # Auto-grade if possible
            if question.question_type.value in ["mcq", "mcq_multiple", "true_false"]:
                if ans.selected_options and question.correct_options:
                    is_correct = set(ans.selected_options) == set(question.correct_options)
                    attempt.is_correct = is_correct
                    attempt.marks_obtained = question.marks if is_correct else -question.negative_marks
                    marks_obtained += attempt.marks_obtained
                    auto_graded_count += 1
            elif question.question_type.value == "fill_blank":
                if ans.answer and question.correct_answer:
                    is_correct = ans.answer.strip().lower() == question.correct_answer.strip().lower()
                    attempt.is_correct = is_correct
                    attempt.marks_obtained = question.marks if is_correct else 0
                    marks_obtained += attempt.marks_obtained
                    auto_graded_count += 1
            else:
                attempt.needs_manual_grading = True
                needs_manual += 1
            
            self.session.add(attempt)
        
        # Update submission
        submission.submitted_at = now
        submission.marks_obtained = marks_obtained
        submission.percentage = (marks_obtained / submission.total_marks * 100) if submission.total_marks > 0 else 0
        
        if submission.started_at:
            submission.time_taken_seconds = int((now - submission.started_at).total_seconds())
        
        if needs_manual > 0:
            submission.status = SubmissionStatus.SUBMITTED
        else:
            submission.status = SubmissionStatus.GRADED
            if assignment.passing_marks:
                submission.is_passed = marks_obtained >= assignment.passing_marks
        
        await self.session.commit()
        await self.session.refresh(submission)
        return submission
    
    async def get_submissions(
        self,
        assignment_id: UUID,
        status: Optional[SubmissionStatus] = None,
    ) -> List[AssignmentSubmission]:
        """Get all submissions for assignment."""
        query = select(AssignmentSubmission).where(
            AssignmentSubmission.tenant_id == self.tenant_id,
            AssignmentSubmission.assignment_id == assignment_id
        )
        if status:
            query = query.where(AssignmentSubmission.status == status)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_student_submissions(
        self,
        student_id: UUID,
        page: int = 1,
        size: int = 20,
    ) -> tuple[List[AssignmentSubmission], int]:
        """Get all submissions by student."""
        query = select(AssignmentSubmission).where(
            AssignmentSubmission.tenant_id == self.tenant_id,
            AssignmentSubmission.student_id == student_id
        ).order_by(AssignmentSubmission.submitted_at.desc())
        
        count_result = await self.session.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar() or 0
        
        skip = (page - 1) * size
        query = query.offset(skip).limit(size)
        result = await self.session.execute(query)
        
        return list(result.scalars().all()), total
    
    # ==================== Worksheets ====================
    
    async def create_worksheet(
        self,
        data: WorksheetCreate,
        created_by: UUID,
    ) -> Worksheet:
        """Create worksheet."""
        # Get questions and calculate marks
        questions = await self.session.execute(
            select(Question).where(Question.id.in_(data.question_ids))
        )
        question_list = list(questions.scalars().all())
        
        total_marks = sum(q.marks for q in question_list)
        
        worksheet = Worksheet(
            tenant_id=self.tenant_id,
            title=data.title,
            description=data.description,
            section_id=data.section_id,
            subject_id=data.subject_id,
            topic_id=data.topic_id,
            created_by=created_by,
            questions=data.question_ids,
            total_questions=len(data.question_ids),
            total_marks=total_marks,
            estimated_time_minutes=data.estimated_time_minutes,
        )
        self.session.add(worksheet)
        await self.session.commit()
        await self.session.refresh(worksheet)
        return worksheet
    
    async def get_worksheets(
        self,
        section_id: Optional[UUID] = None,
        subject_id: Optional[UUID] = None,
    ) -> List[Worksheet]:
        """Get worksheets."""
        query = select(Worksheet).where(Worksheet.tenant_id == self.tenant_id)
        if section_id:
            query = query.where(Worksheet.section_id == section_id)
        if subject_id:
            query = query.where(Worksheet.subject_id == subject_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_worksheet(self, worksheet_id: UUID) -> Worksheet:
        """Get worksheet by ID."""
        query = select(Worksheet).where(
            Worksheet.tenant_id == self.tenant_id,
            Worksheet.id == worksheet_id
        )
        result = await self.session.execute(query)
        worksheet = result.scalar_one_or_none()
        if not worksheet:
            raise ResourceNotFoundError("Worksheet", str(worksheet_id))
        return worksheet
