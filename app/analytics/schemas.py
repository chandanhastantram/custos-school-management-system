"""
CUSTOS Analytics Schemas

Pydantic schemas with strict role-based visibility enforcement.

CORE PRINCIPLE: Two score types, separate visibility.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from app.analytics.models import AnalyticsPeriod


# ============================================
# Generation Request Schemas
# ============================================

class AnalyticsGenerateRequest(BaseModel):
    """Request to generate analytics snapshots."""
    period_start: date
    period_end: date
    period_type: AnalyticsPeriod = AnalyticsPeriod.WEEKLY
    class_id: Optional[UUID] = None
    subject_id: Optional[UUID] = None


class AnalyticsGenerateResponse(BaseModel):
    """Response from analytics generation."""
    success: bool
    students_processed: int = 0
    teachers_processed: int = 0
    classes_processed: int = 0
    message: str


# ============================================
# Student Analytics Schemas (VISIBILITY-AWARE)
# ============================================

class StudentActivityScoreResponse(BaseModel):
    """
    Student-visible activity score only.
    
    This is what STUDENTS can see - NO actual performance score.
    """
    model_config = ConfigDict(from_attributes=True)
    
    student_id: UUID
    period_start: date
    period_end: date
    period_type: AnalyticsPeriod
    
    # VISIBLE: Activity score and breakdown
    activity_score: float
    daily_loop_participation_pct: float
    weekly_test_participation_pct: float
    lesson_eval_participation_pct: float
    attendance_pct: float
    
    # VISIBLE: Raw participation counts
    daily_loops_completed: int
    daily_loops_total: int
    weekly_tests_completed: int
    weekly_tests_total: int
    lesson_evals_completed: int
    lesson_evals_total: int
    school_days_present: int
    school_days_total: int
    
    generated_at: datetime
    
    # NOTE: actual_score and mastery metrics are EXCLUDED


class StudentProgressSummary(BaseModel):
    """
    Student's progress summary for self-view.
    
    Shows participation trends, NOT performance rankings.
    """
    student_id: UUID
    student_name: str
    class_name: Optional[str] = None
    
    # Current period
    current_activity_score: float
    current_attendance_pct: float
    current_participation_trend: str  # "improving", "stable", "declining"
    
    # Historical (last 4 weeks)
    activity_scores_history: List[float] = []
    
    # Personal goals (self-comparison only)
    personal_improvement_pct: Optional[float] = None


class StudentFullAnalyticsResponse(BaseModel):
    """
    Full student analytics for teachers/admin only.
    
    Contains BOTH activity and actual scores.
    Students and parents should NEVER see this.
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    student_id: UUID
    class_id: UUID
    subject_id: Optional[UUID] = None
    period_start: date
    period_end: date
    period_type: AnalyticsPeriod
    
    # Activity Score (student-visible)
    activity_score: float
    daily_loop_participation_pct: float
    weekly_test_participation_pct: float
    lesson_eval_participation_pct: float
    attendance_pct: float
    
    # Actual Performance Score (HIDDEN from students)
    actual_score: float
    daily_mastery_pct: float
    weekly_test_mastery_pct: float
    lesson_eval_mastery_pct: float
    overall_mastery_pct: float
    
    # Raw counts
    daily_loops_total: int
    daily_loops_completed: int
    weekly_tests_total: int
    weekly_tests_completed: int
    lesson_evals_total: int
    lesson_evals_completed: int
    school_days_total: int
    school_days_present: int
    
    # Concept analysis (for teacher insight, NOT ranking)
    weak_concepts_json: Optional[list] = None
    strong_concepts_json: Optional[list] = None
    
    generated_at: datetime
    
    # Denormalized
    student_name: Optional[str] = None
    class_name: Optional[str] = None
    subject_name: Optional[str] = None


class StudentAnalyticsListItem(BaseModel):
    """
    List item for teachers viewing class students.
    
    Shows mastery, NOT rankings. No "top/bottom" indicators.
    """
    student_id: UUID
    student_name: str
    activity_score: float
    actual_score: float
    overall_mastery_pct: float
    attendance_pct: float


# ============================================
# Teacher Analytics Schemas
# ============================================

class TeacherSelfAnalyticsResponse(BaseModel):
    """
    Teacher's own analytics view.
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    teacher_id: UUID
    subject_id: Optional[UUID] = None
    class_id: Optional[UUID] = None
    period_start: date
    period_end: date
    period_type: AnalyticsPeriod
    
    # Teaching metrics
    syllabus_coverage_pct: float
    lessons_planned: int
    lessons_completed: int
    schedule_adherence_pct: float
    periods_scheduled: int
    periods_conducted: int
    
    # Student engagement (aggregate only)
    student_participation_pct: float
    class_mastery_avg: float
    
    # Assessment activity
    daily_loops_created: int
    weekly_tests_created: int
    lesson_evals_created: int
    
    # Overall score
    engagement_score: float
    
    generated_at: datetime
    
    # Denormalized
    subject_name: Optional[str] = None
    class_name: Optional[str] = None


class TeacherAnalyticsListItem(BaseModel):
    """
    List item for admin viewing teachers.
    
    For monitoring, NOT ranking or comparison.
    """
    teacher_id: UUID
    teacher_name: str
    syllabus_coverage_pct: float
    schedule_adherence_pct: float
    student_participation_pct: float
    engagement_score: float


class TeacherFullAnalyticsResponse(BaseModel):
    """
    Full teacher analytics for admin view.
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    teacher_id: UUID
    subject_id: Optional[UUID] = None
    class_id: Optional[UUID] = None
    period_start: date
    period_end: date
    period_type: AnalyticsPeriod
    
    # All metrics
    syllabus_coverage_pct: float
    lessons_planned: int
    lessons_completed: int
    schedule_adherence_pct: float
    periods_scheduled: int
    periods_conducted: int
    student_participation_pct: float
    class_mastery_avg: float
    daily_loops_created: int
    weekly_tests_created: int
    lesson_evals_created: int
    engagement_score: float
    
    generated_at: datetime
    
    # Denormalized
    teacher_name: Optional[str] = None
    subject_name: Optional[str] = None
    class_name: Optional[str] = None


# ============================================
# Class Analytics Schemas
# ============================================

class ClassAnalyticsResponse(BaseModel):
    """
    Class analytics for teachers and admin.
    
    Shows aggregate patterns, NO individual student data.
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    class_id: UUID
    subject_id: Optional[UUID] = None
    period_start: date
    period_end: date
    period_type: AnalyticsPeriod
    
    # Class info
    total_students: int
    
    # Aggregate metrics (averages only)
    avg_mastery_pct: float
    avg_activity_score: float
    avg_attendance_pct: float
    
    # Participation rates
    daily_loop_participation_avg: float
    weekly_test_participation_avg: float
    lesson_eval_participation_avg: float
    
    # Topic patterns (for teaching focus, NOT comparison)
    common_weak_topics_json: Optional[list] = None
    common_strong_topics_json: Optional[list] = None
    weak_topic_count: int
    strong_topic_count: int
    
    # Progress
    syllabus_coverage_pct: float
    
    generated_at: datetime
    
    # Denormalized
    class_name: Optional[str] = None
    subject_name: Optional[str] = None


class ClassAnalyticsListItem(BaseModel):
    """
    List item for viewing multiple classes.
    """
    class_id: UUID
    class_name: str
    subject_name: Optional[str] = None
    total_students: int
    avg_mastery_pct: float
    avg_activity_score: float
    avg_attendance_pct: float
    syllabus_coverage_pct: float


# ============================================
# Period Filter Schema
# ============================================

class AnalyticsPeriodFilter(BaseModel):
    """Filter for analytics queries."""
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    period_type: Optional[AnalyticsPeriod] = None
    class_id: Optional[UUID] = None
    subject_id: Optional[UUID] = None


# ============================================
# Dashboard Summary Schemas
# ============================================

class PrincipalDashboardSummary(BaseModel):
    """
    Principal's high-level dashboard.
    
    Aggregate insights, NO individual student data.
    """
    period_start: date
    period_end: date
    
    # School-wide
    total_students: int
    total_teachers: int
    total_classes: int
    
    # Averages
    school_avg_mastery: float
    school_avg_attendance: float
    school_avg_activity: float
    
    # Teaching
    avg_syllabus_coverage: float
    avg_teacher_engagement: float
    
    # Attention areas (patterns, not names)
    classes_needing_attention: int  # Below threshold
    subjects_with_low_mastery: int


class TeacherDashboardSummary(BaseModel):
    """
    Teacher's dashboard for their classes.
    """
    teacher_id: UUID
    teacher_name: str
    period_start: date
    period_end: date
    
    # Their metrics
    total_classes: int
    total_students: int
    avg_syllabus_coverage: float
    avg_student_participation: float
    avg_class_mastery: float
    
    # Their engagement score
    engagement_score: float
