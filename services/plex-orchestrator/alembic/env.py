"""Alembic migration environment (sync driver; URL from app settings)."""
from __future__ import annotations

import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings  # noqa: E402
from app.infrastructure.persistence.base import Base  # noqa: E402
from app.infrastructure.persistence.active_downloads.model import (  # noqa: F401, E402
    active_download_orm,
)
from app.infrastructure.persistence.antivirus.model import antivirus_orm  # noqa: F401, E402
from app.infrastructure.persistence.blacklist_torrent.model import (  # noqa: F401, E402
    blacklist_torrent_orm,
)
from app.infrastructure.persistence.deferred_downloads.models import (  # noqa: F401, E402
    deferred_download_orm,
)
from app.infrastructure.persistence.plex.models import (  # noqa: F401, E402
    plex_library_path_orm,
    plex_server_config_orm,
    plex_user_orm,
)

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _sync_database_url() -> str:
    url = settings.database_url
    if url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql+asyncpg://", "postgresql://", 1)
    return url


def run_migrations_offline() -> None:
    context.configure(
        url=_sync_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    section = config.get_section(config.config_ini_section) or {}
    section["sqlalchemy.url"] = _sync_database_url()
    connectable = engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
