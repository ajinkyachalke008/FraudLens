import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from backend.database import SQLALCHEMY_DATABASE_URL

async def check_postgres():
    try:
        engine = create_async_engine(SQLALCHEMY_DATABASE_URL)
        async with engine.connect() as conn:
            print("PostgreSQL connection successful!")
    except Exception as e:
        print(f"PostgreSQL connection failed: {e}")

if __name__ == "__main__":
    print("Running health checks...")
    asyncio.run(check_postgres())
