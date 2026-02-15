import sqlite3
import uuid
import time

def setup_demo_plaintext():
    print("🚀 Connecting to SQLite database...")
    conn = sqlite3.connect('custos.db')
    cursor = conn.cursor()
    
    # 0. CREATE TABLES (Fallback if Alembic failed)
    print("Checking tables...")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tenants (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        slug TEXT UNIQUE,
        email TEXT,
        phone TEXT,
        type TEXT,
        status TEXT,
        is_verified INTEGER DEFAULT 0,
        country TEXT,
        city TEXT,
        state TEXT,
        timezone TEXT,
        primary_color TEXT,
        settings TEXT,
        created_at REAL,
        updated_at REAL
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        first_name TEXT,
        last_name TEXT,
        is_active INTEGER DEFAULT 1,
        is_verified INTEGER DEFAULT 0,
        tenant_id TEXT,
        roles TEXT,
        permissions TEXT,
        last_login REAL,
        created_at REAL,
        updated_at REAL,
        FOREIGN KEY (tenant_id) REFERENCES tenants (id)
    )
    """)
    print("✅ Tables ensured.")
    
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
            INSERT INTO tenants (id, name, slug, email, status, type, is_verified, created_at, updated_at, primary_color)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (tenant_id, "Demo Public School", slug, "admin@demo-school.edu", "active", "school", 1, time.time(), time.time(), "#4F46E5"))
        print("✅ Tenant Created")

    # 2. UPSERT Student
    email = "student@demo.school"
    # PLAINTEXT PASSWORD (enabled in security.py)
    password_hash = "Admin@123"
    
    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    
    if row:
        print(f"✓ User exists: {email}")
        # Update password to be sure
        cursor.execute("UPDATE users SET password_hash = ?, is_active = 1, tenant_id = ? WHERE email = ?", 
                      (password_hash, tenant_id, email))
        print("✅ User Password Reset to Plaintext: Admin@123")
    else:
        print(f"Creating user: {email}")
        user_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO users (id, email, password_hash, first_name, last_name, is_active, is_verified, tenant_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, email, password_hash, "Alex", "Chen", 1, 1, tenant_id, time.time(), time.time()))
        print("✅ User Created (Plaintext Password)")

    # 3. Add Role
    try:
        # Update roles if column exists (it should after alembic)
        cursor.execute("UPDATE users SET roles = ? WHERE email = ?", ('["student"]', email))
        print("✅ Roles updated")
    except Exception as e:
        print(f"⚠️ Could not update roles (maybe column missing?): {e}")

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
    setup_demo_plaintext()
