"""Scheduled task implementations."""
import logging
from app.infrastructure.persistence.database import AsyncSessionLocal
from app.factories.orchestrators.findFiles2Download import create_download_watch_list_media_use_case

logger = logging.getLogger(__name__)


async def download_watch_list_media_task():
    """Scheduled task to download watch list media."""
    try:
        logger.info("Running scheduled task: download watch list media")
        # Create a database session for this task
        async with AsyncSessionLocal() as session:
            # Use the orchestrator factory directly
            use_case = create_download_watch_list_media_use_case(session=session)
            await use_case.execute()
        logger.info("Scheduled task completed successfully")
    except Exception as e:
        logger.error(f"Error in scheduled task: {e}", exc_info=True)

