"""
CUSTOS Activity Points Service

Business logic for activity submissions and point calculations.
"""

import logging
from datetime import datetime
from typing import Optional, List, Tuple
from uuid import UUID, uuid4

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.activity_points.models import (
    ActivityPointConfig, ActivitySubmission, StudentActivitySummary,
    SemesterActivityPoints, ActivityCertificate,
    ActivityCategory, ActivityLevel, AchievementType, SubmissionStatus
)
from app.activity_points.schemas import (
    ActivitySubmissionCreate, ActivitySubmissionUpdate,
    ActivityReviewRequest, CertificateGenerateRequest
)
from app.core.exceptions import NotFoundError, ValidationError

logger = logging.getLogger(__name__)


class ActivityPointsService:
    """Service for activity points management."""
    
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
    
    # ============================================
    # Configuration
    # ============================================
    
    async def get_points_for_activity(
        self,
        category: ActivityCategory,
        level: ActivityLevel,
        achievement_type: AchievementType
    ) -> int:
        """Get points for an activity based on config."""
        result = await self.db.execute(
            select(ActivityPointConfig).where(
                ActivityPointConfig.tenant_id == self.tenant_id,
                ActivityPointConfig.category == category,
                ActivityPointConfig.level == level,
                ActivityPointConfig.achievement_type == achievement_type,
                ActivityPointConfig.is_active == True,
            )
        )
        config = result.scalar_one_or_none()
        
        if not config:
            # Default points
            return self._get_default_points(level, achievement_type)
        
        return config.points
    
    def _get_default_points(
        self,
        level: ActivityLevel,
        achievement_type: AchievementType
    ) -> int:
        """Get default points based on level and achievement."""
        level_multiplier = {
            ActivityLevel.COLLEGE: 1,
            ActivityLevel.INTRA_COLLEGE: 1,
            ActivityLevel.INTER_COLLEGE: 2,
            ActivityLevel.UNIVERSITY: 3,
            ActivityLevel.STATE: 4,
            ActivityLevel.NATIONAL: 5,
            ActivityLevel.INTERNATIONAL: 6,
        }
        
        achievement_base = {
            AchievementType.PARTICIPATION: 2,
            AchievementType.MERIT: 3,
            AchievementType.SECOND_RUNNER_UP: 4,
            AchievementType.FIRST_RUNNER_UP: 5,
            AchievementType.WINNER: 6,
            AchievementType.CERTIFICATION: 3,
            AchievementType.PUBLICATION: 8,
            AchievementType.PATENT: 10,
        }
        
        return achievement_base.get(achievement_type, 2) * level_multiplier.get(level, 1)
    
    # ============================================
    # Submissions
    # ============================================
    
    async def create_submission(
        self,
        data: ActivitySubmissionCreate,
        student_id: UUID,
        academic_year_id: UUID,
        semester: int
    ) -> ActivitySubmission:
        """Create a new activity submission."""
        # Calculate points
        points = await self.get_points_for_activity(
            data.category, data.level, data.achievement_type
        )
        
        submission = ActivitySubmission(
            tenant_id=self.tenant_id,
            student_id=student_id,
            academic_year_id=academic_year_id,
            semester=semester,
            category=data.category,
            level=data.level,
            achievement_type=data.achievement_type,
            activity_name=data.activity_name,
            description=data.description,
            activity_date=data.activity_date,
            end_date=data.end_date,
            venue=data.venue,
            organizer=data.organizer,
            requested_points=points,
            status=SubmissionStatus.SUBMITTED,
            proof_documents=[d.model_dump() for d in data.proof_documents] if data.proof_documents else None,
            submitted_at=datetime.utcnow(),
        )
        
        self.db.add(submission)
        await self.db.commit()
        await self.db.refresh(submission)
        
        logger.info(f"Created activity submission for student {student_id}")
        return submission
    
    async def get_submission(self, submission_id: UUID) -> Optional[ActivitySubmission]:
        """Get submission by ID."""
        result = await self.db.execute(
            select(ActivitySubmission).where(
                ActivitySubmission.id == submission_id,
                ActivitySubmission.tenant_id == self.tenant_id,
            )
        )
        return result.scalar_one_or_none()
    
    async def list_submissions(
        self,
        student_id: Optional[UUID] = None,
        status: Optional[str] = None,
        category: Optional[str] = None,
        academic_year_id: Optional[UUID] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[ActivitySubmission], int]:
        """List submissions with filters."""
        query = select(ActivitySubmission).where(
            ActivitySubmission.tenant_id == self.tenant_id,
        )
        
        if student_id:
            query = query.where(ActivitySubmission.student_id == student_id)
        if status:
            query = query.where(ActivitySubmission.status == status)
        if category:
            query = query.where(ActivitySubmission.category == category)
        if academic_year_id:
            query = query.where(ActivitySubmission.academic_year_id == academic_year_id)
        
        # Count
        count_result = await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar()
        
        # Paginate
        query = query.order_by(ActivitySubmission.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.db.execute(query)
        return result.scalars().all(), total
    
    async def update_submission(
        self,
        submission_id: UUID,
        data: ActivitySubmissionUpdate,
        student_id: UUID
    ) -> ActivitySubmission:
        """Update a submission (only draft/needs_clarification)."""
        submission = await self.get_submission(submission_id)
        if not submission:
            raise NotFoundError("Submission not found")
        
        if submission.student_id != student_id:
            raise ValidationError("Cannot update another student's submission")
        
        if submission.status not in [SubmissionStatus.DRAFT, SubmissionStatus.NEEDS_CLARIFICATION]:
            raise ValidationError("Cannot update submission in current status")
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if key == "proof_documents" and value:
                value = [d.model_dump() for d in value]
            setattr(submission, key, value)
        
        submission.status = SubmissionStatus.SUBMITTED
        submission.submitted_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(submission)
        return submission
    
    async def review_submission(
        self,
        submission_id: UUID,
        data: ActivityReviewRequest,
        reviewed_by: UUID
    ) -> ActivitySubmission:
        """Review and approve/reject a submission."""
        submission = await self.get_submission(submission_id)
        if not submission:
            raise NotFoundError("Submission not found")
        
        submission.status = data.status
        submission.review_comments = data.review_comments
        submission.reviewed_by = reviewed_by
        submission.reviewed_at = datetime.utcnow()
        
        if data.status == SubmissionStatus.APPROVED:
            submission.approved_points = data.approved_points or submission.requested_points
            # Update summaries
            await self._update_student_summary(
                submission.student_id,
                submission.academic_year_id,
                submission.semester
            )
        elif data.status == SubmissionStatus.REJECTED:
            submission.rejection_reason = data.rejection_reason
        
        await self.db.commit()
        await self.db.refresh(submission)
        return submission
    
    # ============================================
    # Summaries
    # ============================================
    
    async def get_student_summary(
        self,
        student_id: UUID,
        academic_year_id: UUID
    ) -> Optional[StudentActivitySummary]:
        """Get student activity summary."""
        result = await self.db.execute(
            select(StudentActivitySummary).where(
                StudentActivitySummary.student_id == student_id,
                StudentActivitySummary.academic_year_id == academic_year_id,
                StudentActivitySummary.tenant_id == self.tenant_id,
            )
        )
        return result.scalar_one_or_none()
    
    async def _update_student_summary(
        self,
        student_id: UUID,
        academic_year_id: UUID,
        semester: Optional[int] = None
    ):
        """Update student's activity summary after approval."""
        # Get or create summary
        summary = await self.get_student_summary(student_id, academic_year_id)
        
        if not summary:
            summary = StudentActivitySummary(
                tenant_id=self.tenant_id,
                student_id=student_id,
                academic_year_id=academic_year_id,
                required_points=100,  # Default
            )
            self.db.add(summary)
        
        # Calculate totals
        submissions = await self.db.execute(
            select(ActivitySubmission).where(
                ActivitySubmission.student_id == student_id,
                ActivitySubmission.academic_year_id == academic_year_id,
                ActivitySubmission.tenant_id == self.tenant_id,
            )
        )
        all_submissions = submissions.scalars().all()
        
        summary.total_submissions = len(all_submissions)
        summary.approved_submissions = len([s for s in all_submissions if s.status == SubmissionStatus.APPROVED])
        summary.pending_submissions = len([s for s in all_submissions if s.status in [SubmissionStatus.SUBMITTED, SubmissionStatus.UNDER_REVIEW]])
        summary.rejected_submissions = len([s for s in all_submissions if s.status == SubmissionStatus.REJECTED])
        
        # Calculate points
        total_points = sum(s.approved_points or 0 for s in all_submissions if s.status == SubmissionStatus.APPROVED)
        summary.total_points = total_points
        summary.points_deficit = max(0, summary.required_points - total_points)
        summary.is_requirement_met = total_points >= summary.required_points
        
        # Category breakdown
        points_by_category = {}
        for s in all_submissions:
            if s.status == SubmissionStatus.APPROVED:
                cat = s.category.value
                points_by_category[cat] = points_by_category.get(cat, 0) + (s.approved_points or 0)
        summary.points_by_category = points_by_category
        
        summary.calculated_at = datetime.utcnow()
        
        await self.db.flush()
    
    # ============================================
    # Certificates
    # ============================================
    
    async def generate_certificate(
        self,
        data: CertificateGenerateRequest,
        generated_by: UUID
    ) -> ActivityCertificate:
        """Generate activity points certificate."""
        # Get approved activities in date range
        submissions = await self.db.execute(
            select(ActivitySubmission).where(
                ActivitySubmission.student_id == data.student_id,
                ActivitySubmission.tenant_id == self.tenant_id,
                ActivitySubmission.status == SubmissionStatus.APPROVED,
                ActivitySubmission.activity_date >= data.from_date,
                ActivitySubmission.activity_date <= data.to_date,
            )
        )
        approved = submissions.scalars().all()
        
        total_points = sum(s.approved_points or 0 for s in approved)
        
        # Create summary
        activities_summary = {}
        for s in approved:
            cat = s.category.value
            if cat not in activities_summary:
                activities_summary[cat] = {"count": 0, "points": 0}
            activities_summary[cat]["count"] += 1
            activities_summary[cat]["points"] += s.approved_points or 0
        
        certificate = ActivityCertificate(
            tenant_id=self.tenant_id,
            student_id=data.student_id,
            certificate_number=self._generate_certificate_number(),
            title=data.title or "Activity Points Certificate",
            from_date=data.from_date,
            to_date=data.to_date,
            total_points=total_points,
            activities_summary=activities_summary,
            generated_by=generated_by,
            verification_code=str(uuid4())[:12].upper(),
        )
        
        self.db.add(certificate)
        await self.db.commit()
        await self.db.refresh(certificate)
        
        return certificate
    
    def _generate_certificate_number(self) -> str:
        """Generate unique certificate number."""
        timestamp = datetime.utcnow().strftime("%Y%m%d")
        random_part = str(uuid4())[:6].upper()
        return f"ACT-{timestamp}-{random_part}"
