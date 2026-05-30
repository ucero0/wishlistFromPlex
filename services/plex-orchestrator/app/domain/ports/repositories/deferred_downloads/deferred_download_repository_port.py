"""Repository port for deferred torrent downloads."""
from typing import List, Optional, Protocol

from app.domain.models.deferred_download import DeferredDownload


class DeferredDownloadRepositoryPort(Protocol):
    async def get_pending_by_guid_plex(
        self, guid_plex: str
    ) -> DeferredDownload | None:
        ...

    async def get_pending_by_guid_prowlarr(
        self, guid_prowlarr: str
    ) -> DeferredDownload | None:
        ...

    async def get_pending_by_media_identity(
        self,
        title: str,
        year: Optional[int],
        media_type: str,
    ) -> DeferredDownload | None:
        ...

    async def list_pending(self, *, limit: int = 50) -> List[DeferredDownload]:
        ...

    async def upsert_pending(self, item: DeferredDownload) -> DeferredDownload:
        """Create or replace the pending row for this Plex guid."""
        ...

    async def mark_sent(self, item_id: int) -> None:
        ...

    async def increment_attempt(self, item_id: int) -> None:
        ...

    async def update(self, item: DeferredDownload) -> DeferredDownload:
        ...
