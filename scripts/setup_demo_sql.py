import sqlite3
import uuid
import time
from passlib.context import CryptContext

# Setup password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
hashed_password = pwd_context.hash("Admin@123")

def setup_demo_sql():
    print("🚀 Connecting to SQLite database...")
    conn = sqlite3.connect('custos.db')
    cursor = conn.cursor()
    
    # 1. UPSERT Tenant
    tenant_id = str(uuid.uuid4())
    slug = "demo-school"
    
    # Check if exists
    cursor.execute("SELECT id FROM tenants WHERE slug = ?", (slug,))
    row = cursor.fetchone()
    
    if row:
        tenant_id = row[0]
        print(f"✓ Tenant exists: {slug} (ID: {tenant_id})")
    else:
        print(f"Creating tenant: {slug}")
        cursor.execute("""
            INSERT INTO tenants (id, name, slug, email, status, type, is_verified, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (tenant_id, "Demo Public School", slug, "admin@demo-school.edu", "active", "school", 1, time.time(), time.time()))
        print("✅ Tenant Created")

    # 2. UPSERT Student
    email = "student@demo.school"
    
    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    
    if row:
        print(f"✓ User exists: {email}")
        # Update password to be sure
        cursor.execute("UPDATE users SET password_hash = ?, is_active = 1, tenant_id = ? WHERE email = ?", 
                      (hashed_password, tenant_id, email))
        print("✅ User Password Reset to Admin@123")
    else:
        print(f"Creating user: {email}")
        user_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO users (id, email, password_hash, first_name, last_name, is_active, is_verified, tenant_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, email, hashed_password, "Alex", "Chen", 1, 1, tenant_id, time.time(), time.time()))
        print("✅ User Created")

    # 3. Add Role (if tables exist, usually 'users' has roles column or separate table)
    # Checking schema for roles
    try:
        # Try inserting into user_roles if it exists, or update roles JSON
        # Inspect user table columns
        cursor.execute("PRAGMA table_info(users)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if "roles" in columns:
            # It's likely a JSON column or string
            cursor.execute("UPDATE users SET roles = ? WHERE email = ?", ('["student"]', email))
            print("✅ Roles updated")
    except Exception as e:
        print(f"⚠️ Could not update roles: {e}")

    conn.commit()
    conn.close()
    
    print("\n" + "="*40)
    print("LOGIN CREDENTIALS READY")
    print("="*40)
    print(f"School ID: {slug}")
    print(f"Email:     {email}")
    print(f"Password:  Admin@123")
    print("="*40)

if __name__ == "__main__":
    setup_demo_sql()
