"""Use case for triggering partial scan of Plex library."""
import logging
from app.domain.ports.external.plex.plexServerLibraryProvider import PlexServerLibraryProvider

logger = logging.getLogger(__name__)


class PartialScanLibraryUseCase:
    """Use case for triggering a partial scan of the Plex library."""
    
    def __init__(self, provider: PlexServerLibraryProvider):
        self.provider = provider
    
    async def execute(
        self, 
        user_token: str, 
        section_id: int, 
        folder_path: str
    ) -> bool:
        """
        Trigger a partial scan of a specific folder in the Plex library.
        
        Args:
            user_token: Plex user token
            section_id: Library section ID
            folder_path: Absolute path to the folder to scan
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Triggering partial scan for section {section_id}, folder: {folder_path}")
        try:
            result = await self.provider.partial_scan_library(user_token, section_id, folder_path)
            if result:
                logger.info(f"Successfully triggered partial scan for section {section_id}")
            return result
        except Exception as e:
            logger.error(f"Error triggering partial scan: {e}", exc_info=True)
            raise
