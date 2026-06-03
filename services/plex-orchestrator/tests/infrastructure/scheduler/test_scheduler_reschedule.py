"""Tests for hot-rescheduling interval jobs."""
from app.infrastructure.scheduler.scheduler_service import SchedulerService


async def _noop():
    return None


def test_reschedule_interval_updates_trigger():
    service = SchedulerService()
    service.register_interval_task(
        _noop,
        interval_minutes=10,
        job_id="process_deluge_torrents",
        name="Deluge Ingest",
    )
    service.reschedule_interval("process_deluge_torrents", 3)
    jobs = {job.id: job for job in service.scheduler.get_jobs()}
    trigger = jobs["process_deluge_torrents"].trigger
    assert int(trigger.interval.total_seconds() // 60) == 3
