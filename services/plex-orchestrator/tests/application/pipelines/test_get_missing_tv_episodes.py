"""Tests for GetMissingTvEpisodesQuery."""
import pytest

from app.application.pipelines.watchlist.queries.get_missing_tv_episodes_query import (
    GetMissingTvEpisodesQuery,
)
from app.domain.models.media import MediaItem, MediaType
from app.domain.models.tv_episode import TvEpisode


class _FakeCatalog:
    async def execute(self, watchlist, user_token, plex_user_token=None):
        return [TvEpisode(season=1, episode=i) for i in range(1, 6)]


class _FakeOwned:
    async def execute(self, show_guid):
        return []


class _FakeEpisodeQueued:
    async def execute(self, plex_guid, title, episode):
        return False

    async def execute_for_watchlist(self, watchlist, episode):
        return False


class _FakeLatestWatched:
    def __init__(self, latest):
        self._latest = latest

    async def execute(self, show_guid):
        return self._latest


def _build_query(latest):
    return GetMissingTvEpisodesQuery(
        _FakeCatalog(),
        _FakeOwned(),
        _FakeEpisodeQueued(),
        _FakeLatestWatched(latest),
    )


@pytest.mark.asyncio
async def test_get_missing_all_when_not_for_download():
    watchlist = MediaItem(guid="plex://show/1", title="Show", type=MediaType.SHOW)
    missing = await _build_query(TvEpisode(season=1, episode=2)).execute(
        watchlist, "token", for_download=False
    )
    assert len(missing) == 5


@pytest.mark.asyncio
async def test_get_missing_for_download_applies_buffer(monkeypatch):
    monkeypatch.setattr(
        "app.application.pipelines.watchlist.queries.get_missing_tv_episodes_query.settings.tv_watchlist_ahead_episodes",
        2,
    )
    query = _build_query(TvEpisode(season=1, episode=2))
    watchlist = MediaItem(guid="plex://show/1", title="Show", type=MediaType.SHOW)
    missing = await query.execute(watchlist, "token", for_download=True)
    assert missing == [
        TvEpisode(season=1, episode=3),
        TvEpisode(season=1, episode=4),
    ]


@pytest.mark.asyncio
async def test_get_missing_for_download_uses_first_catalog_episodes_when_unwatched(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.application.pipelines.watchlist.queries.get_missing_tv_episodes_query.settings.tv_watchlist_ahead_episodes",
        2,
    )
    query = _build_query(None)
    watchlist = MediaItem(guid="plex://show/1", title="Show", type=MediaType.SHOW)
    missing = await query.execute(watchlist, "token", for_download=True)
    assert missing == [
        TvEpisode(season=1, episode=1),
        TvEpisode(season=1, episode=2),
    ]
