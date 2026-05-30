"""Composition root for blacklist torrent queries and use cases."""
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.blacklist_torrent.queries import (
    GetBlacklistTorrentByGuidQuery,
    IsBlacklistedByGuidProwlarrQuery,
    ListBlacklistTorrentsQuery,
)
from app.application.blacklist_torrent.use_cases import (
    AddTorrentToBlacklistByHashUseCase,
    AddTorrentToBlacklistUseCase,
    RemoveTorrentFromBlacklistUseCase,
)
from app.composition.persistence import build_blacklist_torrent_repository
from app.composition.active_downloads import build_get_active_download_by_uid_query


def build_is_blacklisted_by_guid_prowlarr_query(
    session: AsyncSession,
) -> IsBlacklistedByGuidProwlarrQuery:
    return IsBlacklistedByGuidProwlarrQuery(build_blacklist_torrent_repository(session))


def build_add_torrent_to_blacklist_use_case(
    session: AsyncSession,
) -> AddTorrentToBlacklistUseCase:
    return AddTorrentToBlacklistUseCase(build_blacklist_torrent_repository(session))


def build_list_blacklist_torrents_query(
    session: AsyncSession,
) -> ListBlacklistTorrentsQuery:
    return ListBlacklistTorrentsQuery(build_blacklist_torrent_repository(session))


def build_get_blacklist_torrent_by_guid_query(
    session: AsyncSession,
) -> GetBlacklistTorrentByGuidQuery:
    return GetBlacklistTorrentByGuidQuery(build_blacklist_torrent_repository(session))


def build_remove_torrent_from_blacklist_use_case(
    session: AsyncSession,
) -> RemoveTorrentFromBlacklistUseCase:
    return RemoveTorrentFromBlacklistUseCase(build_blacklist_torrent_repository(session))


def build_add_torrent_to_blacklist_by_hash_use_case(
    session: AsyncSession,
) -> AddTorrentToBlacklistByHashUseCase:
    return AddTorrentToBlacklistByHashUseCase(
        build_get_active_download_by_uid_query(session),
        build_add_torrent_to_blacklist_use_case(session),
    )
