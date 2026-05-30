"""Domain errors for Plex integrations (server + watchlist)."""
from app.domain.errors.external import ExternalServiceError


class PlexError(ExternalServiceError):
    service = "plex"


class PlexConnectionError(PlexError):
    """Plex API is unreachable."""


class PlexOperationError(PlexError):
    """Plex API call failed (HTTP or invalid response)."""


class PlexAuthError(PlexError):
    """Plex token is invalid or unauthorized."""


class PlexServerAdminTokenNotConfiguredError(PlexError):
    """Server admin token is missing from configuration."""


class PlexServerAuthError(PlexAuthError):
    """PLEX_SERVER_ADMIN_TOKEN is invalid or unauthorized for this Plex server."""


class PlexUserAuthError(PlexAuthError):
    """A Plex user watchlist token is invalid or unauthorized."""


class PlexLibraryPathNotConfiguredError(PlexError):
    """No active library paths in DB for the media type (sync from Plex first)."""


class PlexLibraryPathNoSpaceError(PlexError):
    """No library path has enough free disk space for the ingest."""
