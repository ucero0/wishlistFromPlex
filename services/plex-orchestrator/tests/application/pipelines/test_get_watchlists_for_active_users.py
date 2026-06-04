"""Tests for merging watchlists across Plex and TMDB users."""
import pytest

from app.application.pipelines.watchlist.queries.get_watchlists_for_active_users_query import (
    GetWatchlistsForActiveUsersQuery,
)
from app.domain.models.media import MediaItem, MediaType
from app.domain.models.plex_user import PlexUser
from app.domain.models.tmdb_user import TmdbUser
from app.domain.models.watchlist_source import WatchlistSource


class _FakeGetPlexUsers:
    def __init__(self, users):
        self._users = users

    async def execute(self):
        return self._users


class _FakeGetWatchlist:
    def __init__(self, by_token: dict):
        self._by_token = by_token

    async def execute(self, token: str):
        return self._by_token[token]


class _FakeGetTmdbUsers:
    def __init__(self, users):
        self._users = users

    async def execute(self):
        return self._users


class _FakeGetTmdbWatchlist:
    def __init__(self, by_account: dict):
        self._by_account = by_account

    async def execute(self, account_id: int, access_token: str):
        return self._by_account[(account_id, access_token)]


@pytest.mark.asyncio
async def test_merge_deduplicates_by_guid_and_includes_tmdb_users():
    plex_users = [PlexUser(id=1, name="a", plex_token="tok-a", active=True)]
    tmdb_users = [
        TmdbUser(id=2, name="tmdb-user", account_id=99, access_token="tmdb-tok", active=True)
    ]
    plex_item = MediaItem(
        guid="plex://movie/guid1",
        title="Film",
        year=2020,
        type=MediaType.MOVIE,
    )
    tmdb_item = MediaItem(
        guid="tmdb://movie/550",
        title="Fight Club",
        year=1999,
        type=MediaType.MOVIE,
    )
    query = GetWatchlistsForActiveUsersQuery(
        _FakeGetPlexUsers(plex_users),
        _FakeGetWatchlist({"tok-a": [plex_item]}),
        _FakeGetTmdbUsers(tmdb_users),
        _FakeGetTmdbWatchlist({(99, "tmdb-tok"): [tmdb_item]}),
    )

    merged = await query.execute()

    assert len(merged) == 2
    plex_entry = next(e for e in merged if e.source == WatchlistSource.PLEX)
    tmdb_entry = next(e for e in merged if e.source == WatchlistSource.TMDB)
    assert plex_entry.plex_user_id == 1
    assert tmdb_entry.tmdb_user_id == 2
    assert tmdb_entry.tmdb_account_id == 99


class _FailingTmdbWatchlist:
    def __init__(self, by_account: dict, fail_accounts: set[int]):
        self._by_account = by_account
        self._fail_accounts = fail_accounts

    async def execute(self, account_id: int, access_token: str):
        if account_id in self._fail_accounts:
            raise TimeoutError(f"get watchlist for account {account_id} timed out")
        return self._by_account[(account_id, access_token)]


@pytest.mark.asyncio
async def test_continues_when_one_tmdb_user_watchlist_fails():
    plex_users = [PlexUser(id=1, name="plex", plex_token="tok-a", active=True)]
    tmdb_users = [
        TmdbUser(id=2, name="bad", account_id=1, access_token="bad-tok", active=True),
        TmdbUser(id=3, name="good", account_id=99, access_token="good-tok", active=True),
    ]
    plex_item = MediaItem(
        guid="plex://movie/guid1",
        title="Film",
        year=2020,
        type=MediaType.MOVIE,
    )
    tmdb_item = MediaItem(
        guid="tmdb://movie/550",
        title="Fight Club",
        year=1999,
        type=MediaType.MOVIE,
    )
    query = GetWatchlistsForActiveUsersQuery(
        _FakeGetPlexUsers(plex_users),
        _FakeGetWatchlist({"tok-a": [plex_item]}),
        _FakeGetTmdbUsers(tmdb_users),
        _FailingTmdbWatchlist({(99, "good-tok"): [tmdb_item]}, fail_accounts={1}),
    )

    merged = await query.execute()

    assert len(merged) == 2
    assert any(e.source == WatchlistSource.PLEX for e in merged)
    assert any(e.source == WatchlistSource.TMDB and e.tmdb_account_id == 99 for e in merged)
