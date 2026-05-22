"""Map domain external-service errors to HTTP responses."""
from fastapi import Request
from fastapi.responses import JSONResponse

from app.adapters.http.schemas.common.external_service_schemas import (
    ExternalServiceErrorResponse,
)
from app.domain.errors.antivirus import (
    AntivirusConnectionError,
    AntivirusOperationError,
    AntivirusPathNotFoundError,
)
from app.domain.errors.deluge import (
    DelugeConnectionError,
    DelugeOperationError,
    DelugeTorrentNotFoundError,
)
from app.domain.errors.external import ExternalServiceError
from app.domain.errors.plex import (
    PlexAuthError,
    PlexConnectionError,
    PlexLibraryPathNoSpaceError,
    PlexLibraryPathNotConfiguredError,
    PlexOperationError,
)
from app.domain.errors.prowlarr import (
    ProwlarrConnectionError,
    ProwlarrDownloadError,
    ProwlarrOperationError,
)
from app.domain.errors.tmdb import (
    TMDBConfigurationError,
    TMDBConnectionError,
    TMDBOperationError,
)
from app.domain.errors.gluetun import GluetunConnectionError, GluetunUnhealthyError


def _error_response(
    *,
    status_code: int,
    service: str,
    error_type: str,
    detail: str,
) -> JSONResponse:
    body = ExternalServiceErrorResponse(
        service=service,
        error_type=error_type,
        detail=detail,
    )
    return JSONResponse(status_code=status_code, content=body.model_dump())


def _status_and_type(exc: ExternalServiceError) -> tuple[int, str]:
    if isinstance(
        exc,
        (
            DelugeTorrentNotFoundError,
            AntivirusPathNotFoundError,
        ),
    ):
        return 404, "not_found"
    if isinstance(exc, PlexAuthError):
        return 401, "auth"
    if isinstance(exc, PlexLibraryPathNotConfiguredError):
        return 412, "library_paths_not_synced"
    if isinstance(exc, PlexLibraryPathNoSpaceError):
        return 507, "insufficient_storage"
    if isinstance(
        exc,
        (
            DelugeConnectionError,
            ProwlarrConnectionError,
            AntivirusConnectionError,
            PlexConnectionError,
            TMDBConnectionError,
            TMDBConfigurationError,
            GluetunConnectionError,
        ),
    ):
        return 503, "connection"
    if isinstance(exc, GluetunUnhealthyError):
        return 503, "unhealthy"
    if isinstance(exc, ProwlarrDownloadError):
        return 502, "download"
    return 502, "operation"


async def external_service_error_handler(
    _request: Request,
    exc: ExternalServiceError,
) -> JSONResponse:
    status_code, error_type = _status_and_type(exc)
    return _error_response(
        status_code=status_code,
        service=exc.service,
        error_type=error_type,
        detail=exc.message,
    )
