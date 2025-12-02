import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import SessionLocal
from app.modules.plex.service import sync_all_users

logger = logging.getLogger(__name__)

scheduler = None


def run_sync_job():
    """Job function to run the sync in the background."""
    logger.info("Starting scheduled sync job")
    db: Session = SessionLocal()
    try:
        # Note: sync_all_users is async, but APScheduler runs sync functions
        # We need to handle this properly - either make sync_all_users sync
        # or use asyncio.run() here
        import asyncio
        result = asyncio.run(sync_all_users(db))
        logger.info(f"Scheduled sync completed: {result}")
    except Exception as e:
        logger.error(f"Error in scheduled sync: {e}", exc_info=True)
    finally:
        db.close()


def start_scheduler():
    """Start the background scheduler for periodic syncing."""
    global scheduler
    
    if scheduler is not None:
        logger.warning("Scheduler already started")
        return
    
    scheduler = BackgroundScheduler()
    
    # Schedule sync job
    interval_hours = settings.plex_sync_interval_hours
    scheduler.add_job(
        run_sync_job,
        trigger=IntervalTrigger(hours=interval_hours),
        id="sync_watchlists",
        name="Sync Plex Watchlists",
        replace_existing=True,
    )
    
    scheduler.start()
    logger.info(f"Scheduler started - sync will run every {interval_hours} hours")


def stop_scheduler():
    """Stop the background scheduler."""
    global scheduler
    
    if scheduler is None:
        return
    
    scheduler.shutdown()
    scheduler = None
    logger.info("Scheduler stopped")



