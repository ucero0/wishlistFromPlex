"""Shared fixtures for repository integration tests."""
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.infrastructure.persistence.antivirus.model.antivirus_orm import AntivirusItem
from app.infrastructure.persistence.base import Base
from app.infrastructure.persistence.blacklist_torrent.model.blacklist_torrent_orm import (
    BlacklistTorrentOrm,
)
from app.infrastructure.persistence.deferred_downloads.models.deferred_download_orm import (
    DeferredDownloadOrm,
)
from app.infrastructure.persistence.plex.models.plex_library_path_orm import PlexLibraryPathOrm
from app.infrastructure.persistence.plex.models.plex_user_orm import PlexUserOrm
from app.infrastructure.persistence.active_downloads.model.active_download_orm import ActiveDownloadOrm


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )
    async with session_factory() as session:
        yield session

    await engine.dispose()
