"""Use case for triggering partial scan of Plex library."""
import logging
from app.domain.ports.external.plex.plex_server_library_provider import PlexServerLibraryProvider

logger = logging.getLogger(__name__)


class PartialScanLibraryUseCase:
    """Use case for triggering a partial scan of the Plex library."""
    
    def __init__(self, provider: PlexServerLibraryProvider):
        self.provider = provider
    
    async def execute(
        self,
        section_id: int,
        folder_path: str,
    ) -> bool:
        """
        Trigger a partial scan of a specific folder in the Plex library.

        Uses PLEX_SERVER_ADMIN_TOKEN (server operator credential).
        """
        logger.info(
            "Triggering partial scan for section %s, folder: %s",
            section_id,
            folder_path,
        )
        try:
            result = await self.provider.partial_scan_library(section_id, folder_path)
            if result:
                logger.info(
                    "Successfully triggered partial scan for section %s", section_id
                )
            return result
        except Exception as e:
            logger.error("Error triggering partial scan: %s", e, exc_info=True)
            raise
