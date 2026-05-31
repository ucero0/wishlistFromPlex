"""Tests for ShouldSkipWatchlistItemQuery."""

from types import SimpleNamespace



import pytest



from app.application.pipelines.watchlist.queries.should_skip_watchlist_item_query import (

    ShouldSkipWatchlistItemQuery,

)

from app.application.pipelines.watchlist.use_cases.remove_watchlist_entry_use_case import (
    RemoveWatchlistEntryUseCase,
)

from app.domain.models.media import MediaItem, MediaType

from app.domain.models.tv_episode import TvEpisode

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





class _FakeGetMissingTvEpisodes:
    def __init__(self, missing=None):
        self._missing = missing if missing is not None else [TvEpisode(season=1, episode=1)]

    async def execute(self, watchlist, user_token, *, for_download=False):
        return list(self._missing)


class _FakeRemove:

    def __init__(self):

        self.removed: list[WatchlistItemForUser] = []

    async def execute(self, entry: WatchlistItemForUser):

        self.removed.append(entry)

    @staticmethod
    def should_remove_when_already_queued(queue_reason: str | None) -> bool:
        return RemoveWatchlistEntryUseCase.should_remove_when_already_queued(
            queue_reason
        )





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

        _FakeGetMissingTvEpisodes(missing=[TvEpisode(season=1, episode=1)]),

    )

    skip, reason = await query.execute(_entry())

    assert skip is True

    assert reason == "already_in_library"

    assert len(remove.removed) == 1
    assert remove.removed[0].item.rating_key == "123"





@pytest.mark.asyncio

async def test_skips_when_already_queued():

    remove = _FakeRemove()

    query = ShouldSkipWatchlistItemQuery(

        _FakeIsInLibrary(),

        _FakeQueued(queued=True, reason="already_downloading"),

        remove,

        _FakeGetMissingTvEpisodes(missing=[TvEpisode(season=1, episode=1)]),

    )

    skip, reason = await query.execute(_entry())

    assert skip is True

    assert reason == "already_downloading"
    assert len(remove.removed) == 1


@pytest.mark.asyncio
async def test_skips_when_same_title_queued_from_other_platform_without_removing():
    remove = _FakeRemove()
    query = ShouldSkipWatchlistItemQuery(
        _FakeIsInLibrary(),
        _FakeQueued(queued=True, reason="same_media_identity_downloading"),
        remove,
        _FakeGetMissingTvEpisodes(missing=[TvEpisode(season=1, episode=1)]),
    )
    skip, reason = await query.execute(_entry())
    assert skip is True
    assert reason == "same_media_identity_downloading"
    assert len(remove.removed) == 0


@pytest.mark.asyncio

async def test_does_not_skip_new_item():

    query = ShouldSkipWatchlistItemQuery(

        _FakeIsInLibrary(),

        _FakeQueued(),

        _FakeRemove(),

        _FakeGetMissingTvEpisodes(missing=[TvEpisode(season=1, episode=1)]),

    )

    skip, reason = await query.execute(_entry())

    assert skip is False

    assert reason is None


@pytest.mark.asyncio
async def test_skips_show_when_all_episodes_complete():
    remove = _FakeRemove()
    query = ShouldSkipWatchlistItemQuery(
        _FakeIsInLibrary(in_library=True),
        _FakeQueued(),
        remove,
        _FakeGetMissingTvEpisodes(missing=[]),
    )
    skip, reason = await query.execute(
        _entry(title="Breaking Bad", guid="plex://show/1", type=MediaType.SHOW)
    )
    assert skip is True
    assert reason == "show_complete"
    assert len(remove.removed) == 1
    assert remove.removed[0].item.rating_key == "123"


@pytest.mark.asyncio
async def test_does_not_skip_show_with_missing_episodes():
    query = ShouldSkipWatchlistItemQuery(
        _FakeIsInLibrary(in_library=True),
        _FakeQueued(),
        _FakeRemove(),
        _FakeGetMissingTvEpisodes(missing=[TvEpisode(season=2, episode=1)]),
    )
    skip, reason = await query.execute(
        _entry(title="Breaking Bad", guid="plex://show/1", type=MediaType.SHOW)
    )
    assert skip is False
    assert reason is None

