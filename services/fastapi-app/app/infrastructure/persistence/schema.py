"""Create PostgreSQL tables from ORM metadata on startup."""
from __future__ import annotations

import logging

from app.infrastructure.persistence.base import Base
from app.infrastructure.persistence.database import async_engine

# Import ORM modules so tables register on Base.metadata.
from app.infrastructure.persistence.active_downloads.model import active_download_orm  # noqa: F401
from app.infrastructure.persistence.antivirus.model import antivirus_orm  # noqa: F401
from app.infrastructure.persistence.blacklist_torrent.model import blacklist_torrent_orm  # noqa: F401
from app.infrastructure.persistence.deferred_downloads.models import deferred_download_orm  # noqa: F401
from app.infrastructure.persistence.plex.models import plex_library_path_orm  # noqa: F401
from app.infrastructure.persistence.plex.models import plex_user_orm  # noqa: F401
from app.infrastructure.persistence.plex.models import plex_server_config_orm  # noqa: F401

logger = logging.getLogger(__name__)


async def init_database() -> None:
    """Create any missing tables. Safe to run on every startup."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database schema ready (%s tables)", len(Base.metadata.tables))
