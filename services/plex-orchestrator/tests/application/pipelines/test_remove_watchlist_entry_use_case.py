"""Tests for RemoveWatchlistEntryUseCase TMDB id resolution."""

import pytest

from app.application.pipelines.watchlist.use_cases.remove_watchlist_entry_use_case import (
    RemoveWatchlistEntryUseCase,
)
from app.domain.models.media import MediaItem, MediaType
from app.domain.models.watchlist_item_for_user import WatchlistItemForUser
from app.domain.models.watchlist_source import WatchlistSource
from app.domain.models.watchlist_subscriber import WatchlistSubscriber


def test_tmdb_media_id_prefers_guid_over_plex_rating_key_after_enrichment():
    entry = WatchlistItemForUser(
        item=MediaItem(
            guid="tmdb://movie/1062722",
            rating_key="5384",
            title="Frankenstein",
            year=2025,
            type=MediaType.MOVIE,
            plex_library_guid="plex://movie/5d776e1651dd69001fe48a6e",
        ),
        source=WatchlistSource.TMDB,
        tmdb_account_id=22487439,
        tmdb_access_token="token",
        subscribers=[
            WatchlistSubscriber(
                source=WatchlistSource.TMDB,
                tmdb_account_id=22487439,
                tmdb_access_token="token",
                tmdb_media_id=1062722,
            )
        ],
    )

    assert RemoveWatchlistEntryUseCase._tmdb_media_id_from_entry(entry) == 1062722


class _FakeRemoveTmdb:
    def __init__(self):
        self.calls: list[tuple[int, str, str, int]] = []

    async def execute(
        self, account_id: int, access_token: str, media_type: str, media_id: int
    ) -> None:
        self.calls.append((account_id, access_token, media_type, media_id))


class _FakeRemovePlex:
    def __init__(self):
        self.calls: list[tuple[str, str]] = []

    async def execute(self, rating_key: str, token: str) -> None:
        self.calls.append((rating_key, token))


@pytest.mark.asyncio
async def test_execute_removes_from_all_subscribers():
    remove_tmdb = _FakeRemoveTmdb()
    remove_plex = _FakeRemovePlex()
    use_case = RemoveWatchlistEntryUseCase(
        remove_plex_watchlist_item_use_case=remove_plex,
        remove_tmdb_watchlist_item_use_case=remove_tmdb,
        tmdb_watchlist_provider=object(),  # type: ignore[arg-type]
    )
    entry = WatchlistItemForUser(
        item=MediaItem(
            guid="tmdb://movie/1062722",
            rating_key="5384",
            title="Frankenstein",
            year=2025,
            type=MediaType.MOVIE,
            plex_library_guid="plex://movie/5d776e1651dd69001fe48a6e",
        ),
        source=WatchlistSource.TMDB,
        subscribers=[
            WatchlistSubscriber(
                source=WatchlistSource.TMDB,
                tmdb_account_id=22487439,
                tmdb_access_token="tmdb-token",
                tmdb_media_id=1062722,
            ),
            WatchlistSubscriber(
                source=WatchlistSource.PLEX,
                plex_user_id=2,
                plex_user_token="plex-token",
                plex_watchlist_rating_key="111",
            ),
        ],
    )

    await use_case.execute(entry)

    assert remove_tmdb.calls == [(22487439, "tmdb-token", "movie", 1062722)]
    assert remove_plex.calls == [("111", "plex-token")]


@pytest.mark.asyncio
async def test_execute_does_not_remove_show_for_movie_style_reason():
    remove_tmdb = _FakeRemoveTmdb()
    remove_plex = _FakeRemovePlex()
    use_case = RemoveWatchlistEntryUseCase(
        remove_plex_watchlist_item_use_case=remove_plex,
        remove_tmdb_watchlist_item_use_case=remove_tmdb,
        tmdb_watchlist_provider=object(),  # type: ignore[arg-type]
    )
    entry = WatchlistItemForUser(
        item=MediaItem(
            guid="tmdb://tv/1434",
            rating_key="1434",
            title="Family Guy",
            type=MediaType.SHOW,
        ),
        source=WatchlistSource.TMDB,
        subscribers=[
            WatchlistSubscriber(
                source=WatchlistSource.TMDB,
                tmdb_account_id=22487439,
                tmdb_access_token="tmdb-token",
                tmdb_media_id=1434,
            )
        ],
    )

    await use_case.execute(entry, removal_reason="already_in_library")

    assert remove_tmdb.calls == []
    assert remove_plex.calls == []
