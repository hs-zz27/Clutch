from urllib.parse import urlsplit, urlunsplit
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    pass


def _to_asyncpg(url: str) -> str:
    parts = urlsplit(url)
    scheme = "postgresql+asyncpg"
    # drop sslmode & channel_binding; asyncpg handles SSL via connect_args
    return urlunsplit((scheme, parts.netloc, parts.path, "", ""))


engine = create_async_engine(
    _to_asyncpg(settings.DATABASE_URL),
    connect_args={
        "ssl": True,  # enforce SSL for Neon
        # Neon's pooled endpoint runs pgbouncer in transaction mode, which does
        # not support server-side prepared statements. Disabling asyncpg's
        # statement cache avoids "prepared statement does not exist" errors.
        "statement_cache_size": 0,
    },
    echo=settings.SQL_ECHO,
    pool_pre_ping=True,  # transparently replace stale/dropped Neon connections
    pool_recycle=1800,   # recycle connections every 30 minutes
    pool_size=5,
    max_overflow=10,
)

async_session = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
        except Exception:
            # never leave a half-applied transaction behind on a failed request
            await session.rollback()
            raise
