"""Use case for updating a torrent download."""
from app.domain.ports.repositories.torrentDownload.torrentDownloadRepo import TorrentDownloadRepoPort
from app.domain.models.torrentDownload import TorrentDownload


class UpdateTorrentDownloadUseCase:
    """Use case for updating an existing torrent download."""
    
    def __init__(self, repo: TorrentDownloadRepoPort):
        self.repo = repo
    
    async def execute(self, torrent_download: TorrentDownload) -> TorrentDownload:
        """
        Update an existing torrent download.
        
        Args:
            torrent_download: The torrent download to update (must have an ID)
            
        Returns:
            The updated TorrentDownload
        """
        return await self.repo.update(torrent_download)

