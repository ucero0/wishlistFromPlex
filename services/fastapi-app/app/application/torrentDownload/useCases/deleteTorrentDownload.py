"""Use case for deleting a torrent download."""
from app.domain.ports.repositories.torrentDownload.torrentDownloadRepo import TorrentDownloadRepoPort
from app.domain.models.torrentDownload import TorrentDownload


class DeleteTorrentDownloadUseCase:
    """Use case for deleting a torrent download."""
    
    def __init__(self, repo: TorrentDownloadRepoPort):
        self.repo = repo
    
    async def execute(self, torrent_download: TorrentDownload) -> None:
        """
        Delete a torrent download.
        
        Args:
            torrent_download: The torrent download to delete (must have an ID)
        """
        await self.repo.delete(torrent_download)


class DeleteTorrentDownloadByIdUseCase:
    """Use case for deleting a torrent download by ID."""
    
    def __init__(self, repo: TorrentDownloadRepoPort):
        self.repo = repo
    
    async def execute(self, torrent_id: int) -> bool:
        """
        Delete a torrent download by its ID.
        
        Args:
            torrent_id: The ID of the torrent download to delete
            
        Returns:
            True if deleted, False if not found
        """
        return await self.repo.delete_by_id(torrent_id)

