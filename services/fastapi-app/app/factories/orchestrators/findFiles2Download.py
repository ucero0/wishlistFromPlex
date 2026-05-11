from app.application.orchestrators.useCases.downloadWatchListMedia import DownloadWatchListMediaUseCase
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from app.infrastructure.persistence.database import get_db
from app.composition.orchestrators import build_download_watch_list_media_use_case


def create_download_watch_list_media_use_case(
    session: AsyncSession = Depends(get_db)
) -> DownloadWatchListMediaUseCase:
    """FastAPI DI wrapper around the composition root builder."""
    return build_download_watch_list_media_use_case(session=session)

