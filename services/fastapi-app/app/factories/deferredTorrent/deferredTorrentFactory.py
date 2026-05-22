"""Factories for deferred torrent download queue."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.deferredTorrent.queries.listDeferredTorrentDownloads import (
    ListDeferredTorrentDownloadsQuery,
)
from app.application.deferredTorrent.useCases.processDeferredTorrentDownloads import (
    ProcessDeferredTorrentDownloadsUseCase,
)
from app.composition.deferred_torrent_downloads import (
    build_process_deferred_torrent_downloads_use_case,
)
from app.infrastructure.persistence.database import get_db
from app.infrastructure.persistence.deferredTorrent.repo.deferredTorrentRepo import (
    DeferredTorrentRepository,
)


def create_list_deferred_torrent_downloads_query(
    session: AsyncSession = Depends(get_db),
) -> ListDeferredTorrentDownloadsQuery:
    return ListDeferredTorrentDownloadsQuery(DeferredTorrentRepository(session))


def create_process_deferred_torrent_downloads_use_case(
    session: AsyncSession = Depends(get_db),
) -> ProcessDeferredTorrentDownloadsUseCase:
    return build_process_deferred_torrent_downloads_use_case(session)
