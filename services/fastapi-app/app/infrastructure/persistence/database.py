# app/infrastructure/persistence/database.py
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine
from app.core.config import settings

# Ensure we're using an async driver for PostgreSQL
database_url = settings.database_url
async_database_url = database_url
if database_url.startswith("postgresql://") and not database_url.startswith("postgresql+asyncpg://"):
    # Convert postgresql:// to postgresql+asyncpg:// for async operations
    async_database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

engine_kwargs = {"pool_pre_ping": True}

if database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
else:
    connect_args = {}
    engine_kwargs.update({
        "pool_size": 5,
        "max_overflow": 10,
    })

# Async engine for async operations
async_engine = create_async_engine(
    async_database_url,
    connect_args=connect_args,
    **engine_kwargs
)

# Sync engine for sync operations (repositories that use Session)
sync_database_url = database_url
if database_url.startswith("postgresql+asyncpg://"):
    # Convert back to postgresql:// for sync operations
    sync_database_url = database_url.replace("postgresql+asyncpg://", "postgresql://", 1)

sync_engine = create_engine(
    sync_database_url,
    connect_args=connect_args,
    **engine_kwargs
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    autoflush=False,
    expire_on_commit=False,
)

SessionLocal = sessionmaker(
    bind=sync_engine,
    autoflush=False,
    expire_on_commit=False,
)

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

def get_db_sync() -> Session:
    """Get a synchronous database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()