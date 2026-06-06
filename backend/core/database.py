import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./fraudlens.db")

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

async def init_db():
    from models.sql.base import Base
    # import all models so Base knows about them before create_all
    import models.sql.user
    import models.sql.account
    import models.sql.case
    import models.sql.transaction
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
