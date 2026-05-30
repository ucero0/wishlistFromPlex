"""FastAPI DI for watchlist download pipeline."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.pipelines.watchlist.use_cases.process_plex_watchlist_downloads_use_case import (
    ProcessPlexWatchlistDownloadsUseCase,
)
from app.composition.watchlist_pipeline import build_process_plex_watchlist_downloads_use_case
from app.infrastructure.persistence.database import get_db


def create_process_plex_watchlist_downloads_use_case(
    session: AsyncSession = Depends(get_db),
) -> ProcessPlexWatchlistDownloadsUseCase:
    return build_process_plex_watchlist_downloads_use_case(session=session)
