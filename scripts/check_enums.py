import asyncio
import asyncpg

DB_URL = "postgresql://neondb_owner:npg_1Tw8FvUjGHfE@ep-quiet-breeze-aijreic6-pooler.c-4.us-east-1.aws.neon.tech/neondb?ssl=require"

async def check_enums():
    conn = await asyncpg.connect(DB_URL)
    try:
        print("Checking 'tenantstatus' values:")
        rows = await conn.fetch("SELECT unnest(enum_range(NULL::tenantstatus)) as val")
        for r in rows:
            print(f" - {r['val']}")
            
        print("\nChecking 'tenanttype' values:")
        rows = await conn.fetch("SELECT unnest(enum_range(NULL::tenanttype)) as val")     
        for r in rows:
            print(f" - {r['val']}")
            
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(check_enums())
