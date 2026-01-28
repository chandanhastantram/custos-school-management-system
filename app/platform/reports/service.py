"""
CUSTOS Report Service
"""

from datetime import datetime, timezone
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession


class ReportService:
    """Report generation service."""
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
    
    async def get_student_report(
        self,
        student_id: UUID,
        subject_id: Optional[UUID] = None,
    ) -> dict:
        """Generate student performance report."""
        from app.academics.models.assignments import Submission, SubmissionStatus
        
        query = select(Submission).where(
            Submission.tenant_id == self.tenant_id,
            Submission.student_id == student_id,
            Submission.status == SubmissionStatus.GRADED,
        )
        result = await self.session.execute(query)
        submissions = list(result.scalars().all())
        
        if not submissions:
            return {
                "student_id": str(student_id),
                "total_assignments": 0,
                "completed": 0,
                "average_score": 0,
                "performance": [],
            }
        
        total = len(submissions)
        avg_percentage = sum(s.percentage or 0 for s in submissions) / total
        
        return {
            "student_id": str(student_id),
            "total_assignments": total,
            "completed": total,
            "average_score": round(avg_percentage, 2),
            "highest_score": max(s.percentage or 0 for s in submissions),
            "lowest_score": min(s.percentage or 0 for s in submissions),
            "submissions": [
                {
                    "assignment_id": str(s.assignment_id),
                    "marks": s.marks_obtained,
                    "total": s.total_marks,
                    "percentage": s.percentage,
                    "graded_at": str(s.graded_at),
                }
                for s in submissions[-10:]  # Last 10
            ],
        }
    
    async def get_class_report(
        self,
        section_id: UUID,
        subject_id: Optional[UUID] = None,
    ) -> dict:
        """Generate class performance report."""
        from app.academics.models.assignments import Assignment, Submission, SubmissionStatus
        from app.users.models import User, StudentProfile
        
        # Get students in section
        students_query = select(User).join(StudentProfile).where(
            User.tenant_id == self.tenant_id,
            StudentProfile.section_id == section_id,
        )
        students_result = await self.session.execute(students_query)
        students = list(students_result.scalars().all())
        
        # Get assignments for section
        assignments_query = select(Assignment).where(
            Assignment.tenant_id == self.tenant_id,
            Assignment.section_id == section_id,
        )
        assignments_result = await self.session.execute(assignments_query)
        assignments = list(assignments_result.scalars().all())
        
        # Get all graded submissions
        submissions_query = select(Submission).where(
            Submission.tenant_id == self.tenant_id,
            Submission.assignment_id.in_([a.id for a in assignments]),
            Submission.status == SubmissionStatus.GRADED,
        )
        submissions_result = await self.session.execute(submissions_query)
        submissions = list(submissions_result.scalars().all())
        
        if not submissions:
            avg = 0
        else:
            avg = sum(s.percentage or 0 for s in submissions) / len(submissions)
        
        return {
            "section_id": str(section_id),
            "total_students": len(students),
            "total_assignments": len(assignments),
            "total_submissions": len(submissions),
            "class_average": round(avg, 2),
            "pass_rate": round(
                len([s for s in submissions if (s.percentage or 0) >= 35]) / max(len(submissions), 1) * 100, 2
            ),
        }
    
    async def get_teacher_report(
        self,
        teacher_id: UUID,
    ) -> dict:
        """Generate teacher activity report."""
        from app.academics.models.assignments import Assignment, Submission
        from app.academics.models.questions import Question
        
        # Assignments created
        assignments_query = select(func.count()).where(
            Assignment.tenant_id == self.tenant_id,
            Assignment.created_by == teacher_id,
        )
        assignments_count = await self.session.execute(assignments_query)
        
        # Questions created
        questions_query = select(func.count()).where(
            Question.tenant_id == self.tenant_id,
            Question.created_by == teacher_id,
        )
        questions_count = await self.session.execute(questions_query)
        
        # Submissions graded
        graded_query = select(func.count()).where(
            Submission.tenant_id == self.tenant_id,
            Submission.graded_by == teacher_id,
        )
        graded_count = await self.session.execute(graded_query)
        
        return {
            "teacher_id": str(teacher_id),
            "assignments_created": assignments_count.scalar() or 0,
            "questions_created": questions_count.scalar() or 0,
            "submissions_graded": graded_count.scalar() or 0,
        }
