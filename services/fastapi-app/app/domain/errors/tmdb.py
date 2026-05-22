"""Domain errors for TMDB integration."""
from app.domain.errors.external import ExternalServiceError


class TMDBError(ExternalServiceError):
    service = "tmdb"


class TMDBConnectionError(TMDBError):
    """TMDB API is unreachable."""


class TMDBOperationError(TMDBError):
    """TMDB API call failed."""


class TMDBConfigurationError(TMDBError):
    """TMDB API key is missing or invalid."""
