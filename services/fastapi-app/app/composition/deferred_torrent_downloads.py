"""Composition helpers for deferred torrent download queue."""
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.deferredTorrent.useCases.enqueueDeferredTorrentDownload import (
    EnqueueDeferredTorrentDownloadUseCase,
)
from app.application.deferredTorrent.useCases.processDeferredTorrentDownloads import (
    ProcessDeferredTorrentDownloadsUseCase,
)
from app.application.torrentDownload.services.sendTorrentToDeluge import (
    SendTorrentToDelugeService,
)
from app.composition.infrastructure_services import build_download_volume_space_checker
from app.factories.deluge.delugeFactory import createGetTorrentByNameQuery
from app.factories.plex.plexWatchListFactory import createRemoveWatchListItemUseCase
from app.factories.prowlarr.prowlarrFactory import createDownloadTorrentUseCase
from app.factories.torrentDownload.torrentDownloadFactory import (
    create_create_torrent_download_use_case,
)
from app.infrastructure.persistence.deferredTorrent.repo.deferredTorrentRepo import (
    DeferredTorrentRepository,
)


def build_send_torrent_to_deluge_service() -> SendTorrentToDelugeService:
    return SendTorrentToDelugeService(
        createDownloadTorrentUseCase(),
        createGetTorrentByNameQuery(),
    )


def build_enqueue_deferred_torrent_download_use_case(
    session: AsyncSession,
) -> EnqueueDeferredTorrentDownloadUseCase:
    return EnqueueDeferredTorrentDownloadUseCase(
        DeferredTorrentRepository(session),
        build_download_volume_space_checker(),
    )


def build_process_deferred_torrent_downloads_use_case(
    session: AsyncSession,
) -> ProcessDeferredTorrentDownloadsUseCase:
    return ProcessDeferredTorrentDownloadsUseCase(
        DeferredTorrentRepository(session),
        build_download_volume_space_checker(),
        build_send_torrent_to_deluge_service(),
        create_create_torrent_download_use_case(session),
        createRemoveWatchListItemUseCase(),
    )
