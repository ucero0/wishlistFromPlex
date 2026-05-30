"""Tests for media identity normalization."""
from app.domain.services.media_identity import (
    normalize_media_type_for_queue_match,
    normalize_title,
)


def test_normalize_title_strips_and_lowercases():
    assert normalize_title("  The Matrix  ") == "the matrix"


def test_normalize_media_type_movie_and_show():
    assert normalize_media_type_for_queue_match("movie") == "movie"
    assert normalize_media_type_for_queue_match("tvshow") == "show"
    assert normalize_media_type_for_queue_match("MediaType.SHOW") == "show"
