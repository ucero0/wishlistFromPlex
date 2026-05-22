"""Verify required Alembic revisions are applied before serving traffic."""
from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Current head revision (011 deferred_torrent_downloads). Update when adding migrations.
REQUIRED_ALEMBIC_REVISION = "e1f2a3b4c5d6"
REQUIRED_TABLES = ("deferred_torrent_downloads", "plex_library_paths")


async def verify_database_schema(session: AsyncSession) -> None:
    """
    Fail fast when migrations were not applied (e.g. after deploy without entrypoint).

    Logs a warning if revision is behind head; raises if critical tables are missing.
    """
    for table in REQUIRED_TABLES:
        result = await session.execute(
            text(
                "SELECT 1 FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_name = :name"
            ),
            {"name": table},
        )
        if result.scalar() is None:
            raise RuntimeError(
                f"Database table '{table}' is missing. "
                f"Run: alembic -c migrations/alembic.ini upgrade head"
            )

    rev_result = await session.execute(
        text("SELECT version_num FROM alembic_version LIMIT 1")
    )
    current = rev_result.scalar_one_or_none()
    if current is None:
        logger.warning(
            "alembic_version table is empty; schema tables exist but revision is unknown"
        )
        return

    if current != REQUIRED_ALEMBIC_REVISION:
        logger.warning(
            "Database Alembic revision is %s (expected head %s). "
            "Run migrations if you see missing columns or queue errors.",
            current,
            REQUIRED_ALEMBIC_REVISION,
        )
