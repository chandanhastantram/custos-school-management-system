"""
CUSTOS AI Lesson Plan Generator Service

Generates structured lesson plans using AI with:
- Syllabus topic ordering
- Calendar-aware period allocation
- Timetable constraint respect
- Cost-controlled usage
"""

from datetime import datetime, date
from typing import Optional, List, Dict
from uuid import UUID
import json

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundError, ValidationError, UsageLimitExceededError
from app.ai.models import AILessonPlanJob, AIJobStatus
from app.ai.schemas import (
    GenerateAILessonPlanRequest,
    GenerateAILessonPlanResponse,
    GeneratedUnitInfo,
    LessonPlanPreferences,
    PacePreference,
    FocusPreference,
    TopicForAI,
    CalendarInfo,
    TimetableInfo,
    AIInputSnapshot,
    AITopicAllocation,
    AIOutputSnapshot,
)
from app.ai.providers.openai import OpenAIProvider
from app.academics.models.lesson_plans import LessonPlan, LessonPlanUnit, LessonPlanStatus
from app.academics.models.syllabus import SyllabusSubject, Chapter, SyllabusTopic
from app.academics.models.structure import Class
from app.academics.models.curriculum import Subject
from app.scheduling.models.timetable import TimetableEntry


class AILessonPlanService:
    """
    AI Lesson Plan Generation Service.
    
    Workflow:
    1. Fetch syllabus topics in order
    2. Fetch academic calendar working days
    3. Fetch timetable entries for class+subject
    4. Calculate total available periods
    5. Build structured AI prompt
    6. Call AI provider
    7. Parse response and allocate periods
    8. Create LessonPlan and LessonPlanUnits
    9. Store job record for auditing
    """
    
    # Period allocation based on pace
    PACE_MULTIPLIERS = {
        PacePreference.SLOW: 1.3,
        PacePreference.NORMAL: 1.0,
        PacePreference.FAST: 0.8,
    }
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
        self.provider = OpenAIProvider()
    
    async def generate_lesson_plan(
        self,
        teacher_id: UUID,
        request: GenerateAILessonPlanRequest,
    ) -> GenerateAILessonPlanResponse:
        """
        Generate AI lesson plan from syllabus.
        
        Steps:
        1. Check AI usage quota
        2. Gather input data (syllabus, calendar, timetable)
        3. Create job record
        4. Call AI for period allocation
        5. Create lesson plan and units
        6. Update job with result
        """
        # 1. Check usage quota
        await self._check_ai_quota()
        
        # 2. Gather input data
        topics = await self._get_syllabus_topics(request.syllabus_subject_id)
        if not topics:
            raise ValidationError("No topics found in syllabus")
        
        class_info = await self._get_class_info(request.class_id)
        subject_info = await self._get_subject_info(request.subject_id)
        
        periods_per_week = await self._get_periods_per_week(
            request.class_id,
            request.subject_id,
            request.preferences.periods_per_week,
        )
        
        total_periods = self._calculate_total_periods(
            request.start_date,
            request.end_date,
            periods_per_week,
        )
        
        # 3. Build input snapshot
        input_snapshot = self._build_input_snapshot(
            class_name=class_info["name"],
            subject_name=subject_info["name"],
            topics=topics,
            start_date=request.start_date,
            end_date=request.end_date,
            periods_per_week=periods_per_week,
            total_periods=total_periods,
            preferences=request.preferences,
        )
        
        # 4. Create job record
        job = await self._create_job(
            teacher_id=teacher_id,
            class_id=request.class_id,
            subject_id=request.subject_id,
            syllabus_subject_id=request.syllabus_subject_id,
            input_snapshot=input_snapshot,
        )
        
        try:
            # 5. Update job status
            job.status = AIJobStatus.RUNNING
            job.started_at = datetime.utcnow()
            await self.session.flush()
            
            # 6. Call AI for period allocation
            ai_response = await self._call_ai_for_allocation(
                topics=topics,
                total_periods=total_periods,
                preferences=request.preferences,
                class_name=class_info["name"],
                subject_name=subject_info["name"],
            )
            
            job.output_snapshot = ai_response
            
            # 7. Parse AI response
            allocations = self._parse_ai_response(ai_response, topics)
            
            # 8. Create lesson plan
            title = request.title or f"{subject_info['name']} Lesson Plan - {class_info['name']}"
            
            lesson_plan = await self._create_lesson_plan(
                teacher_id=teacher_id,
                class_id=request.class_id,
                section_id=request.section_id,
                subject_id=request.subject_id,
                syllabus_subject_id=request.syllabus_subject_id,
                title=title,
                start_date=request.start_date,
                end_date=request.end_date,
                allocations=allocations,
                topics=topics,
            )
            
            # 9. Update job
            job.status = AIJobStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            job.lesson_plan_id = lesson_plan.id
            await self.session.flush()
            
            # 10. Increment usage
            await self._increment_ai_usage()
            
            # Build response
            units_info = [
                GeneratedUnitInfo(
                    topic_id=unit.topic_id,
                    topic_name=next((t["name"] for t in topics if str(t["id"]) == str(unit.topic_id)), ""),
                    estimated_periods=unit.estimated_periods,
                    notes=unit.notes,
                    order=unit.order,
                )
                for unit in lesson_plan.units
            ]
            
            return GenerateAILessonPlanResponse(
                job_id=job.id,
                lesson_plan_id=lesson_plan.id,
                title=title,
                total_units=len(lesson_plan.units),
                total_periods=lesson_plan.total_periods,
                start_date=request.start_date,
                end_date=request.end_date,
                units=units_info,
            )
            
        except Exception as e:
            # Update job with error
            job.status = AIJobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            await self.session.flush()
            raise
    
    # ============================================
    # Data Gathering
    # ============================================
    
    async def _get_syllabus_topics(self, syllabus_subject_id: UUID) -> List[dict]:
        """Get all topics from syllabus in order."""
        # Get chapters first (chapters are the units/sections of a syllabus subject)
        chapters_query = select(Chapter).where(
            Chapter.subject_id == syllabus_subject_id,
            Chapter.tenant_id == self.tenant_id,
            Chapter.is_deleted == False,
        ).order_by(Chapter.order)
        
        result = await self.session.execute(chapters_query)
        chapters = result.scalars().all()
        
        topics = []
        for chapter in chapters:
            # Get topics for this chapter
            topics_query = select(SyllabusTopic).where(
                SyllabusTopic.chapter_id == chapter.id,
                SyllabusTopic.tenant_id == self.tenant_id,
                SyllabusTopic.is_deleted == False,
            ).order_by(SyllabusTopic.order)
            
            result = await self.session.execute(topics_query)
            chapter_topics = result.scalars().all()
            
            for topic in chapter_topics:
                topics.append({
                    "id": topic.id,
                    "name": topic.name,
                    "unit_name": chapter.name,
                    "order": len(topics) + 1,
                    "description": topic.description,
                })
        
        return topics
    
    async def _get_class_info(self, class_id: UUID) -> dict:
        """Get class information."""
        query = select(Class).where(
            Class.id == class_id,
            Class.tenant_id == self.tenant_id,
            Class.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        cls = result.scalar_one_or_none()
        
        if not cls:
            raise ResourceNotFoundError("Class", class_id)
        
        return {"id": cls.id, "name": cls.name}
    
    async def _get_subject_info(self, subject_id: UUID) -> dict:
        """Get subject information."""
        query = select(Subject).where(
            Subject.id == subject_id,
            Subject.tenant_id == self.tenant_id,
            Subject.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        subj = result.scalar_one_or_none()
        
        if not subj:
            raise ResourceNotFoundError("Subject", subject_id)
        
        return {"id": subj.id, "name": subj.name}
    
    async def _get_periods_per_week(
        self,
        class_id: UUID,
        subject_id: UUID,
        override: Optional[int] = None,
    ) -> int:
        """Get periods per week from timetable or use override."""
        if override:
            return override
        
        # Count timetable entries for this class+subject
        query = select(func.count(TimetableEntry.id)).where(
            TimetableEntry.class_id == class_id,
            TimetableEntry.subject_id == subject_id,
            TimetableEntry.tenant_id == self.tenant_id,
            TimetableEntry.deleted_at.is_(None),
        )
        result = await self.session.scalar(query) or 0
        
        # Default to 5 periods/week if no timetable
        return result if result > 0 else 5
    
    def _calculate_total_periods(
        self,
        start_date: date,
        end_date: date,
        periods_per_week: int,
    ) -> int:
        """Calculate total available periods."""
        # Calculate weeks
        total_days = (end_date - start_date).days + 1
        weeks = total_days / 7
        
        # Total periods
        total = int(weeks * periods_per_week)
        
        # Reduce by ~10% for holidays/unforeseen
        return int(total * 0.9)
    
    # ============================================
    # AI Interaction
    # ============================================
    
    def _build_input_snapshot(
        self,
        class_name: str,
        subject_name: str,
        topics: List[dict],
        start_date: date,
        end_date: date,
        periods_per_week: int,
        total_periods: int,
        preferences: LessonPlanPreferences,
    ) -> dict:
        """Build input snapshot for auditing."""
        return {
            "class_name": class_name,
            "subject_name": subject_name,
            "topics": [
                {
                    "topic_id": str(t["id"]),
                    "name": t["name"],
                    "unit_name": t["unit_name"],
                    "order": t["order"],
                }
                for t in topics
            ],
            "calendar": {
                "start_date": str(start_date),
                "end_date": str(end_date),
                "total_working_days": (end_date - start_date).days,
            },
            "timetable": {
                "periods_per_week": periods_per_week,
            },
            "preferences": {
                "pace": preferences.pace.value,
                "focus": preferences.focus.value,
                "include_revision": preferences.include_revision_periods,
                "revision_percent": preferences.revision_percent,
            },
            "total_available_periods": total_periods,
        }
    
    async def _call_ai_for_allocation(
        self,
        topics: List[dict],
        total_periods: int,
        preferences: LessonPlanPreferences,
        class_name: str,
        subject_name: str,
    ) -> dict:
        """Call AI to allocate periods to topics."""
        # Build prompt
        topics_text = "\n".join([
            f"{i+1}. {t['name']} (Unit: {t['unit_name']})"
            for i, t in enumerate(topics)
        ])
        
        pace_desc = {
            PacePreference.SLOW: "slow pace with thorough coverage",
            PacePreference.NORMAL: "standard pace",
            PacePreference.FAST: "fast pace for quick coverage",
        }
        
        focus_desc = {
            FocusPreference.CONCEPTS: "focus on theoretical understanding",
            FocusPreference.PROBLEMS: "focus on practice problems",
            FocusPreference.REVISION: "focus on quick revision",
            FocusPreference.BALANCED: "balanced approach",
        }
        
        prompt = f"""You are an expert curriculum planner. Create a lesson plan allocation for:

Class: {class_name}
Subject: {subject_name}
Total Available Periods: {total_periods}
Teaching Pace: {pace_desc[preferences.pace]}
Teaching Focus: {focus_desc[preferences.focus]}

Topics to cover (in order):
{topics_text}

{"Include revision periods: " + str(preferences.revision_percent) + "% of total" if preferences.include_revision_periods else "No separate revision periods"}

Allocate periods to each topic considering:
1. Topic complexity (based on name and unit)
2. Logical teaching sequence
3. Available time constraints
4. Specified teaching pace

Return a JSON object with allocations."""

        schema = {
            "allocations": [
                {
                    "topic_index": "1-indexed number",
                    "estimated_periods": "integer",
                    "notes": "optional teaching notes"
                }
            ],
            "revision_periods": "integer if applicable",
            "teaching_notes": "optional overall notes"
        }
        
        return await self.provider.generate_structured(prompt, schema)
    
    def _parse_ai_response(
        self,
        response: dict,
        topics: List[dict],
    ) -> List[AITopicAllocation]:
        """Parse AI response into allocations."""
        allocations = []
        
        raw_allocations = response.get("allocations", [])
        
        for alloc in raw_allocations:
            # Get topic index (1-indexed)
            topic_index = alloc.get("topic_index", 0)
            if isinstance(topic_index, str):
                try:
                    topic_index = int(topic_index)
                except ValueError:
                    continue
            
            if 1 <= topic_index <= len(topics):
                topic = topics[topic_index - 1]
                allocations.append(AITopicAllocation(
                    topic_id=str(topic["id"]),
                    estimated_periods=alloc.get("estimated_periods", 1),
                    notes=alloc.get("notes"),
                ))
        
        # If AI didn't allocate all topics, distribute remaining evenly
        if len(allocations) < len(topics):
            allocated_ids = {a.topic_id for a in allocations}
            for topic in topics:
                if str(topic["id"]) not in allocated_ids:
                    allocations.append(AITopicAllocation(
                        topic_id=str(topic["id"]),
                        estimated_periods=1,
                        notes=None,
                    ))
        
        return allocations
    
    # ============================================
    # Lesson Plan Creation
    # ============================================
    
    async def _create_lesson_plan(
        self,
        teacher_id: UUID,
        class_id: UUID,
        section_id: Optional[UUID],
        subject_id: UUID,
        syllabus_subject_id: UUID,
        title: str,
        start_date: date,
        end_date: date,
        allocations: List[AITopicAllocation],
        topics: List[dict],
    ) -> LessonPlan:
        """Create lesson plan and units from allocations."""
        # Calculate total periods
        total_periods = sum(a.estimated_periods for a in allocations)
        
        # Create lesson plan
        lesson_plan = LessonPlan(
            tenant_id=self.tenant_id,
            teacher_id=teacher_id,
            class_id=class_id,
            section_id=section_id,
            subject_id=subject_id,
            syllabus_subject_id=syllabus_subject_id,
            title=title,
            start_date=start_date,
            end_date=end_date,
            status=LessonPlanStatus.DRAFT,
            total_periods=total_periods,
        )
        self.session.add(lesson_plan)
        await self.session.flush()
        
        # Create units
        topic_map = {str(t["id"]): t for t in topics}
        
        for i, alloc in enumerate(allocations):
            topic = topic_map.get(alloc.topic_id)
            
            unit = LessonPlanUnit(
                tenant_id=self.tenant_id,
                lesson_plan_id=lesson_plan.id,
                topic_id=UUID(alloc.topic_id),
                order=i + 1,
                estimated_periods=alloc.estimated_periods,
                notes=alloc.notes or (topic.get("description") if topic else None),
            )
            self.session.add(unit)
        
        await self.session.flush()
        await self.session.refresh(lesson_plan)
        
        return lesson_plan
    
    # ============================================
    # Job Management
    # ============================================
    
    async def _create_job(
        self,
        teacher_id: UUID,
        class_id: UUID,
        subject_id: UUID,
        syllabus_subject_id: UUID,
        input_snapshot: dict,
    ) -> AILessonPlanJob:
        """Create AI job record."""
        job = AILessonPlanJob(
            tenant_id=self.tenant_id,
            teacher_id=teacher_id,
            class_id=class_id,
            subject_id=subject_id,
            syllabus_subject_id=syllabus_subject_id,
            input_snapshot=input_snapshot,
            status=AIJobStatus.PENDING,
            ai_provider="openai",
        )
        self.session.add(job)
        await self.session.flush()
        return job
    
    async def get_job(self, job_id: UUID) -> Optional[AILessonPlanJob]:
        """Get job by ID."""
        query = select(AILessonPlanJob).where(
            AILessonPlanJob.id == job_id,
            AILessonPlanJob.tenant_id == self.tenant_id,
            AILessonPlanJob.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def list_jobs(
        self,
        teacher_id: Optional[UUID] = None,
        status: Optional[AIJobStatus] = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple:
        """List AI jobs with filters."""
        query = select(AILessonPlanJob).where(
            AILessonPlanJob.tenant_id == self.tenant_id,
            AILessonPlanJob.deleted_at.is_(None),
        )
        
        if teacher_id:
            query = query.where(AILessonPlanJob.teacher_id == teacher_id)
        if status:
            query = query.where(AILessonPlanJob.status == status)
        
        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.session.scalar(count_query) or 0
        
        # Paginate
        query = query.order_by(AILessonPlanJob.created_at.desc())
        query = query.offset((page - 1) * size).limit(size)
        
        result = await self.session.execute(query)
        return list(result.scalars().all()), total
    
    # ============================================
    # Usage Management
    # ============================================
    
    async def _check_ai_quota(self) -> None:
        """Check if tenant has AI credits remaining."""
        from app.billing.models import UsageLimit
        
        now = datetime.now()
        query = select(UsageLimit).where(
            UsageLimit.tenant_id == self.tenant_id,
            UsageLimit.year == now.year,
            UsageLimit.month == now.month,
        )
        result = await self.session.execute(query)
        usage = result.scalar_one_or_none()
        
        if usage:
            # Get limit from subscription (hardcoded for now)
            max_requests = 100
            if usage.ai_requests_used >= max_requests:
                raise UsageLimitExceededError(
                    "AI requests", usage.ai_requests_used, max_requests
                )
    
    async def _increment_ai_usage(self) -> None:
        """Increment AI usage counter."""
        from app.billing.models import UsageLimit
        
        now = datetime.now()
        query = select(UsageLimit).where(
            UsageLimit.tenant_id == self.tenant_id,
            UsageLimit.year == now.year,
            UsageLimit.month == now.month,
        )
        result = await self.session.execute(query)
        usage = result.scalar_one_or_none()
        
        if usage:
            usage.ai_requests_used += 1
        else:
            # Create usage record if doesn't exist
            usage = UsageLimit(
                tenant_id=self.tenant_id,
                year=now.year,
                month=now.month,
                ai_requests_used=1,
            )
            self.session.add(usage)
        
        await self.session.flush()
    
    async def get_usage(self) -> dict:
        """Get current AI usage."""
        from app.billing.models import UsageLimit
        
        now = datetime.now()
        query = select(UsageLimit).where(
            UsageLimit.tenant_id == self.tenant_id,
            UsageLimit.year == now.year,
            UsageLimit.month == now.month,
        )
        result = await self.session.execute(query)
        usage = result.scalar_one_or_none()
        
        used = usage.ai_requests_used if usage else 0
        limit = 100  # Would come from subscription
        
        return {
            "month": now.month,
            "year": now.year,
            "ai_requests_used": used,
            "ai_requests_limit": limit,
            "remaining": max(0, limit - used),
            "percent_used": round((used / limit) * 100, 2) if limit > 0 else 0,
        }
