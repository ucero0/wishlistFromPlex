"""Tests for manual Deluge torrent tracking helpers."""
from app.domain.models.torrent import Torrent
from app.domain.services.manual_torrent_tracking import (
    active_download_from_deluge_torrent,
    infer_media_type,
    infer_title,
    is_manual_active_download,
    manual_prowlarr_guid,
    parse_season_episode,
)


def test_parse_season_episode():
    assert parse_season_episode("Show.Name.S01E02.mkv") == (1, 2)
    assert parse_season_episode("movie.mkv") is None


def test_infer_media_type():
    assert infer_media_type("Show.Name.S01E02.mkv") == "show"
    assert infer_media_type("Movie.2024.mkv") == "movie"


def test_infer_title_uses_top_level_folder():
    assert infer_title("My Movie 2024/My Movie 2024.mkv") == "My Movie 2024"


def test_manual_prowlarr_guid_is_stable():
    assert manual_prowlarr_guid("ABC123") == "manual:abc123"


def test_active_download_from_deluge_torrent_show():
    torrent = Torrent(
        hash="A" * 40,
        file_name="Breaking.Bad.S05E14.mkv",
        state="Seeding",
        progress=100.0,
    )
    active = active_download_from_deluge_torrent(torrent, title="Breaking Bad")
    assert active.type == "show"
    assert active.season == 5
    assert active.episode == 14
    assert active.prowlarr_guid == f"manual:{'a' * 40}"
    assert is_manual_active_download(active)


def test_active_download_from_deluge_torrent_movie_with_hints():
    torrent = Torrent(
        hash="b" * 40,
        file_name="Dune.2021.mkv",
        state="Seeding",
        progress=100.0,
    )
    active = active_download_from_deluge_torrent(
        torrent, media_type="movie", title="Dune", year=2021
    )
    assert active.type == "movie"
    assert active.title == "Dune"
    assert active.year == 2021
    assert active.season is None
