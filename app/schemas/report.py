"""
CUSTOS Report Schemas
"""

from datetime import datetime, date
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel

from app.models.report import ReportType, ReportPeriod


class ReportRequest(BaseModel):
    report_type: ReportType
    period: ReportPeriod
    start_date: date
    end_date: date
    
    student_id: Optional[UUID] = None
    teacher_id: Optional[UUID] = None
    class_id: Optional[UUID] = None
    section_id: Optional[UUID] = None
    subject_id: Optional[UUID] = None


class ReportResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    title: str
    report_type: ReportType
    period: ReportPeriod
    
    start_date: date
    end_date: date
    
    data: dict
    summary: Optional[dict] = None
    insights: Optional[List[str]] = None
    
    generated_by: UUID
    generated_at: datetime
    pdf_url: Optional[str] = None
    
    class Config:
        from_attributes = True


class StudentReportSummary(BaseModel):
    student_id: UUID
    student_name: str
    
    total_assignments: int
    completed_assignments: int
    passed_assignments: int
    
    total_marks: float
    marks_obtained: float
    percentage: float
    
    accuracy: float
    rank_in_class: Optional[int] = None
    
    strength_topics: List[str]
    weakness_topics: List[str]


class ClassAnalytics(BaseModel):
    class_id: UUID
    section_id: UUID
    
    total_students: int
    avg_score: float
    pass_rate: float
    
    top_performers: List[dict]
    at_risk_students: List[dict]
    
    subject_wise_performance: List[dict]
    topic_wise_analysis: List[dict]


class TeacherEffectivenessReport(BaseModel):
    teacher_id: UUID
    teacher_name: str
    
    lessons_planned: int
    lessons_completed: int
    syllabus_completion: float
    
    assignments_created: int
    avg_grading_time_hours: float
    
    class_avg_score: float
    pass_rate: float
    
    student_engagement: float
