"""
CUSTOS Database Seeder

Seed initial data for development and testing.
"""

import asyncio
from datetime import date, timedelta
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.auth.password import hash_password
from app.models.tenant import Tenant, TenantStatus, TenantType
from app.models.user import User, Role, Permission, UserStatus
from app.models.academic import AcademicYear, Class, Section, Subject
from app.models.billing import Plan, PlanType


async def seed_permissions(session: AsyncSession) -> list[Permission]:
    """Seed system permissions."""
    from app.auth.rbac import Permission as PermEnum
    
    permissions = []
    for perm in PermEnum:
        # Parse category from code (e.g., "user:create" -> "user")
        parts = perm.value.split(":")
        category = parts[0] if len(parts) > 1 else "general"
        
        p = Permission(
            id=uuid4(),
            name=perm.name.replace("_", " ").title(),
            code=perm.value,
            category=category,
        )
        session.add(p)
        permissions.append(p)
    
    await session.flush()
    return permissions


async def seed_plans(session: AsyncSession) -> list[Plan]:
    """Seed subscription plans."""
    plans_data = [
        {
            "name": "Free",
            "code": "free",
            "plan_type": PlanType.FREE,
            "description": "Basic features for small schools",
            "price_monthly": 0,
            "price_yearly": 0,
            "max_students": 50,
            "max_teachers": 5,
            "max_admins": 2,
            "max_storage_gb": 1,
            "ai_tokens_monthly": 1000,
            "features": ["basic_reports"],
            "display_order": 1,
        },
        {
            "name": "Starter",
            "code": "starter",
            "plan_type": PlanType.STARTER,
            "description": "Perfect for small schools",
            "price_monthly": 999,
            "price_yearly": 9999,
            "max_students": 200,
            "max_teachers": 20,
            "max_admins": 5,
            "max_storage_gb": 5,
            "ai_tokens_monthly": 10000,
            "features": ["basic_reports", "assignments", "worksheets"],
            "display_order": 2,
        },
        {
            "name": "Standard",
            "code": "standard",
            "plan_type": PlanType.STANDARD,
            "description": "For growing institutions",
            "price_monthly": 2499,
            "price_yearly": 24999,
            "max_students": 500,
            "max_teachers": 50,
            "max_admins": 10,
            "max_storage_gb": 20,
            "ai_tokens_monthly": 50000,
            "features": ["basic_reports", "assignments", "worksheets", "ai_basic"],
            "display_order": 3,
        },
        {
            "name": "Premium",
            "code": "premium",
            "plan_type": PlanType.PREMIUM,
            "description": "Full-featured solution",
            "price_monthly": 4999,
            "price_yearly": 49999,
            "max_students": 2000,
            "max_teachers": 200,
            "max_admins": 20,
            "max_storage_gb": 100,
            "ai_tokens_monthly": 200000,
            "features": ["basic_reports", "assignments", "worksheets", "ai_basic", "ai_advanced", "custom_reports"],
            "display_order": 4,
        },
        {
            "name": "Enterprise",
            "code": "enterprise",
            "plan_type": PlanType.ENTERPRISE,
            "description": "Unlimited everything",
            "price_monthly": 9999,
            "price_yearly": 99999,
            "max_students": 99999,
            "max_teachers": 9999,
            "max_admins": 999,
            "max_storage_gb": 500,
            "ai_tokens_monthly": 1000000,
            "features": ["*"],
            "display_order": 5,
        },
    ]
    
    plans = []
    for data in plans_data:
        plan = Plan(id=uuid4(), **data)
        session.add(plan)
        plans.append(plan)
    
    await session.flush()
    return plans


async def seed_demo_tenant(session: AsyncSession, permissions: list[Permission]) -> tuple:
    """Seed demo school tenant."""
    tenant_id = uuid4()
    
    # Create tenant
    tenant = Tenant(
        id=tenant_id,
        name="Demo Public School",
        slug="demo-school",
        email="admin@demo-school.edu",
        phone="+91 9876543210",
        type=TenantType.SCHOOL,
        status=TenantStatus.ACTIVE,
        is_verified=True,
        country="IN",
        city="Mumbai",
        state="Maharashtra",
        timezone="Asia/Kolkata",
        primary_color="#4F46E5",
    )
    session.add(tenant)
    
    # Create roles
    from app.auth.rbac import ROLE_PERMISSIONS, SystemRole
    
    roles = {}
    for role_enum in SystemRole:
        role = Role(
            id=uuid4(),
            tenant_id=tenant_id,
            name=role_enum.name.replace("_", " ").title(),
            code=role_enum.value,
            is_system=True,
            is_active=True,
            hierarchy_level=100 if role_enum == SystemRole.SUPER_ADMIN else 50,
        )
        
        # Assign permissions
        role_perms = ROLE_PERMISSIONS.get(role_enum, set())
        for perm in permissions:
            if perm.code in [p.value for p in role_perms]:
                role.permissions.append(perm)
        
        session.add(role)
        roles[role_enum.value] = role
    
    await session.flush()
    
    # Create admin user
    admin = User(
        id=uuid4(),
        tenant_id=tenant_id,
        email="admin@demo-school.edu",
        password_hash=hash_password("Admin@123"),
        first_name="System",
        last_name="Admin",
        phone="+91 9876543210",
        status=UserStatus.ACTIVE,
        is_email_verified=True,
    )
    admin.roles.append(roles["super_admin"])
    session.add(admin)
    
    # Create teacher
    teacher = User(
        id=uuid4(),
        tenant_id=tenant_id,
        email="teacher@demo-school.edu",
        password_hash=hash_password("Teacher@123"),
        first_name="Demo",
        last_name="Teacher",
        status=UserStatus.ACTIVE,
        is_email_verified=True,
    )
    teacher.roles.append(roles["teacher"])
    session.add(teacher)
    
    # Create student
    student = User(
        id=uuid4(),
        tenant_id=tenant_id,
        email="student@demo-school.edu",
        password_hash=hash_password("Student@123"),
        first_name="Demo",
        last_name="Student",
        status=UserStatus.ACTIVE,
        is_email_verified=True,
    )
    student.roles.append(roles["student"])
    session.add(student)
    
    await session.flush()
    
    # Create academic year
    today = date.today()
    academic_year = AcademicYear(
        id=uuid4(),
        tenant_id=tenant_id,
        name=f"{today.year}-{today.year + 1}",
        start_date=date(today.year, 4, 1),
        end_date=date(today.year + 1, 3, 31),
        is_current=True,
        is_active=True,
    )
    session.add(academic_year)
    
    # Create classes
    classes = []
    for i in range(1, 11):
        cls = Class(
            id=uuid4(),
            tenant_id=tenant_id,
            academic_year_id=academic_year.id,
            name=f"Class {i}",
            code=f"C{i}",
            grade_level=i,
            display_order=i,
        )
        session.add(cls)
        classes.append(cls)
    
    await session.flush()
    
    # Create sections for class 10
    class_10 = classes[9]
    for section_name in ["A", "B", "C"]:
        section = Section(
            id=uuid4(),
            tenant_id=tenant_id,
            class_id=class_10.id,
            name=f"Section {section_name}",
            code=section_name,
            capacity=40,
        )
        session.add(section)
    
    # Create subjects
    subjects_data = [
        ("Mathematics", "MATH", "Science", "#3B82F6"),
        ("Science", "SCI", "Science", "#10B981"),
        ("English", "ENG", "Language", "#8B5CF6"),
        ("Hindi", "HIN", "Language", "#F59E0B"),
        ("Social Studies", "SST", "Social", "#EF4444"),
        ("Computer Science", "CS", "Technology", "#6366F1"),
    ]
    
    for name, code, category, color in subjects_data:
        subject = Subject(
            id=uuid4(),
            tenant_id=tenant_id,
            name=name,
            code=code,
            category=category,
            color=color,
        )
        session.add(subject)
    
    await session.commit()
    
    return tenant, admin, teacher, student


async def main():
    """Run seeder."""
    print("🌱 Starting database seeding...")
    
    async with AsyncSessionLocal() as session:
        # Seed permissions
        print("📝 Seeding permissions...")
        permissions = await seed_permissions(session)
        print(f"   ✓ Created {len(permissions)} permissions")
        
        # Seed plans
        print("💳 Seeding subscription plans...")
        plans = await seed_plans(session)
        print(f"   ✓ Created {len(plans)} plans")
        
        # Seed demo tenant
        print("🏫 Creating demo school...")
        tenant, admin, teacher, student = await seed_demo_tenant(session, permissions)
        print(f"   ✓ Created tenant: {tenant.name}")
        print(f"   ✓ Created admin: {admin.email} (password: Admin@123)")
        print(f"   ✓ Created teacher: {teacher.email} (password: Teacher@123)")
        print(f"   ✓ Created student: {student.email} (password: Student@123)")
        
        await session.commit()
    
    print("\n✅ Seeding complete!")


if __name__ == "__main__":
    asyncio.run(main())
