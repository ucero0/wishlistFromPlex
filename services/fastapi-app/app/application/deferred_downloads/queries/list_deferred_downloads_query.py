"""Query: list deferred torrent downloads."""
from app.domain.models.deferred_download import DeferredDownload
from app.domain.ports.repositories.deferred_downloads.deferred_download_repository_port import (
    DeferredDownloadRepositoryPort,
)


class ListDeferredDownloadsQuery:
    def __init__(self, deferred_repo: DeferredDownloadRepositoryPort):
        self._deferred_repo = deferred_repo

    async def execute(self, *, limit: int = 100) -> list[DeferredDownload]:
        return await self._deferred_repo.list_pending(limit=limit)
