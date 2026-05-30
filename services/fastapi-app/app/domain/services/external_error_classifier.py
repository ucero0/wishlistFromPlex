"""Classify external-service domain errors (transport-agnostic, no HTTP codes)."""
from app.domain.errors.antivirus import (
    AntivirusConnectionError,
    AntivirusPathNotFoundError,
)
from app.domain.errors.deluge import (
    DelugeConnectionError,
    DelugeTorrentNotFoundError,
)
from app.domain.errors.external import ExternalServiceError
from app.domain.errors.gluetun import GluetunConnectionError, GluetunUnhealthyError
from app.domain.errors.plex import (
    PlexAuthError,
    PlexConnectionError,
    PlexLibraryPathNoSpaceError,
    PlexLibraryPathNotConfiguredError,
    PlexServerAdminTokenNotConfiguredError,
    PlexServerAuthError,
    PlexUserAuthError,
)
from app.domain.errors.prowlarr import (
    ProwlarrConnectionError,
    ProwlarrDownloadError,
)
from app.domain.errors.tmdb import TMDBConfigurationError, TMDBConnectionError


def classify_external_service_error(exc: ExternalServiceError) -> str:
    """Return a stable machine-readable category for any external service error."""
    if isinstance(
        exc,
        (
            DelugeTorrentNotFoundError,
            AntivirusPathNotFoundError,
        ),
    ):
        return "not_found"
    if isinstance(exc, PlexServerAuthError):
        return "server_auth"
    if isinstance(exc, PlexUserAuthError):
        return "user_auth"
    if isinstance(exc, PlexAuthError):
        return "auth"
    if isinstance(exc, PlexServerAdminTokenNotConfiguredError):
        return "configuration"
    if isinstance(exc, PlexLibraryPathNotConfiguredError):
        return "library_paths_not_synced"
    if isinstance(exc, PlexLibraryPathNoSpaceError):
        return "insufficient_storage"
    if isinstance(exc, TMDBConfigurationError):
        return "configuration"
    if isinstance(
        exc,
        (
            DelugeConnectionError,
            ProwlarrConnectionError,
            AntivirusConnectionError,
            PlexConnectionError,
            TMDBConnectionError,
            GluetunConnectionError,
        ),
    ):
        return "connection"
    if isinstance(exc, GluetunUnhealthyError):
        return "unhealthy"
    if isinstance(exc, ProwlarrDownloadError):
        return "download"
    return "operation"
