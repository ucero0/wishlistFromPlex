"""Apply database schema via Alembic migrations."""
from __future__ import annotations

import logging
from pathlib import Path

from alembic import command
from alembic.config import Config

logger = logging.getLogger(__name__)

_ALEMBIC_INI = Path(__file__).resolve().parents[3] / "alembic.ini"


def init_database() -> None:
    """Upgrade to the latest Alembic revision (idempotent)."""
    cfg = Config(str(_ALEMBIC_INI))
    command.upgrade(cfg, "head")
    logger.info("Database migrations applied (alembic head)")
