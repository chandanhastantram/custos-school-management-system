import asyncio
import sys
import os
from uuid import uuid4

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.tenant import Tenant, TenantStatus, TenantType
from app.models.user import User, UserStatus
from sqlalchemy import select

async def setup_demo():
    async with AsyncSessionLocal() as session:
        print("🚀 Setting up Demo School...")
        
        # 1. Create Tenant
        result = await session.execute(select(Tenant).where(Tenant.slug == "demo-school"))
        tenant = result.scalar_one_or_none()
        
        if not tenant:
            tenant_id = uuid4()
            tenant = Tenant(
                id=tenant_id,
                name="Demo Public School",
                slug="demo-school",
                email="admin@demo-school.edu",
                status=TenantStatus.ACTIVE,
                is_verified=True,
                type=TenantType.SCHOOL
            )
            session.add(tenant)
            await session.commit()
            await session.refresh(tenant)
            print(f"✅ Created Tenant: {tenant.name} (ID: {tenant.id})")
        else:
            print(f"✓ Tenant already exists: {tenant.name} (ID: {tenant.id})")

        # 2. Create Student User
        result = await session.execute(select(User).where(User.email == "student@demo.school"))
        student = result.scalar_one_or_none()
        
        if not student:
            student = User(
                email="student@demo.school",
                password_hash=hash_password("Admin@123"),
                first_name="Alex",
                last_name="Chen",
                is_active=True,
                is_verified=True,
                tenant_id=tenant.id,
                roles=["student"]
            )
            session.add(student)
            await session.commit()
            print("✅ Created Student: student@demo.school / Admin@123")
        else:
            # Update password just in case
            student.password_hash = hash_password("Admin@123")
            student.tenant_id = tenant.id
            student.is_active = True
            session.add(student)
            await session.commit()
            print("✓ Updated Student: student@demo.school / Admin@123")

        # 3. Create Key Information Output
        print("\n" + "="*40)
        print("LOGIN CREDENTIALS CONFIRMED")
        print("="*40)
        print(f"School ID: {tenant.slug}")
        print("Email:     student@demo.school")
        print("Password:  Admin@123")
        print("="*40)

if __name__ == "__main__":
    asyncio.run(setup_demo())
