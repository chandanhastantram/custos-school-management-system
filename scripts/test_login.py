"""
Script to test login and print exact error.
"""
import httpx
import asyncio

API_URL = "http://localhost:8000/api/v1/auth/login"
TENANT_ID = "demo-school"

async def get_tenant_id():
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"http://localhost:8000/api/v1/tenants/slug/{TENANT_ID}")
            if resp.status_code == 200:
                return resp.json()['id']
        except Exception:
            pass
    return None

async def test_login():
    t_id = await get_tenant_id()
    if not t_id:
        print(f"❌ Could not find tenant {TENANT_ID}")
        return

    print(f"Tenant ID: {t_id}")
    
    payload = {
        "email": "student@demo.school",
        "password": "Admin@123"
    }
    
    headers = {
        "X-Tenant-ID": t_id,
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(API_URL, json=payload, headers=headers)
            print(f"Status: {resp.status_code}")
            print(f"Response: {resp.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_login())
