"""Tests for Plex title normalization in torrent search queries."""
from unittest.mock import AsyncMock

import pytest

from app.application.pipelines.watchlist.services.watchlist_search_builder import (
    WatchlistSearchQueryBuilder,
)
from app.domain.models.media import MediaItem, MediaType
from app.domain.models.tv_episode import TvEpisode
from app.domain.services.torrent_search_title import normalize_title_for_torrent_search


def test_normalize_title_replaces_colon_space():
    assert (
        normalize_title_for_torrent_search("Torrente 5: Operation Eurovegas")
        == "Torrente 5 Operation Eurovegas"
    )


def test_normalize_title_replaces_colon_without_space():
    assert normalize_title_for_torrent_search("Foo:Bar") == "Foo Bar"


def test_normalize_title_collapses_whitespace():
    assert normalize_title_for_torrent_search("  Star   Wars  ") == "Star Wars"
    assert normalize_title_for_torrent_search("") == ""


@pytest.mark.asyncio
async def test_watchlist_search_builder_normalizes_movie_title():
    tmdb = AsyncMock()
    tmdb.execute = AsyncMock(return_value=None)
    builder = WatchlistSearchQueryBuilder(tmdb)
    watchlist = MediaItem(
        guid="plex://movie/1",
        title="Torrente 5: Operation Eurovegas",
        year=2014,
        type=MediaType.MOVIE,
    )

    query = await builder.execute(watchlist)

    assert query == "Torrente 5 Operation Eurovegas 2014"


@pytest.mark.asyncio
async def test_watchlist_search_builder_normalizes_spanish_original_title():
    tmdb = AsyncMock()
    tmdb.execute = AsyncMock(return_value=("El laberinto: del fauno", "es"))
    builder = WatchlistSearchQueryBuilder(tmdb)
    watchlist = MediaItem(
        guid="plex://movie/2",
        title="Pan's Labyrinth",
        year=2006,
        type=MediaType.MOVIE,
    )

    query = await builder.execute(watchlist)

    assert query == "El laberinto del fauno 2006"


def test_watchlist_search_builder_normalizes_tv_show_title():
    tmdb = AsyncMock()
    builder = WatchlistSearchQueryBuilder(tmdb)
    watchlist = MediaItem(
        guid="plex://show/1",
        title="Star Trek: The Next Generation",
        year=1987,
        type=MediaType.SHOW,
    )
    episode = TvEpisode(season=1, episode=1, name="Encounter at Farpoint")

    queries = builder.build_tv_episode_search_queries(watchlist, episode)

    assert queries[0] == (
        "Star Trek The Next Generation S01E01 Encounter at Farpoint"
    )
    assert queries[1] == "Star Trek The Next Generation S01E01"
