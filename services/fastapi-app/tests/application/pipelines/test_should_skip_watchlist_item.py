"""Tests for ShouldSkipWatchlistItemQuery."""

from types import SimpleNamespace



import pytest



from app.application.pipelines.watchlist.queries.should_skip_watchlist_item_query import (

    ShouldSkipWatchlistItemQuery,

)

from app.domain.models.media import MediaItem, MediaType

from app.domain.models.watchlist_item_for_user import WatchlistItemForUser





class _FakeIsInLibrary:

    def __init__(self, in_library: bool = False):

        self._in_library = in_library



    async def execute(self, watchlist):

        return self._in_library





class _FakeQueued:

    def __init__(self, queued: bool = False, reason: str | None = None):

        self._queued = queued

        self._reason = reason



    async def execute(self, guid_plex, **kwargs):

        if self._queued:

            return True, self._reason

        return False, None





class _FakeRemove:

    def __init__(self):

        self.removed: list[tuple] = []



    async def execute(self, rating_key, user_token):

        self.removed.append((rating_key, user_token))





def _entry(**kwargs):

    defaults = dict(

        title="Dune",

        guid="plex://movie/1",

        rating_key="123",

        year=2021,

        type=MediaType.MOVIE,

        plex_user_id=7,

        plex_user_token="user-token",

    )

    defaults.update(kwargs)

    return WatchlistItemForUser(

        item=MediaItem(

            guid=defaults["guid"],

            rating_key=defaults["rating_key"],

            title=defaults["title"],

            year=defaults["year"],

            type=defaults["type"],

        ),

        plex_user_id=defaults["plex_user_id"],

        plex_user_token=defaults["plex_user_token"],

    )





@pytest.mark.asyncio

async def test_skips_when_already_in_library():

    remove = _FakeRemove()

    query = ShouldSkipWatchlistItemQuery(

        _FakeIsInLibrary(in_library=True),

        _FakeQueued(),

        remove,

    )

    skip, reason = await query.execute(_entry())

    assert skip is True

    assert reason == "already_in_library"

    assert remove.removed == [("123", "user-token")]





@pytest.mark.asyncio

async def test_skips_when_already_queued():

    remove = _FakeRemove()

    query = ShouldSkipWatchlistItemQuery(

        _FakeIsInLibrary(),

        _FakeQueued(queued=True, reason="already_downloading"),

        remove,

    )

    skip, reason = await query.execute(_entry())

    assert skip is True

    assert reason == "already_downloading"





@pytest.mark.asyncio

async def test_does_not_skip_new_item():

    query = ShouldSkipWatchlistItemQuery(

        _FakeIsInLibrary(),

        _FakeQueued(),

        _FakeRemove(),

    )

    skip, reason = await query.execute(_entry())

    assert skip is False

    assert reason is None

