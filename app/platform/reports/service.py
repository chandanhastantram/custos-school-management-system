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
    
    async def generate_report_card(
        self,
        student_id: UUID,
        academic_year: str = "2024-25",
        term: str = "Mid-Term",
    ) -> dict:
        """
        Generate comprehensive report card for a student.
        
        Returns all data needed to render a report card including:
        - Student info
        - Subject-wise marks
        - Attendance summary
        - Teacher remarks
        - Grade calculation
        """
        from app.users.models import User, StudentProfile
        from app.academics.models.assignments import Submission, SubmissionStatus
        from app.attendance.models import AttendanceRecord
        
        # Get student info
        student_query = select(User).where(
            User.tenant_id == self.tenant_id,
            User.id == student_id,
        )
        student_result = await self.session.execute(student_query)
        student = student_result.scalar_one_or_none()
        
        if not student:
            return {"error": "Student not found"}
        
        # Get all graded submissions
        submissions_query = select(Submission).where(
            Submission.tenant_id == self.tenant_id,
            Submission.student_id == student_id,
            Submission.status == SubmissionStatus.GRADED,
        )
        submissions_result = await self.session.execute(submissions_query)
        submissions = list(submissions_result.scalars().all())
        
        # Calculate subject-wise performance (mock data for now)
        subjects = [
            {"name": "Mathematics", "max_marks": 100, "obtained": 85, "grade": "A"},
            {"name": "Science", "max_marks": 100, "obtained": 78, "grade": "B+"},
            {"name": "English", "max_marks": 100, "obtained": 82, "grade": "A"},
            {"name": "Hindi", "max_marks": 100, "obtained": 75, "grade": "B+"},
            {"name": "Social Science", "max_marks": 100, "obtained": 80, "grade": "A"},
            {"name": "Computer Science", "max_marks": 100, "obtained": 92, "grade": "A+"},
        ]
        
        total_max = sum(s["max_marks"] for s in subjects)
        total_obtained = sum(s["obtained"] for s in subjects)
        percentage = (total_obtained / total_max) * 100 if total_max > 0 else 0
        
        # Calculate overall grade
        if percentage >= 90:
            overall_grade = "A+"
        elif percentage >= 80:
            overall_grade = "A"
        elif percentage >= 70:
            overall_grade = "B+"
        elif percentage >= 60:
            overall_grade = "B"
        elif percentage >= 50:
            overall_grade = "C"
        else:
            overall_grade = "D"
        
        return {
            "student": {
                "id": str(student_id),
                "name": student.full_name or student.username,
                "roll_number": "2024/101",  # Would come from StudentProfile
                "class": "10-A",
                "admission_number": "CUST/2024/1001",
            },
            "academic_year": academic_year,
            "term": term,
            "subjects": subjects,
            "summary": {
                "total_marks": total_max,
                "obtained_marks": total_obtained,
                "percentage": round(percentage, 2),
                "grade": overall_grade,
                "rank": 5,  # Would be calculated
                "class_strength": 45,
            },
            "attendance": {
                "total_days": 120,
                "present": 112,
                "absent": 8,
                "percentage": 93.3,
            },
            "remarks": {
                "class_teacher": "Excellent performance. Keep up the good work!",
                "principal": "Promoted to next class with distinction.",
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
    
    async def get_report_card_pdf_data(
        self,
        student_id: UUID,
        academic_year: str = "2024-25",
        term: str = "Mid-Term",
    ) -> dict:
        """Get report card data formatted for PDF generation."""
        report_card = await self.generate_report_card(student_id, academic_year, term)
        
        # Add school info for PDF header
        report_card["school"] = {
            "name": "CUSTOS International School",
            "address": "123 Education Lane, Knowledge City",
            "phone": "+91 1234567890",
            "email": "info@custos.school",
            "logo_url": "/static/school_logo.png",
        }
        
        return report_card

