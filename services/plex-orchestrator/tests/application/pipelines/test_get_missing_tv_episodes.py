"""Tests for GetMissingTvEpisodesQuery."""
import pytest

from app.application.pipelines.watchlist.queries.get_missing_tv_episodes_query import (
    GetMissingTvEpisodesQuery,
)
from app.domain.models.media import MediaItem, MediaType
from app.domain.models.runtime_settings import RuntimeSettings
from app.domain.models.tv_episode import TvEpisode
from app.application.settings.services.runtime_settings_service import (
    runtime_settings_service,
)


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
    runtime_settings_service._cache = RuntimeSettings(tv_watchlist_ahead_episodes=2)
    query = _build_query(TvEpisode(season=1, episode=2))
    watchlist = MediaItem(guid="plex://show/1", title="Show", type=MediaType.SHOW)
    missing = await query.execute(watchlist, "token", for_download=True)
    assert missing == [
        TvEpisode(season=1, episode=1),
        TvEpisode(season=1, episode=2),
        TvEpisode(season=1, episode=3),
        TvEpisode(season=1, episode=4),
    ]


@pytest.mark.asyncio
async def test_get_missing_for_download_uses_first_catalog_episodes_when_unwatched():
    runtime_settings_service._cache = RuntimeSettings(tv_watchlist_ahead_episodes=2)
    query = _build_query(None)
    watchlist = MediaItem(guid="plex://show/1", title="Show", type=MediaType.SHOW)
    missing = await query.execute(watchlist, "token", for_download=True)
    assert missing == [
        TvEpisode(season=1, episode=1),
        TvEpisode(season=1, episode=2),
    ]


@pytest.mark.asyncio
async def test_get_missing_for_removal_still_counts_queued_episodes():
    class _QueuedEp1:
        async def execute(self, plex_guid, title, episode):
            return episode.season == 1 and episode.episode == 1

        async def execute_for_watchlist(self, watchlist, episode):
            return episode.season == 1 and episode.episode == 1

    query = GetMissingTvEpisodesQuery(
        _FakeCatalog(),
        _FakeOwned(),
        _QueuedEp1(),
        _FakeLatestWatched(None),
    )
    watchlist = MediaItem(guid="plex://show/1", title="Show", type=MediaType.SHOW)
    missing = await query.execute(watchlist, "token", for_download=False)
    assert missing is not None
    assert TvEpisode(season=1, episode=1) in missing
    assert len(missing) == 5


@pytest.mark.asyncio
async def test_get_missing_returns_none_when_catalog_empty():
    class _EmptyCatalog:
        async def execute(self, watchlist, user_token, plex_user_token=None):
            return []

    query = GetMissingTvEpisodesQuery(
        _EmptyCatalog(),
        _FakeOwned(),
        _FakeEpisodeQueued(),
        _FakeLatestWatched(None),
    )
    watchlist = MediaItem(guid="plex://show/1", title="Show", type=MediaType.SHOW)
    missing = await query.execute(watchlist, "token", for_download=False)
    assert missing is None
