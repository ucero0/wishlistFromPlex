"""Tests for merging watchlists across Plex users by guid."""

import pytest



from app.application.pipelines.watchlist.queries.get_watchlists_for_active_users_query import (

    GetWatchlistsForActiveUsersQuery,

)

from app.domain.models.media import MediaItem, MediaType

from app.domain.models.plex_user import PlexUser





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





@pytest.mark.asyncio

async def test_merge_deduplicates_by_plex_guid_and_keeps_user_context():

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

    query = GetWatchlistsForActiveUsersQuery(

        _FakeGetPlexUsers(users),

        _FakeGetWatchlist(

            {

                "tok-a": [item_a],

                "tok-b": [item_dup, item_other],

            }

        ),

    )



    merged = await query.execute()



    assert len(merged) == 2

    assert {entry.item.guid for entry in merged} == {

        "plex://movie/guid1",

        "plex://movie/guid2",

    }

    guid1 = next(e for e in merged if e.item.guid == "plex://movie/guid1")

    assert guid1.plex_user_id == 1

    assert guid1.plex_user_token == "tok-a"

    guid2 = next(e for e in merged if e.item.guid == "plex://movie/guid2")

    assert guid2.plex_user_id == 2

    assert guid2.plex_user_token == "tok-b"

