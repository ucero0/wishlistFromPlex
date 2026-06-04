"""Composition root for media integrity verification."""
from app.adapters.external.media_integrity.adapter import MediaIntegrityAdapter
from app.application.pipelines.ingest.use_cases.verify_media_integrity_use_case import (
    VerifyMediaIntegrityUseCase,
)
from app.core.config import settings
from app.infrastructure.external_apis.media_integrity.ffprobe_client import (
    FfprobeMediaIntegrityClient,
)


def build_media_integrity_provider() -> MediaIntegrityAdapter:
    return MediaIntegrityAdapter(
        FfprobeMediaIntegrityClient(
            ffprobe_bin=settings.ffprobe_bin,
            timeout_seconds=settings.media_integrity_timeout_seconds,
            min_file_bytes=settings.media_integrity_min_file_bytes,
        )
    )


def build_verify_media_integrity_use_case(
    filesystem_service,
) -> VerifyMediaIntegrityUseCase:
    return VerifyMediaIntegrityUseCase(
        filesystem_service=filesystem_service,
        media_integrity_provider=build_media_integrity_provider(),
    )
