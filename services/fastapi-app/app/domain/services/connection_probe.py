"""Helpers for non-throwing connectivity probes at the adapter boundary."""
import logging
from collections.abc import Awaitable, Callable

from app.domain.errors.external import ExternalServiceError
from app.domain.models.external_connection import ExternalConnectionStatus
from app.domain.services.external_error_classifier import classify_external_service_error

logger = logging.getLogger(__name__)


def connection_status_from_error(exc: ExternalServiceError) -> ExternalConnectionStatus:
    return ExternalConnectionStatus(
        service=exc.service,
        connected=False,
        error=exc.message,
        error_type=classify_external_service_error(exc),
    )


def connection_status_ok(service: str, **extra) -> ExternalConnectionStatus:
    return ExternalConnectionStatus(service=service, connected=True, **extra)


def capture_sync_connection_probe(
    service: str,
    probe: Callable[[], None],
) -> ExternalConnectionStatus:
    try:
        probe()
        return connection_status_ok(service)
    except ExternalServiceError as exc:
        return connection_status_from_error(exc)
    except Exception as exc:
        logger.exception("Unexpected error probing %s connection", service)
        return ExternalConnectionStatus(
            service=service,
            connected=False,
            error=str(exc),
            error_type="connection",
        )


async def capture_async_connection_probe(
    service: str,
    probe: Callable[[], Awaitable[None]],
) -> ExternalConnectionStatus:
    try:
        await probe()
        return connection_status_ok(service)
    except ExternalServiceError as exc:
        return connection_status_from_error(exc)
    except Exception as exc:
        logger.exception("Unexpected error probing %s connection", service)
        return ExternalConnectionStatus(
            service=service,
            connected=False,
            error=str(exc),
            error_type="connection",
        )
