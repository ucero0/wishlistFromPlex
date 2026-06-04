"""Media integrity domain errors."""


class MediaIntegrityError(Exception):
    """Base error for media integrity operations."""


class MediaIntegrityProbeUnavailableError(MediaIntegrityError):
    """Integrity backend (e.g. ffprobe) is missing or not executable."""
