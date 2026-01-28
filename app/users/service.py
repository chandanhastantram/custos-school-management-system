"""
CUSTOS User Service

User management business logic.
"""

from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import hash_password
from app.core.exceptions import ResourceNotFoundError, DuplicateError, ValidationError
from app.users.models import (
    User, Role, StudentProfile, TeacherProfile, UserStatus,
)
from app.users.schemas import UserCreate, UserUpdate, StudentCreate, TeacherCreate


class UserService:
    """User management service."""
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
    
    async def create_user(self, data: UserCreate, created_by: UUID) -> User:
        """Create user."""
        # Check email uniqueness
        exists = await self._email_exists(data.email)
        if exists:
            raise DuplicateError("User", "email", data.email)
        
        user = User(
            tenant_id=self.tenant_id,
            email=data.email.lower(),
            password_hash=hash_password(data.password),
            first_name=data.first_name,
            last_name=data.last_name,
            phone=data.phone,
            date_of_birth=data.date_of_birth,
            gender=data.gender,
            status=UserStatus.ACTIVE,
        )
        
        # Assign roles
        if data.role_ids:
            roles = await self._get_roles(data.role_ids)
            user.roles.extend(roles)
        
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        
        return user
    
    async def get_user(self, user_id: UUID) -> User:
        """Get user by ID."""
        query = select(User).where(
            User.tenant_id == self.tenant_id,
            User.id == user_id,
            User.is_deleted == False,
        ).options(selectinload(User.roles))
        
        result = await self.session.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            raise ResourceNotFoundError("User", str(user_id))
        
        return user
    
    async def list_users(
        self,
        status: Optional[UserStatus] = None,
        role: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        size: int = 20,
    ) -> Tuple[List[User], int]:
        """List users with filters."""
        query = select(User).where(
            User.tenant_id == self.tenant_id,
            User.is_deleted == False,
        )
        
        if status:
            query = query.where(User.status == status)
        
        if search:
            search_term = f"%{search}%"
            query = query.where(
                (User.email.ilike(search_term)) |
                (User.first_name.ilike(search_term)) |
                (User.last_name.ilike(search_term))
            )
        
        # Count
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0
        
        # Paginate
        skip = (page - 1) * size
        query = query.order_by(User.created_at.desc()).offset(skip).limit(size)
        query = query.options(selectinload(User.roles))
        
        result = await self.session.execute(query)
        users = list(result.scalars().all())
        
        return users, total
    
    async def update_user(self, user_id: UUID, data: UserUpdate) -> User:
        """Update user."""
        user = await self.get_user(user_id)
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(user, key, value)
        
        await self.session.commit()
        await self.session.refresh(user)
        
        return user
    
    async def delete_user(self, user_id: UUID) -> bool:
        """Soft delete user."""
        user = await self.get_user(user_id)
        user.soft_delete()
        await self.session.commit()
        return True
    
    async def create_student(self, data: StudentCreate) -> User:
        """Create student user with profile."""
        # Check email
        if await self._email_exists(data.email):
            raise DuplicateError("User", "email", data.email)
        
        # Get student role
        student_role = await self._get_role_by_code("student")
        if not student_role:
            raise ValidationError("Student role not configured")
        
        # Create user
        user = User(
            tenant_id=self.tenant_id,
            email=data.email.lower(),
            password_hash=hash_password(data.password),
            first_name=data.first_name,
            last_name=data.last_name,
            phone=data.phone,
            date_of_birth=data.date_of_birth,
            gender=data.gender,
            status=UserStatus.ACTIVE,
        )
        user.roles.append(student_role)
        self.session.add(user)
        await self.session.flush()
        
        # Create profile
        profile = StudentProfile(
            tenant_id=self.tenant_id,
            user_id=user.id,
            admission_number=data.admission_number,
            admission_date=data.admission_date,
            section_id=data.section_id,
            roll_number=data.roll_number,
        )
        self.session.add(profile)
        
        await self.session.commit()
        await self.session.refresh(user)
        
        return user
    
    async def create_teacher(self, data: TeacherCreate) -> User:
        """Create teacher user with profile."""
        # Check email
        if await self._email_exists(data.email):
            raise DuplicateError("User", "email", data.email)
        
        # Get teacher role
        teacher_role = await self._get_role_by_code("teacher")
        if not teacher_role:
            raise ValidationError("Teacher role not configured")
        
        # Create user
        user = User(
            tenant_id=self.tenant_id,
            email=data.email.lower(),
            password_hash=hash_password(data.password),
            first_name=data.first_name,
            last_name=data.last_name,
            phone=data.phone,
            date_of_birth=data.date_of_birth,
            gender=data.gender,
            status=UserStatus.ACTIVE,
        )
        user.roles.append(teacher_role)
        self.session.add(user)
        await self.session.flush()
        
        # Create profile
        profile = TeacherProfile(
            tenant_id=self.tenant_id,
            user_id=user.id,
            employee_id=data.employee_id,
            joining_date=data.joining_date,
            designation=data.designation,
            department=data.department,
            qualifications=data.qualifications,
        )
        self.session.add(profile)
        
        await self.session.commit()
        await self.session.refresh(user)
        
        return user
    
    async def assign_roles(self, user_id: UUID, role_ids: List[UUID]) -> User:
        """Assign roles to user."""
        user = await self.get_user(user_id)
        roles = await self._get_roles(role_ids)
        
        user.roles.clear()
        user.roles.extend(roles)
        
        await self.session.commit()
        await self.session.refresh(user)
        
        return user
    
    async def _email_exists(self, email: str) -> bool:
        """Check if email exists."""
        query = select(func.count()).where(
            User.tenant_id == self.tenant_id,
            User.email == email.lower(),
            User.is_deleted == False,
        )
        result = await self.session.execute(query)
        return (result.scalar() or 0) > 0
    
    async def _get_roles(self, role_ids: List[UUID]) -> List[Role]:
        """Get roles by IDs."""
        query = select(Role).where(
            Role.tenant_id == self.tenant_id,
            Role.id.in_(role_ids),
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def _get_role_by_code(self, code: str) -> Optional[Role]:
        """Get role by code."""
        query = select(Role).where(
            Role.tenant_id == self.tenant_id,
            Role.code == code,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
