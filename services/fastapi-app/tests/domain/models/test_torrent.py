"""Tests for Torrent domain helpers."""
from app.domain.models.torrent import Torrent


def test_is_finished_when_progress_complete():
    t = Torrent(
        hash="a" * 40,
        fileName="movie.mkv",
        state="Downloading",
        progress=100.0,
    )
    assert t.is_finished is True


def test_is_finished_when_seeding():
    t = Torrent(
        hash="a" * 40,
        fileName="movie.mkv",
        state="Seeding",
        progress=50.0,
    )
    assert t.is_finished is True


def test_is_finished_false_while_downloading():
    t = Torrent(
        hash="a" * 40,
        fileName="movie.mkv",
        state="Downloading",
        progress=10.0,
    )
    assert t.is_finished is False
