"""Map httpx failures to domain external-service errors."""
import httpx


def raise_mapped_httpx_error(
    exc: Exception,
    *,
    connection_error_type: type,
    operation_error_type: type,
    target: str,
    operation: str,
) -> None:
    """Re-raise httpx errors as typed domain errors."""
    if isinstance(exc, httpx.ConnectError):
        raise connection_error_type(
            f"Cannot connect to {target}: {exc}"
        ) from exc
    if isinstance(exc, httpx.TimeoutException):
        raise operation_error_type(
            f"{operation} timed out for {target}: {exc}"
        ) from exc
    if isinstance(exc, httpx.HTTPStatusError):
        status = exc.response.status_code
        raise operation_error_type(
            f"{operation} failed for {target}: HTTP {status}"
        ) from exc
    if isinstance(exc, (connection_error_type, operation_error_type)):
        raise exc
    raise operation_error_type(
        f"{operation} failed for {target}: {exc}"
    ) from exc
