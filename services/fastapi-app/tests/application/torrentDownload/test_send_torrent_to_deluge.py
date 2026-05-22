"""Tests for SendTorrentToDelugeService."""
from unittest.mock import AsyncMock

import pytest

from app.application.torrentDownload.services.sendTorrentToDeluge import (
    SendTorrentToDelugeService,
)
from app.domain.models.torrent import Torrent
from app.domain.models.torrent_search import QualityInfo, TorrentSearchResult


@pytest.mark.asyncio
async def test_execute_returns_torrent_when_found_in_deluge():
    download = AsyncMock()
    get_by_name = AsyncMock(
        return_value=Torrent(hash="abc", file_name="r.mkv")
    )
    service = SendTorrentToDelugeService(download, get_by_name)
    result = TorrentSearchResult(
        guid="prowlarr-1",
        title="Release",
        indexerId=1,
        size=1_000,
        quality_score=10,
        quality_info=QualityInfo(),
    )

    torrent = await service.execute(result, time_added_threshold=3.0, settle_seconds=0)

    download.execute.assert_awaited_once_with(result)
    get_by_name.execute.assert_awaited_once_with("Release", time_added_threshold=3.0)
    assert torrent is not None
    assert torrent.hash == "abc"


@pytest.mark.asyncio
async def test_execute_returns_none_when_deluge_has_no_match():
    download = AsyncMock()
    get_by_name = AsyncMock(return_value=None)
    service = SendTorrentToDelugeService(download, get_by_name)

    torrent = await service.execute(
        TorrentSearchResult(
            title="X",
            guid="g",
            indexerId=1,
            quality_score=1,
            quality_info=QualityInfo(),
        ),
        settle_seconds=0,
    )

    assert torrent is None
