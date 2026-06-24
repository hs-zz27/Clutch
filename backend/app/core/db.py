from urllib.parse import urlsplit, urlunsplit
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
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
    connect_args={"ssl": True},   # enforce SSL for Neon
    echo=True,
)
async_session = async_sessionmaker(engine, expire_on_commit=False)