"""
CUSTOS AI Insights Service

Explainable AI Decision Support.

CORE PHILOSOPHY:
1. AI EXPLAINS — IT NEVER DECIDES
2. NO STUDENT COMPARISON
3. NO AUTOMATED ACTIONS
4. GOVERNANCE FIRST
5. INSIGHTS ARE SUGGESTIONS ONLY

SECURITY:
- Students/Parents CANNOT request or view AI insights
- All AI calls are audited
- Data is anonymized before AI processing
- Insights reference snapshots, not raw data
"""

import json
from datetime import datetime, timezone, date, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ResourceNotFoundError,
    ValidationError,
    PermissionDeniedError,
)
from app.insights.models import (
    InsightJob,
    GeneratedInsight,
    InsightQuota,
    InsightType,
    InsightCategory,
    InsightSeverity,
    JobStatus,
    RequestorRole,
)
from app.insights.schemas import (
    AnonymizedStudentData,
    AnonymizedClassData,
    AnonymizedTeacherData,
)
from app.analytics.models import (
    StudentAnalyticsSnapshot,
    TeacherAnalyticsSnapshot,
    ClassAnalyticsSnapshot,
)
from app.governance.service import GovernanceService
from app.governance.models import ActionType, EntityType


class InsightsService:
    """
    AI Insights & Decision Support Service.
    
    Generates explainable, governance-safe insights.
    
    CRITICAL RULES:
    - Never expose raw student data to AI
    - Never compare students
    - Always audit AI usage
    - Insights are advisory only
    """
    
    # AI Configuration
    AI_MODEL = "gpt-4"
    AI_TEMPERATURE = 0.25  # Low temperature for consistency
    PROMPT_VERSION = "v1.0"
    
    # Quota defaults
    DEFAULT_MAX_REQUESTS = 100
    DEFAULT_MAX_TOKENS = 100000
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
    
    # ============================================
    # Governance Validation
    # ============================================
    
    async def validate_governance_rules(
        self,
        requestor_id: UUID,
        requestor_role: RequestorRole,
        insight_type: InsightType,
        target_id: Optional[UUID],
    ) -> None:
        """
        Validate that the request meets governance rules.
        
        RULES:
        - Students & Parents: NO ACCESS EVER
        - Teachers: own classes and students only
        - Admins: all access
        """
        # Rule 1: Only Admin/Teacher can request
        if requestor_role not in [RequestorRole.ADMIN, RequestorRole.PRINCIPAL, RequestorRole.TEACHER]:
            raise PermissionDeniedError("Only administrators and teachers can request AI insights")
        
        # Rule 2: SCHOOL insights are Admin-only
        if insight_type == InsightType.SCHOOL and requestor_role == RequestorRole.TEACHER:
            raise PermissionDeniedError("School-wide insights are admin-only")
        
        # Rule 3: Target ID required for non-SCHOOL types
        if insight_type != InsightType.SCHOOL and target_id is None:
            raise ValidationError(f"target_id is required for {insight_type.value} insights")
        
        # Rule 4: Teachers can only view their own teacher insights
        if insight_type == InsightType.TEACHER and requestor_role == RequestorRole.TEACHER:
            if target_id != requestor_id:
                raise PermissionDeniedError("Teachers can only view their own performance insights")
        
        # Rule 5: Teachers must have class assignment for student/class insights
        # (In production, would check class assignments here)
        # For now, we allow teachers to request insights for any class/student
        # The frontend should filter based on assignments
        
        # All checks passed
    
    async def check_quota(self) -> InsightQuota:
        """Check and return current quota status."""
        now = datetime.now(timezone.utc)
        
        query = select(InsightQuota).where(
            InsightQuota.tenant_id == self.tenant_id,
            InsightQuota.month == now.month,
            InsightQuota.year == now.year,
        )
        result = await self.session.execute(query)
        quota = result.scalar_one_or_none()
        
        if not quota:
            # Create new quota for this month
            quota = InsightQuota(
                tenant_id=self.tenant_id,
                month=now.month,
                year=now.year,
                max_requests=self.DEFAULT_MAX_REQUESTS,
                max_tokens=self.DEFAULT_MAX_TOKENS,
                requests_used=0,
                tokens_used=0,
            )
            self.session.add(quota)
            await self.session.commit()
            await self.session.refresh(quota)
        
        return quota
    
    async def validate_quota(self) -> None:
        """Validate that quota is not exceeded."""
        quota = await self.check_quota()
        
        if quota.requests_used >= quota.max_requests:
            raise ValidationError(
                f"Monthly insight request quota exceeded ({quota.max_requests} requests)"
            )
        
        if quota.tokens_used >= quota.max_tokens:
            raise ValidationError(
                f"Monthly token quota exceeded ({quota.max_tokens} tokens)"
            )
    
    async def update_quota_usage(self, tokens_used: int) -> None:
        """Update quota after AI usage."""
        quota = await self.check_quota()
        quota.requests_used += 1
        quota.tokens_used += tokens_used
        quota.last_request_at = datetime.now(timezone.utc)
        await self.session.commit()
    
    # ============================================
    # Insight Request
    # ============================================
    
    async def request_insight(
        self,
        requestor_id: UUID,
        requestor_role: RequestorRole,
        requestor_email: Optional[str],
        insight_type: InsightType,
        target_id: Optional[UUID],
        period_start: date,
        period_end: date,
        ip_address: Optional[str] = None,
    ) -> InsightJob:
        """
        Request AI-generated insights.
        
        Creates a job and initiates processing.
        """
        # Validate governance rules
        await self.validate_governance_rules(
            requestor_id, requestor_role, insight_type, target_id
        )
        
        # Validate quota
        await self.validate_quota()
        
        # Get target name for display
        target_name = await self._get_target_name(insight_type, target_id)
        
        # Create job
        job = InsightJob(
            tenant_id=self.tenant_id,
            requested_by=requestor_id,
            requestor_role=requestor_role,
            requestor_email=requestor_email,
            insight_type=insight_type,
            target_id=target_id,
            target_name=target_name,
            period_start=datetime.combine(period_start, datetime.min.time()).replace(tzinfo=timezone.utc),
            period_end=datetime.combine(period_end, datetime.max.time()).replace(tzinfo=timezone.utc),
            status=JobStatus.PENDING,
            prompt_version=self.PROMPT_VERSION,
            model_used=self.AI_MODEL,
            ip_address=ip_address,
        )
        
        self.session.add(job)
        await self.session.commit()
        await self.session.refresh(job)
        
        # Audit the request
        governance = GovernanceService(self.session, self.tenant_id)
        await governance.log_action(
            action_type=ActionType.CREATE,
            entity_type=EntityType.ANALYTICS,
            entity_id=job.id,
            entity_name=f"AI Insight: {insight_type.value}",
            actor_user_id=requestor_id,
            description=f"Requested AI insights: {insight_type.value} for {target_name or 'school'}",
            ip_address=ip_address,
        )
        
        return job
    
    async def _get_target_name(
        self,
        insight_type: InsightType,
        target_id: Optional[UUID],
    ) -> Optional[str]:
        """Get display name for the target."""
        if not target_id:
            return None
        
        # In production, would query actual tables
        # For now, return a placeholder
        if insight_type == InsightType.STUDENT:
            return f"Student ({str(target_id)[:8]})"
        elif insight_type == InsightType.CLASS:
            return f"Class ({str(target_id)[:8]})"
        elif insight_type == InsightType.TEACHER:
            return f"Teacher ({str(target_id)[:8]})"
        
        return None
    
    # ============================================
    # Insight Generation
    # ============================================
    
    async def generate_insight(self, job_id: UUID) -> InsightJob:
        """
        Generate insights for a job.
        
        This is the main AI processing function.
        Data is FULLY ANONYMIZED before AI processing.
        """
        # Get job
        query = select(InsightJob).where(
            InsightJob.tenant_id == self.tenant_id,
            InsightJob.id == job_id,
        )
        result = await self.session.execute(query)
        job = result.scalar_one_or_none()
        
        if not job:
            raise ResourceNotFoundError("Insight job not found")
        
        if job.status not in [JobStatus.PENDING, JobStatus.FAILED]:
            raise ValidationError(f"Job is already {job.status.value}")
        
        # Update status to processing
        job.status = JobStatus.PROCESSING
        job.processing_started_at = datetime.now(timezone.utc)
        await self.session.commit()
        
        try:
            # Collect and anonymize data
            anonymized_data = await self._collect_anonymized_data(job)
            
            # Store snapshot references (not raw data)
            job.snapshot_ids_json = anonymized_data.get("snapshot_ids", [])
            
            # Generate insights using AI
            insights = await self._call_ai_for_insights(job, anonymized_data)
            
            # Store insights
            for insight_data in insights:
                insight = GeneratedInsight(
                    tenant_id=self.tenant_id,
                    insight_job_id=job.id,
                    category=insight_data["category"],
                    severity=insight_data["severity"],
                    title=insight_data["title"],
                    explanation_text=insight_data["explanation"],
                    evidence_json=insight_data.get("evidence"),
                    suggested_actions=insight_data.get("actions"),
                    confidence_score=Decimal(str(insight_data.get("confidence", 0.7))),
                    display_order=insight_data.get("order", 0),
                    is_actionable=insight_data.get("actionable", True),
                )
                self.session.add(insight)
            
            # Update job
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now(timezone.utc)
            job.tokens_used = anonymized_data.get("tokens_used", 0)
            
            await self.session.commit()
            await self.session.refresh(job)
            
            # Update quota
            await self.update_quota_usage(job.tokens_used)
            
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.now(timezone.utc)
            await self.session.commit()
            raise
        
        return job
    
    async def _collect_anonymized_data(self, job: InsightJob) -> dict:
        """
        Collect and anonymize data for AI processing.
        
        CRITICAL: No identifiable information in the output.
        """
        data = {
            "insight_type": job.insight_type.value,
            "period_days": (job.period_end - job.period_start).days,
            "snapshot_ids": [],
            "tokens_used": 0,
        }
        
        if job.insight_type == InsightType.STUDENT:
            data["student_data"] = await self._get_anonymized_student_data(
                job.target_id, job.period_start, job.period_end
            )
        elif job.insight_type == InsightType.CLASS:
            data["class_data"] = await self._get_anonymized_class_data(
                job.target_id, job.period_start, job.period_end
            )
        elif job.insight_type == InsightType.TEACHER:
            data["teacher_data"] = await self._get_anonymized_teacher_data(
                job.target_id, job.period_start, job.period_end
            )
        elif job.insight_type == InsightType.SCHOOL:
            data["school_data"] = await self._get_anonymized_school_data(
                job.period_start, job.period_end
            )
        
        return data
    
    async def _get_anonymized_student_data(
        self,
        student_id: UUID,
        period_start: datetime,
        period_end: datetime,
    ) -> dict:
        """
        Get anonymized student data.
        
        CRITICAL: Never include actual_score - students can't see it.
        """
        query = select(StudentAnalyticsSnapshot).where(
            StudentAnalyticsSnapshot.tenant_id == self.tenant_id,
            StudentAnalyticsSnapshot.student_id == student_id,
            StudentAnalyticsSnapshot.period_start >= period_start.date(),
            StudentAnalyticsSnapshot.period_end <= period_end.date(),
        ).order_by(StudentAnalyticsSnapshot.period_start)
        
        result = await self.session.execute(query)
        snapshots = list(result.scalars().all())
        
        if not snapshots:
            return {
                "activity_score": 0,
                "participation_trend": "no_data",
                "weak_concept_count": 0,
                "strong_concept_count": 0,
            }
        
        # Aggregate but anonymize
        latest = snapshots[-1]
        first = snapshots[0]
        
        # Calculate trend
        if len(snapshots) >= 2:
            if float(latest.activity_score) > float(first.activity_score) + 5:
                trend = "improving"
            elif float(latest.activity_score) < float(first.activity_score) - 5:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"
        
        return {
            "activity_score": float(latest.activity_score),
            "daily_participation_pct": float(latest.daily_loop_participation_pct),
            "weekly_participation_pct": float(latest.weekly_test_participation_pct),
            "lesson_participation_pct": float(latest.lesson_eval_participation_pct),
            "attendance_pct": float(latest.attendance_pct),
            "trend": trend,
            "weak_concept_count": len(latest.weak_concepts_json) if latest.weak_concepts_json else 0,
            "strong_concept_count": len(latest.strong_concepts_json) if latest.strong_concepts_json else 0,
            "snapshot_count": len(snapshots),
            # NOTE: NO actual_score, NO student_id, NO name
        }
    
    async def _get_anonymized_class_data(
        self,
        class_id: UUID,
        period_start: datetime,
        period_end: datetime,
    ) -> dict:
        """Get anonymized class data."""
        query = select(ClassAnalyticsSnapshot).where(
            ClassAnalyticsSnapshot.tenant_id == self.tenant_id,
            ClassAnalyticsSnapshot.class_id == class_id,
            ClassAnalyticsSnapshot.period_start >= period_start.date(),
            ClassAnalyticsSnapshot.period_end <= period_end.date(),
        ).order_by(ClassAnalyticsSnapshot.period_start)
        
        result = await self.session.execute(query)
        snapshots = list(result.scalars().all())
        
        if not snapshots:
            return {
                "student_count": 0,
                "avg_participation": 0,
                "avg_attendance": 0,
            }
        
        latest = snapshots[-1]
        
        return {
            "student_count": latest.total_students,
            "avg_activity_score": float(latest.avg_activity_score),
            "avg_attendance": float(latest.avg_attendance_pct),
            "daily_participation_avg": float(latest.daily_loop_participation_avg),
            "weekly_participation_avg": float(latest.weekly_test_participation_avg),
            "weak_topic_count": latest.weak_topic_count,
            "strong_topic_count": latest.strong_topic_count,
            "syllabus_coverage": float(latest.syllabus_coverage_pct),
            "snapshot_count": len(snapshots),
            # NOTE: NO individual student data
        }
    
    async def _get_anonymized_teacher_data(
        self,
        teacher_id: UUID,
        period_start: datetime,
        period_end: datetime,
    ) -> dict:
        """Get anonymized teacher data."""
        query = select(TeacherAnalyticsSnapshot).where(
            TeacherAnalyticsSnapshot.tenant_id == self.tenant_id,
            TeacherAnalyticsSnapshot.teacher_id == teacher_id,
            TeacherAnalyticsSnapshot.period_start >= period_start.date(),
            TeacherAnalyticsSnapshot.period_end <= period_end.date(),
        ).order_by(TeacherAnalyticsSnapshot.period_start)
        
        result = await self.session.execute(query)
        snapshots = list(result.scalars().all())
        
        if not snapshots:
            return {
                "syllabus_coverage": 0,
                "schedule_adherence": 0,
                "engagement_score": 0,
            }
        
        latest = snapshots[-1]
        
        return {
            "syllabus_coverage": float(latest.syllabus_coverage_pct),
            "lessons_planned": latest.lessons_planned,
            "lessons_completed": latest.lessons_completed,
            "schedule_adherence": float(latest.schedule_adherence_pct),
            "student_participation": float(latest.student_participation_pct),
            "class_mastery_avg": float(latest.class_mastery_avg),
            "engagement_score": float(latest.engagement_score),
            "assessments_created": (
                latest.daily_loops_created +
                latest.weekly_tests_created +
                latest.lesson_evals_created
            ),
            "snapshot_count": len(snapshots),
            # NOTE: NO teacher identity
        }
    
    async def _get_anonymized_school_data(
        self,
        period_start: datetime,
        period_end: datetime,
    ) -> dict:
        """Get anonymized school-wide data."""
        # Aggregate class data
        class_query = select(ClassAnalyticsSnapshot).where(
            ClassAnalyticsSnapshot.tenant_id == self.tenant_id,
            ClassAnalyticsSnapshot.period_start >= period_start.date(),
            ClassAnalyticsSnapshot.period_end <= period_end.date(),
        )
        result = await self.session.execute(class_query)
        class_snapshots = list(result.scalars().all())
        
        # Aggregate teacher data
        teacher_query = select(TeacherAnalyticsSnapshot).where(
            TeacherAnalyticsSnapshot.tenant_id == self.tenant_id,
            TeacherAnalyticsSnapshot.period_start >= period_start.date(),
            TeacherAnalyticsSnapshot.period_end <= period_end.date(),
        )
        result = await self.session.execute(teacher_query)
        teacher_snapshots = list(result.scalars().all())
        
        if not class_snapshots:
            return {
                "class_count": 0,
                "teacher_count": 0,
                "overall_participation": 0,
            }
        
        # Calculate aggregates (NO INDIVIDUAL DATA)
        total_students = sum(s.total_students for s in class_snapshots)
        avg_participation = sum(float(s.avg_activity_score) for s in class_snapshots) / len(class_snapshots)
        avg_attendance = sum(float(s.avg_attendance_pct) for s in class_snapshots) / len(class_snapshots)
        
        # Count unique classes and teachers
        unique_classes = len(set(s.class_id for s in class_snapshots))
        unique_teachers = len(set(s.teacher_id for s in teacher_snapshots))
        
        return {
            "class_count": unique_classes,
            "teacher_count": unique_teachers,
            "total_students": total_students,
            "avg_participation": avg_participation,
            "avg_attendance": avg_attendance,
            "avg_syllabus_coverage": (
                sum(float(s.syllabus_coverage_pct) for s in class_snapshots) / len(class_snapshots)
                if class_snapshots else 0
            ),
            # NOTE: NO individual class/teacher/student data
        }
    
    async def _call_ai_for_insights(
        self,
        job: InsightJob,
        data: dict,
    ) -> List[dict]:
        """
        Call AI model for insight generation.
        
        This is a PLACEHOLDER implementation.
        In production, would call actual AI service.
        
        AI receives ONLY anonymized aggregate data.
        """
        # Build prompt based on insight type
        prompt = self._build_insight_prompt(job, data)
        
        # PLACEHOLDER: Generate insights based on data patterns
        # In production, this would call OpenAI/Claude API
        insights = self._generate_placeholder_insights(job, data)
        
        # Estimate tokens used (placeholder)
        data["tokens_used"] = len(prompt) // 4 + 500
        
        return insights
    
    def _build_insight_prompt(self, job: InsightJob, data: dict) -> str:
        """
        Build AI prompt for insight generation.
        
        CRITICAL: Prompt contains NO identifiable information.
        """
        prompt = f"""You are an educational advisor analyzing anonymized school data.
Your role is to EXPLAIN patterns and SUGGEST improvements, not to JUDGE or RANK.

ANALYSIS TYPE: {job.insight_type.value}
PERIOD: {job.period_start.date()} to {job.period_end.date()}

DATA (ANONYMIZED):
{json.dumps(data, indent=2, default=str)}

INSTRUCTIONS:
1. Identify notable patterns in the data
2. Explain what these patterns MIGHT indicate
3. Suggest possible actions (as OPTIONS, not requirements)
4. Use encouraging, supportive language
5. NEVER compare to other students/teachers/classes
6. Express uncertainty appropriately (use "may", "could", "suggests")

Generate 2-4 insights in the following format:
- category: engagement|mastery|attendance|coverage|pacing|recovery|consistency
- severity: info|warning|critical
- title: Brief, positive title
- explanation: Detailed explanation (2-3 sentences)
- actions: List of suggested actions
- confidence: 0.0-1.0
"""
        return prompt
    
    def _generate_placeholder_insights(
        self,
        job: InsightJob,
        data: dict,
    ) -> List[dict]:
        """
        Generate placeholder insights based on data patterns.
        
        This is a DETERMINISTIC fallback when AI is not available.
        """
        insights = []
        
        if job.insight_type == InsightType.STUDENT:
            student_data = data.get("student_data", {})
            
            # Check participation
            activity = student_data.get("activity_score", 0)
            if activity >= 80:
                insights.append({
                    "category": InsightCategory.ENGAGEMENT,
                    "severity": InsightSeverity.INFO,
                    "title": "Strong Participation Pattern",
                    "explanation": f"The activity score of {activity:.1f} indicates consistent engagement with learning activities. This positive pattern suggests the student is actively participating in daily loops, weekly tests, and lesson evaluations.",
                    "evidence": {"activity_score": activity, "source": "analytics_snapshot"},
                    "actions": [
                        "Continue encouraging active participation",
                        "Consider providing additional challenges if appropriate",
                    ],
                    "confidence": 0.85,
                    "order": 1,
                    "actionable": True,
                })
            elif activity < 50:
                insights.append({
                    "category": InsightCategory.ENGAGEMENT,
                    "severity": InsightSeverity.WARNING,
                    "title": "Participation May Need Attention",
                    "explanation": f"The activity score of {activity:.1f} suggests participation could be improved. This may indicate various factors that could be explored with the student or parent.",
                    "evidence": {"activity_score": activity, "source": "analytics_snapshot"},
                    "actions": [
                        "Consider a supportive conversation with the student",
                        "Review if any barriers to participation exist",
                        "Explore if additional support might help",
                    ],
                    "confidence": 0.75,
                    "order": 1,
                    "actionable": True,
                })
            
            # Check trend
            trend = student_data.get("trend", "stable")
            if trend == "improving":
                insights.append({
                    "category": InsightCategory.RECOVERY,
                    "severity": InsightSeverity.INFO,
                    "title": "Positive Trend Observed",
                    "explanation": "Recent data shows improvement in activity patterns. This upward trend is encouraging and suggests effective engagement with the learning process.",
                    "evidence": {"trend": trend, "source": "analytics_snapshot"},
                    "actions": [
                        "Acknowledge and encourage the positive progress",
                        "Maintain current support approach",
                    ],
                    "confidence": 0.80,
                    "order": 2,
                    "actionable": True,
                })
            elif trend == "declining":
                insights.append({
                    "category": InsightCategory.CONSISTENCY,
                    "severity": InsightSeverity.WARNING,
                    "title": "Activity Pattern Change",
                    "explanation": "Recent data shows a change in activity patterns. This could indicate various factors that may be worth exploring supportively.",
                    "evidence": {"trend": trend, "source": "analytics_snapshot"},
                    "actions": [
                        "Check in with the student about their experience",
                        "Review if any recent changes may have affected participation",
                    ],
                    "confidence": 0.70,
                    "order": 2,
                    "actionable": True,
                })
        
        elif job.insight_type == InsightType.CLASS:
            class_data = data.get("class_data", {})
            
            avg_activity = class_data.get("avg_activity_score", 0)
            if avg_activity >= 75:
                insights.append({
                    "category": InsightCategory.ENGAGEMENT,
                    "severity": InsightSeverity.INFO,
                    "title": "Strong Class Engagement",
                    "explanation": f"The class shows an average activity score of {avg_activity:.1f}, indicating consistent participation across the group.",
                    "evidence": {"avg_activity_score": avg_activity},
                    "actions": [
                        "Continue current teaching approach",
                        "Consider peer learning activities",
                    ],
                    "confidence": 0.85,
                    "order": 1,
                    "actionable": True,
                })
            
            coverage = class_data.get("syllabus_coverage", 0)
            if coverage < 70:
                insights.append({
                    "category": InsightCategory.COVERAGE,
                    "severity": InsightSeverity.WARNING,
                    "title": "Syllabus Coverage Review Suggested",
                    "explanation": f"Current syllabus coverage is at {coverage:.1f}%. Reviewing pacing may help ensure all topics are addressed.",
                    "evidence": {"syllabus_coverage": coverage},
                    "actions": [
                        "Review upcoming topics and time allocation",
                        "Consider prioritizing key concepts if needed",
                    ],
                    "confidence": 0.75,
                    "order": 2,
                    "actionable": True,
                })
        
        elif job.insight_type == InsightType.TEACHER:
            teacher_data = data.get("teacher_data", {})
            
            engagement = teacher_data.get("engagement_score", 0)
            schedule = teacher_data.get("schedule_adherence", 0)
            
            if engagement >= 80 and schedule >= 80:
                insights.append({
                    "category": InsightCategory.CONSISTENCY,
                    "severity": InsightSeverity.INFO,
                    "title": "Strong Teaching Consistency",
                    "explanation": f"High engagement score ({engagement:.1f}) and schedule adherence ({schedule:.1f}%) indicate effective classroom management and teaching consistency.",
                    "evidence": {"engagement_score": engagement, "schedule_adherence": schedule},
                    "actions": [
                        "Continue current practices",
                        "Consider sharing effective strategies with peers",
                    ],
                    "confidence": 0.85,
                    "order": 1,
                    "actionable": True,
                })
        
        elif job.insight_type == InsightType.SCHOOL:
            school_data = data.get("school_data", {})
            
            avg_participation = school_data.get("avg_participation", 0)
            avg_attendance = school_data.get("avg_attendance", 0)
            
            insights.append({
                "category": InsightCategory.ENGAGEMENT,
                "severity": InsightSeverity.INFO,
                "title": "School-Wide Participation Summary",
                "explanation": f"Overall school participation averages {avg_participation:.1f}% with attendance at {avg_attendance:.1f}%. These metrics provide a baseline for tracking improvement over time.",
                "evidence": {"avg_participation": avg_participation, "avg_attendance": avg_attendance},
                "actions": [
                    "Continue monitoring trends",
                    "Identify classes that may benefit from additional support",
                ],
                "confidence": 0.80,
                "order": 1,
                "actionable": True,
            })
        
        # Always add at least one insight
        if not insights:
            insights.append({
                "category": InsightCategory.ENGAGEMENT,
                "severity": InsightSeverity.INFO,
                "title": "Data Review Complete",
                "explanation": "The available data has been analyzed. No significant patterns requiring immediate attention were identified. Continue regular monitoring.",
                "evidence": {"status": "normal"},
                "actions": [
                    "Continue regular data collection",
                    "Review again in the next period",
                ],
                "confidence": 0.70,
                "order": 1,
                "actionable": False,
            })
        
        return insights
    
    # ============================================
    # Query Methods
    # ============================================
    
    async def get_jobs(
        self,
        requestor_id: Optional[UUID] = None,
        insight_type: Optional[InsightType] = None,
        status: Optional[JobStatus] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[InsightJob]:
        """Get insight jobs with optional filtering."""
        query = select(InsightJob).where(
            InsightJob.tenant_id == self.tenant_id
        )
        
        if requestor_id:
            query = query.where(InsightJob.requested_by == requestor_id)
        if insight_type:
            query = query.where(InsightJob.insight_type == insight_type)
        if status:
            query = query.where(InsightJob.status == status)
        
        query = query.order_by(desc(InsightJob.created_at)).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_job_by_id(self, job_id: UUID) -> Optional[InsightJob]:
        """Get a single job by ID."""
        query = select(InsightJob).where(
            InsightJob.tenant_id == self.tenant_id,
            InsightJob.id == job_id,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_insights_for_job(self, job_id: UUID) -> List[GeneratedInsight]:
        """Get all insights for a job."""
        query = select(GeneratedInsight).where(
            GeneratedInsight.tenant_id == self.tenant_id,
            GeneratedInsight.insight_job_id == job_id,
        ).order_by(GeneratedInsight.display_order)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_my_insights(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> List[InsightJob]:
        """Get insights requested by a specific user."""
        return await self.get_jobs(requestor_id=user_id, skip=skip, limit=limit)
    
    async def get_quota_status(self) -> dict:
        """Get current quota status."""
        quota = await self.check_quota()
        
        return {
            "month": quota.month,
            "year": quota.year,
            "max_requests": quota.max_requests,
            "max_tokens": quota.max_tokens,
            "requests_used": quota.requests_used,
            "tokens_used": quota.tokens_used,
            "requests_remaining": max(0, quota.max_requests - quota.requests_used),
            "tokens_remaining": max(0, quota.max_tokens - quota.tokens_used),
            "usage_percentage": (quota.requests_used / quota.max_requests * 100) if quota.max_requests > 0 else 0,
        }
    
    async def get_insight_summary(self) -> dict:
        """Get summary of insights for dashboard."""
        jobs_query = select(func.count(InsightJob.id)).where(
            InsightJob.tenant_id == self.tenant_id
        )
        result = await self.session.execute(jobs_query)
        total_jobs = result.scalar() or 0
        
        completed_query = jobs_query.where(InsightJob.status == JobStatus.COMPLETED)
        result = await self.session.execute(completed_query)
        completed_jobs = result.scalar() or 0
        
        pending_query = select(func.count(InsightJob.id)).where(
            InsightJob.tenant_id == self.tenant_id,
            InsightJob.status.in_([JobStatus.PENDING, JobStatus.PROCESSING]),
        )
        result = await self.session.execute(pending_query)
        pending_jobs = result.scalar() or 0
        
        insights_query = select(func.count(GeneratedInsight.id)).where(
            GeneratedInsight.tenant_id == self.tenant_id
        )
        result = await self.session.execute(insights_query)
        total_insights = result.scalar() or 0
        
        # Count by severity
        for severity, var_name in [
            (InsightSeverity.CRITICAL, "critical"),
            (InsightSeverity.WARNING, "warning"),
            (InsightSeverity.INFO, "info"),
        ]:
            severity_query = select(func.count(GeneratedInsight.id)).where(
                GeneratedInsight.tenant_id == self.tenant_id,
                GeneratedInsight.severity == severity,
            )
            result = await self.session.execute(severity_query)
            locals()[f"{var_name}_insights"] = result.scalar() or 0
        
        quota = await self.check_quota()
        
        return {
            "total_jobs": total_jobs,
            "completed_jobs": completed_jobs,
            "pending_jobs": pending_jobs,
            "total_insights": total_insights,
            "critical_insights": locals().get("critical_insights", 0),
            "warning_insights": locals().get("warning_insights", 0),
            "info_insights": locals().get("info_insights", 0),
            "tokens_used_this_month": quota.tokens_used,
            "quota_remaining": quota.max_requests - quota.requests_used,
        }
