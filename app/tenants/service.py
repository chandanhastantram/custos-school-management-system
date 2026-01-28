"""
CUSTOS Tenant Service

Tenant business logic.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import hash_password
from app.core.exceptions import (
    DuplicateError, ResourceNotFoundError, ValidationError,
)
from app.tenants.models import Tenant, TenantStatus, TenantType
from app.tenants.repository import TenantRepository
from app.tenants.schemas import TenantCreate, TenantUpdate


class TenantService:
    """Tenant management service."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = TenantRepository(session)
    
    async def register(
        self,
        data: TenantCreate,
        admin_email: str,
        admin_password: str,
    ) -> Tuple[Tenant, "User"]:
        """
        Register new tenant (school).
        
        Creates:
        - Tenant record
        - Default roles
        - Admin user
        - Trial subscription
        """
        from app.users.models import User, Role, UserStatus
        from app.billing.models import UsageLimit
        
        # Check uniqueness
        if await self.repo.slug_exists(data.slug):
            raise DuplicateError("Tenant", "slug", data.slug)
        
        if await self.repo.email_exists(data.email):
            raise DuplicateError("Tenant", "email", data.email)
        
        # Create tenant
        tenant = Tenant(
            name=data.name,
            slug=data.slug,
            type=data.type,
            email=data.email.lower(),
            phone=data.phone,
            website=data.website,
            address=data.address,
            city=data.city,
            state=data.state,
            country=data.country,
            timezone=data.timezone,
            status=TenantStatus.TRIAL,
            trial_ends_at=datetime.now(timezone.utc) + timedelta(days=settings.trial_days),
        )
        tenant = await self.repo.create(tenant)
        
        # Create default roles
        default_roles = [
            ("Super Admin", "super_admin"),
            ("Principal", "principal"),
            ("Sub Admin", "sub_admin"),
            ("Teacher", "teacher"),
            ("Student", "student"),
            ("Parent", "parent"),
        ]
        
        roles = {}
        for name, code in default_roles:
            role = Role(
                tenant_id=tenant.id,
                name=name,
                code=code,
                is_system=True,
            )
            self.session.add(role)
            roles[code] = role
        
        await self.session.flush()
        
        # Create admin user
        admin = User(
            tenant_id=tenant.id,
            email=admin_email.lower(),
            password_hash=hash_password(admin_password),
            first_name="Admin",
            last_name=data.name,
            status=UserStatus.ACTIVE,
        )
        admin.roles.append(roles["super_admin"])
        self.session.add(admin)
        
        # Create usage limit record
        usage = UsageLimit(
            tenant_id=tenant.id,
            year=datetime.now(timezone.utc).year,
            month=datetime.now(timezone.utc).month,
        )
        self.session.add(usage)
        
        await self.session.commit()
        await self.session.refresh(tenant)
        await self.session.refresh(admin)
        
        return tenant, admin
    
    async def get_by_id(self, tenant_id: UUID) -> Tenant:
        """Get tenant by ID."""
        tenant = await self.repo.get_by_id(tenant_id)
        if not tenant:
            raise ResourceNotFoundError("Tenant", str(tenant_id))
        return tenant
    
    async def get_by_slug(self, slug: str) -> Optional[Tenant]:
        """Get tenant by slug."""
        return await self.repo.get_by_slug(slug)
    
    async def update(self, tenant_id: UUID, data: TenantUpdate) -> Tenant:
        """Update tenant."""
        tenant = await self.get_by_id(tenant_id)
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(tenant, key, value)
        
        await self.session.commit()
        await self.session.refresh(tenant)
        return tenant
    
    async def activate(self, tenant_id: UUID) -> Tenant:
        """Activate tenant."""
        tenant = await self.get_by_id(tenant_id)
        tenant.status = TenantStatus.ACTIVE
        tenant.is_verified = True
        tenant.verified_at = datetime.now(timezone.utc)
        await self.session.commit()
        return tenant
    
    async def suspend(self, tenant_id: UUID, reason: Optional[str] = None) -> Tenant:
        """Suspend tenant."""
        tenant = await self.get_by_id(tenant_id)
        tenant.status = TenantStatus.SUSPENDED
        await self.session.commit()
        return tenant
    
    async def get_stats(self, tenant_id: UUID) -> dict:
        """Get tenant statistics."""
        from sqlalchemy import select, func
        from app.users.models import User, StudentProfile, TeacherProfile
        
        # Count students
        students = await self.session.execute(
            select(func.count()).select_from(User).join(StudentProfile).where(
                User.tenant_id == tenant_id,
                User.is_deleted == False,
            )
        )
        student_count = students.scalar() or 0
        
        # Count teachers
        teachers = await self.session.execute(
            select(func.count()).select_from(User).join(TeacherProfile).where(
                User.tenant_id == tenant_id,
                User.is_deleted == False,
            )
        )
        teacher_count = teachers.scalar() or 0
        
        return {
            "tenant_id": str(tenant_id),
            "student_count": student_count,
            "teacher_count": teacher_count,
            "question_count": 0,  # TODO
            "assignment_count": 0,  # TODO
        }
