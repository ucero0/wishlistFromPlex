"""Use case for updating a torrent download."""
from app.domain.ports.repositories.active_downloads.active_download_repository_port import ActiveDownloadRepositoryPort
from app.domain.models.active_download import ActiveDownload


class UpdateActiveDownloadUseCase:
    """Use case for updating an existing torrent download."""
    
    def __init__(self, repo: ActiveDownloadRepositoryPort):
        self.repo = repo
    
    async def execute(self, torrent_download: ActiveDownload) -> ActiveDownload:
        """
        Update an existing torrent download.
        
        Args:
            torrent_download: The torrent download to update (must have an ID)
            
        Returns:
            The updated ActiveDownload
        """
        return await self.repo.update(torrent_download)

