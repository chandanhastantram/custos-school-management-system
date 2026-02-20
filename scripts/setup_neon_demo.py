"""
Setup demo data for Neon PostgreSQL using direct SQL.

Avoids ORM relationship issues by using raw SQL INSERT statements.
"""

import asyncio
import asyncpg
import uuid
import time
from datetime import datetime


async def setup_neon_demo():
    
    print("🚀 Setting up demo data in Neon PostgreSQL...")
    
    # Connection string from .env
    DATABASE_URL = 
    
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        # 1. Check/Create Tenant
        tenant_id = str(uuid.uuid4())
        slug = "demo-school"
        
        existing_tenant = await conn.fetchrow(
            "SELECT id FROM tenants WHERE slug = $1", slug
        )
        
        if existing_tenant:
            tenant_id = existing_tenant['id']
            print(f"✓ Tenant exists: {slug} (ID: {tenant_id})")
        else:
            print(f"Creating tenant: {slug}")
            now = datetime.utcnow()
            # Note: Enum values in Python are lowercase ("active", "school")
            # but we need to check what Alembic created in the database
            await conn.execute("""
                INSERT INTO tenants (
                    id, name, slug, email, status, type, is_verified, 
                    created_at, updated_at, primary_color
                )
                VALUES ($1, $2, $3, $4, 'active', 'school', $5, $6, $7, $8)
            """, tenant_id, "Demo Public School", slug, "admin@demo-school.edu",
                True, now, now, "#4F46E5")
            print("✅ Tenant Created")
        
        # 2. Check/Create User
        email = "student@demo.school"
        password_hash = "Admin@123"  # Plaintext (enabled in security.py)
        
        existing_user = await conn.fetchrow(
            "SELECT id FROM users WHERE email = $1", email
        )
        
        if existing_user:
            print(f"✓ User exists: {email}")
            # Update password
            await conn.execute("""
                UPDATE users 
                SET password_hash = $1, is_active = $2, tenant_id = $3
                WHERE email = $4
            """, password_hash, True, tenant_id, email)
            print("✅ User Password Reset")
        else:
            print(f"Creating user: {email}")
            user_id = str(uuid.uuid4())
            now = datetime.utcnow()
            await conn.execute("""
                INSERT INTO users (
                    id, email, password_hash, first_name, last_name,
                    is_active, is_verified, tenant_id, roles, created_at, updated_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """, user_id, email, password_hash, "Alex", "Chen",
                True, True, tenant_id, '["student"]', now, now)
            print("✅ User Created")
        
        print("\n" + "="*40)
        print("NEON DATABASE READY")
        print("="*40)
        print(f"School ID: {slug}")
        print(f"Email:     {email}")
        print(f"Password:  {password_hash}")
        print("="*40)
        
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(setup_neon_demo())
