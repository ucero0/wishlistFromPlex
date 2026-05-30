"""Pure logic to compute Plex library ingest paths from torrent metadata."""
from pathlib import Path

from app.domain.models.media import MediaType
from app.domain.models.active_download import ActiveDownload


class IngestDestinationResolver:
    """Build the destination folder/file path under a Plex library root."""

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
        show_or_movie_folder = self._media_folder_name(torrent_download)
        media_type = torrent_download.type

        if self._is_movie(media_type):
            if is_file:
                destination = parent / show_or_movie_folder / destination.name
            else:
                destination = parent / show_or_movie_folder
        elif self._is_show(media_type):
            season_num = torrent_download.season if torrent_download.season else 1
            season_folder = self._season_folder_name(season_num)
            if is_file:
                destination = (
                    parent / show_or_movie_folder / season_folder / destination.name
                )
            else:
                destination = parent / show_or_movie_folder / season_folder
        elif is_file:
            destination = parent / show_or_movie_folder / destination.name
        else:
            destination = parent / show_or_movie_folder

        return str(destination)

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
    def _media_folder_name(torrent_download: ActiveDownload) -> str:
        if torrent_download.year:
            return f"{torrent_download.title} ({torrent_download.year})"
        return torrent_download.title

    @staticmethod
    def _season_folder_name(season_num: int) -> str:
        return f"Season {season_num:02d}"
