"""Tests for ResolveTorrentForIngestQuery."""
from unittest.mock import AsyncMock

import pytest

from app.application.pipelines.ingest.queries.resolve_torrent_for_ingest_query import (
    ResolveTorrentForIngestQuery,
)
from app.domain.errors.deluge import DelugeTorrentNotFoundError
from app.domain.models.active_download import ActiveDownload
from app.domain.models.torrent import Torrent


def _tracked() -> ActiveDownload:
    return ActiveDownload(
        plex_guid="plex://movie/1",
        prowlarr_guid="prowlarr-guid",
        uid="a" * 40,
        title="Tracked",
        type="movie",
    )


@pytest.mark.asyncio
async def test_resolve_prefers_active_download():
    get_active = AsyncMock()
    get_active.execute = AsyncMock(return_value=_tracked())
    get_status = AsyncMock()
    query = ResolveTorrentForIngestQuery(get_active, get_status)

    resolved = await query.execute("a" * 40)

    assert resolved is not None
    assert resolved.is_manual is False
    assert resolved.active_download.title == "Tracked"
    get_status.execute.assert_not_called()


@pytest.mark.asyncio
async def test_resolve_falls_back_to_deluge():
    get_active = AsyncMock()
    get_active.execute = AsyncMock(return_value=None)
    get_status = AsyncMock()
    get_status.execute = AsyncMock(
        return_value=Torrent(
            hash="b" * 40,
            file_name="Manual.Movie.mkv",
            state="Seeding",
            progress=100.0,
        )
    )
    query = ResolveTorrentForIngestQuery(get_active, get_status)

    resolved = await query.execute("B" * 40, title="Manual Movie", media_type="movie")

    assert resolved is not None
    assert resolved.is_manual is True
    assert resolved.active_download.title == "Manual Movie"
    assert resolved.active_download.prowlarr_guid == f"manual:{'b' * 40}"


@pytest.mark.asyncio
async def test_resolve_returns_none_when_missing_everywhere():
    get_active = AsyncMock()
    get_active.execute = AsyncMock(return_value=None)
    get_status = AsyncMock()
    get_status.execute = AsyncMock(side_effect=DelugeTorrentNotFoundError("missing"))
    query = ResolveTorrentForIngestQuery(get_active, get_status)

    resolved = await query.execute("missing")

    assert resolved is None
