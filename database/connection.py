from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config.settings import settings
from database.models import Base

engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
)

async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db() -> None:
    """Initialize database tables and upgrade existing columns if needed."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        if "postgresql" in settings.database_url:
            await conn.execute(
                text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN NOT NULL DEFAULT FALSE;")
            )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency / context helper for database sessions."""
    async with async_session() as session:
        yield session
