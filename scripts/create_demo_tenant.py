"""Quick script to create demo tenant"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import asyncio
from uuid import uuid4
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.tenant import Tenant, TenantStatus, TenantType
from app.models.user import User, UserStatus

async def main():
    async with AsyncSessionLocal() as session:
        # Check if tenant exists
        from sqlalchemy import select
        result = await session.execute(select(Tenant).where(Tenant.slug == "demo-school"))
        existing = result.scalar_one_or_none()
        
        if existing:
            print(f"✓ Tenant 'demo-school' already exists (ID: {existing.id})")
            print(f"  Name: {existing.name}")
            return
        
        # Create tenant
        tenant_id = uuid4()
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
        await session.flush()
        
        print(f"✓ Created tenant: {tenant.name} (ID: {tenant.id})")
        print(f"  Slug: {tenant.slug}")
        print(f"  Tenant ID for login: {tenant.id}")
        
        await session.commit()

if __name__ == "__main__":
    asyncio.run(main())
