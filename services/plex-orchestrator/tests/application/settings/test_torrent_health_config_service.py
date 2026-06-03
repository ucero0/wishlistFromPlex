"""Tests for DB-backed torrent health config."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.application.settings.services.torrent_health_config_service import (
    TorrentHealthConfigService,
)
from app.domain.models.torrent_health_config import (
    TorrentHealthConfig,
    TorrentHealthConfigUpdate,
)


@pytest.mark.asyncio
async def test_update_config_persists_patch():
    existing = TorrentHealthConfig(grace_hours=6)
    updated = TorrentHealthConfig(grace_hours=2)
    repo = MagicMock()
    repo.get_config = AsyncMock(return_value=existing)
    repo.update_config = AsyncMock(return_value=updated)

    session_cm = MagicMock()
    session = MagicMock()
    session_cm.__aenter__ = AsyncMock(return_value=session)
    session_cm.__aexit__ = AsyncMock(return_value=None)

    service = TorrentHealthConfigService()
    with patch(
        "app.application.settings.services.torrent_health_config_service.async_session_scope",
        return_value=session_cm,
    ), patch(
        "app.application.settings.services.torrent_health_config_service.TorrentHealthConfigRepository",
        return_value=repo,
    ):
        result = await service.update_config(TorrentHealthConfigUpdate(grace_hours=2))

    assert result.grace_hours == 2
    repo.update_config.assert_awaited_once()
