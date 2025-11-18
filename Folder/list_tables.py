import asyncio
from sqlalchemy import text
from database import AsyncSessionLocal

async def main():
    async with AsyncSessionLocal() as s:
        result = await s.execute(
            text("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY 1")
        )
        print([row[0] for row in result.fetchall()])

if __name__ == "__main__":
    asyncio.run(main())
