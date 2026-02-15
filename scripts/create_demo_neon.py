"""
Create demo tenant and user in Neon database using application ORM.

This uses the proper application models and services.
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.getcwd())

# Import after path setup
from app.core.database import AsyncSessionLocal
from app.tenants.models import Tenant, TenantStatus, TenantType
from app.users.models import User
from sqlalchemy import select


async def create_demo_data():
    """Create demo tenant and user."""
    print("🚀 Creating demo data in Neon PostgreSQL...")
    
    async with AsyncSessionLocal() as db:
        try:
            # 1. Create/Get Tenant
            result = await db.execute(
                select(Tenant).where(Tenant.slug == "demo-school")
            )
            tenant = result.scalar_one_or_none()
            
            if not tenant:
                print("Creating tenant: demo-school")
                tenant = Tenant(
                    name="Demo Public School",
                    slug="demo-school",
                    email="admin@demo-school.edu",
                    status=TenantStatus.ACTIVE,
                    type=TenantType.SCHOOL,
                    is_verified=True,
                    primary_color="#4F46E5",
                )
                db.add(tenant)
                await db.flush()  # Get the ID
                print(f"✅ Tenant Created (ID: {tenant.id})")
            else:
                print(f"✓ Tenant exists: {tenant.slug} (ID: {tenant.id})")
            
            # 2. Create/Get User
            result = await db.execute(
                select(User).where(User.email == "student@demo.school")
            )
            user = result.scalar_one_or_none()
            
            if not user:
                print("Creating user: student@demo.school")
                user = User(
                    email="student@demo.school",
                    password_hash="Admin@123",  # Plaintext (enabled in security.py)
                    first_name="Alex",
                    last_name="Chen",
                    is_active=True,
                    is_verified=True,
                    tenant_id=tenant.id,
                    roles=["student"],
                )
                db.add(user)
                print("✅ User Created")
            else:
                print(f"✓ User exists: {user.email}")
                # Update password
                user.password_hash = "Admin@123"
                user.is_active = True
                user.tenant_id = tenant.id
                print("✅ User Password Reset")
            
            await db.commit()
            
            print("\n" + "="*40)
            print("NEON DATABASE READY")
            print("="*40)
            print(f"School ID: demo-school")
            print(f"Email:     student@demo.school")
            print(f"Password:  Admin@123")
            print("="*40)
            
        except Exception as e:
            print(f"❌ Error: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(create_demo_data())
