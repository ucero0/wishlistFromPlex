"""Tests for ResolveTmdbTvIdForShowQuery."""
from types import SimpleNamespace

import pytest

from app.application.tmdb.queries.resolve_tmdb_tv_id_for_show_query import (
    ResolveTmdbTvIdForShowQuery,
)
from app.domain.models.media import MediaItem, MediaType


class _FakeDiscoverMetadata:
    def __init__(self, guids: list[str] | None = None):
        self._guids = guids or []
        self.calls: list[tuple[str, str]] = []

    async def get_metadata_guids(self, rating_key: str, user_token: str) -> list[str]:
        self.calls.append((rating_key, user_token))
        return self._guids


class _FakeTmdbClient:
    def __init__(self, tv_id: int | None = None):
        self._tv_id = tv_id
        self.search_calls: list[tuple] = []

    async def search(self, title, year=None, media_type="movie"):
        self.search_calls.append((title, year, media_type))
        if self._tv_id is None:
            return None
        return SimpleNamespace(id=self._tv_id)


@pytest.mark.asyncio
async def test_resolves_from_tmdb_guid():
    query = ResolveTmdbTvIdForShowQuery(
        _FakeTmdbClient(),
        _FakeDiscoverMetadata(),
    )
    watchlist = MediaItem(guid="tmdb://tv/1399", title="GoT", type=MediaType.SHOW)
    assert await query.execute(watchlist, "token") == 1399


@pytest.mark.asyncio
async def test_resolves_from_plex_discover_guids():
    discover = _FakeDiscoverMetadata(
        ["plex://show/123", "com.plexapp.agents.themoviedb://tv/456?lang=en"]
    )
    query = ResolveTmdbTvIdForShowQuery(_FakeTmdbClient(), discover)
    watchlist = MediaItem(
        guid="plex://show/123",
        rating_key="123",
        title="Breaking Bad",
        type=MediaType.SHOW,
    )
    assert await query.execute(watchlist, "token") == 456
    assert discover.calls == [("123", "token")]


@pytest.mark.asyncio
async def test_falls_back_to_tmdb_search():
    client = _FakeTmdbClient(tv_id=789)
    query = ResolveTmdbTvIdForShowQuery(client, _FakeDiscoverMetadata())
    watchlist = MediaItem(
        guid="plex://show/999",
        rating_key="999",
        title="Scrubs",
        year=2001,
        type=MediaType.SHOW,
    )
    assert await query.execute(watchlist, "token") == 789
    assert client.search_calls == [("Scrubs", 2001, "tv")]
