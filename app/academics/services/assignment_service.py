"""
CUSTOS Assignment Service
"""

from datetime import datetime, timezone
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ResourceNotFoundError, ValidationError
from app.academics.models.assignments import (
    Assignment, AssignmentQuestion, Submission, SubmissionAnswer,
    AssignmentStatus, SubmissionStatus,
)


class AssignmentService:
    """Assignment management."""
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
    
    async def create_assignment(
        self,
        section_id: UUID,
        subject_id: UUID,
        created_by: UUID,
        title: str,
        due_date: datetime,
        description: Optional[str] = None,
        instructions: Optional[str] = None,
        total_marks: float = 100,
        passing_marks: float = 35,
        time_limit_minutes: Optional[int] = None,
    ) -> Assignment:
        """Create assignment."""
        assignment = Assignment(
            tenant_id=self.tenant_id,
            section_id=section_id,
            subject_id=subject_id,
            created_by=created_by,
            title=title,
            description=description,
            instructions=instructions,
            total_marks=total_marks,
            passing_marks=passing_marks,
            due_date=due_date,
            time_limit_minutes=time_limit_minutes,
            status=AssignmentStatus.DRAFT,
        )
        self.session.add(assignment)
        await self.session.commit()
        await self.session.refresh(assignment)
        return assignment
    
    async def add_questions(
        self,
        assignment_id: UUID,
        questions: List[dict],  # [{"question_id": UUID, "marks": float}]
    ) -> Assignment:
        """Add questions to assignment."""
        assignment = await self.get_assignment(assignment_id)
        
        for idx, q in enumerate(questions):
            aq = AssignmentQuestion(
                tenant_id=self.tenant_id,
                assignment_id=assignment_id,
                question_id=q["question_id"],
                order=idx,
                marks=q["marks"],
            )
            self.session.add(aq)
        
        # Update total marks
        total = sum(q["marks"] for q in questions)
        assignment.total_marks = total
        
        await self.session.commit()
        return assignment
    
    async def publish_assignment(self, assignment_id: UUID) -> Assignment:
        """Publish assignment."""
        assignment = await self.get_assignment(assignment_id)
        
        if assignment.status != AssignmentStatus.DRAFT:
            raise ValidationError("Only draft assignments can be published")
        
        assignment.status = AssignmentStatus.PUBLISHED
        assignment.published_at = datetime.now(timezone.utc)
        
        await self.session.commit()
        return assignment
    
    async def get_assignment(self, assignment_id: UUID) -> Assignment:
        """Get assignment by ID."""
        query = select(Assignment).where(
            Assignment.tenant_id == self.tenant_id,
            Assignment.id == assignment_id,
        ).options(selectinload(Assignment.questions))
        
        result = await self.session.execute(query)
        assignment = result.scalar_one_or_none()
        if not assignment:
            raise ResourceNotFoundError("Assignment", str(assignment_id))
        return assignment
    
    async def get_assignments(
        self,
        section_id: Optional[UUID] = None,
        subject_id: Optional[UUID] = None,
        status: Optional[AssignmentStatus] = None,
        page: int = 1,
        size: int = 20,
    ) -> Tuple[List[Assignment], int]:
        """Get assignments with filters."""
        query = select(Assignment).where(
            Assignment.tenant_id == self.tenant_id,
            Assignment.is_deleted == False,
        )
        
        if section_id:
            query = query.where(Assignment.section_id == section_id)
        if subject_id:
            query = query.where(Assignment.subject_id == subject_id)
        if status:
            query = query.where(Assignment.status == status)
        
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0
        
        skip = (page - 1) * size
        query = query.order_by(Assignment.due_date.desc()).offset(skip).limit(size)
        result = await self.session.execute(query)
        
        return list(result.scalars().all()), total
    
    # Submissions
    async def start_submission(
        self,
        assignment_id: UUID,
        student_id: UUID,
    ) -> Submission:
        """Start assignment attempt."""
        assignment = await self.get_assignment(assignment_id)
        
        if assignment.status != AssignmentStatus.PUBLISHED:
            raise ValidationError("Assignment is not published")
        
        # Check max attempts
        existing = await self.session.execute(
            select(func.count()).where(
                Submission.tenant_id == self.tenant_id,
                Submission.assignment_id == assignment_id,
                Submission.student_id == student_id,
            )
        )
        attempt_count = existing.scalar() or 0
        
        if attempt_count >= assignment.max_attempts:
            raise ValidationError("Maximum attempts reached")
        
        submission = Submission(
            tenant_id=self.tenant_id,
            assignment_id=assignment_id,
            student_id=student_id,
            status=SubmissionStatus.IN_PROGRESS,
            started_at=datetime.now(timezone.utc),
            attempt_number=attempt_count + 1,
        )
        self.session.add(submission)
        await self.session.commit()
        await self.session.refresh(submission)
        return submission
    
    async def submit_answer(
        self,
        submission_id: UUID,
        question_id: UUID,
        answer_text: Optional[str] = None,
        answer_data: Optional[dict] = None,
    ) -> SubmissionAnswer:
        """Submit answer for a question."""
        answer = SubmissionAnswer(
            tenant_id=self.tenant_id,
            submission_id=submission_id,
            question_id=question_id,
            answer_text=answer_text,
            answer_data=answer_data,
        )
        self.session.add(answer)
        await self.session.commit()
        await self.session.refresh(answer)
        return answer
    
    async def complete_submission(self, submission_id: UUID) -> Submission:
        """Complete and submit assignment."""
        query = select(Submission).where(
            Submission.tenant_id == self.tenant_id,
            Submission.id == submission_id,
        ).options(selectinload(Submission.answers))
        
        result = await self.session.execute(query)
        submission = result.scalar_one_or_none()
        if not submission:
            raise ResourceNotFoundError("Submission", str(submission_id))
        
        submission.status = SubmissionStatus.SUBMITTED
        submission.submitted_at = datetime.now(timezone.utc)
        
        # Check if late
        assignment = await self.get_assignment(submission.assignment_id)
        if submission.submitted_at > assignment.due_date:
            submission.is_late = True
            if assignment.late_penalty_percent > 0:
                submission.late_penalty_applied = assignment.late_penalty_percent
        
        await self.session.commit()
        return submission
    
    async def grade_submission(
        self,
        submission_id: UUID,
        graded_by: UUID,
        marks_obtained: float,
        feedback: Optional[str] = None,
    ) -> Submission:
        """Grade submission."""
        query = select(Submission).where(
            Submission.tenant_id == self.tenant_id,
            Submission.id == submission_id,
        )
        result = await self.session.execute(query)
        submission = result.scalar_one_or_none()
        if not submission:
            raise ResourceNotFoundError("Submission", str(submission_id))
        
        assignment = await self.get_assignment(submission.assignment_id)
        
        # Apply late penalty
        final_marks = marks_obtained
        if submission.late_penalty_applied > 0:
            final_marks = marks_obtained * (1 - submission.late_penalty_applied / 100)
        
        submission.marks_obtained = final_marks
        submission.total_marks = assignment.total_marks
        submission.percentage = (final_marks / assignment.total_marks) * 100
        submission.graded_by = graded_by
        submission.graded_at = datetime.now(timezone.utc)
        submission.feedback = feedback
        submission.status = SubmissionStatus.GRADED
        
        await self.session.commit()
        return submission
    
    # File Attachment
    async def attach_file_to_submission(
        self,
        submission_id: UUID,
        student_id: UUID,
        file_url: str,
        file_name: str,
        file_type: str,
        file_size_bytes: int,
    ) -> Submission:
        """Attach file to submission."""
        query = select(Submission).where(
            Submission.tenant_id == self.tenant_id,
            Submission.id == submission_id,
            Submission.student_id == student_id,
        )
        result = await self.session.execute(query)
        submission = result.scalar_one_or_none()
        if not submission:
            raise ResourceNotFoundError("Submission", str(submission_id))
        
        submission.file_url = file_url
        submission.file_name = file_name
        submission.file_type = file_type
        submission.file_size_bytes = file_size_bytes
        
        await self.session.commit()
        return submission
    
    # Student: Get my assignments
    async def get_student_assignments(
        self,
        student_id: UUID,
        status: Optional[str] = None,
        page: int = 1,
        size: int = 20,
    ) -> dict:
        """Get assignments for student with their submission status."""
        # Get published assignments for student's section
        # For now, get all published assignments
        query = select(Assignment).where(
            Assignment.tenant_id == self.tenant_id,
            Assignment.status == AssignmentStatus.PUBLISHED,
        ).order_by(Assignment.due_date.desc())
        
        result = await self.session.execute(query)
        assignments = list(result.scalars().all())
        
        # Get submissions for this student
        sub_query = select(Submission).where(
            Submission.tenant_id == self.tenant_id,
            Submission.student_id == student_id,
        )
        sub_result = await self.session.execute(sub_query)
        submissions_map = {s.assignment_id: s for s in sub_result.scalars().all()}
        
        items = []
        for a in assignments:
            sub = submissions_map.get(a.id)
            items.append({
                "assignment": a,
                "submission": sub,
                "status": sub.status.value if sub else "not_started",
            })
        
        # Filter by status if provided
        if status:
            items = [i for i in items if i["status"] == status]
        
        skip = (page - 1) * size
        return {
            "items": items[skip:skip+size],
            "total": len(items),
            "page": page,
            "size": size,
        }
    
    async def get_submission(self, submission_id: UUID, user_id: UUID) -> Submission:
        """Get submission details."""
        query = select(Submission).where(
            Submission.tenant_id == self.tenant_id,
            Submission.id == submission_id,
        ).options(
            selectinload(Submission.answers),
            selectinload(Submission.assignment),
        )
        result = await self.session.execute(query)
        submission = result.scalar_one_or_none()
        if not submission:
            raise ResourceNotFoundError("Submission", str(submission_id))
        return submission
    
    async def get_assignment_submissions(
        self,
        assignment_id: UUID,
        status: Optional[str] = None,
        page: int = 1,
        size: int = 50,
    ) -> dict:
        """Get all submissions for an assignment (Teacher)."""
        query = select(Submission).where(
            Submission.tenant_id == self.tenant_id,
            Submission.assignment_id == assignment_id,
        )
        
        if status:
            query = query.where(Submission.status == status)
        
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0
        
        skip = (page - 1) * size
        query = query.order_by(Submission.submitted_at.desc()).offset(skip).limit(size)
        result = await self.session.execute(query)
        
        return {
            "items": list(result.scalars().all()),
            "total": total,
            "page": page,
            "size": size,
        }

