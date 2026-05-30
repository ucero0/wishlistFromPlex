"""Domain errors for business and external-service failures."""
from app.domain.errors.antivirus import (
    AntivirusError,
    AntivirusConnectionError,
    AntivirusOperationError,
    AntivirusPathNotFoundError,
)
from app.domain.errors.deluge import (
    DelugeError,
    DelugeConnectionError,
    DelugeOperationError,
    DelugeTorrentNotFoundError,
)
from app.domain.errors.external import ExternalServiceError
from app.domain.errors.plex import (
    PlexError,
    PlexAuthError,
    PlexConnectionError,
    PlexLibraryPathNoSpaceError,
    PlexLibraryPathNotConfiguredError,
    PlexOperationError,
    PlexServerAdminTokenNotConfiguredError,
    PlexServerAuthError,
    PlexUserAuthError,
)
from app.domain.errors.prowlarr import (
    ProwlarrError,
    ProwlarrConnectionError,
    ProwlarrDownloadError,
    ProwlarrOperationError,
)
from app.domain.errors.tmdb import (
    TMDBError,
    TMDBConfigurationError,
    TMDBConnectionError,
    TMDBOperationError,
)

__all__ = [
    "ExternalServiceError",
    "DelugeError",
    "DelugeConnectionError",
    "DelugeOperationError",
    "DelugeTorrentNotFoundError",
    "ProwlarrError",
    "ProwlarrConnectionError",
    "ProwlarrOperationError",
    "ProwlarrDownloadError",
    "AntivirusError",
    "AntivirusConnectionError",
    "AntivirusOperationError",
    "AntivirusPathNotFoundError",
    "PlexError",
    "PlexConnectionError",
    "PlexOperationError",
    "PlexAuthError",
    "PlexServerAdminTokenNotConfiguredError",
    "PlexServerAuthError",
    "PlexUserAuthError",
    "PlexLibraryPathNotConfiguredError",
    "PlexLibraryPathNoSpaceError",
    "TMDBError",
    "TMDBConnectionError",
    "TMDBOperationError",
    "TMDBConfigurationError",
]
