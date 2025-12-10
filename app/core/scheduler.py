import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import SessionLocal
from app.modules.orchestration.service import OrchestrationService

logger = logging.getLogger(__name__)

scheduler = None


def run_orchestration_job():
    """Job function to run the orchestration workflow in the background."""
    logger.info("Starting scheduled orchestration job")
    db: Session = SessionLocal()
    try:
        import asyncio
        service = OrchestrationService(db)
        result = asyncio.run(service.run_full_workflow(auto_search=True, force_research=False))
        logger.info(f"Scheduled orchestration completed: {result.get('items_searched', 0)} searched, "
                   f"{result.get('items_added_to_deluge', 0)} added to Deluge")
    except Exception as e:
        logger.error(f"Error in scheduled orchestration: {e}", exc_info=True)
    finally:
        db.close()


def start_scheduler():
    """Start the background scheduler for periodic syncing."""
    global scheduler
    
    if scheduler is not None:
        logger.warning("Scheduler already started")
        return
    
    scheduler = BackgroundScheduler()
    
    # Schedule orchestration job (syncs watchlists, searches torrents, adds to Deluge)
    interval_hours = settings.plex_sync_interval_hours
    scheduler.add_job(
        run_orchestration_job,
        trigger=IntervalTrigger(hours=interval_hours),
        id="orchestration_workflow",
        name="Orchestration Workflow (Sync + Search + Download)",
        replace_existing=True,
    )
    
    scheduler.start()
    logger.info(f"Scheduler started - orchestration workflow will run every {interval_hours} hours")


def stop_scheduler():
    """Stop the background scheduler."""
    global scheduler
    
    if scheduler is None:
        return
    
    scheduler.shutdown()
    scheduler = None
    logger.info("Scheduler stopped")



