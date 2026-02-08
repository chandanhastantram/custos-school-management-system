"""
CUSTOS Activity Points Models

Student activity credits, extracurricular tracking, and point system.
"""

from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional, List
from uuid import UUID

from sqlalchemy import (
    String, Text, Integer, Float, Boolean, Date, DateTime,
    ForeignKey, UniqueConstraint, Index, JSON
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import TenantBaseModel


# ============================================
# Enums
# ============================================

class ActivityCategory(str, Enum):
    """Activity categories for points."""
    SPORTS = "sports"
    CULTURAL = "cultural"
    TECHNICAL = "technical"
    LITERARY = "literary"
    SOCIAL_SERVICE = "social_service"
    NCC = "ncc"
    NSS = "nss"
    SCOUTS_GUIDES = "scouts_guides"
    ENTREPRENEURSHIP = "entrepreneurship"
    RESEARCH = "research"
    CERTIFICATION = "certification"
    WORKSHOP = "workshop"
    CLUB = "club"
    OTHER = "other"


class ActivityLevel(str, Enum):
    """Level of activity/participation."""
    COLLEGE = "college"
    INTRA_COLLEGE = "intra_college"
    INTER_COLLEGE = "inter_college"
    UNIVERSITY = "university"
    STATE = "state"
    NATIONAL = "national"
    INTERNATIONAL = "international"


class AchievementType(str, Enum):
    """Type of achievement."""
    PARTICIPATION = "participation"
    WINNER = "winner"
    FIRST_RUNNER_UP = "first_runner_up"
    SECOND_RUNNER_UP = "second_runner_up"
    MERIT = "merit"
    CERTIFICATION = "certification"
    PUBLICATION = "publication"
    PATENT = "patent"


class SubmissionStatus(str, Enum):
    """Activity submission status."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_CLARIFICATION = "needs_clarification"


# ============================================
# Activity Point Configuration
# ============================================

class ActivityPointConfig(TenantBaseModel):
    """
    Configuration for activity point allocation.
    
    Defines how many points are awarded for each activity type/level/achievement.
    """
    __tablename__ = "activity_point_configs"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "category", "level", "achievement_type",
            name="uq_activity_config"
        ),
        Index("ix_config_category", "tenant_id", "category"),
        {"extend_existing": True},
    )
    
    # Activity classification
    category: Mapped[ActivityCategory] = mapped_column(
        SQLEnum(ActivityCategory, name="activity_category_enum"),
    )
    level: Mapped[ActivityLevel] = mapped_column(
        SQLEnum(ActivityLevel, name="activity_level_enum"),
    )
    achievement_type: Mapped[AchievementType] = mapped_column(
        SQLEnum(AchievementType, name="achievement_type_enum"),
    )
    
    # Points
    points: Mapped[int] = mapped_column(Integer)
    
    # Limits
    max_points_per_semester: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_points_per_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Description
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


# ============================================
# Activity Submission
# ============================================

class ActivitySubmission(TenantBaseModel):
    """
    Student activity submission for points.
    
    Students submit activities with proof for approval.
    """
    __tablename__ = "activity_submissions"
    __table_args__ = (
        Index("ix_submission_student", "tenant_id", "student_id"),
        Index("ix_submission_status", "tenant_id", "status"),
        Index("ix_submission_category", "tenant_id", "category"),
        {"extend_existing": True},
    )
    
    # Student
    student_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    
    # Academic context
    academic_year_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("academic_years.id", ondelete="CASCADE"),
    )
    semester: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Activity details
    category: Mapped[ActivityCategory] = mapped_column(
        SQLEnum(ActivityCategory, name="activity_category_enum"),
    )
    level: Mapped[ActivityLevel] = mapped_column(
        SQLEnum(ActivityLevel, name="activity_level_enum"),
    )
    achievement_type: Mapped[AchievementType] = mapped_column(
        SQLEnum(AchievementType, name="achievement_type_enum"),
    )
    
    # Activity info
    activity_name: Mapped[str] = mapped_column(String(300))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    activity_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Venue/Organizer
    venue: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    organizer: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # Points
    requested_points: Mapped[int] = mapped_column(Integer)
    approved_points: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Status
    status: Mapped[SubmissionStatus] = mapped_column(
        SQLEnum(SubmissionStatus, name="submission_status_enum"),
        default=SubmissionStatus.DRAFT
    )
    
    # Proof documents (JSON array)
    proof_documents: Mapped[Optional[List[dict]]] = mapped_column(JSON, nullable=True)
    
    # Submission
    submitted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Review
    reviewed_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    review_comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Verification by faculty advisor / HOD
    verified_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    verification_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


# ============================================
# Student Activity Summary
# ============================================

class StudentActivitySummary(TenantBaseModel):
    """
    Aggregated activity points summary per student per year.
    """
    __tablename__ = "student_activity_summaries"
    __table_args__ = (
        UniqueConstraint(
            "student_id", "academic_year_id",
            name="uq_activity_summary"
        ),
        Index("ix_summary_student", "tenant_id", "student_id"),
        {"extend_existing": True},
    )
    
    student_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    academic_year_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("academic_years.id", ondelete="CASCADE"),
    )
    
    # Points breakdown by category (JSON: {category: points})
    points_by_category: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Total points
    total_submissions: Mapped[int] = mapped_column(Integer, default=0)
    approved_submissions: Mapped[int] = mapped_column(Integer, default=0)
    pending_submissions: Mapped[int] = mapped_column(Integer, default=0)
    rejected_submissions: Mapped[int] = mapped_column(Integer, default=0)
    
    # Points
    total_points: Mapped[int] = mapped_column(Integer, default=0)
    
    # Required points for graduation
    required_points: Mapped[int] = mapped_column(Integer, default=100)
    points_deficit: Mapped[int] = mapped_column(Integer, default=0)
    is_requirement_met: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Last updated
    calculated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


# ============================================
# Semester Activity Points
# ============================================

class SemesterActivityPoints(TenantBaseModel):
    """
    Semester-wise activity points tracking.
    """
    __tablename__ = "semester_activity_points"
    __table_args__ = (
        UniqueConstraint(
            "student_id", "academic_year_id", "semester",
            name="uq_semester_activity"
        ),
        Index("ix_semester_activity_student", "tenant_id", "student_id"),
        {"extend_existing": True},
    )
    
    student_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    academic_year_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("academic_years.id", ondelete="CASCADE"),
    )
    semester: Mapped[int] = mapped_column(Integer)
    
    # Points
    total_points: Mapped[int] = mapped_column(Integer, default=0)
    max_allowed: Mapped[int] = mapped_column(Integer, default=50)  # Max per semester
    
    # Breakdown
    points_by_category: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Activities count
    activities_count: Mapped[int] = mapped_column(Integer, default=0)


# ============================================
# Activity Certificate
# ============================================

class ActivityCertificate(TenantBaseModel):
    """
    Generated activity certificate for student.
    """
    __tablename__ = "activity_certificates"
    __table_args__ = (
        Index("ix_certificate_student", "tenant_id", "student_id"),
        {"extend_existing": True},
    )
    
    student_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    
    # Certificate details
    certificate_number: Mapped[str] = mapped_column(String(50), unique=True)
    title: Mapped[str] = mapped_column(String(200))
    
    # Covering period
    from_date: Mapped[date] = mapped_column(Date)
    to_date: Mapped[date] = mapped_column(Date)
    
    # Points summary
    total_points: Mapped[int] = mapped_column(Integer)
    activities_summary: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Document
    pdf_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Generation
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    generated_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
    )
    
    # Verification
    verification_code: Mapped[str] = mapped_column(String(50))
