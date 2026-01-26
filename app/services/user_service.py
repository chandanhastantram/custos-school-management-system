"""
CUSTOS User Service

User management business logic.
"""

from typing import Optional, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.password import hash_password
from app.auth.rbac import SystemRole, get_default_permissions
from app.core.exceptions import ResourceNotFoundError, DuplicateError, ValidationError
from app.models.user import User, Role, UserStatus, StudentProfile, TeacherProfile
from app.repositories.user_repo import UserRepository, RoleRepository
from app.schemas.user import (
    UserCreate, UserUpdate, UserResponse,
    StudentProfileCreate, TeacherProfileCreate,
)


class UserService:
    """User management service."""
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
        self.user_repo = UserRepository(session, tenant_id)
        self.role_repo = RoleRepository(session, tenant_id)
    
    async def create_user(
        self,
        data: UserCreate,
        created_by: Optional[UUID] = None,
    ) -> User:
        """Create new user."""
        # Check email uniqueness
        if await self.user_repo.email_exists(data.email):
            raise DuplicateError("User", "email", data.email)
        
        # Get roles
        roles = []
        if data.role_codes:
            roles = await self.role_repo.get_by_codes(data.role_codes)
            if len(roles) != len(data.role_codes):
                raise ValidationError("Some roles not found")
        
        # Create user
        user = await self.user_repo.create(
            email=data.email,
            password_hash=hash_password(data.password),
            first_name=data.first_name,
            last_name=data.last_name,
            phone=data.phone,
            gender=data.gender,
            date_of_birth=data.date_of_birth,
            address=data.address,
            city=data.city,
            state=data.state,
            status=UserStatus.ACTIVE,
        )
        
        # Assign roles
        for role in roles:
            user.roles.append(role)
        
        await self.session.commit()
        await self.session.refresh(user)
        
        return user
    
    async def get_user(self, user_id: UUID) -> User:
        """Get user by ID."""
        user = await self.user_repo.get_by_id_with_roles(user_id)
        if not user:
            raise ResourceNotFoundError("User", str(user_id))
        return user
    
    async def update_user(self, user_id: UUID, data: UserUpdate) -> User:
        """Update user."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundError("User", str(user_id))
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(user, key, value)
        
        await self.session.commit()
        await self.session.refresh(user)
        
        return user
    
    async def delete_user(self, user_id: UUID, deleted_by: UUID) -> bool:
        """Soft delete user."""
        return await self.user_repo.soft_delete(user_id, deleted_by)
    
    async def list_users(
        self,
        role_code: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[List[User], int]:
        """List users with pagination."""
        skip = (page - 1) * size
        
        if search:
            users = await self.user_repo.search(search, role_code, skip, size)
        elif role_code:
            users = await self.user_repo.get_users_by_role(role_code, skip, size)
        else:
            users = await self.user_repo.get_all(skip, size)
        
        total = await self.user_repo.count()
        
        return users, total
    
    async def assign_roles(self, user_id: UUID, role_codes: List[str]) -> User:
        """Assign roles to user."""
        user = await self.user_repo.get_by_id_with_roles(user_id)
        if not user:
            raise ResourceNotFoundError("User", str(user_id))
        
        roles = await self.role_repo.get_by_codes(role_codes)
        
        # Clear existing and assign new
        user.roles.clear()
        for role in roles:
            user.roles.append(role)
        
        await self.session.commit()
        await self.session.refresh(user)
        
        return user
    
    async def create_student(
        self,
        user_data: UserCreate,
        profile_data: StudentProfileCreate,
    ) -> tuple[User, StudentProfile]:
        """Create student with profile."""
        # Add student role
        user_data.role_codes = ["student"]
        user = await self.create_user(user_data)
        
        # Create profile
        profile = StudentProfile(
            tenant_id=self.tenant_id,
            user_id=user.id,
            **profile_data.model_dump(),
        )
        self.session.add(profile)
        await self.session.commit()
        await self.session.refresh(profile)
        
        return user, profile
    
    async def create_teacher(
        self,
        user_data: UserCreate,
        profile_data: TeacherProfileCreate,
    ) -> tuple[User, TeacherProfile]:
        """Create teacher with profile."""
        user_data.role_codes = ["teacher"]
        user = await self.create_user(user_data)
        
        profile = TeacherProfile(
            tenant_id=self.tenant_id,
            user_id=user.id,
            **profile_data.model_dump(),
        )
        self.session.add(profile)
        await self.session.commit()
        await self.session.refresh(profile)
        
        return user, profile
    
    async def get_students_by_section(
        self,
        section_id: UUID,
        page: int = 1,
        size: int = 50,
    ) -> List[User]:
        """Get students in a section."""
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        
        skip = (page - 1) * size
        query = select(User).join(StudentProfile).where(
            User.tenant_id == self.tenant_id,
            StudentProfile.section_id == section_id,
            User.is_deleted == False
        ).offset(skip).limit(size)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def activate_user(self, user_id: UUID) -> User:
        """Activate user account."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundError("User", str(user_id))
        
        user.status = UserStatus.ACTIVE
        await self.session.commit()
        return user
    
    async def suspend_user(self, user_id: UUID) -> User:
        """Suspend user account."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundError("User", str(user_id))
        
        user.status = UserStatus.SUSPENDED
        await self.session.commit()
        return user
