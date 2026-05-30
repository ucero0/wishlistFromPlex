"""Composition root helpers for deferred torrent download queue."""
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.deferred_downloads.queries.list_deferred_downloads_query import (
    ListDeferredDownloadsQuery,
)
from app.application.deferred_downloads.use_cases.enqueue_deferred_download_use_case import (
    EnqueueDeferredDownloadUseCase,
)
from app.application.deferred_downloads.use_cases.process_deferred_downloads_use_case import (
    ProcessDeferredDownloadsUseCase,
)
from app.application.active_downloads.services.send_torrent_to_deluge_service import (
    SendTorrentToDelugeService,
)
from app.composition.infrastructure_services import build_download_volume_space_checker
from app.composition.persistence import build_deferred_download_repository
from app.composition.active_downloads import build_create_active_download_use_case
from app.composition.deluge import build_get_torrent_by_name_query
from app.composition.plex_external import build_remove_watchlist_item_use_case
from app.composition.prowlarr import build_download_torrent_use_case


def build_send_torrent_to_deluge_service() -> SendTorrentToDelugeService:
    return SendTorrentToDelugeService(
        build_download_torrent_use_case(),
        build_get_torrent_by_name_query(),
    )


def build_list_deferred_downloads_query(
    session: AsyncSession,
) -> ListDeferredDownloadsQuery:
    return ListDeferredDownloadsQuery(build_deferred_download_repository(session))


def build_enqueue_deferred_download_use_case(
    session: AsyncSession,
) -> EnqueueDeferredDownloadUseCase:
    return EnqueueDeferredDownloadUseCase(
        build_deferred_download_repository(session),
        build_download_volume_space_checker(),
    )


def build_process_deferred_downloads_use_case(
    session: AsyncSession,
) -> ProcessDeferredDownloadsUseCase:
    return ProcessDeferredDownloadsUseCase(
        build_deferred_download_repository(session),
        build_download_volume_space_checker(),
        build_send_torrent_to_deluge_service(),
        build_create_active_download_use_case(session),
        build_remove_watchlist_item_use_case(),
    )
