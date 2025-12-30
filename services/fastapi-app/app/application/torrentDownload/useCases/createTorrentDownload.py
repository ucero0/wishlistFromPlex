"""Use case for creating a torrent download."""
from app.domain.ports.repositories.torrentDownload.torrentDownloadRepo import TorrentDownloadRepoPort
from app.domain.models.torrentDownload import TorrentDownload


class CreateTorrentDownloadUseCase:
    """Use case for creating a new torrent download."""
    
    def __init__(self, repo: TorrentDownloadRepoPort):
        self.repo = repo
    
    async def execute(self, torrent_download: TorrentDownload) -> TorrentDownload:
        """
        Create a new torrent download.
        
        Args:
            torrent_download: The torrent download to create
            
        Returns:
            The created TorrentDownload with ID and timestamps
        """
        return await self.repo.create(torrent_download)

