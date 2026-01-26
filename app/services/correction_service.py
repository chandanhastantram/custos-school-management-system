"""
CUSTOS Correction Service

Manual correction workflow.
"""

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundError, ValidationError
from app.models.assignment import (
    Assignment, AssignmentSubmission, Correction, 
    CorrectionStatus, SubmissionStatus
)
from app.models.question import QuestionAttempt
from app.schemas.assignment import CorrectionData, QuestionCorrection, BulkCorrectionRequest


class CorrectionService:
    """Manual correction workflow service."""
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
    
    async def get_pending_corrections(
        self,
        teacher_id: Optional[UUID] = None,
        assignment_id: Optional[UUID] = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[List[AssignmentSubmission], int]:
        """Get submissions pending correction."""
        skip = (page - 1) * size
        
        query = select(AssignmentSubmission).where(
            AssignmentSubmission.tenant_id == self.tenant_id,
            AssignmentSubmission.status == SubmissionStatus.SUBMITTED
        )
        
        if assignment_id:
            query = query.where(AssignmentSubmission.assignment_id == assignment_id)
        
        if teacher_id:
            query = query.join(Assignment).where(Assignment.created_by == teacher_id)
        
        query = query.offset(skip).limit(size)
        result = await self.session.execute(query)
        submissions = list(result.scalars().all())
        
        # Count total
        count_query = select(func.count()).select_from(AssignmentSubmission).where(
            AssignmentSubmission.tenant_id == self.tenant_id,
            AssignmentSubmission.status == SubmissionStatus.SUBMITTED
        )
        from sqlalchemy import func
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0
        
        return submissions, total
    
    async def get_spreadsheet_data(
        self,
        assignment_id: UUID,
    ) -> dict:
        """
        Get correction data in spreadsheet format.
        
        Returns data structured for easy spreadsheet display:
        - rows: students
        - columns: questions
        - cells: marks obtained
        """
        # Get assignment with questions
        assignment = await self.session.get(Assignment, assignment_id)
        if not assignment or assignment.tenant_id != self.tenant_id:
            raise ResourceNotFoundError("Assignment", str(assignment_id))
        
        # Get all submissions
        query = select(AssignmentSubmission).where(
            AssignmentSubmission.assignment_id == assignment_id
        )
        result = await self.session.execute(query)
        submissions = list(result.scalars().all())
        
        # Get all attempts for this assignment
        attempt_query = select(QuestionAttempt).where(
            QuestionAttempt.tenant_id == self.tenant_id,
            QuestionAttempt.assignment_id == assignment_id
        )
        attempt_result = await self.session.execute(attempt_query)
        attempts = list(attempt_result.scalars().all())
        
        # Build spreadsheet data
        rows = []
        for submission in submissions:
            student_attempts = [a for a in attempts if a.student_id == submission.student_id]
            
            row = {
                "submission_id": str(submission.id),
                "student_id": str(submission.student_id),
                "status": submission.status.value,
                "total_marks": submission.marks_obtained,
                "questions": {}
            }
            
            for attempt in student_attempts:
                row["questions"][str(attempt.question_id)] = {
                    "attempt_id": str(attempt.id),
                    "answer": attempt.answer,
                    "selected_options": attempt.selected_options,
                    "is_correct": attempt.is_correct,
                    "marks_obtained": attempt.marks_obtained,
                    "needs_grading": attempt.needs_manual_grading,
                    "feedback": attempt.grader_feedback,
                }
            
            rows.append(row)
        
        return {
            "assignment_id": str(assignment_id),
            "title": assignment.title,
            "total_marks": assignment.total_marks,
            "submissions": rows,
        }
    
    async def apply_correction(
        self,
        submission_id: UUID,
        corrections: List[QuestionCorrection],
        teacher_id: UUID,
    ) -> AssignmentSubmission:
        """Apply corrections to a submission."""
        submission = await self.session.get(AssignmentSubmission, submission_id)
        if not submission or submission.tenant_id != self.tenant_id:
            raise ResourceNotFoundError("Submission", str(submission_id))
        
        total_marks_obtained = 0.0
        
        for correction in corrections:
            # Get attempt
            query = select(QuestionAttempt).where(
                QuestionAttempt.tenant_id == self.tenant_id,
                QuestionAttempt.assignment_id == submission.assignment_id,
                QuestionAttempt.student_id == submission.student_id,
                QuestionAttempt.question_id == correction.question_id
            )
            result = await self.session.execute(query)
            attempt = result.scalar_one_or_none()
            
            if attempt:
                attempt.marks_obtained = correction.marks_obtained
                attempt.grader_feedback = correction.feedback
                attempt.graded_by = teacher_id
                attempt.graded_at = datetime.now(timezone.utc)
                attempt.needs_manual_grading = False
                
                if attempt.is_correct is None:
                    attempt.is_correct = correction.marks_obtained > 0
            
            total_marks_obtained += correction.marks_obtained
        
        # Update submission
        submission.marks_obtained = total_marks_obtained
        submission.percentage = (total_marks_obtained / submission.total_marks * 100) if submission.total_marks > 0 else 0
        submission.graded_by = teacher_id
        submission.graded_at = datetime.now(timezone.utc)
        submission.status = SubmissionStatus.GRADED
        
        # Check pass/fail
        assignment = await self.session.get(Assignment, submission.assignment_id)
        if assignment and assignment.passing_marks:
            submission.is_passed = total_marks_obtained >= assignment.passing_marks
        
        await self.session.commit()
        return submission
    
    async def bulk_correct(
        self,
        corrections: List[CorrectionData],
        teacher_id: UUID,
    ) -> dict:
        """Apply bulk corrections."""
        success_count = 0
        failure_count = 0
        failures = []
        
        for correction_data in corrections:
            try:
                await self.apply_correction(
                    submission_id=correction_data.submission_id,
                    corrections=correction_data.corrections,
                    teacher_id=teacher_id,
                )
                success_count += 1
            except Exception as e:
                failure_count += 1
                failures.append({
                    "submission_id": str(correction_data.submission_id),
                    "error": str(e)
                })
        
        await self.session.commit()
        
        return {
            "success_count": success_count,
            "failure_count": failure_count,
            "failures": failures,
        }
    
    async def auto_grade_mcq(self, submission_id: UUID) -> AssignmentSubmission:
        """Auto-grade MCQ questions in a submission."""
        submission = await self.session.get(AssignmentSubmission, submission_id)
        if not submission:
            raise ResourceNotFoundError("Submission", str(submission_id))
        
        # Get attempts that can be auto-graded
        query = select(QuestionAttempt).where(
            QuestionAttempt.tenant_id == self.tenant_id,
            QuestionAttempt.assignment_id == submission.assignment_id,
            QuestionAttempt.student_id == submission.student_id
        )
        result = await self.session.execute(query)
        attempts = list(result.scalars().all())
        
        total_marks = 0.0
        
        for attempt in attempts:
            if attempt.is_correct is not None:
                total_marks += attempt.marks_obtained
        
        submission.marks_obtained = total_marks
        submission.percentage = (total_marks / submission.total_marks * 100) if submission.total_marks > 0 else 0
        
        await self.session.commit()
        return submission
