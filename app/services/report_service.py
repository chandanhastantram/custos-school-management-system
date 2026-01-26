"""
CUSTOS Report Service

Report generation and analytics.
"""

from datetime import date, datetime, timezone
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, StudentProfile
from app.models.assignment import AssignmentSubmission, Assignment
from app.models.question import QuestionAttempt
from app.models.report import Report, ReportType, ReportPeriod, StudentPerformance, TeacherEffectiveness
from app.models.academic import Lesson
from app.schemas.report import (
    ReportRequest, StudentReportSummary, ClassAnalytics, TeacherEffectivenessReport
)


class ReportService:
    """Report generation service."""
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
    
    async def generate_student_report(
        self,
        student_id: UUID,
        start_date: date,
        end_date: date,
        subject_id: Optional[UUID] = None,
    ) -> StudentReportSummary:
        """Generate student performance report."""
        # Get student
        student = await self.session.get(User, student_id)
        if not student:
            raise ValueError("Student not found")
        
        # Get submissions in period
        query = select(AssignmentSubmission).join(Assignment).where(
            AssignmentSubmission.tenant_id == self.tenant_id,
            AssignmentSubmission.student_id == student_id,
            Assignment.due_date >= start_date,
            Assignment.due_date <= end_date,
        )
        if subject_id:
            query = query.where(Assignment.subject_id == subject_id)
        
        result = await self.session.execute(query)
        submissions = list(result.scalars().all())
        
        # Calculate metrics
        total = len(submissions)
        completed = len([s for s in submissions if s.submitted_at is not None])
        passed = len([s for s in submissions if s.is_passed == True])
        
        total_marks = sum(s.total_marks for s in submissions)
        marks_obtained = sum(s.marks_obtained for s in submissions)
        percentage = (marks_obtained / total_marks * 100) if total_marks > 0 else 0
        
        # Get question attempts for accuracy
        attempt_query = select(QuestionAttempt).where(
            QuestionAttempt.tenant_id == self.tenant_id,
            QuestionAttempt.student_id == student_id,
            QuestionAttempt.attempted_at >= datetime.combine(start_date, datetime.min.time()),
            QuestionAttempt.attempted_at <= datetime.combine(end_date, datetime.max.time()),
        )
        attempt_result = await self.session.execute(attempt_query)
        attempts = list(attempt_result.scalars().all())
        
        total_attempts = len(attempts)
        correct_attempts = len([a for a in attempts if a.is_correct == True])
        accuracy = (correct_attempts / total_attempts * 100) if total_attempts > 0 else 0
        
        # TODO: Calculate strength/weakness topics from attempt data
        
        return StudentReportSummary(
            student_id=student_id,
            student_name=student.full_name,
            total_assignments=total,
            completed_assignments=completed,
            passed_assignments=passed,
            total_marks=total_marks,
            marks_obtained=marks_obtained,
            percentage=round(percentage, 2),
            accuracy=round(accuracy, 2),
            rank_in_class=None,  # Would need class context
            strength_topics=[],
            weakness_topics=[],
        )
    
    async def generate_class_analytics(
        self,
        class_id: UUID,
        section_id: UUID,
        start_date: date,
        end_date: date,
    ) -> ClassAnalytics:
        """Generate class performance analytics."""
        # Get all students in section
        student_query = select(User).join(StudentProfile).where(
            User.tenant_id == self.tenant_id,
            StudentProfile.section_id == section_id,
        )
        result = await self.session.execute(student_query)
        students = list(result.scalars().all())
        
        # Get all submissions for section
        submission_query = select(AssignmentSubmission).join(Assignment).where(
            AssignmentSubmission.tenant_id == self.tenant_id,
            Assignment.section_id == section_id,
            Assignment.due_date >= start_date,
            Assignment.due_date <= end_date,
        )
        sub_result = await self.session.execute(submission_query)
        submissions = list(sub_result.scalars().all())
        
        # Calculate averages
        if submissions:
            avg_score = sum(s.percentage for s in submissions) / len(submissions)
            passed = len([s for s in submissions if s.is_passed == True])
            pass_rate = (passed / len(submissions) * 100)
        else:
            avg_score = 0
            pass_rate = 0
        
        # Get top performers
        student_scores = {}
        for sub in submissions:
            if sub.student_id not in student_scores:
                student_scores[sub.student_id] = []
            student_scores[sub.student_id].append(sub.percentage)
        
        top_performers = []
        at_risk = []
        for student_id, scores in student_scores.items():
            avg = sum(scores) / len(scores)
            student = next((s for s in students if s.id == student_id), None)
            if student:
                entry = {"student_id": str(student_id), "name": student.full_name, "avg_score": round(avg, 2)}
                if avg >= 80:
                    top_performers.append(entry)
                elif avg < 40:
                    at_risk.append(entry)
        
        return ClassAnalytics(
            class_id=class_id,
            section_id=section_id,
            total_students=len(students),
            avg_score=round(avg_score, 2),
            pass_rate=round(pass_rate, 2),
            top_performers=sorted(top_performers, key=lambda x: x["avg_score"], reverse=True)[:10],
            at_risk_students=at_risk,
            subject_wise_performance=[],
            topic_wise_analysis=[],
        )
    
    async def generate_teacher_report(
        self,
        teacher_id: UUID,
        start_date: date,
        end_date: date,
    ) -> TeacherEffectivenessReport:
        """Generate teacher effectiveness report."""
        teacher = await self.session.get(User, teacher_id)
        if not teacher:
            raise ValueError("Teacher not found")
        
        # Get lessons
        lesson_query = select(Lesson).where(
            Lesson.tenant_id == self.tenant_id,
            Lesson.teacher_id == teacher_id,
        )
        lesson_result = await self.session.execute(lesson_query)
        lessons = list(lesson_result.scalars().all())
        
        lessons_planned = len(lessons)
        lessons_completed = len([l for l in lessons if l.completed_at is not None])
        
        # Get assignments created
        assignment_query = select(Assignment).where(
            Assignment.tenant_id == self.tenant_id,
            Assignment.created_by == teacher_id,
            Assignment.created_at >= datetime.combine(start_date, datetime.min.time()),
        )
        assign_result = await self.session.execute(assignment_query)
        assignments = list(assign_result.scalars().all())
        
        # Get submissions for teacher's assignments
        submission_query = select(AssignmentSubmission).where(
            AssignmentSubmission.assignment_id.in_([a.id for a in assignments]),
            AssignmentSubmission.status == 'graded',
        )
        sub_result = await self.session.execute(submission_query)
        submissions = list(sub_result.scalars().all())
        
        avg_score = sum(s.percentage for s in submissions) / len(submissions) if submissions else 0
        pass_rate = len([s for s in submissions if s.is_passed]) / len(submissions) * 100 if submissions else 0
        
        return TeacherEffectivenessReport(
            teacher_id=teacher_id,
            teacher_name=teacher.full_name,
            lessons_planned=lessons_planned,
            lessons_completed=lessons_completed,
            syllabus_completion=round(lessons_completed / lessons_planned * 100, 2) if lessons_planned > 0 else 0,
            assignments_created=len(assignments),
            avg_grading_time_hours=0,  # Would need tracking
            class_avg_score=round(avg_score, 2),
            pass_rate=round(pass_rate, 2),
            student_engagement=0,  # Would need tracking
        )
    
    async def save_report(
        self,
        request: ReportRequest,
        data: dict,
        generated_by: UUID,
    ) -> Report:
        """Save generated report."""
        report = Report(
            tenant_id=self.tenant_id,
            title=f"{request.report_type.value} Report",
            report_type=request.report_type,
            period=request.period,
            start_date=request.start_date,
            end_date=request.end_date,
            student_id=request.student_id,
            teacher_id=request.teacher_id,
            class_id=request.class_id,
            section_id=request.section_id,
            subject_id=request.subject_id,
            data=data,
            generated_by=generated_by,
            generated_at=datetime.now(timezone.utc),
        )
        
        self.session.add(report)
        await self.session.commit()
        await self.session.refresh(report)
        
        return report
