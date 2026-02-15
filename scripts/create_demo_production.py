"""
Production-safe setup script for Neon PostgreSQL.
Uses API for Tenant (safe) and SQL for User (privileged).
"""

import asyncio
import json
import urllib.request
import urllib.error
import asyncpg
import uuid

# Configuration
API_URL = "http://localhost:8000/api/v1/tenants"
DB_URL = "postgresql://neondb_owner:npg_1Tw8FvUjGHfE@ep-quiet-breeze-aijreic6-pooler.c-4.us-east-1.aws.neon.tech/neondb?ssl=require"

def create_tenant_via_api():
    """Create tenant using the running API to ensure all business logic runs."""
    print("🚀 Step 1: Creating Tenant via API...")
    
    data = {
        "name": "Demo Public School",
        "slug": "demo-school",
        "email": "admin@demo-school.edu",
        "type": "school",
        "phone": "+91 9876543210", 
        "primary_color": "#4F46E5",
        "country": "India",
        "city": "Mumbai"
    }
    
    req = urllib.request.Request(
        API_URL, 
        data=json.dumps(data).encode('utf-8'), 
        headers={'Content-Type': 'application/json'}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            print(f"✅ Tenant Created: {result['name']} ({result['id']})")
            return result['id']
            
    except urllib.error.HTTPError as e:
        if e.code == 400: # Likely conflict/validation error
            print(f"⚠️ API Info: {e.read().decode()}")
            return None # Will fetch via SQL
        print(f"❌ API Error: {e}")
        return None
    except Exception as e:
        print(f"❌ Connection Error (is backend running?): {e}")
        return None

async def create_user_via_sql(tenant_id):
    """Create admin user directly in DB since public registration is closed."""
    print("\n🚀 Step 2: Creating User via SQL...")
    
    conn = await asyncpg.connect(DB_URL)
    try:
        # 1. Fetch Tenant ID if missing
        if not tenant_id:
            print("   Fetching tenant ID from DB...")
            row = await conn.fetchrow("SELECT id FROM tenants WHERE slug = $1", 'demo-school')
            if row:
                tenant_id = str(row['id'])
                print(f"   Found Tenant ID: {tenant_id}")
            else:
                print("❌ Fatal: Tenant 'demo-school' not found! API creation failed?")
                return

        # 2. Upsert User
        email = "student@demo.school"
        password = "Admin@123" # Plaintext enabled
        
        user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", email)
        
        if user:
            print(f"   User {email} exists. Updating...")
            await conn.execute("""
                UPDATE users 
                SET password_hash = $1, 
                    is_active = true, 
                    tenant_id = $2::uuid,
                    status = 'active',
                    roles = '["student"]'
                WHERE email = $3
            """, password, tenant_id, email)
            print("✅ User Password Reset & Activated")
        else:
            print(f"   Creating new user {email}...")
            await conn.execute("""
                INSERT INTO users (
                    id, email, password_hash, first_name, last_name, 
                    is_active, is_verified, tenant_id, 
                    roles, status, created_at, updated_at
                ) VALUES (
                    gen_random_uuid(), $1, $2, 'Alex', 'Chen', 
                    true, true, $3::uuid, 
                    '["student"]', 'active', now(), now()
                )
            """, email, password, tenant_id)
            print("✅ User Created")
            
        print("\n" + "="*50)
        print("🎉 SUCCESS! LOGIN CREDENTIALS:")
        print("="*50)
        print("School ID: demo-school")
        print("Email:     student@demo.school")
        print("Password:  Admin@123")
        print("="*50)
            
    except Exception as e:
        print(f"❌ SQL Error: {e}")
    finally:
        await conn.close()

def main():
    # 1. API Call (Sync)
    tid = create_tenant_via_api()
    
    # 2. SQL Call (Async)
    asyncio.run(create_user_via_sql(tid))

if __name__ == "__main__":
    main()
