"""Query: list deferred torrent downloads."""
from app.domain.models.deferred_torrent_download import DeferredTorrentDownload
from app.domain.ports.repositories.deferredTorrent.deferredTorrentRepo import (
    DeferredTorrentRepoPort,
)


class ListDeferredTorrentDownloadsQuery:
    def __init__(self, deferred_repo: DeferredTorrentRepoPort):
        self._deferred_repo = deferred_repo

    async def execute(self, *, limit: int = 100) -> list[DeferredTorrentDownload]:
        return await self._deferred_repo.list_pending(limit=limit)
