"""
CUSTOS Teaching Assignment Service

Business logic for teaching assignments.
"""

from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.academics.repositories.teaching_assignment_repo import TeachingAssignmentRepository
from app.academics.models.teaching_assignments import TeachingAssignment
from app.academics.schemas.teaching_assignments import (
    TeachingAssignmentCreate,
    TeachingAssignmentBulkCreate,
    TeachingAssignmentUpdate,
    TeachingAssignmentStats,
    TeacherAssignmentSummary,
    ClassAssignmentSummary,
)


class TeachingAssignmentService:
    """
    Teaching assignment service.
    
    Handles:
    - Assignment creation/deletion
    - Lookup by teacher/class/subject
    - Statistics and summaries
    """
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
        self.repo = TeachingAssignmentRepository(session, tenant_id)
    
    # ========================================
    # CRUD Operations
    # ========================================
    
    async def create(self, data: TeachingAssignmentCreate) -> TeachingAssignment:
        """Create a new teaching assignment."""
        return await self.repo.create(**data.model_dump())
    
    async def create_bulk(self, data: TeachingAssignmentBulkCreate) -> List[TeachingAssignment]:
        """Create multiple assignments at once."""
        assignments_data = [a.model_dump() for a in data.assignments]
        return await self.repo.create_bulk(assignments_data)
    
    async def get(self, assignment_id: UUID) -> TeachingAssignment:
        """Get assignment by ID."""
        return await self.repo.get(assignment_id)
    
    async def list(
        self,
        academic_year_id: Optional[UUID] = None,
        teacher_id: Optional[UUID] = None,
        class_id: Optional[UUID] = None,
        section_id: Optional[UUID] = None,
        subject_id: Optional[UUID] = None,
        is_active: Optional[bool] = True,
        is_primary: Optional[bool] = None,
        page: int = 1,
        size: int = 50,
    ) -> Tuple[List[TeachingAssignment], int]:
        """List assignments with filters."""
        return await self.repo.list(
            academic_year_id=academic_year_id,
            teacher_id=teacher_id,
            class_id=class_id,
            section_id=section_id,
            subject_id=subject_id,
            is_active=is_active,
            is_primary=is_primary,
            page=page,
            size=size,
        )
    
    async def update(
        self,
        assignment_id: UUID,
        data: TeachingAssignmentUpdate,
    ) -> TeachingAssignment:
        """Update an assignment."""
        update_data = data.model_dump(exclude_unset=True)
        return await self.repo.update(assignment_id, **update_data)
    
    async def delete(self, assignment_id: UUID) -> None:
        """Soft delete an assignment."""
        await self.repo.delete(assignment_id)
    
    async def deactivate(self, assignment_id: UUID) -> TeachingAssignment:
        """Deactivate an assignment (instead of deleting)."""
        return await self.repo.deactivate(assignment_id)
    
    # ========================================
    # Lookup Operations
    # ========================================
    
    async def get_teacher_assignments(
        self,
        teacher_id: UUID,
        academic_year_id: Optional[UUID] = None,
    ) -> List[TeachingAssignment]:
        """Get all assignments for a teacher."""
        return await self.repo.get_by_teacher(teacher_id, academic_year_id)
    
    async def get_class_assignments(
        self,
        class_id: UUID,
        academic_year_id: Optional[UUID] = None,
    ) -> List[TeachingAssignment]:
        """Get all assignments for a class."""
        return await self.repo.get_by_class(class_id, academic_year_id)
    
    async def get_subject_assignments(
        self,
        subject_id: UUID,
        academic_year_id: Optional[UUID] = None,
    ) -> List[TeachingAssignment]:
        """Get all assignments for a subject."""
        return await self.repo.get_by_subject(subject_id, academic_year_id)
    
    async def get_teacher_for_class_subject(
        self,
        class_id: UUID,
        subject_id: UUID,
        academic_year_id: UUID,
        section_id: Optional[UUID] = None,
    ) -> Optional[TeachingAssignment]:
        """
        Get the primary teacher for a class-subject combination.
        
        Used by timetable and lesson planning.
        """
        return await self.repo.get_teacher_for_class_subject(
            class_id, subject_id, academic_year_id, section_id
        )
    
    async def is_teacher_assigned(
        self,
        teacher_id: UUID,
        class_id: UUID,
        subject_id: UUID,
        academic_year_id: UUID,
    ) -> bool:
        """Check if teacher is assigned to class-subject."""
        assignment = await self.repo.get_teacher_for_class_subject(
            class_id, subject_id, academic_year_id
        )
        return assignment is not None and assignment.teacher_id == teacher_id
    
    # ========================================
    # Summaries
    # ========================================
    
    async def get_teacher_summary(
        self,
        teacher_id: UUID,
        academic_year_id: Optional[UUID] = None,
    ) -> TeacherAssignmentSummary:
        """Get summary of a teacher's assignments."""
        assignments = await self.repo.get_by_teacher(teacher_id, academic_year_id)
        
        classes = list(set(str(a.class_id) for a in assignments))
        subjects = list(set(str(a.subject_id) for a in assignments))
        total_periods = sum(a.periods_per_week for a in assignments)
        
        return TeacherAssignmentSummary(
            teacher_id=teacher_id,
            teacher_name=None,  # Loaded separately if needed
            total_assignments=len(assignments),
            classes=classes,
            subjects=subjects,
            total_periods_per_week=total_periods,
        )
    
    async def get_class_summary(
        self,
        class_id: UUID,
        academic_year_id: Optional[UUID] = None,
    ) -> ClassAssignmentSummary:
        """Get summary of assignments for a class."""
        assignments = await self.repo.get_by_class(class_id, academic_year_id)
        
        teachers = list(set(str(a.teacher_id) for a in assignments))
        subjects = list(set(str(a.subject_id) for a in assignments))
        
        return ClassAssignmentSummary(
            class_id=class_id,
            class_name=None,
            section_id=None,
            section_name=None,
            total_subjects=len(subjects),
            teachers=teachers,
            subjects=subjects,
        )
    
    # ========================================
    # Statistics
    # ========================================
    
    async def get_stats(
        self,
        academic_year_id: Optional[UUID] = None,
    ) -> TeachingAssignmentStats:
        """Get assignment statistics."""
        stats = await self.repo.get_stats(academic_year_id)
        return TeachingAssignmentStats(**stats)
    
    # ========================================
    # Validation Helpers
    # ========================================
    
    async def validate_teacher_access(
        self,
        teacher_id: UUID,
        class_id: UUID,
        subject_id: UUID,
        academic_year_id: UUID,
    ) -> bool:
        """
        Validate that a teacher has access to class-subject.
        
        Used by lesson planning to verify ownership.
        """
        assignments, _ = await self.repo.list(
            teacher_id=teacher_id,
            class_id=class_id,
            subject_id=subject_id,
            academic_year_id=academic_year_id,
            is_active=True,
        )
        return len(assignments) > 0
    
    async def get_teacher_classes(
        self,
        teacher_id: UUID,
        academic_year_id: UUID,
    ) -> List[UUID]:
        """Get list of class IDs teacher is assigned to."""
        assignments = await self.repo.get_by_teacher(teacher_id, academic_year_id)
        return list(set(a.class_id for a in assignments))
    
    async def get_teacher_subjects(
        self,
        teacher_id: UUID,
        academic_year_id: UUID,
    ) -> List[UUID]:
        """Get list of subject IDs teacher is assigned to."""
        assignments = await self.repo.get_by_teacher(teacher_id, academic_year_id)
        return list(set(a.subject_id for a in assignments))
