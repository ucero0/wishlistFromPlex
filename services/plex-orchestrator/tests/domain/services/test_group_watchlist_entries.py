"""Tests for grouping watchlist entries by media identity."""

from app.domain.models.media import MediaItem, MediaType
from app.domain.models.watchlist_item_for_user import WatchlistItemForUser
from app.domain.models.watchlist_source import WatchlistSource
from app.domain.models.watchlist_subscriber import WatchlistSubscriber
from app.domain.services.group_watchlist_entries import group_watchlist_entries


def _plex_entry(user_id: int, rating_key: str, guid: str, title: str) -> WatchlistItemForUser:
    return WatchlistItemForUser(
        item=MediaItem(
            guid=guid,
            rating_key=rating_key,
            title=title,
            type=MediaType.MOVIE,
            plex_library_guid=guid,
        ),
        source=WatchlistSource.PLEX,
        plex_user_id=user_id,
        plex_user_token=f"plex-token-{user_id}",
        plex_watchlist_rating_key=rating_key,
        subscribers=[
            WatchlistSubscriber(
                source=WatchlistSource.PLEX,
                plex_user_id=user_id,
                plex_user_token=f"plex-token-{user_id}",
                plex_watchlist_rating_key=rating_key,
            )
        ],
    )


def _tmdb_entry(account_id: int, tmdb_id: int, plex_lib_guid: str) -> WatchlistItemForUser:
    return WatchlistItemForUser(
        item=MediaItem(
            guid=f"tmdb://movie/{tmdb_id}",
            rating_key="999",
            title="Frankenstein",
            year=2025,
            type=MediaType.MOVIE,
            plex_library_guid=plex_lib_guid,
        ),
        source=WatchlistSource.TMDB,
        tmdb_user_id=1,
        tmdb_account_id=account_id,
        tmdb_access_token="tmdb-token",
        subscribers=[
            WatchlistSubscriber(
                source=WatchlistSource.TMDB,
                tmdb_user_id=1,
                tmdb_account_id=account_id,
                tmdb_access_token="tmdb-token",
                tmdb_media_id=tmdb_id,
            )
        ],
    )


def test_groups_plex_and_tmdb_subscribers_for_same_movie():
    plex_guid = "plex://movie/abc"
    grouped = group_watchlist_entries(
        [
            _plex_entry(1, "111", plex_guid, "Frankenstein"),
            _tmdb_entry(22487439, 1062722, plex_guid),
        ]
    )

    assert len(grouped) == 1
    assert len(grouped[0].all_subscribers()) == 2
    sources = {s.source for s in grouped[0].all_subscribers()}
    assert sources == {WatchlistSource.PLEX, WatchlistSource.TMDB}


def test_keeps_separate_groups_for_different_movies():
    grouped = group_watchlist_entries(
        [
            _plex_entry(1, "111", "plex://movie/a", "Movie A"),
            _plex_entry(2, "222", "plex://movie/b", "Movie B"),
        ]
    )

    assert len(grouped) == 2
