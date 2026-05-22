"""Tests for cross-user media identity queue detection."""
import pytest

from app.application.orchestrators.queries.isMediaAlreadyQueuedForDownload import (
    IsMediaAlreadyQueuedForDownloadQuery,
)


class _FakeTorrentRepo:
    def __init__(self, *, identity_match: bool = False):
        self._identity_match = identity_match

    async def is_guid_plex_downloading(self, guid_plex: str) -> bool:
        return False

    async def get_by_guid_prowlarr(self, guid_prowlarr: str):
        return None

    async def has_by_media_identity(self, title, year, media_type) -> bool:
        return self._identity_match


class _FakeDeferredRepo:
    def __init__(self):
        pass

    async def get_pending_by_guid_plex(self, guid_plex: str):
        return None

    async def get_pending_by_guid_prowlarr(self, guid_prowlarr: str):
        return None

    async def get_pending_by_media_identity(self, title, year, media_type):
        return None


@pytest.mark.asyncio
async def test_same_title_year_type_blocks_second_plex_guid():
    query = IsMediaAlreadyQueuedForDownloadQuery(
        _FakeTorrentRepo(identity_match=True),
        _FakeDeferredRepo(),
    )

    queued, reason = await query.execute(
        "plex://movie/other-guid",
        title="Dune",
        year=2021,
        media_type="movie",
    )

    assert queued is True
    assert reason == "same_media_identity_downloading"
