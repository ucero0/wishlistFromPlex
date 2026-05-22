"""Scheduled task implementations."""
import asyncio
import logging

from app.composition.deferred_torrent_downloads import (
    build_process_deferred_torrent_downloads_use_case,
)
from app.composition.orchestrators import build_download_watch_list_media_use_case
from app.composition.plex_library_paths import (
    build_sync_plex_library_paths_for_active_users_use_case,
)
from app.infrastructure.persistence.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


async def download_watch_list_media_task():
    """Scheduled task to download watch list media."""
    try:
        logger.info("Running scheduled task: download watch list media")
        # Create a database session for this task
        async with AsyncSessionLocal() as session:
            use_case = build_download_watch_list_media_use_case(session=session)
            await use_case.execute()
        logger.info("Scheduled task completed successfully")
    except asyncio.CancelledError:
        logger.warning("Scheduled task was cancelled")
        raise  # Re-raise cancellation
    except Exception as e:
        logger.error(f"Error in scheduled task: {e}", exc_info=True)


async def process_deferred_torrent_downloads_task():
    """Try to send queued torrents to Prowlarr when download volume has space."""
    try:
        logger.info("Running scheduled task: process deferred torrent downloads")
        async with AsyncSessionLocal() as session:
            use_case = build_process_deferred_torrent_downloads_use_case(session)
            result = await use_case.execute()
        logger.info(
            "Deferred torrent processing: checked=%s sent=%s pending=%s failed=%s",
            result.checked,
            result.sent,
            result.still_pending,
            result.failed,
        )
    except asyncio.CancelledError:
        logger.warning("Deferred torrent task was cancelled")
        raise
    except Exception as e:
        logger.error("Error processing deferred torrents: %s", e, exc_info=True)


async def sync_plex_library_paths_task():
    """
    Pull library locations from Plex Server API and update the database.

    Deactivates paths removed in Plex; adds or reactivates new folders.
    """
    try:
        logger.info("Running scheduled task: sync Plex library paths from server")
        async with AsyncSessionLocal() as session:
            use_case = build_sync_plex_library_paths_for_active_users_use_case(session)
            result = await use_case.execute()
        logger.info(
            "Plex library path sync done: users=%s paths=%s active=%s errors=%s",
            result["users_synced"],
            result["synced_from_server"],
            result["active_in_database"],
            len(result["errors"]),
        )
    except asyncio.CancelledError:
        logger.warning("Plex library path sync task was cancelled")
        raise
    except Exception as e:
        logger.error("Error syncing Plex library paths: %s", e, exc_info=True)

