"""Port (Protocol) for torrent search provider."""
from typing import Protocol, List

from app.domain.models.external_connection import ExternalConnectionStatus
from app.domain.models.torrent_search import TorrentSearchResult
from app.domain.models.prowlarr_indexer import ProwlarrIndexerInfo


class TorrentSearchProvider(Protocol):
    """Protocol defining the contract for torrent search operations."""

    async def search_torrents(
        self,
        query: str,
        media_type: str = "movie",
    ) -> List[TorrentSearchResult]:
        ...

    async def send_to_download_client(
        self,
        guid: str,
        indexer_id: int,
    ) -> bool:
        ...

    async def test_connection(self) -> ExternalConnectionStatus:
        """Probe connectivity (non-throwing health check)."""
        ...

    async def get_indexers(self) -> List[ProwlarrIndexerInfo]:
        ...
