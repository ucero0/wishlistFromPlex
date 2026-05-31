"""Tests for Plex Discover rating key resolution."""
from app.application.pipelines.watchlist.services.show_watchlist_helpers import (
    discover_rating_key_for_show,
)
from app.domain.models.media import MediaItem, MediaType


def test_discover_rating_key_from_plex_show_guid():
    item = MediaItem(
        guid="plex://show/abc123",
        title="Scrubs",
        type=MediaType.SHOW,
    )
    assert discover_rating_key_for_show(item) == "abc123"


def test_discover_rating_key_prefers_explicit_rating_key_for_plex_show():
    item = MediaItem(
        guid="plex://show/abc123",
        rating_key="rk999",
        title="Scrubs",
        type=MediaType.SHOW,
    )
    assert discover_rating_key_for_show(item) == "rk999"


def test_discover_rating_key_ignores_tmdb_watchlist_rating_key():
    item = MediaItem(
        guid="tmdb://tv/1434",
        rating_key="1434",
        title="Family Guy",
        type=MediaType.SHOW,
    )
    assert discover_rating_key_for_show(item) is None
