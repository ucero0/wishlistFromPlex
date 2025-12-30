"""Use case for downloading a torrent to the download client."""
import logging
from app.domain.ports.external.prowlarr.torrent_search_provider import TorrentSearchProvider
from app.domain.models.torrent_search import TorrentSearchResult

logger = logging.getLogger(__name__)


class DownloadTorrentUseCase:
    """Use case for sending a torrent to the download client."""
    
    def __init__(self, search_provider: TorrentSearchProvider):
        self.search_provider = search_provider
    
    async def execute(
        self,
        torrent_result: TorrentSearchResult,
    ) -> bool:
        """
        Send a torrent to the download client.
        
        Args:
            torrent_result: The TorrentSearchResult to download
            
        Returns:
            True if successful, False otherwise
        """

        send_result = await self.search_provider.send_to_download_client(
            torrent_result.guid, 
            torrent_result.indexerId
        )

        return send_result
