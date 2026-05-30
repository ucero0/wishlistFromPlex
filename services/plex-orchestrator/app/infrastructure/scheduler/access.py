"""Access to the process-wide scheduler instance."""
from app.infrastructure.scheduler.scheduler_service import SchedulerService

_scheduler: SchedulerService | None = None


def bind_scheduler(service: SchedulerService) -> None:
    global _scheduler
    _scheduler = service


def get_scheduler_service() -> SchedulerService:
    if _scheduler is None:
        raise RuntimeError("Scheduler service is not initialized")
    return _scheduler
