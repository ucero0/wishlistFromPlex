"""Map domain external-service outcomes to HTTP responses (single HTTP boundary)."""
from fastapi.responses import JSONResponse

from app.adapters.http.schemas.common.external_service_schemas import (
    ExternalServiceErrorResponse,
)
from app.domain.errors.external import ExternalServiceError
from app.domain.models.external_connection import ExternalConnectionStatus
from app.domain.services.external_error_classifier import classify_external_service_error

HTTP_STATUS_BY_ERROR_TYPE: dict[str, int] = {
    "not_found": 404,
    "server_auth": 401,
    "user_auth": 401,
    "auth": 401,
    "library_paths_not_synced": 412,
    "insufficient_storage": 507,
    "connection": 503,
    "configuration": 503,
    "unhealthy": 503,
    "download": 502,
    "operation": 502,
}


def http_status_for_error_type(error_type: str | None) -> int:
    if not error_type:
        return 503
    return HTTP_STATUS_BY_ERROR_TYPE.get(error_type, 502)


def http_status_for_external_error(exc: ExternalServiceError) -> tuple[int, str]:
    error_type = classify_external_service_error(exc)
    return http_status_for_error_type(error_type), error_type


def external_service_error_to_json_response(exc: ExternalServiceError) -> JSONResponse:
    status_code, error_type = http_status_for_external_error(exc)
    body = ExternalServiceErrorResponse(
        service=exc.service,
        error_type=error_type,
        detail=exc.message,
    )
    return JSONResponse(status_code=status_code, content=body.model_dump())


def connection_status_to_http_status(status: ExternalConnectionStatus) -> int:
    if status.connected:
        return 200
    return http_status_for_error_type(status.error_type or "connection")


def connection_status_to_response_body(
    status: ExternalConnectionStatus,
    **extra,
) -> dict:
    error_type = status.error_type
    if not status.connected and not error_type:
        error_type = "connection"
    return {
        "connected": status.connected,
        "status": "healthy" if status.connected else "unhealthy",
        "service": status.service,
        "error": status.error,
        "error_type": error_type if not status.connected else None,
        **extra,
    }


def external_connection_to_json_response(
    status: ExternalConnectionStatus,
    **extra,
) -> JSONResponse:
    content = connection_status_to_response_body(status, **extra)
    return JSONResponse(
        status_code=connection_status_to_http_status(status),
        content=content,
    )
