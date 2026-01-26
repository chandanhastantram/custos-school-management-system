"""
CUSTOS User Repository
"""

from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User, Role, Permission, StudentProfile, TeacherProfile
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """User repository."""
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        super().__init__(User, session, tenant_id)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        query = self._base_query().where(User.email == email)
        query = query.options(selectinload(User.roles).selectinload(Role.permissions))
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_id_with_roles(self, id: UUID) -> Optional[User]:
        """Get user with roles loaded."""
        query = self._base_query().where(User.id == id)
        query = query.options(selectinload(User.roles).selectinload(Role.permissions))
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_users_by_role(self, role_code: str, skip: int = 0, limit: int = 100) -> List[User]:
        """Get users with specific role."""
        query = self._base_query().join(User.roles).where(Role.code == role_code)
        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def count_by_role(self, role_code: str) -> int:
        """Count users with specific role."""
        query = select(func.count()).select_from(User).join(User.roles).where(
            User.tenant_id == self.tenant_id,
            Role.code == role_code
        )
        result = await self.session.execute(query)
        return result.scalar() or 0
    
    async def email_exists(self, email: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if email exists."""
        query = select(func.count()).select_from(User).where(
            User.tenant_id == self.tenant_id,
            User.email == email
        )
        if exclude_id:
            query = query.where(User.id != exclude_id)
        result = await self.session.execute(query)
        return (result.scalar() or 0) > 0
    
    async def search(
        self,
        query_str: str,
        role_code: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[User]:
        """Search users by name or email."""
        query = self._base_query()
        
        search = f"%{query_str}%"
        query = query.where(
            (User.first_name.ilike(search)) |
            (User.last_name.ilike(search)) |
            (User.email.ilike(search))
        )
        
        if role_code:
            query = query.join(User.roles).where(Role.code == role_code)
        
        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())


class RoleRepository(BaseRepository[Role]):
    """Role repository."""
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        super().__init__(Role, session, tenant_id)
    
    async def get_by_code(self, code: str) -> Optional[Role]:
        """Get role by code."""
        query = self._base_query().where(Role.code == code)
        query = query.options(selectinload(Role.permissions))
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_codes(self, codes: List[str]) -> List[Role]:
        """Get roles by codes."""
        query = self._base_query().where(Role.code.in_(codes))
        query = query.options(selectinload(Role.permissions))
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_system_roles(self) -> List[Role]:
        """Get system-defined roles."""
        query = self._base_query().where(Role.is_system == True)
        result = await self.session.execute(query)
        return list(result.scalars().all())


class PermissionRepository:
    """Permission repository (not tenant-scoped)."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_all(self) -> List[Permission]:
        """Get all permissions."""
        query = select(Permission).order_by(Permission.category, Permission.name)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_by_codes(self, codes: List[str]) -> List[Permission]:
        """Get permissions by codes."""
        query = select(Permission).where(Permission.code.in_(codes))
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_by_category(self, category: str) -> List[Permission]:
        """Get permissions by category."""
        query = select(Permission).where(Permission.category == category)
        result = await self.session.execute(query)
        return list(result.scalars().all())
