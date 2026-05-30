"""Map domain external-service errors to HTTP responses."""
from fastapi import Request
from fastapi.responses import JSONResponse

from app.adapters.http.mappers.external_service_http_mapper import (
    external_service_error_to_json_response,
)
from app.domain.errors.external import ExternalServiceError


async def external_service_error_handler(
    _request: Request,
    exc: ExternalServiceError,
) -> JSONResponse:
    return external_service_error_to_json_response(exc)
