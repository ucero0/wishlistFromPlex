"""FastAPI DI for scan and ingest pipeline."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.pipelines.ingest.use_cases.scan_and_ingest_torrent_use_case import (
    ScanAndIngestTorrentUseCase,
)
from app.application.pipelines.ingest.use_cases.scan_torrent_use_case import (
    ScanTorrentUseCase,
)
from app.composition.ingest_pipeline import (
    build_scan_and_ingest_torrent_use_case,
    build_scan_torrent_use_case,
)
from app.infrastructure.persistence.database import get_db


def create_scan_torrent_use_case(
    session: AsyncSession = Depends(get_db),
) -> ScanTorrentUseCase:
    return build_scan_torrent_use_case(session)


def create_scan_and_ingest_torrent_use_case(
    session: AsyncSession = Depends(get_db),
) -> ScanAndIngestTorrentUseCase:
    return build_scan_and_ingest_torrent_use_case(session)
