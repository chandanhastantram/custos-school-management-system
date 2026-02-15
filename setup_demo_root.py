import asyncio
import sys
import os
from uuid import uuid4

# Add current directory to path explicitly
current_dir = os.getcwd()
if current_dir not in sys.path:
    sys.path.append(current_dir)

print(f"Python Path: {sys.path}")

try:
    from app.core.database import AsyncSessionLocal
    from app.core.security import hash_password
    from app.models.tenant import Tenant, TenantStatus, TenantType
    from app.models.user import User, UserStatus
    from sqlalchemy import select
except ImportError as e:
    print(f"❌ Import Error: {e}")
    exit(1)

async def setup_demo():
    print("🚀 Connecting to database...")
    async with AsyncSessionLocal() as session:
        print("✓ Connected.")
        
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
                type=TenantType.SCHOOL,
                primary_color="#4F46E5",
                timezone="Asia/Kolkata"
            )
            session.add(tenant)
            await session.commit()
            await session.refresh(tenant)
            print(f"✅ Created Tenant: {tenant.name} (ID: {tenant.id})")
        else:
            print(f"✓ Tenant exists: {tenant.name} (ID: {tenant.id})")

        # 2. Create Student User
        # Check by email
        result = await session.execute(select(User).where(User.email == "student@demo.school"))
        student = result.scalar_one_or_none()
        
        if not student:
            # Create new
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
            print("✅ Created User from scratch")
        else:
            # FORCE UPDATE PASSWORD
            student.password_hash = hash_password("Admin@123")
            student.tenant_id = tenant.id
            student.is_active = True
            session.add(student)
            await session.commit()
            print("✅ Updated Existing User Password")

        # 3. Create Credentials File
        with open("demo_credentials.txt", "w") as f:
            f.write(f"School ID: {tenant.slug}\n")
            f.write("User: student@demo.school\n")
            f.write("Pass: Admin@123\n")

if __name__ == "__main__":
    asyncio.run(setup_demo())
