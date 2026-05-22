"""Repository port for deferred torrent downloads."""
from typing import List, Optional, Protocol

from app.domain.models.deferred_torrent_download import DeferredTorrentDownload


class DeferredTorrentRepoPort(Protocol):
    async def get_pending_by_guid_plex(
        self, guid_plex: str
    ) -> DeferredTorrentDownload | None:
        ...

    async def get_pending_by_guid_prowlarr(
        self, guid_prowlarr: str
    ) -> DeferredTorrentDownload | None:
        ...

    async def get_pending_by_media_identity(
        self,
        title: str,
        year: Optional[int],
        media_type: str,
    ) -> DeferredTorrentDownload | None:
        ...

    async def list_pending(self, *, limit: int = 50) -> List[DeferredTorrentDownload]:
        ...

    async def upsert_pending(self, item: DeferredTorrentDownload) -> DeferredTorrentDownload:
        """Create or replace the pending row for this Plex guid."""
        ...

    async def mark_sent(self, item_id: int) -> None:
        ...

    async def increment_attempt(self, item_id: int) -> None:
        ...

    async def update(self, item: DeferredTorrentDownload) -> DeferredTorrentDownload:
        ...
