
import asyncio
import sys
import sys
import os
# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.auth.password import hash_password

async def main():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        print(f"Total users found: {len(users)}")
        for user in users:
            print(f"User: {user.email}, Role: {[r.name for r in user.roles]}, Status: {user.status}")

if __name__ == "__main__":
    asyncio.run(main())
