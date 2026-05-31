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


def test_movie_file_uses_title_year_filename():
    resolver = IngestDestinationResolver()
    path = resolver.resolve(
        "/media/movies",
        _movie_torrent(),
        "/quarantine/Dune.2021.mkv",
        is_file=True,
    )
    assert path.replace("\\", "/") == "/media/movies/Dune (2021)/Dune (2021).mkv"


def test_movie_directory_destination_is_title_year_folder():
    resolver = IngestDestinationResolver()
    path = resolver.resolve(
        "/media/movies",
        _movie_torrent(file_name="Dune.2021.2160p"),
        "/quarantine/Dune.2021.2160p",
        is_file=False,
    )
    assert path.replace("\\", "/") == "/media/movies/Dune (2021)"


def test_show_file_uses_show_season_and_episode_filename():
    resolver = IngestDestinationResolver()
    path = resolver.resolve(
        "/media/tv",
        _movie_torrent(
            title="Breaking Bad",
            file_name="Breaking.Bad.S01E02.mkv",
            type="show",
            season=1,
            episode=2,
            year=2008,
        ),
        "/quarantine/Breaking.Bad.S01E02.mkv",
        is_file=True,
    )
    normalized = path.replace("\\", "/")
    assert normalized == (
        "/media/tv/Breaking Bad (2008)/Season 01/Breaking Bad - s01e02.mkv"
    )


def test_show_file_includes_episode_title_when_available():
    resolver = IngestDestinationResolver()
    path = resolver.resolve(
        "/media/tv",
        _movie_torrent(
            title="Scrubs",
            file_name="Scrubs.S01E01.mkv",
            type="show",
            season=1,
            episode=1,
            year=2001,
            episode_name="My First Day",
        ),
        "/quarantine/Scrubs.S01E01.mkv",
        is_file=True,
    )
    normalized = path.replace("\\", "/")
    assert normalized == (
        "/media/tv/Scrubs (2001)/Season 01/Scrubs - s01e01 - My First Day.mkv"
    )


def test_show_parses_season_episode_from_release_name_when_db_missing():
    resolver = IngestDestinationResolver()
    path = resolver.resolve(
        "/media/tv",
        _movie_torrent(
            title="The Last of Us",
            file_name="The.Last.of.Us.S01E01.mkv",
            type="show",
            season=None,
            episode=None,
        ),
        "/quarantine/The.Last.of.Us.S01E01.mkv",
        is_file=True,
    )
    normalized = path.replace("\\", "/")
    assert normalized.endswith("The Last of Us - s01e01.mkv")
    assert "/The Last of Us/Season 01/" in normalized


def test_show_folder_includes_year_when_available():
    resolver = IngestDestinationResolver()
    path = resolver.resolve(
        "/media/tv",
        _movie_torrent(
            title="Breaking Bad",
            file_name="Breaking.Bad.S01E01",
            type="show",
            season=1,
            year=2008,
        ),
        "/quarantine/Breaking.Bad.S01E01",
        is_file=False,
    )
    assert path.replace("\\", "/") == "/media/tv/Breaking Bad (2008)/Season 01"


def test_show_folder_omits_year_when_unknown():
    resolver = IngestDestinationResolver()
    path = resolver.resolve(
        "/media/tv",
        _movie_torrent(
            title="Breaking Bad",
            file_name="Breaking.Bad.S01E01",
            type="show",
            season=1,
            year=None,
        ),
        "/quarantine/Breaking.Bad.S01E01",
        is_file=False,
    )
    assert path.replace("\\", "/") == "/media/tv/Breaking Bad/Season 01"


def test_apply_plex_media_names_renames_movie_file():
    resolver = IngestDestinationResolver()
    files = {"/lib/Dune (2021)/release.mkv": "/lib/Dune (2021)/Dune (2021).mkv"}

    def list_videos(_path: str) -> list[str]:
        return ["/lib/Dune (2021)/release.mkv"]

    def rename(src: str, dest: str) -> bool:
        files[dest] = files.pop(src)
        return True

    count = resolver.apply_plex_media_names(
        "/lib/Dune (2021)",
        _movie_torrent(),
        list_video_files=list_videos,
        rename_file=rename,
    )
    assert count == 1
    assert "/lib/Dune (2021)/Dune (2021).mkv" in files


def test_folder_path_for_plex_scan_file_uses_parent():
    resolver = IngestDestinationResolver()
    result = resolver.folder_path_for_plex_scan(
        "/media/movies/Dune (2021)/Dune (2021).mkv", True
    )
    assert result.replace("\\", "/") == "/media/movies/Dune (2021)"
