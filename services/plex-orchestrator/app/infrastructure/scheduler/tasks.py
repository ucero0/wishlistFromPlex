"""Scheduled task implementations."""
import asyncio
import logging

from app.composition.deferred_downloads import (
    build_process_deferred_downloads_use_case,
)
from app.composition.watchlist_pipeline import build_process_plex_watchlist_downloads_use_case
from app.composition.plex_library_paths import (
    build_sync_plex_library_paths_for_active_users_use_case,
)
from app.infrastructure.persistence.database import async_session_scope

logger = logging.getLogger(__name__)


async def download_watch_list_media_task():
    """Scheduled task to download watch list media."""
    try:
        logger.info("Running scheduled task: download watch list media")
        result = await run_watchlist_downloads_now()
        logger.info(
            "Watchlist download run: entries=%s sent=%s deferred=%s skipped=%s no_torrent=%s failed=%s",
            result.watchlist_entries,
            result.sent_to_deluge,
            result.deferred,
            result.skipped,
            result.no_torrent,
            result.send_failed,
        )
        return result
    except asyncio.CancelledError:
        logger.warning("Scheduled task was cancelled")
        raise
    except Exception as e:
        logger.error(f"Error in scheduled task: {e}", exc_info=True)
        raise


async def run_watchlist_downloads_now():
    """On-demand watchlist orchestration (same logic as the scheduler job)."""
    async with async_session_scope() as session:
        use_case = build_process_plex_watchlist_downloads_use_case(session=session)
        return await use_case.execute()


async def run_deferred_downloads_now():
    async with async_session_scope() as session:
        use_case = build_process_deferred_downloads_use_case(session)
        return await use_case.execute()


async def run_sync_plex_library_paths_now():
    async with async_session_scope() as session:
        use_case = build_sync_plex_library_paths_for_active_users_use_case(session)
        return await use_case.execute()


async def process_deferred_downloads_task():
    """Try to send queued torrents to Prowlarr when download volume has space."""
    try:
        logger.info("Running scheduled task: process deferred torrent downloads")
        result = await run_deferred_downloads_now()
        logger.info(
            "Deferred torrent processing: checked=%s sent=%s pending=%s failed=%s",
            result.checked,
            result.sent,
            result.still_pending,
            result.failed,
        )
        return result
    except asyncio.CancelledError:
        logger.warning("Deferred torrent task was cancelled")
        raise
    except Exception as e:
        logger.error("Error processing deferred torrents: %s", e, exc_info=True)
        raise


async def sync_plex_library_paths_task():
    """
    Pull library locations from Plex Server API and update the database.

    Deactivates paths removed in Plex; adds or reactivates new folders.
    """
    try:
        logger.info("Running scheduled task: sync Plex library paths from server")
        result = await run_sync_plex_library_paths_now()
        logger.info(
            "Plex library path sync done: users=%s paths=%s active=%s errors=%s",
            result["users_synced"],
            result["synced_from_server"],
            result["active_in_database"],
            len(result["errors"]),
        )
        return result
    except asyncio.CancelledError:
        logger.warning("Plex library path sync task was cancelled")
        raise
    except Exception as e:
        logger.error("Error syncing Plex library paths: %s", e, exc_info=True)
        raise


def register_scheduler_manual_runners(scheduler_service) -> None:
    """Wire on-demand runners for each registered scheduler job."""
    scheduler_service.register_manual_runner(
        "download_watch_list_media",
        run_watchlist_downloads_now,
    )
    scheduler_service.register_manual_runner(
        "sync_plex_library_paths",
        run_sync_plex_library_paths_now,
    )
    scheduler_service.register_manual_runner(
        "process_deferred_downloads",
        run_deferred_downloads_now,
    )
