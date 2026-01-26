"""
CUSTOS Tenant Service

Tenant management and registration.
"""

from datetime import datetime, timezone
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundError, DuplicateError
from app.auth.password import hash_password
from app.models.tenant import Tenant, TenantStatus, TenantType
from app.models.user import User, Role, UserStatus
from app.models.billing import Subscription, UsageLimit
from app.schemas.tenant import TenantCreate, TenantUpdate


class TenantService:
    """Tenant management service."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def register_tenant(
        self,
        data: TenantCreate,
        admin_email: str,
        admin_password: str,
    ) -> tuple[Tenant, User]:
        """
        Register new tenant (school).
        
        Creates tenant, admin user, and default roles.
        """
        # Check slug uniqueness
        existing = await self.session.execute(
            select(Tenant).where(Tenant.slug == data.slug)
        )
        if existing.scalar_one_or_none():
            raise DuplicateError("Tenant", "slug", data.slug)
        
        # Check email
        existing_email = await self.session.execute(
            select(Tenant).where(Tenant.email == data.email)
        )
        if existing_email.scalar_one_or_none():
            raise DuplicateError("Tenant", "email", data.email)
        
        # Create tenant
        tenant = Tenant(
            name=data.name,
            slug=data.slug,
            email=data.email,
            phone=data.phone,
            type=data.type or TenantType.SCHOOL,
            status=TenantStatus.PENDING,
            country=data.country,
            city=data.city,
            state=data.state,
            timezone=data.timezone or "UTC",
        )
        self.session.add(tenant)
        await self.session.flush()
        
        # Create default roles
        from app.auth.rbac import SystemRole, ROLE_PERMISSIONS, Permission
        
        roles = {}
        for role_enum in SystemRole:
            role = Role(
                tenant_id=tenant.id,
                name=role_enum.name.replace("_", " ").title(),
                code=role_enum.value,
                is_system=True,
                is_active=True,
            )
            self.session.add(role)
            roles[role_enum.value] = role
        
        await self.session.flush()
        
        # Create admin user
        admin = User(
            tenant_id=tenant.id,
            email=admin_email,
            password_hash=hash_password(admin_password),
            first_name="Admin",
            last_name=data.name,
            status=UserStatus.ACTIVE,
            is_email_verified=False,
        )
        admin.roles.append(roles["super_admin"])
        self.session.add(admin)
        
        # Create usage limit record
        now = datetime.now(timezone.utc)
        usage = UsageLimit(
            tenant_id=tenant.id,
            year=now.year,
            month=now.month,
        )
        self.session.add(usage)
        
        await self.session.commit()
        await self.session.refresh(tenant)
        await self.session.refresh(admin)
        
        return tenant, admin
    
    async def get_tenant(self, tenant_id: UUID) -> Tenant:
        """Get tenant by ID."""
        tenant = await self.session.get(Tenant, tenant_id)
        if not tenant:
            raise ResourceNotFoundError("Tenant", str(tenant_id))
        return tenant
    
    async def get_tenant_by_slug(self, slug: str) -> Optional[Tenant]:
        """Get tenant by slug."""
        query = select(Tenant).where(Tenant.slug == slug)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def update_tenant(
        self,
        tenant_id: UUID,
        data: TenantUpdate,
    ) -> Tenant:
        """Update tenant settings."""
        tenant = await self.get_tenant(tenant_id)
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(tenant, key, value)
        
        await self.session.commit()
        await self.session.refresh(tenant)
        return tenant
    
    async def activate_tenant(self, tenant_id: UUID) -> Tenant:
        """Activate tenant."""
        tenant = await self.get_tenant(tenant_id)
        tenant.status = TenantStatus.ACTIVE
        tenant.is_verified = True
        await self.session.commit()
        return tenant
    
    async def suspend_tenant(self, tenant_id: UUID, reason: str = None) -> Tenant:
        """Suspend tenant."""
        tenant = await self.get_tenant(tenant_id)
        tenant.status = TenantStatus.SUSPENDED
        await self.session.commit()
        return tenant
    
    async def get_tenant_stats(self, tenant_id: UUID) -> dict:
        """Get tenant statistics."""
        from app.models.user import User, StudentProfile, TeacherProfile
        from app.models.question import Question
        from app.models.assignment import Assignment
        
        # Count students
        students = await self.session.execute(
            select(func.count()).select_from(User).join(
                StudentProfile, User.id == StudentProfile.user_id
            ).where(User.tenant_id == tenant_id, User.is_deleted == False)
        )
        student_count = students.scalar() or 0
        
        # Count teachers
        teachers = await self.session.execute(
            select(func.count()).select_from(User).join(
                TeacherProfile, User.id == TeacherProfile.user_id
            ).where(User.tenant_id == tenant_id, User.is_deleted == False)
        )
        teacher_count = teachers.scalar() or 0
        
        # Count questions
        questions = await self.session.execute(
            select(func.count()).select_from(Question).where(
                Question.tenant_id == tenant_id
            )
        )
        question_count = questions.scalar() or 0
        
        # Count assignments
        assignments = await self.session.execute(
            select(func.count()).select_from(Assignment).where(
                Assignment.tenant_id == tenant_id
            )
        )
        assignment_count = assignments.scalar() or 0
        
        return {
            "tenant_id": str(tenant_id),
            "student_count": student_count,
            "teacher_count": teacher_count,
            "question_count": question_count,
            "assignment_count": assignment_count,
        }
    
    async def list_tenants(
        self,
        status: Optional[TenantStatus] = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[List[Tenant], int]:
        """List all tenants (platform admin)."""
        query = select(Tenant)
        if status:
            query = query.where(Tenant.status == status)
        
        count_result = await self.session.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar() or 0
        
        skip = (page - 1) * size
        query = query.order_by(Tenant.created_at.desc()).offset(skip).limit(size)
        result = await self.session.execute(query)
        
        return list(result.scalars().all()), total
