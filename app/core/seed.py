"""
CUSTOS Database Seeding

Seed default data for the application.
"""

import asyncio
from datetime import datetime, timezone

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.billing.models import Plan, PlanTier
from app.platform.admin.models import PlatformAdmin, PlatformRole
from app.users.models import Permission


async def seed_plans():
    """Seed default subscription plans."""
    async with AsyncSessionLocal() as session:
        # Check if plans exist
        result = await session.execute(select(Plan).limit(1))
        if result.scalar_one_or_none():
            print("Plans already seeded")
            return
        
        plans = [
            Plan(
                name="Free",
                code="free",
                tier=PlanTier.FREE,
                description="Perfect for small schools just getting started",
                price_monthly=0,
                price_yearly=0,
                currency="INR",
                max_students=50,
                max_teachers=5,
                max_questions=500,
                max_ai_requests=0,
                max_storage_mb=500,
                features={
                    "core": True,
                    "assignments": True,
                    "notifications": True,
                    "reports_basic": True,
                },
                display_order=1,
            ),
            Plan(
                name="Starter",
                code="starter",
                tier=PlanTier.STARTER,
                description="For growing schools with basic needs",
                price_monthly=2999,
                price_yearly=29990,
                currency="INR",
                max_students=200,
                max_teachers=20,
                max_questions=2000,
                max_ai_requests=50,
                max_storage_mb=5000,
                features={
                    "core": True,
                    "assignments": True,
                    "question_bank": True,
                    "notifications": True,
                    "reports": True,
                    "calendar": True,
                    "file_storage": True,
                },
                display_order=2,
            ),
            Plan(
                name="Professional",
                code="professional",
                tier=PlanTier.PROFESSIONAL,
                description="Full-featured solution for established schools",
                price_monthly=7999,
                price_yearly=79990,
                currency="INR",
                max_students=1000,
                max_teachers=100,
                max_questions=10000,
                max_ai_requests=500,
                max_storage_mb=50000,
                features={
                    "core": True,
                    "assignments": True,
                    "question_bank": True,
                    "exams": True,
                    "ai_features": True,
                    "ai_lesson_plan": True,
                    "ai_questions": True,
                    "lms": True,
                    "gamification": True,
                    "notifications": True,
                    "reports": True,
                    "calendar": True,
                    "timetable": True,
                    "file_storage": True,
                    "parent_portal": True,
                },
                display_order=3,
            ),
            Plan(
                name="Enterprise",
                code="enterprise",
                tier=PlanTier.ENTERPRISE,
                description="Unlimited features for large institutions",
                price_monthly=19999,
                price_yearly=199990,
                currency="INR",
                max_students=999999,
                max_teachers=999999,
                max_questions=999999,
                max_ai_requests=5000,
                max_storage_mb=500000,
                features={
                    "all": True,
                    "custom_domain": True,
                    "api_access": True,
                    "sso": True,
                    "priority_support": True,
                    "dedicated_manager": True,
                },
                display_order=4,
            ),
        ]
        
        for plan in plans:
            session.add(plan)
        
        await session.commit()
        print(f"Seeded {len(plans)} plans")


async def seed_platform_owner(
    email: str = "admin@custos.school",
    password: str = "Admin@123",
):
    """Seed platform owner account."""
    async with AsyncSessionLocal() as session:
        # Check if exists
        result = await session.execute(
            select(PlatformAdmin).where(PlatformAdmin.email == email)
        )
        if result.scalar_one_or_none():
            print("Platform owner already exists")
            return
        
        admin = PlatformAdmin(
            email=email,
            password_hash=hash_password(password),
            first_name="Platform",
            last_name="Owner",
            role=PlatformRole.PLATFORM_OWNER,
            is_active=True,
        )
        session.add(admin)
        await session.commit()
        print(f"Seeded platform owner: {email}")


async def seed_permissions():
    """Seed default permissions."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Permission).limit(1))
        if result.scalar_one_or_none():
            print("Permissions already seeded")
            return
        
        from app.users.rbac import Permission as PermEnum
        
        for perm in PermEnum:
            module = perm.value.split(":")[0]
            permission = Permission(
                name=perm.name.replace("_", " ").title(),
                code=perm.value,
                module=module,
            )
            session.add(permission)
        
        await session.commit()
        print(f"Seeded {len(PermEnum)} permissions")


async def seed_all():
    """Run all seed functions."""
    print("Starting database seeding...")
    await seed_plans()
    await seed_permissions()
    await seed_platform_owner()
    print("Database seeding complete!")


if __name__ == "__main__":
    asyncio.run(seed_all())
