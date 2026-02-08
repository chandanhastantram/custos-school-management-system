"""
CUSTOS Activity Points Schemas

Pydantic schemas for activity submissions and points tracking.
"""

from datetime import datetime, date
from enum import Enum
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


# ============================================
# Enums (mirrored from models)
# ============================================

class ActivityCategory(str, Enum):
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
    COLLEGE = "college"
    INTRA_COLLEGE = "intra_college"
    INTER_COLLEGE = "inter_college"
    UNIVERSITY = "university"
    STATE = "state"
    NATIONAL = "national"
    INTERNATIONAL = "international"


class AchievementType(str, Enum):
    PARTICIPATION = "participation"
    WINNER = "winner"
    FIRST_RUNNER_UP = "first_runner_up"
    SECOND_RUNNER_UP = "second_runner_up"
    MERIT = "merit"
    CERTIFICATION = "certification"
    PUBLICATION = "publication"
    PATENT = "patent"


class SubmissionStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_CLARIFICATION = "needs_clarification"


# ============================================
# Document Schema
# ============================================

class ProofDocument(BaseModel):
    """Schema for proof document."""
    file_name: str
    file_url: str
    file_type: Optional[str] = None
    uploaded_at: Optional[datetime] = None


# ============================================
# Activity Point Config Schemas
# ============================================

class ActivityPointConfigCreate(BaseModel):
    """Schema for creating activity point config."""
    category: ActivityCategory
    level: ActivityLevel
    achievement_type: AchievementType
    points: int = Field(..., ge=1, le=50)
    max_points_per_semester: Optional[int] = None
    max_points_per_year: Optional[int] = None
    description: Optional[str] = None


class ActivityPointConfigResponse(BaseModel):
    """Schema for activity config response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    category: ActivityCategory
    level: ActivityLevel
    achievement_type: AchievementType
    points: int
    max_points_per_semester: Optional[int] = None
    max_points_per_year: Optional[int] = None
    is_active: bool
    description: Optional[str] = None


# ============================================
# Activity Submission Schemas
# ============================================

class ActivitySubmissionCreate(BaseModel):
    """Schema for submitting an activity."""
    category: ActivityCategory
    level: ActivityLevel
    achievement_type: AchievementType
    activity_name: str = Field(..., min_length=5, max_length=300)
    description: Optional[str] = None
    activity_date: date
    end_date: Optional[date] = None
    venue: Optional[str] = None
    organizer: Optional[str] = None
    proof_documents: Optional[List[ProofDocument]] = None


class ActivitySubmissionUpdate(BaseModel):
    """Schema for updating a submission."""
    activity_name: Optional[str] = Field(None, min_length=5, max_length=300)
    description: Optional[str] = None
    activity_date: Optional[date] = None
    end_date: Optional[date] = None
    venue: Optional[str] = None
    organizer: Optional[str] = None
    proof_documents: Optional[List[ProofDocument]] = None


class ActivitySubmissionResponse(BaseModel):
    """Schema for submission response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    student_id: UUID
    academic_year_id: UUID
    semester: Optional[int] = None
    category: ActivityCategory
    level: ActivityLevel
    achievement_type: AchievementType
    activity_name: str
    description: Optional[str] = None
    activity_date: date
    end_date: Optional[date] = None
    venue: Optional[str] = None
    organizer: Optional[str] = None
    requested_points: int
    approved_points: Optional[int] = None
    status: SubmissionStatus
    proof_documents: Optional[List[dict]] = None
    submitted_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    review_comments: Optional[str] = None
    rejection_reason: Optional[str] = None
    created_at: datetime


class ActivitySubmissionListResponse(BaseModel):
    """Schema for paginated submission list."""
    items: List[ActivitySubmissionResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ============================================
# Review Schemas
# ============================================

class ActivityReviewRequest(BaseModel):
    """Schema for reviewing an activity submission."""
    status: SubmissionStatus
    approved_points: Optional[int] = Field(None, ge=0, le=50)
    review_comments: Optional[str] = None
    rejection_reason: Optional[str] = None


# ============================================
# Summary Schemas
# ============================================

class CategoryPointsSummary(BaseModel):
    """Schema for category-wise points summary."""
    category: ActivityCategory
    points: int
    activities_count: int


class StudentActivitySummaryResponse(BaseModel):
    """Schema for student activity summary."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    student_id: UUID
    academic_year_id: UUID
    total_submissions: int
    approved_submissions: int
    pending_submissions: int
    rejected_submissions: int
    total_points: int
    required_points: int
    points_deficit: int
    is_requirement_met: bool
    points_by_category: Optional[dict] = None


class SemesterPointsResponse(BaseModel):
    """Schema for semester-wise points."""
    model_config = ConfigDict(from_attributes=True)
    
    semester: int
    total_points: int
    max_allowed: int
    activities_count: int
    points_by_category: Optional[dict] = None


class StudentPointsDashboard(BaseModel):
    """Schema for student points dashboard."""
    student_id: UUID
    student_name: str
    enrollment_number: str
    current_semester: int
    total_points_earned: int
    required_points: int
    points_remaining: int
    is_requirement_met: bool
    semester_breakdown: List[SemesterPointsResponse]
    category_breakdown: List[CategoryPointsSummary]
    recent_submissions: List[ActivitySubmissionResponse]


# ============================================
# Certificate Schemas
# ============================================

class CertificateGenerateRequest(BaseModel):
    """Schema for generating activity certificate."""
    student_id: UUID
    from_date: date
    to_date: date
    title: Optional[str] = "Activity Points Certificate"


class CertificateResponse(BaseModel):
    """Schema for certificate response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    student_id: UUID
    certificate_number: str
    title: str
    from_date: date
    to_date: date
    total_points: int
    activities_summary: Optional[dict] = None
    pdf_url: Optional[str] = None
    verification_code: str
    generated_at: datetime


# ============================================
# Statistics Schemas
# ============================================

class ActivityStatistics(BaseModel):
    """Schema for activity statistics."""
    total_students: int
    students_met_requirement: int
    avg_points_per_student: float
    most_popular_category: str
    category_distribution: List[CategoryPointsSummary]
