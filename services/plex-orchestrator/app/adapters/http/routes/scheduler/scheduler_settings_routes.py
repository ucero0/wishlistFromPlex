"""Runtime scheduler and operational settings (database-backed)."""
from fastapi import APIRouter, Depends

from app.adapters.http.schemas.settings.runtime_settings_schemas import (
    RuntimeSettingsResponse,
    UpdateRuntimeSettingsRequest,
)
from app.adapters.http.security.dependencies import APIKey
from app.application.settings.services.runtime_settings_service import (
    runtime_settings_service,
)
from app.domain.models.runtime_settings import RuntimeSettingsUpdate
from app.infrastructure.scheduler.access import get_scheduler_service

scheduler_settings_routes = APIRouter()


@scheduler_settings_routes.get(
    "/settings",
    response_model=RuntimeSettingsResponse,
    summary="Get runtime scheduler and operational settings",
)
async def get_scheduler_settings(_api_key: APIKey):
    """
    Values from PostgreSQL plus current APScheduler intervals (after reschedule).

    Interval changes from PUT apply immediately to running jobs (no restart).
    """
    config = await runtime_settings_service.get()
    jobs = get_scheduler_service().list_jobs()
    return RuntimeSettingsResponse.from_domain(config, scheduler_jobs=jobs)


@scheduler_settings_routes.put(
    "/settings",
    response_model=RuntimeSettingsResponse,
    summary="Update runtime scheduler and operational settings",
)
async def update_scheduler_settings(
    request: UpdateRuntimeSettingsRequest,
    _api_key: APIKey,
):
    """
    Patch any subset of fields.

    Scheduler interval fields reschedule jobs immediately.
    Download buffer / TV ahead values apply on the next use case run.
    """
    scheduler = get_scheduler_service()
    if not request.model_dump(exclude_unset=True):
        config = await runtime_settings_service.get()
        jobs = scheduler.list_jobs()
        return RuntimeSettingsResponse.from_domain(config, scheduler_jobs=jobs)

    config = await runtime_settings_service.update(
        RuntimeSettingsUpdate.model_validate(request.model_dump(exclude_unset=True)),
        scheduler=scheduler,
    )
    jobs = scheduler.list_jobs()
    return RuntimeSettingsResponse.from_domain(config, scheduler_jobs=jobs)
