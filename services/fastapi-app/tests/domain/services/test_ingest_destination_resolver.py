"""Tests for IngestDestinationResolver."""
from app.domain.models.active_download import ActiveDownload
from app.domain.services.ingest_destination_resolver import IngestDestinationResolver


def _movie_torrent(**overrides) -> ActiveDownload:
    base = dict(
        plex_guid="plex://movie/guid",
        prowlarr_guid="prowlarr-guid",
        uid="a" * 40,
        title="Dune",
        file_name="Dune.2021.mkv",
        year=2021,
        type="movie",
    )
    base.update(overrides)
    return ActiveDownload(**base)


def test_movie_file_goes_into_title_year_folder():
    resolver = IngestDestinationResolver()
    path = resolver.resolve(
        "/media/movies",
        _movie_torrent(),
        "/quarantine/Dune.2021.mkv",
        is_file=True,
    )
    assert path.replace("\\", "/").endswith("/media/movies/Dune (2021)/Dune.2021.mkv")


def test_show_file_includes_season_folder():
    resolver = IngestDestinationResolver()
    path = resolver.resolve(
        "/media/tv",
        _movie_torrent(
            title="Breaking Bad",
            file_name="Breaking.Bad.S01E01.mkv",
            type="show",
            season=1,
        ),
        "/quarantine/Breaking.Bad.S01E01.mkv",
        is_file=True,
    )
    normalized = path.replace("\\", "/")
    assert "Breaking Bad (2021)" in normalized or "Breaking Bad" in normalized
    assert "Season 01" in normalized
    assert normalized.endswith("Breaking.Bad.S01E01.mkv")


def test_folder_path_for_plex_scan_file_uses_parent():
    resolver = IngestDestinationResolver()
    result = resolver.folder_path_for_plex_scan("/media/movies/Dune/Dune.mkv", True)
    assert result.replace("\\", "/") == "/media/movies/Dune"
