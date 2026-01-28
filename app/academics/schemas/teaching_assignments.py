"""
CUSTOS Teaching Assignment Schemas

Pydantic schemas for teaching assignment CRUD operations.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


# ============================================
# TeachingAssignment Schemas
# ============================================

class TeachingAssignmentBase(BaseModel):
    """Base schema for TeachingAssignment."""
    academic_year_id: UUID
    teacher_id: UUID
    class_id: UUID
    section_id: Optional[UUID] = None
    subject_id: UUID
    is_primary: bool = True
    periods_per_week: int = Field(0, ge=0)
    notes: Optional[str] = Field(None, max_length=500)


class TeachingAssignmentCreate(TeachingAssignmentBase):
    """Schema for creating a TeachingAssignment."""
    pass


class TeachingAssignmentBulkCreate(BaseModel):
    """Schema for bulk creating assignments."""
    assignments: List[TeachingAssignmentBase]


class TeachingAssignmentUpdate(BaseModel):
    """Schema for updating a TeachingAssignment."""
    is_active: Optional[bool] = None
    is_primary: Optional[bool] = None
    periods_per_week: Optional[int] = Field(None, ge=0)
    notes: Optional[str] = Field(None, max_length=500)


class TeachingAssignmentResponse(BaseModel):
    """Schema for TeachingAssignment response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    academic_year_id: UUID
    teacher_id: UUID
    class_id: UUID
    section_id: Optional[UUID]
    subject_id: UUID
    is_active: bool
    is_primary: bool
    periods_per_week: int
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime


class TeachingAssignmentWithDetails(TeachingAssignmentResponse):
    """Assignment with related entity names."""
    teacher_name: Optional[str] = None
    class_name: Optional[str] = None
    section_name: Optional[str] = None
    subject_name: Optional[str] = None
    academic_year_name: Optional[str] = None


# ============================================
# Query/Filter Schemas
# ============================================

class TeachingAssignmentFilter(BaseModel):
    """Filter schema for listing assignments."""
    academic_year_id: Optional[UUID] = None
    teacher_id: Optional[UUID] = None
    class_id: Optional[UUID] = None
    section_id: Optional[UUID] = None
    subject_id: Optional[UUID] = None
    is_active: Optional[bool] = True
    is_primary: Optional[bool] = None


# ============================================
# Summary Schemas
# ============================================

class TeacherAssignmentSummary(BaseModel):
    """Summary of a teacher's assignments."""
    teacher_id: UUID
    teacher_name: Optional[str] = None
    total_assignments: int
    classes: List[str]
    subjects: List[str]
    total_periods_per_week: int


class ClassAssignmentSummary(BaseModel):
    """Summary of assignments for a class."""
    class_id: UUID
    class_name: Optional[str] = None
    section_id: Optional[UUID] = None
    section_name: Optional[str] = None
    total_subjects: int
    teachers: List[str]
    subjects: List[str]


class SubjectAssignmentSummary(BaseModel):
    """Summary of assignments for a subject."""
    subject_id: UUID
    subject_name: Optional[str] = None
    total_teachers: int
    total_classes: int


# ============================================
# Stats Schema
# ============================================

class TeachingAssignmentStats(BaseModel):
    """Statistics for teaching assignments."""
    total_assignments: int
    active_assignments: int
    total_teachers_assigned: int
    total_classes_covered: int
    total_subjects_covered: int
    unassigned_classes: int
    unassigned_subjects: int
