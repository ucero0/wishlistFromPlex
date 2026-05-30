"""Factory for blacklist torrent query and use cases."""
from fastapi import Depends
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
from app.composition.blacklist_torrent import (
    build_add_torrent_to_blacklist_by_hash_use_case,
    build_add_torrent_to_blacklist_use_case,
    build_get_blacklist_torrent_by_guid_query,
    build_is_blacklisted_by_guid_prowlarr_query,
    build_list_blacklist_torrents_query,
    build_remove_torrent_from_blacklist_use_case,
)
from app.infrastructure.persistence.database import get_db


def create_is_blacklisted_by_guid_prowlarr_query(
    session: AsyncSession = Depends(get_db),
) -> IsBlacklistedByGuidProwlarrQuery:
    return build_is_blacklisted_by_guid_prowlarr_query(session)


def create_add_torrent_to_blacklist_use_case(
    session: AsyncSession = Depends(get_db),
) -> AddTorrentToBlacklistUseCase:
    return build_add_torrent_to_blacklist_use_case(session)


def create_list_blacklist_torrents_query(
    session: AsyncSession = Depends(get_db),
) -> ListBlacklistTorrentsQuery:
    return build_list_blacklist_torrents_query(session)


def create_get_blacklist_torrent_by_guid_query(
    session: AsyncSession = Depends(get_db),
) -> GetBlacklistTorrentByGuidQuery:
    return build_get_blacklist_torrent_by_guid_query(session)


def create_remove_torrent_from_blacklist_use_case(
    session: AsyncSession = Depends(get_db),
) -> RemoveTorrentFromBlacklistUseCase:
    return build_remove_torrent_from_blacklist_use_case(session)


def create_add_torrent_to_blacklist_by_hash_use_case(
    session: AsyncSession = Depends(get_db),
) -> AddTorrentToBlacklistByHashUseCase:
    return build_add_torrent_to_blacklist_by_hash_use_case(session)
