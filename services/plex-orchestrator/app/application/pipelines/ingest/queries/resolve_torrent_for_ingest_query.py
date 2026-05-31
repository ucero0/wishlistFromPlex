"""Resolve tracked or manual Deluge torrent context for scan/ingest."""
from dataclasses import dataclass

from app.application.active_downloads.queries.get_active_download_queries import (
    GetActiveDownloadByUidQuery,
)
from app.application.deluge.queries.get_torrent_status_query import GetTorrentStatusQuery
from app.domain.errors.deluge import DelugeTorrentNotFoundError
from app.domain.models.active_download import ActiveDownload
from app.domain.services.manual_torrent_tracking import (
    active_download_from_deluge_torrent,
    normalize_torrent_hash,
)


@dataclass(frozen=True)
class ResolvedTorrentForIngest:
    active_download: ActiveDownload
    is_manual: bool


class ResolveTorrentForIngestQuery:
    def __init__(
        self,
        get_active_download_by_uid_query: GetActiveDownloadByUidQuery,
        get_torrent_status_query: GetTorrentStatusQuery,
    ):
        self._get_active_download = get_active_download_by_uid_query
        self._get_torrent_status = get_torrent_status_query

    async def execute(
        self,
        torrent_hash: str,
        *,
        media_type: str | None = None,
        title: str | None = None,
        year: int | None = None,
    ) -> ResolvedTorrentForIngest | None:
        normalized_hash = normalize_torrent_hash(torrent_hash)
        tracked = await self._get_active_download.execute(normalized_hash)
        if tracked is not None:
            return ResolvedTorrentForIngest(active_download=tracked, is_manual=False)

        try:
            deluge_torrent = await self._get_torrent_status.execute(normalized_hash)
        except DelugeTorrentNotFoundError:
            return None

        return ResolvedTorrentForIngest(
            active_download=active_download_from_deluge_torrent(
                deluge_torrent,
                media_type=media_type,
                title=title,
                year=year,
            ),
            is_manual=True,
        )
