"""Pure logic to compute Plex library ingest paths from torrent metadata."""
import logging
import re
from collections.abc import Callable
from pathlib import Path

from app.domain.models.media import MediaType
from app.domain.models.active_download import ActiveDownload

logger = logging.getLogger(__name__)

_VIDEO_EXTENSIONS = {
    ".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v",
    ".mpg", ".mpeg", ".3gp", ".ogv", ".ts", ".m2ts", ".mts", ".vob",
    ".divx", ".xvid", ".asf", ".rm", ".rmvb", ".f4v", ".mxf",
}

_SEASON_EPISODE_RE = re.compile(r"[Ss](?P<season>\d{1,2})[Ee](?P<episode>\d{1,3})")


class IngestDestinationResolver:
    """Build Plex-style library folder and media file names."""

    def resolve(
        self,
        library_root_path: str,
        torrent_download: ActiveDownload,
        scan_path: str,
        is_file: bool,
    ) -> str:
        base_path = str(Path(library_root_path) / (torrent_download.file_name or ""))
        destination = Path(base_path)
        parent = destination.parent
        media_type = torrent_download.type

        if self._is_movie(media_type):
            movie_folder = self._movie_folder_name(torrent_download)
            if is_file:
                ext = Path(scan_path).suffix or destination.suffix
                destination = parent / movie_folder / self._movie_file_name(
                    torrent_download, ext
                )
            else:
                destination = parent / movie_folder
        elif self._is_show(media_type):
            show_folder = self._show_folder_name(torrent_download)
            season_num = torrent_download.season if torrent_download.season else 1
            season_folder = self._season_folder_name(season_num)
            if is_file:
                ext = Path(scan_path).suffix or destination.suffix
                destination = (
                    parent
                    / show_folder
                    / season_folder
                    / self._episode_file_name(torrent_download, ext, Path(scan_path).name)
                )
            else:
                destination = parent / show_folder / season_folder
        elif is_file:
            ext = Path(scan_path).suffix or destination.suffix
            folder = self._movie_folder_name(torrent_download)
            destination = parent / folder / self._movie_file_name(torrent_download, ext)
        else:
            destination = parent / self._movie_folder_name(torrent_download)

        return str(destination)

    def apply_plex_media_names(
        self,
        library_path: str,
        torrent_download: ActiveDownload,
        *,
        list_video_files: Callable[[str], list[str]],
        rename_file: Callable[[str, str], bool],
    ) -> int:
        """
        Rename video files under a library folder to Plex-style names.

        Used after moving a torrent directory when filenames still use release names.
        """
        renamed = 0
        media_type = torrent_download.type
        for video_path in list_video_files(library_path):
            path = Path(video_path)
            ext = path.suffix
            if self._is_movie(media_type):
                target_name = self._movie_file_name(torrent_download, ext)
            elif self._is_show(media_type):
                target_name = self._episode_file_name(
                    torrent_download, ext, path.name
                )
            else:
                target_name = self._movie_file_name(torrent_download, ext)

            target_path = str(path.parent / target_name)
            if path.name == target_name:
                continue
            if Path(target_path).exists():
                logger.warning(
                    "Skipping rename %s -> %s: target already exists",
                    path.name,
                    target_name,
                )
                continue
            if rename_file(video_path, target_path):
                renamed += 1
                logger.info("Renamed media file %s -> %s", path.name, target_name)
        return renamed

    @staticmethod
    def folder_path_for_plex_scan(destination_path: str, is_file: bool) -> str:
        if is_file:
            return str(Path(destination_path).parent)
        return destination_path

    def _is_movie(self, media_type: str) -> bool:
        return media_type.lower() == MediaType.MOVIE.value

    def _is_show(self, media_type: str) -> bool:
        normalized = media_type.lower()
        return normalized in (MediaType.SHOW.value, MediaType.TVSHOW.value)

    @staticmethod
    def _movie_folder_name(torrent_download: ActiveDownload) -> str:
        if torrent_download.year:
            return f"{torrent_download.title} ({torrent_download.year})"
        return torrent_download.title

    @staticmethod
    def _show_folder_name(torrent_download: ActiveDownload) -> str:
        return torrent_download.title

    @staticmethod
    def _season_folder_name(season_num: int) -> str:
        return f"Season {season_num:02d}"

    def _movie_file_name(self, torrent_download: ActiveDownload, ext: str) -> str:
        base = self._movie_folder_name(torrent_download)
        return f"{base}{ext}"

    def _episode_file_name(
        self,
        torrent_download: ActiveDownload,
        ext: str,
        release_filename: str,
    ) -> str:
        season, episode = self._resolve_season_episode(
            torrent_download, release_filename
        )
        return f"{torrent_download.title} - S{season:02d}E{episode:02d}{ext}"

    def _resolve_season_episode(
        self, torrent_download: ActiveDownload, release_filename: str
    ) -> tuple[int, int]:
        parsed = self._parse_season_episode(release_filename)
        if parsed:
            return parsed
        season = torrent_download.season if torrent_download.season else 1
        episode = torrent_download.episode if torrent_download.episode else 1
        return season, episode

    @staticmethod
    def _parse_season_episode(filename: str) -> tuple[int, int] | None:
        match = _SEASON_EPISODE_RE.search(filename)
        if not match:
            return None
        return int(match.group("season")), int(match.group("episode"))

    @staticmethod
    def video_extensions() -> frozenset[str]:
        return frozenset(_VIDEO_EXTENSIONS)
