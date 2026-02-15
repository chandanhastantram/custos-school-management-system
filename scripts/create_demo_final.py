"""
Final, schema-compliant setup script for Neon PostgreSQL.
Correctly handles User-Role many-to-many relationship.
"""

import asyncio
import asyncpg
import uuid
import json

# Configuration
DB_URL = "postgresql://neondb_owner:npg_1Tw8FvUjGHfE@ep-quiet-breeze-aijreic6-pooler.c-4.us-east-1.aws.neon.tech/neondb?ssl=require"

async def main():
    print("🚀 Creating Demo Data via Direct SQL...")
    
    conn = await asyncpg.connect(DB_URL)
    try:
        # 1. Tenant
        slug = "demo-school"
        tenant_id = str(uuid.uuid4())
        
        row = await conn.fetchrow("SELECT id FROM tenants WHERE slug = $1", slug)
        if row:
            print(f"✓ Tenant '{slug}' exists.")
            tenant_id = str(row['id'])
        else:
            print(f"Creating tenant '{slug}'...")
            await conn.execute("""
                INSERT INTO tenants (
                    id, name, slug, email, status, type, is_verified, 
                    created_at, updated_at, primary_color, secondary_color, country, city,
                    timezone, locale, date_format, is_deleted
                ) VALUES (
                    $1, 'Demo Public School', $2, 'admin@demo-school.edu', 
                    'ACTIVE', 'SCHOOL', true, now(), now(), 
                    '#4F46E5', '#3B82F6', 'India', 'Mumbai',
                    'Asia/Kolkata', 'en-IN', 'DD/MM/YYYY', false
                )
            """, tenant_id, slug)
            print("✅ Tenant Created")

        # 2. User
        email = "student@demo.school"
        password = "Admin@123" 
        user_id = str(uuid.uuid4())
        
        user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", email)
        if user:
            print(f"✓ User '{email}' exists.")
            user_id = str(user['id'])
            await conn.execute("""
                UPDATE users SET 
                    password_hash = $1, 
                    status = 'ACTIVE',
                    is_email_verified = true,
                    tenant_id = $2::uuid,
                    is_deleted = false
                WHERE email = $3
            """, password, tenant_id, email)
            print("✅ User Updated")
        else:
            print(f"Creating user '{email}'...")
            await conn.execute("""
                INSERT INTO users (
                    id, email, password_hash, first_name, last_name, 
                    status, is_email_verified, tenant_id, 
                    created_at, updated_at,
                    is_deleted, preferences, failed_login_attempts
                ) VALUES (
                    $1, $2, $3, 'Alex', 'Chen', 
                    'ACTIVE', true, $4::uuid, 
                    now(), now(),
                    false, '{}', 0
                )
            """, user_id, email, password, tenant_id)
            print("✅ User Created")

        # 3. Role
        role_code = "student"
        role_id = str(uuid.uuid4())
        
        role = await conn.fetchrow("SELECT id FROM roles WHERE code = $1 AND tenant_id = $2::uuid", role_code, tenant_id)
        if role:
             role_id = str(role['id'])
        else:
             print(f"Creating role '{role_code}'...")
             await conn.execute("""
                INSERT INTO roles (
                    id, name, code, description, tenant_id, is_system, is_active,
                    created_at, updated_at, is_deleted
                ) VALUES (
                    $1, 'Student', $2, 'Student Role', $3::uuid, true, true,
                    now(), now(), false
                )
             """, role_id, role_code, tenant_id)
             print("✅ Role Created")
             
        # 4. User-Role Association
        # Check if exists
        assoc = await conn.fetchrow("SELECT user_id FROM user_roles WHERE user_id = $1::uuid AND role_id = $2::uuid", user_id, role_id)
        if not assoc:
            await conn.execute("""
                INSERT INTO user_roles (user_id, role_id) VALUES ($1::uuid, $2::uuid)
            """, user_id, role_id)
            print("✅ User-Role Assigned")

        print("\n" + "="*50)
        print("🎉 NEON SETUP COMPLETE")
        print("="*50)
        print("School ID: demo-school")
        print("Email:     student@demo.school")
        print("Password:  Admin@123")
        print("="*50)

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
