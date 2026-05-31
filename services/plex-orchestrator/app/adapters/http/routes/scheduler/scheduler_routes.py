"""HTTP routes to inspect and manually run background scheduler jobs."""
from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException

from app.adapters.http.schemas.scheduler.scheduler_schemas import (
    ProcessPlexWatchlistDownloadsResult,
    RunSchedulerJobResponse,
    SchedulerJobInfo,
)
from app.application.pipelines.watchlist.models.watchlist_download_run_result import (
    ProcessPlexWatchlistDownloadsResult as ProcessPlexWatchlistDownloadsResultModel,
)
from app.infrastructure.scheduler.access import get_scheduler_service
from app.infrastructure.scheduler.scheduler_service import SchedulerService

scheduler_routes = APIRouter(prefix="/scheduler", tags=["scheduler"])


def _scheduler_dep() -> SchedulerService:
    return get_scheduler_service()


@scheduler_routes.get("/jobs", response_model=list[SchedulerJobInfo])
async def list_scheduler_jobs(
    scheduler: SchedulerService = Depends(_scheduler_dep),
):
    """List registered interval jobs and their next run time."""
    return scheduler.list_jobs()


@scheduler_routes.post(
    "/jobs/{job_id}/run",
    response_model=RunSchedulerJobResponse,
    summary="Run a scheduler job immediately",
)
async def run_scheduler_job(
    job_id: str,
    scheduler: SchedulerService = Depends(_scheduler_dep),
):
    """
    Manually trigger a background job.

    **download_watch_list_media** — full watchlist orchestration:
    fetch watchlists for active Plex users, skip items already in the library or
    already queued, search Prowlarr, and send torrents to Deluge (or defer when
    download volume is full).
    """
    jobs = {job.id: job for job in scheduler.list_jobs()}
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail=f"Unknown scheduler job: {job_id}")

    try:
        payload = await scheduler.run_job_now(job_id)
    except KeyError:
        raise HTTPException(
            status_code=404, detail=f"No manual runner registered for job: {job_id}"
        ) from None
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Scheduler job {job_id!r} failed: {exc}"
        ) from exc

    response = RunSchedulerJobResponse(
        job_id=job_id,
        job_name=jobs[job_id].name,
        message=f"Scheduler job {job_id!r} completed",
    )
    if isinstance(payload, ProcessPlexWatchlistDownloadsResultModel):
        response.watchlist_downloads = ProcessPlexWatchlistDownloadsResult.model_validate(
            payload.model_dump()
        )
    elif hasattr(payload, "__dataclass_fields__"):
        if job_id == "process_deferred_downloads":
            response.deferred = asdict(payload)
    elif hasattr(payload, "model_dump"):
        if job_id == "process_deluge_torrents":
            response.deluge_maintenance = payload.model_dump()
    elif isinstance(payload, dict):
        response.library_paths = payload
    return response


@scheduler_routes.post(
    "/watchlist-downloads/run",
    response_model=ProcessPlexWatchlistDownloadsResult,
    summary="Run watchlist download orchestration now",
)
async def run_watchlist_downloads(
    scheduler: SchedulerService = Depends(_scheduler_dep),
):
    """
    Shortcut for **POST /scheduler/jobs/download_watch_list_media/run**.

    Same pipeline the scheduler runs on its interval:
    watchlist → skip if in Plex library → Prowlarr search → Deluge.
    """
    try:
        payload = await scheduler.run_job_now("download_watch_list_media")
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Watchlist orchestration failed: {exc}"
        ) from exc
    if not isinstance(payload, ProcessPlexWatchlistDownloadsResultModel):
        raise HTTPException(
            status_code=500,
            detail="Watchlist orchestration returned an unexpected result",
        )
    return ProcessPlexWatchlistDownloadsResult.model_validate(payload.model_dump())
