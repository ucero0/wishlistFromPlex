"""Tests for GetShowCatalogEpisodesQuery (Plex first, TMDB fallback)."""
import pytest

from app.application.plex.queries.get_show_catalog_episodes_query import (
    GetShowCatalogEpisodesQuery,
)
from app.domain.models.media import MediaItem, MediaType
from app.domain.models.tv_episode import TvEpisode


class _FakeDiscoverCatalog:
    def __init__(self, episodes: list[TvEpisode] | None = None):
        self._episodes = episodes or []
        self.calls: list[tuple[str, str]] = []

    async def execute(self, rating_key: str, user_token: str):
        self.calls.append((rating_key, user_token))
        return self._episodes


class _FakeServerCatalog:
    def __init__(self, episodes: list[TvEpisode] | None = None):
        self._episodes = episodes or []
        self.calls: list[str] = []

    async def execute(self, show_guid: str):
        self.calls.append(show_guid)
        return self._episodes


class _FakeResolveTmdbTvId:
    def __init__(self, tmdb_id: int | None):
        self._tmdb_id = tmdb_id

    async def execute(self, watchlist, user_token):
        return self._tmdb_id


class _FakeTmdbCatalog:
    def __init__(self, episodes: list[TvEpisode]):
        self._episodes = episodes
        self.calls: list[int] = []

    async def execute(self, tmdb_tv_id: int):
        self.calls.append(tmdb_tv_id)
        return self._episodes


def _query(
    discover: _FakeDiscoverCatalog,
    server: _FakeServerCatalog,
    tmdb_id: int | None,
    tmdb_eps: list[TvEpisode],
) -> GetShowCatalogEpisodesQuery:
    return GetShowCatalogEpisodesQuery(
        discover,
        server,
        _FakeResolveTmdbTvId(tmdb_id),
        _FakeTmdbCatalog(tmdb_eps),
    )


@pytest.mark.asyncio
async def test_prefers_plex_discover_for_plex_watchlist_show():
    discover = _FakeDiscoverCatalog([TvEpisode(season=1, episode=1)])
    server = _FakeServerCatalog([TvEpisode(season=5, episode=1)])
    query = _query(discover, server, 4556, [TvEpisode(season=9, episode=1)])
    watchlist = MediaItem(
        guid="plex://show/abc123",
        rating_key="abc123",
        title="Scrubs",
        type=MediaType.SHOW,
    )
    episodes = await query.execute(watchlist, "plex-token")
    assert episodes == [TvEpisode(season=1, episode=1)]
    assert discover.calls == [("abc123", "plex-token")]
    assert server.calls == []


@pytest.mark.asyncio
async def test_tmdb_watchlist_uses_tmdb_catalog_not_partial_plex_server():
    discover = _FakeDiscoverCatalog([])
    server = _FakeServerCatalog([TvEpisode(season=1, episode=1)])
    tmdb_eps = [TvEpisode(season=1, episode=i) for i in range(1, 6)]
    query = _query(discover, server, 1434, tmdb_eps)
    watchlist = MediaItem(
        guid="tmdb://tv/1434",
        title="Family Guy",
        type=MediaType.SHOW,
        plex_library_guid="plex://show/family-guy",
        rating_key="7205",
    )
    episodes = await query.execute(watchlist, "tmdb-token", plex_user_token="plex-token")
    assert episodes == tmdb_eps
    assert server.calls == []
    assert discover.calls == []


@pytest.mark.asyncio
async def test_tmdb_watchlist_falls_back_to_tmdb_when_discover_empty():
    discover = _FakeDiscoverCatalog([])
    server = _FakeServerCatalog([TvEpisode(season=1, episode=1)])
    tmdb_eps = [TvEpisode(season=1, episode=i) for i in range(1, 4)]
    query = _query(discover, server, 1434, tmdb_eps)
    watchlist = MediaItem(
        guid="tmdb://tv/1434",
        title="Family Guy",
        type=MediaType.SHOW,
        plex_library_guid="plex://show/family-guy",
    )
    episodes = await query.execute(watchlist, "tmdb-token")
    assert episodes == tmdb_eps
    assert server.calls == []


@pytest.mark.asyncio
async def test_falls_back_to_tmdb_when_plex_has_no_catalog():
    discover = _FakeDiscoverCatalog([])
    server = _FakeServerCatalog([])
    tmdb = [TvEpisode(season=1, episode=1)]
    query = _query(discover, server, 1399, tmdb)
    watchlist = MediaItem(
        guid="tmdb://tv/1399",
        title="Game of Thrones",
        type=MediaType.SHOW,
    )
    episodes = await query.execute(watchlist, "token")
    assert episodes == tmdb
