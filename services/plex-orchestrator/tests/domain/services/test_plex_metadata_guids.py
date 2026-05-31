"""Tests for Plex metadata guid matching."""
from app.domain.services.plex_metadata_guids import metadata_matches_tmdb_id


def test_metadata_matches_tmdb_tv_guid_in_secondary_guids():
    metadata = {
        "guid": "plex://show/5d9c086c7d06d9001ffd279e",
        "Guid": [{"id": "imdb://tt0182576"}, {"id": "tmdb://1434"}],
    }
    assert metadata_matches_tmdb_id(metadata, 1434, "tv")


def test_metadata_matches_tmdb_tv_guid_long_form():
    metadata = {
        "guid": "plex://show/x",
        "Guid": [{"id": "tmdb://tv/1434"}],
    }
    assert metadata_matches_tmdb_id(metadata, 1434, "tv")
