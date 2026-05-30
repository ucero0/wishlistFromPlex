"""Use case for creating a torrent download."""
from app.domain.ports.repositories.active_downloads.active_download_repository_port import ActiveDownloadRepositoryPort
from app.domain.models.active_download import ActiveDownload


class CreateActiveDownloadUseCase:
    """Use case for creating a new torrent download."""
    
    def __init__(self, repo: ActiveDownloadRepositoryPort):
        self.repo = repo
    
    async def execute(self, torrent_download: ActiveDownload) -> ActiveDownload:
        """
        Create a new torrent download.
        
        Args:
            torrent_download: The torrent download to create
            
        Returns:
            The created ActiveDownload with ID and timestamps
        """
        return await self.repo.create(torrent_download)

