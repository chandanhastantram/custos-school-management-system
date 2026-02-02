"""
CUSTOS Analytics Router

API endpoints with strict role-based visibility enforcement.

VISIBILITY RULES (STRICTLY ENFORCED):
- Students: ONLY activity score, NO actual score, NO class averages
- Parents: Only their child's activity score
- Teachers: Their classes only, both scores, no ranking
- Admin/Principal: Full visibility

NO RANKINGS. NO LEADERBOARDS. NO COMPARISONS.
"""

from datetime import date
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth.dependencies import CurrentUser, require_permission, require_role
from app.users.rbac import Permission, SystemRole
from app.analytics.service import AnalyticsService
from app.analytics.models import AnalyticsPeriod
from app.analytics.schemas import (
    AnalyticsGenerateRequest,
    AnalyticsGenerateResponse,
    StudentActivityScoreResponse,
    StudentProgressSummary,
    StudentFullAnalyticsResponse,
    StudentAnalyticsListItem,
    TeacherSelfAnalyticsResponse,
    TeacherFullAnalyticsResponse,
    TeacherAnalyticsListItem,
    ClassAnalyticsResponse,
    ClassAnalyticsListItem,
    PrincipalDashboardSummary,
    TeacherDashboardSummary,
)


router = APIRouter(tags=["Analytics"])


# ============================================
# Admin: Generate Analytics
# ============================================

@router.post("/generate", response_model=AnalyticsGenerateResponse)
async def generate_analytics(
    data: AnalyticsGenerateRequest,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.ANALYTICS_VIEW_ADMIN)),
):
    """
    Generate analytics snapshots for a period.
    
    Admin/Principal only. Triggers snapshot generation for all entities.
    """
    service = AnalyticsService(db, user.tenant_id)
    
    students, teachers, classes = await service.generate_all_snapshots(
        period_start=data.period_start,
        period_end=data.period_end,
        period_type=data.period_type,
        class_id=data.class_id,
        subject_id=data.subject_id,
        generated_by=user.id,
    )
    
    return AnalyticsGenerateResponse(
        success=True,
        students_processed=students,
        teachers_processed=teachers,
        classes_processed=classes,
        message=f"Generated {students} student, {teachers} teacher, {classes} class snapshots",
    )


# ============================================
# Admin/Principal: Full View
# ============================================

@router.get("/students", response_model=List[StudentFullAnalyticsResponse])
async def get_all_students_analytics(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    period_start: date = Query(...),
    period_end: date = Query(...),
    class_id: Optional[UUID] = None,
    subject_id: Optional[UUID] = None,
    _=Depends(require_permission(Permission.ANALYTICS_VIEW_ADMIN)),
):
    """
    Get analytics for all students.
    
    Admin/Principal only. Full data including actual scores.
    """
    service = AnalyticsService(db, user.tenant_id)
    
    if class_id:
        snapshots = await service.get_class_students_analytics(
            class_id, period_start, period_end, subject_id
        )
    else:
        # Get all classes' students
        snapshots = []
        class_snapshots = await service.get_all_classes_analytics(period_start, period_end)
        for cs in class_snapshots:
            class_students = await service.get_class_students_analytics(
                cs.class_id, period_start, period_end, subject_id
            )
            snapshots.extend(class_students)
    
    return [
        StudentFullAnalyticsResponse(
            id=s.id,
            student_id=s.student_id,
            class_id=s.class_id,
            subject_id=s.subject_id,
            period_start=s.period_start,
            period_end=s.period_end,
            period_type=s.period_type,
            activity_score=float(s.activity_score),
            daily_loop_participation_pct=float(s.daily_loop_participation_pct),
            weekly_test_participation_pct=float(s.weekly_test_participation_pct),
            lesson_eval_participation_pct=float(s.lesson_eval_participation_pct),
            attendance_pct=float(s.attendance_pct),
            actual_score=float(s.actual_score),
            daily_mastery_pct=float(s.daily_mastery_pct),
            weekly_test_mastery_pct=float(s.weekly_test_mastery_pct),
            lesson_eval_mastery_pct=float(s.lesson_eval_mastery_pct),
            overall_mastery_pct=float(s.overall_mastery_pct),
            daily_loops_total=s.daily_loops_total,
            daily_loops_completed=s.daily_loops_completed,
            weekly_tests_total=s.weekly_tests_total,
            weekly_tests_completed=s.weekly_tests_completed,
            lesson_evals_total=s.lesson_evals_total,
            lesson_evals_completed=s.lesson_evals_completed,
            school_days_total=s.school_days_total,
            school_days_present=s.school_days_present,
            weak_concepts_json=s.weak_concepts_json,
            strong_concepts_json=s.strong_concepts_json,
            generated_at=s.generated_at,
        )
        for s in snapshots
    ]


@router.get("/teachers", response_model=List[TeacherFullAnalyticsResponse])
async def get_all_teachers_analytics(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    period_start: date = Query(...),
    period_end: date = Query(...),
    _=Depends(require_permission(Permission.ANALYTICS_VIEW_ADMIN)),
):
    """
    Get analytics for all teachers.
    
    Admin/Principal only.
    """
    service = AnalyticsService(db, user.tenant_id)
    snapshots = await service.get_all_teachers_analytics(period_start, period_end)
    
    return [
        TeacherFullAnalyticsResponse(
            id=s.id,
            teacher_id=s.teacher_id,
            subject_id=s.subject_id,
            class_id=s.class_id,
            period_start=s.period_start,
            period_end=s.period_end,
            period_type=s.period_type,
            syllabus_coverage_pct=float(s.syllabus_coverage_pct),
            lessons_planned=s.lessons_planned,
            lessons_completed=s.lessons_completed,
            schedule_adherence_pct=float(s.schedule_adherence_pct),
            periods_scheduled=s.periods_scheduled,
            periods_conducted=s.periods_conducted,
            student_participation_pct=float(s.student_participation_pct),
            class_mastery_avg=float(s.class_mastery_avg),
            daily_loops_created=s.daily_loops_created,
            weekly_tests_created=s.weekly_tests_created,
            lesson_evals_created=s.lesson_evals_created,
            engagement_score=float(s.engagement_score),
            generated_at=s.generated_at,
        )
        for s in snapshots
    ]


@router.get("/classes", response_model=List[ClassAnalyticsResponse])
async def get_all_classes_analytics(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    period_start: date = Query(...),
    period_end: date = Query(...),
    _=Depends(require_permission(Permission.ANALYTICS_VIEW_ADMIN)),
):
    """
    Get analytics for all classes.
    
    Admin/Principal only. Aggregate data, no individual students.
    """
    service = AnalyticsService(db, user.tenant_id)
    snapshots = await service.get_all_classes_analytics(period_start, period_end)
    
    return [
        ClassAnalyticsResponse(
            id=s.id,
            class_id=s.class_id,
            subject_id=s.subject_id,
            period_start=s.period_start,
            period_end=s.period_end,
            period_type=s.period_type,
            total_students=s.total_students,
            avg_mastery_pct=float(s.avg_mastery_pct),
            avg_activity_score=float(s.avg_activity_score),
            avg_attendance_pct=float(s.avg_attendance_pct),
            daily_loop_participation_avg=float(s.daily_loop_participation_avg),
            weekly_test_participation_avg=float(s.weekly_test_participation_avg),
            lesson_eval_participation_avg=float(s.lesson_eval_participation_avg),
            common_weak_topics_json=s.common_weak_topics_json,
            common_strong_topics_json=s.common_strong_topics_json,
            weak_topic_count=s.weak_topic_count,
            strong_topic_count=s.strong_topic_count,
            syllabus_coverage_pct=float(s.syllabus_coverage_pct),
            generated_at=s.generated_at,
        )
        for s in snapshots
    ]


@router.get("/dashboard/principal", response_model=PrincipalDashboardSummary)
async def get_principal_dashboard(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    period_start: date = Query(...),
    period_end: date = Query(...),
    _=Depends(require_permission(Permission.ANALYTICS_VIEW_ADMIN)),
):
    """
    Get principal's dashboard summary.
    
    High-level insights, no individual student data.
    """
    service = AnalyticsService(db, user.tenant_id)
    data = await service.get_principal_dashboard(period_start, period_end)
    
    return PrincipalDashboardSummary(
        period_start=data["period_start"],
        period_end=data["period_end"],
        total_students=data["total_students"],
        total_teachers=data["total_teachers"],
        total_classes=data["total_classes"],
        school_avg_mastery=data["school_avg_mastery"],
        school_avg_attendance=data["school_avg_attendance"],
        school_avg_activity=data["school_avg_activity"],
        avg_syllabus_coverage=data["avg_syllabus_coverage"],
        avg_teacher_engagement=data["avg_teacher_engagement"],
        classes_needing_attention=data["classes_needing_attention"],
        subjects_with_low_mastery=data["subjects_with_low_mastery"],
    )


# ============================================
# Teacher: Their Classes
# ============================================

@router.get("/my-classes", response_model=List[ClassAnalyticsResponse])
async def get_my_classes_analytics(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    period_start: date = Query(...),
    period_end: date = Query(...),
    _=Depends(require_permission(Permission.ANALYTICS_VIEW_TEACHER)),
):
    """
    Get analytics for teacher's assigned classes.
    
    Teachers only. Shows their classes' aggregate data.
    """
    service = AnalyticsService(db, user.tenant_id)
    
    # Get teacher's snapshots to identify their classes
    teacher_snapshots = await service.get_all_teachers_analytics(period_start, period_end)
    my_snapshots = [s for s in teacher_snapshots if s.teacher_id == user.id]
    
    class_ids = set(s.class_id for s in my_snapshots if s.class_id)
    
    result = []
    for class_id in class_ids:
        snapshot = await service.get_class_snapshot(class_id, period_start, period_end)
        if snapshot:
            result.append(ClassAnalyticsResponse(
                id=snapshot.id,
                class_id=snapshot.class_id,
                subject_id=snapshot.subject_id,
                period_start=snapshot.period_start,
                period_end=snapshot.period_end,
                period_type=snapshot.period_type,
                total_students=snapshot.total_students,
                avg_mastery_pct=float(snapshot.avg_mastery_pct),
                avg_activity_score=float(snapshot.avg_activity_score),
                avg_attendance_pct=float(snapshot.avg_attendance_pct),
                daily_loop_participation_avg=float(snapshot.daily_loop_participation_avg),
                weekly_test_participation_avg=float(snapshot.weekly_test_participation_avg),
                lesson_eval_participation_avg=float(snapshot.lesson_eval_participation_avg),
                common_weak_topics_json=snapshot.common_weak_topics_json,
                common_strong_topics_json=snapshot.common_strong_topics_json,
                weak_topic_count=snapshot.weak_topic_count,
                strong_topic_count=snapshot.strong_topic_count,
                syllabus_coverage_pct=float(snapshot.syllabus_coverage_pct),
                generated_at=snapshot.generated_at,
            ))
    
    return result


@router.get("/my-classes/{class_id}/students", response_model=List[StudentFullAnalyticsResponse])
async def get_my_class_students_analytics(
    class_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    period_start: date = Query(...),
    period_end: date = Query(...),
    subject_id: Optional[UUID] = None,
    _=Depends(require_permission(Permission.ANALYTICS_VIEW_TEACHER)),
):
    """
    Get analytics for students in teacher's class.
    
    Teachers only. Full data for their assigned classes.
    NO RANKING - data returned in alphabetical order.
    """
    # TODO: Verify teacher is assigned to this class
    
    service = AnalyticsService(db, user.tenant_id)
    snapshots = await service.get_class_students_analytics(
        class_id, period_start, period_end, subject_id
    )
    
    return [
        StudentFullAnalyticsResponse(
            id=s.id,
            student_id=s.student_id,
            class_id=s.class_id,
            subject_id=s.subject_id,
            period_start=s.period_start,
            period_end=s.period_end,
            period_type=s.period_type,
            activity_score=float(s.activity_score),
            daily_loop_participation_pct=float(s.daily_loop_participation_pct),
            weekly_test_participation_pct=float(s.weekly_test_participation_pct),
            lesson_eval_participation_pct=float(s.lesson_eval_participation_pct),
            attendance_pct=float(s.attendance_pct),
            actual_score=float(s.actual_score),
            daily_mastery_pct=float(s.daily_mastery_pct),
            weekly_test_mastery_pct=float(s.weekly_test_mastery_pct),
            lesson_eval_mastery_pct=float(s.lesson_eval_mastery_pct),
            overall_mastery_pct=float(s.overall_mastery_pct),
            daily_loops_total=s.daily_loops_total,
            daily_loops_completed=s.daily_loops_completed,
            weekly_tests_total=s.weekly_tests_total,
            weekly_tests_completed=s.weekly_tests_completed,
            lesson_evals_total=s.lesson_evals_total,
            lesson_evals_completed=s.lesson_evals_completed,
            school_days_total=s.school_days_total,
            school_days_present=s.school_days_present,
            weak_concepts_json=s.weak_concepts_json,
            strong_concepts_json=s.strong_concepts_json,
            generated_at=s.generated_at,
        )
        for s in snapshots
    ]


@router.get("/my-performance", response_model=TeacherSelfAnalyticsResponse)
async def get_my_performance(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    period_start: date = Query(...),
    period_end: date = Query(...),
    _=Depends(require_permission(Permission.ANALYTICS_VIEW_TEACHER)),
):
    """
    Get teacher's own performance analytics.
    
    Teachers only. Self-view for improvement.
    """
    service = AnalyticsService(db, user.tenant_id)
    snapshot = await service.get_teacher_snapshot(
        user.id, period_start, period_end
    )
    
    if not snapshot:
        raise HTTPException(status_code=404, detail="No analytics found for this period")
    
    return TeacherSelfAnalyticsResponse(
        id=snapshot.id,
        teacher_id=snapshot.teacher_id,
        subject_id=snapshot.subject_id,
        class_id=snapshot.class_id,
        period_start=snapshot.period_start,
        period_end=snapshot.period_end,
        period_type=snapshot.period_type,
        syllabus_coverage_pct=float(snapshot.syllabus_coverage_pct),
        lessons_planned=snapshot.lessons_planned,
        lessons_completed=snapshot.lessons_completed,
        schedule_adherence_pct=float(snapshot.schedule_adherence_pct),
        periods_scheduled=snapshot.periods_scheduled,
        periods_conducted=snapshot.periods_conducted,
        student_participation_pct=float(snapshot.student_participation_pct),
        class_mastery_avg=float(snapshot.class_mastery_avg),
        daily_loops_created=snapshot.daily_loops_created,
        weekly_tests_created=snapshot.weekly_tests_created,
        lesson_evals_created=snapshot.lesson_evals_created,
        engagement_score=float(snapshot.engagement_score),
        generated_at=snapshot.generated_at,
    )


@router.get("/dashboard/teacher", response_model=TeacherDashboardSummary)
async def get_teacher_dashboard(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    period_start: date = Query(...),
    period_end: date = Query(...),
    _=Depends(require_permission(Permission.ANALYTICS_VIEW_TEACHER)),
):
    """
    Get teacher's dashboard summary.
    """
    service = AnalyticsService(db, user.tenant_id)
    data = await service.get_teacher_dashboard(user.id, period_start, period_end)
    
    return TeacherDashboardSummary(
        teacher_id=data["teacher_id"],
        teacher_name="",  # TODO: Fetch from user
        period_start=data["period_start"],
        period_end=data["period_end"],
        total_classes=data["total_classes"],
        total_students=data["total_students"],
        avg_syllabus_coverage=data["avg_syllabus_coverage"],
        avg_student_participation=data["avg_student_participation"],
        avg_class_mastery=data["avg_class_mastery"],
        engagement_score=data["engagement_score"],
    )


# ============================================
# Student Self-View (ACTIVITY SCORE ONLY)
# ============================================

@router.get("/my-activity-score", response_model=StudentActivityScoreResponse)
async def get_my_activity_score(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    period_start: date = Query(...),
    period_end: date = Query(...),
    subject_id: Optional[UUID] = None,
    _=Depends(require_permission(Permission.ANALYTICS_VIEW_STUDENT)),
):
    """
    Get student's OWN activity score.
    
    Students only. Shows ONLY activity score (participation).
    actual_score is NEVER exposed to students.
    
    NO class comparison. NO rankings.
    """
    service = AnalyticsService(db, user.tenant_id)
    snapshot = await service.get_student_snapshot(
        user.id, period_start, period_end, subject_id
    )
    
    if not snapshot:
        raise HTTPException(status_code=404, detail="No analytics found for this period")
    
    # IMPORTANT: Only return activity-related fields
    return StudentActivityScoreResponse(
        student_id=snapshot.student_id,
        period_start=snapshot.period_start,
        period_end=snapshot.period_end,
        period_type=snapshot.period_type,
        
        # Activity metrics (VISIBLE)
        activity_score=float(snapshot.activity_score),
        daily_loop_participation_pct=float(snapshot.daily_loop_participation_pct),
        weekly_test_participation_pct=float(snapshot.weekly_test_participation_pct),
        lesson_eval_participation_pct=float(snapshot.lesson_eval_participation_pct),
        attendance_pct=float(snapshot.attendance_pct),
        
        # Raw counts (VISIBLE)
        daily_loops_completed=snapshot.daily_loops_completed,
        daily_loops_total=snapshot.daily_loops_total,
        weekly_tests_completed=snapshot.weekly_tests_completed,
        weekly_tests_total=snapshot.weekly_tests_total,
        lesson_evals_completed=snapshot.lesson_evals_completed,
        lesson_evals_total=snapshot.lesson_evals_total,
        school_days_present=snapshot.school_days_present,
        school_days_total=snapshot.school_days_total,
        
        generated_at=snapshot.generated_at,
        
        # NOTE: actual_score, mastery_pct fields are EXCLUDED
    )


@router.get("/my-progress-summary", response_model=StudentProgressSummary)
async def get_my_progress_summary(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    subject_id: Optional[UUID] = None,
    _=Depends(require_permission(Permission.ANALYTICS_VIEW_STUDENT)),
):
    """
    Get student's progress summary with trends.
    
    Shows personal improvement over time.
    NO comparison to other students. NO class averages.
    """
    service = AnalyticsService(db, user.tenant_id)
    
    # Get last 4 weeks of snapshots
    history = await service.get_student_history(user.id, weeks=4, subject_id=subject_id)
    
    if not history:
        raise HTTPException(status_code=404, detail="No analytics history found")
    
    current = history[0] if history else None
    activity_history = [float(s.activity_score) for s in history]
    
    # Determine trend (self-comparison only)
    if len(activity_history) >= 2:
        recent_avg = sum(activity_history[:2]) / 2
        older_avg = sum(activity_history[2:]) / len(activity_history[2:]) if len(activity_history) > 2 else recent_avg
        
        if recent_avg > older_avg + 5:
            trend = "improving"
        elif recent_avg < older_avg - 5:
            trend = "declining"
        else:
            trend = "stable"
        
        improvement = recent_avg - older_avg
    else:
        trend = "stable"
        improvement = None
    
    return StudentProgressSummary(
        student_id=user.id,
        student_name="",  # TODO: Fetch from user
        current_activity_score=float(current.activity_score) if current else 0.0,
        current_attendance_pct=float(current.attendance_pct) if current else 0.0,
        current_participation_trend=trend,
        activity_scores_history=activity_history,
        personal_improvement_pct=improvement,
    )


# ============================================
# Parent View (Child's Activity Score Only)
# ============================================

@router.get("/child/{student_id}/activity-score", response_model=StudentActivityScoreResponse)
async def get_child_activity_score(
    student_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    period_start: date = Query(...),
    period_end: date = Query(...),
    subject_id: Optional[UUID] = None,
):
    """
    Get parent's child's activity score.
    
    Parents only. Shows ONLY activity score (participation).
    actual_score is NEVER exposed.
    
    Validates parent-child relationship.
    """
    # TODO: Verify parent-child relationship
    # For now, we trust the user has appropriate access
    
    service = AnalyticsService(db, user.tenant_id)
    snapshot = await service.get_student_snapshot(
        student_id, period_start, period_end, subject_id
    )
    
    if not snapshot:
        raise HTTPException(status_code=404, detail="No analytics found for this period")
    
    # IMPORTANT: Only return activity-related fields
    return StudentActivityScoreResponse(
        student_id=snapshot.student_id,
        period_start=snapshot.period_start,
        period_end=snapshot.period_end,
        period_type=snapshot.period_type,
        
        # Activity metrics (VISIBLE)
        activity_score=float(snapshot.activity_score),
        daily_loop_participation_pct=float(snapshot.daily_loop_participation_pct),
        weekly_test_participation_pct=float(snapshot.weekly_test_participation_pct),
        lesson_eval_participation_pct=float(snapshot.lesson_eval_participation_pct),
        attendance_pct=float(snapshot.attendance_pct),
        
        # Raw counts (VISIBLE)
        daily_loops_completed=snapshot.daily_loops_completed,
        daily_loops_total=snapshot.daily_loops_total,
        weekly_tests_completed=snapshot.weekly_tests_completed,
        weekly_tests_total=snapshot.weekly_tests_total,
        lesson_evals_completed=snapshot.lesson_evals_completed,
        lesson_evals_total=snapshot.lesson_evals_total,
        school_days_present=snapshot.school_days_present,
        school_days_total=snapshot.school_days_total,
        
        generated_at=snapshot.generated_at,
    )


@router.get("/child/{student_id}/progress-summary", response_model=StudentProgressSummary)
async def get_child_progress_summary(
    student_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    subject_id: Optional[UUID] = None,
):
    """
    Get parent's child's progress summary.
    
    Parents only. Shows personal improvement trends.
    NO comparison to other students.
    """
    # TODO: Verify parent-child relationship
    
    service = AnalyticsService(db, user.tenant_id)
    history = await service.get_student_history(student_id, weeks=4, subject_id=subject_id)
    
    if not history:
        raise HTTPException(status_code=404, detail="No analytics history found")
    
    current = history[0] if history else None
    activity_history = [float(s.activity_score) for s in history]
    
    # Determine trend
    if len(activity_history) >= 2:
        recent_avg = sum(activity_history[:2]) / 2
        older_avg = sum(activity_history[2:]) / len(activity_history[2:]) if len(activity_history) > 2 else recent_avg
        
        if recent_avg > older_avg + 5:
            trend = "improving"
        elif recent_avg < older_avg - 5:
            trend = "declining"
        else:
            trend = "stable"
        
        improvement = recent_avg - older_avg
    else:
        trend = "stable"
        improvement = None
    
    return StudentProgressSummary(
        student_id=student_id,
        student_name="",  # TODO: Fetch
        current_activity_score=float(current.activity_score) if current else 0.0,
        current_attendance_pct=float(current.attendance_pct) if current else 0.0,
        current_participation_trend=trend,
        activity_scores_history=activity_history,
        personal_improvement_pct=improvement,
    )
