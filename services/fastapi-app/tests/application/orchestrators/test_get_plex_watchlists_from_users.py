"""Tests for merging watchlists across Plex users by guid."""
import pytest

from app.application.orchestrators.queries.getPlexWatchlistsFromUsers import (
    GetPlexWatchlistsFromUsers,
)
from app.domain.models.media import MediaItem, MediaType
from app.domain.models.plexUser import PlexUser


class _FakeGetPlexUsers:
    def __init__(self, users):
        self._users = users

    async def execute(self):
        return self._users


class _FakeGetWatchList:
    def __init__(self, by_token: dict):
        self._by_token = by_token

    async def execute(self, token: str):
        return self._by_token[token]


@pytest.mark.asyncio
async def test_merge_deduplicates_by_plex_guid():
    users = [
        PlexUser(id=1, name="a", plex_token="tok-a", active=True),
        PlexUser(id=2, name="b", plex_token="tok-b", active=True),
    ]
    item_a = MediaItem(
        guid="plex://movie/guid1",
        title="Film",
        year=2020,
        type=MediaType.MOVIE,
    )
    item_dup = MediaItem(
        guid="plex://movie/guid1",
        title="Film",
        year=2020,
        type=MediaType.MOVIE,
    )
    item_other = MediaItem(
        guid="plex://movie/guid2",
        title="Other",
        year=2021,
        type=MediaType.MOVIE,
    )
    orchestrator = GetPlexWatchlistsFromUsers(
        _FakeGetPlexUsers(users),
        _FakeGetWatchList(
            {
                "tok-a": [item_a],
                "tok-b": [item_dup, item_other],
            }
        ),
    )

    token, merged = await orchestrator.execute()

    assert token == "tok-a"
    assert len(merged) == 2
    assert {m.guid for m in merged} == {"plex://movie/guid1", "plex://movie/guid2"}
