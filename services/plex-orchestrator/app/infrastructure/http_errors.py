"""Map httpx failures to domain external-service errors."""
import httpx


def raise_mapped_httpx_error(
    exc: Exception,
    *,
    connection_error_type: type,
    operation_error_type: type,
    target: str,
    operation: str,
    auth_error_type: type | None = None,
    auth_status_codes: tuple[int, ...] = (401, 403),
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
        if auth_error_type is not None and status in auth_status_codes:
            raise auth_error_type(
                f"{operation} unauthorized for {target}: HTTP {status}"
            ) from exc
        raise operation_error_type(
            f"{operation} failed for {target}: HTTP {status}"
        ) from exc
    if isinstance(exc, (connection_error_type, operation_error_type)):
        raise exc
    if auth_error_type is not None and isinstance(exc, auth_error_type):
        raise exc
    raise operation_error_type(
        f"{operation} failed for {target}: {exc}"
    ) from exc
