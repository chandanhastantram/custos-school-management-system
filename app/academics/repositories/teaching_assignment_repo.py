"""
CUSTOS Teaching Assignment Repository

Data access layer for teaching assignments.
"""

from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundError, DuplicateError, ValidationError
from app.academics.models.teaching_assignments import TeachingAssignment
from app.users.models import User
from app.users.rbac import SystemRole


class TeachingAssignmentRepository:
    """Repository for teaching assignment CRUD operations."""
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
    
    async def create(self, **data) -> TeachingAssignment:
        """Create a new teaching assignment."""
        # Check for duplicate
        existing = await self._check_duplicate(
            data["academic_year_id"],
            data["teacher_id"],
            data["class_id"],
            data["subject_id"],
            data.get("section_id"),
        )
        if existing:
            raise DuplicateError(
                "TeachingAssignment",
                "teacher-class-subject",
                f"{data['teacher_id']}-{data['class_id']}-{data['subject_id']}",
            )
        
        # Validate teacher role
        await self._validate_teacher(data["teacher_id"])
        
        assignment = TeachingAssignment(tenant_id=self.tenant_id, **data)
        self.session.add(assignment)
        await self.session.commit()
        await self.session.refresh(assignment)
        return assignment
    
    async def create_bulk(self, assignments_data: List[dict]) -> List[TeachingAssignment]:
        """Create multiple assignments at once."""
        created = []
        
        for data in assignments_data:
            # Validate teacher
            await self._validate_teacher(data["teacher_id"])
            
            # Check duplicate
            existing = await self._check_duplicate(
                data["academic_year_id"],
                data["teacher_id"],
                data["class_id"],
                data["subject_id"],
                data.get("section_id"),
            )
            if existing:
                continue  # Skip duplicates in bulk
            
            assignment = TeachingAssignment(tenant_id=self.tenant_id, **data)
            self.session.add(assignment)
            created.append(assignment)
        
        await self.session.commit()
        
        for assignment in created:
            await self.session.refresh(assignment)
        
        return created
    
    async def get(self, assignment_id: UUID) -> TeachingAssignment:
        """Get assignment by ID."""
        query = select(TeachingAssignment).where(
            TeachingAssignment.tenant_id == self.tenant_id,
            TeachingAssignment.id == assignment_id,
            TeachingAssignment.is_deleted == False,
        )
        result = await self.session.execute(query)
        assignment = result.scalar_one_or_none()
        if not assignment:
            raise ResourceNotFoundError("TeachingAssignment", str(assignment_id))
        return assignment
    
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
        """List assignments with filtering and pagination."""
        query = select(TeachingAssignment).where(
            TeachingAssignment.tenant_id == self.tenant_id,
            TeachingAssignment.is_deleted == False,
        )
        
        if academic_year_id:
            query = query.where(TeachingAssignment.academic_year_id == academic_year_id)
        if teacher_id:
            query = query.where(TeachingAssignment.teacher_id == teacher_id)
        if class_id:
            query = query.where(TeachingAssignment.class_id == class_id)
        if section_id:
            query = query.where(TeachingAssignment.section_id == section_id)
        if subject_id:
            query = query.where(TeachingAssignment.subject_id == subject_id)
        if is_active is not None:
            query = query.where(TeachingAssignment.is_active == is_active)
        if is_primary is not None:
            query = query.where(TeachingAssignment.is_primary == is_primary)
        
        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.session.execute(count_query)).scalar() or 0
        
        # Paginate
        skip = (page - 1) * size
        query = query.order_by(
            TeachingAssignment.created_at.desc()
        ).offset(skip).limit(size)
        
        result = await self.session.execute(query)
        return list(result.scalars().all()), total
    
    async def get_by_teacher(self, teacher_id: UUID, academic_year_id: Optional[UUID] = None) -> List[TeachingAssignment]:
        """Get all assignments for a teacher."""
        query = select(TeachingAssignment).where(
            TeachingAssignment.tenant_id == self.tenant_id,
            TeachingAssignment.teacher_id == teacher_id,
            TeachingAssignment.is_deleted == False,
            TeachingAssignment.is_active == True,
        )
        
        if academic_year_id:
            query = query.where(TeachingAssignment.academic_year_id == academic_year_id)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_by_class(self, class_id: UUID, academic_year_id: Optional[UUID] = None) -> List[TeachingAssignment]:
        """Get all assignments for a class."""
        query = select(TeachingAssignment).where(
            TeachingAssignment.tenant_id == self.tenant_id,
            TeachingAssignment.class_id == class_id,
            TeachingAssignment.is_deleted == False,
            TeachingAssignment.is_active == True,
        )
        
        if academic_year_id:
            query = query.where(TeachingAssignment.academic_year_id == academic_year_id)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_by_subject(self, subject_id: UUID, academic_year_id: Optional[UUID] = None) -> List[TeachingAssignment]:
        """Get all assignments for a subject."""
        query = select(TeachingAssignment).where(
            TeachingAssignment.tenant_id == self.tenant_id,
            TeachingAssignment.subject_id == subject_id,
            TeachingAssignment.is_deleted == False,
            TeachingAssignment.is_active == True,
        )
        
        if academic_year_id:
            query = query.where(TeachingAssignment.academic_year_id == academic_year_id)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_teacher_for_class_subject(
        self,
        class_id: UUID,
        subject_id: UUID,
        academic_year_id: UUID,
        section_id: Optional[UUID] = None,
    ) -> Optional[TeachingAssignment]:
        """Get the primary teacher for a class-subject combination."""
        query = select(TeachingAssignment).where(
            TeachingAssignment.tenant_id == self.tenant_id,
            TeachingAssignment.class_id == class_id,
            TeachingAssignment.subject_id == subject_id,
            TeachingAssignment.academic_year_id == academic_year_id,
            TeachingAssignment.is_deleted == False,
            TeachingAssignment.is_active == True,
            TeachingAssignment.is_primary == True,
        )
        
        if section_id:
            query = query.where(
                or_(
                    TeachingAssignment.section_id == section_id,
                    TeachingAssignment.section_id.is_(None),
                )
            )
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def update(self, assignment_id: UUID, **data) -> TeachingAssignment:
        """Update an assignment."""
        assignment = await self.get(assignment_id)
        
        for key, value in data.items():
            if value is not None:
                setattr(assignment, key, value)
        
        await self.session.commit()
        await self.session.refresh(assignment)
        return assignment
    
    async def delete(self, assignment_id: UUID) -> None:
        """Soft delete an assignment."""
        assignment = await self.get(assignment_id)
        assignment.soft_delete()
        await self.session.commit()
    
    async def deactivate(self, assignment_id: UUID) -> TeachingAssignment:
        """Deactivate an assignment."""
        assignment = await self.get(assignment_id)
        assignment.is_active = False
        await self.session.commit()
        await self.session.refresh(assignment)
        return assignment
    
    async def _check_duplicate(
        self,
        academic_year_id: UUID,
        teacher_id: UUID,
        class_id: UUID,
        subject_id: UUID,
        section_id: Optional[UUID] = None,
    ) -> Optional[TeachingAssignment]:
        """Check for existing assignment."""
        query = select(TeachingAssignment).where(
            TeachingAssignment.tenant_id == self.tenant_id,
            TeachingAssignment.academic_year_id == academic_year_id,
            TeachingAssignment.teacher_id == teacher_id,
            TeachingAssignment.class_id == class_id,
            TeachingAssignment.subject_id == subject_id,
            TeachingAssignment.is_deleted == False,
        )
        
        if section_id:
            query = query.where(TeachingAssignment.section_id == section_id)
        else:
            query = query.where(TeachingAssignment.section_id.is_(None))
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def _validate_teacher(self, user_id: UUID) -> None:
        """Validate that user is a teacher."""
        from sqlalchemy.orm import selectinload
        
        query = select(User).where(
            User.tenant_id == self.tenant_id,
            User.id == user_id,
            User.is_deleted == False,
        ).options(selectinload(User.roles))
        
        result = await self.session.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            raise ValidationError(f"User {user_id} not found")
        
        # Check if user has teacher role
        user_roles = [r.code for r in user.roles] if user.roles else []
        valid_roles = {SystemRole.TEACHER.value, SystemRole.PRINCIPAL.value, SystemRole.SUPER_ADMIN.value}
        
        if not any(r in valid_roles for r in user_roles):
            raise ValidationError(f"User {user_id} does not have teacher role")
    
    # ========================================
    # Statistics
    # ========================================
    
    async def get_stats(self, academic_year_id: Optional[UUID] = None) -> dict:
        """Get assignment statistics."""
        base_query = select(TeachingAssignment).where(
            TeachingAssignment.tenant_id == self.tenant_id,
            TeachingAssignment.is_deleted == False,
        )
        
        if academic_year_id:
            base_query = base_query.where(
                TeachingAssignment.academic_year_id == academic_year_id
            )
        
        # Total assignments
        total = (await self.session.execute(
            select(func.count()).select_from(base_query.subquery())
        )).scalar() or 0
        
        # Active assignments
        active_query = base_query.where(TeachingAssignment.is_active == True)
        active = (await self.session.execute(
            select(func.count()).select_from(active_query.subquery())
        )).scalar() or 0
        
        # Distinct teachers
        teachers = (await self.session.execute(
            select(func.count(func.distinct(TeachingAssignment.teacher_id))).where(
                TeachingAssignment.tenant_id == self.tenant_id,
                TeachingAssignment.is_deleted == False,
                TeachingAssignment.is_active == True,
            )
        )).scalar() or 0
        
        # Distinct classes
        classes = (await self.session.execute(
            select(func.count(func.distinct(TeachingAssignment.class_id))).where(
                TeachingAssignment.tenant_id == self.tenant_id,
                TeachingAssignment.is_deleted == False,
                TeachingAssignment.is_active == True,
            )
        )).scalar() or 0
        
        # Distinct subjects
        subjects = (await self.session.execute(
            select(func.count(func.distinct(TeachingAssignment.subject_id))).where(
                TeachingAssignment.tenant_id == self.tenant_id,
                TeachingAssignment.is_deleted == False,
                TeachingAssignment.is_active == True,
            )
        )).scalar() or 0
        
        return {
            "total_assignments": total,
            "active_assignments": active,
            "total_teachers_assigned": teachers,
            "total_classes_covered": classes,
            "total_subjects_covered": subjects,
            "unassigned_classes": 0,  # Calculated separately if needed
            "unassigned_subjects": 0,
        }
