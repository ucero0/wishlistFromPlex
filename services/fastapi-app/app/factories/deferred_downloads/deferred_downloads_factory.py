"""Factories for deferred torrent download queue."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.deferred_downloads.queries.list_deferred_downloads_query import (
    ListDeferredDownloadsQuery,
)
from app.application.deferred_downloads.use_cases.process_deferred_downloads_use_case import (
    ProcessDeferredDownloadsUseCase,
)
from app.composition.deferred_downloads import (
    build_list_deferred_downloads_query,
    build_process_deferred_downloads_use_case,
)
from app.infrastructure.persistence.database import get_db


def create_list_deferred_downloads_query(
    session: AsyncSession = Depends(get_db),
) -> ListDeferredDownloadsQuery:
    return build_list_deferred_downloads_query(session)


def create_process_deferred_downloads_use_case(
    session: AsyncSession = Depends(get_db),
) -> ProcessDeferredDownloadsUseCase:
    return build_process_deferred_downloads_use_case(session)
