"""Factory for blacklist torrent query and use cases."""
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.infrastructure.persistence.database import get_db
from app.infrastructure.persistence.blacklist_torrent.repo.blacklist_torrent_repository import (
    BlacklistTorrentRepository,
)
from app.application.blacklist_torrent.queries import (
    IsBlacklistedByGuidProwlarrQuery,
    ListBlacklistTorrentsQuery,
    GetBlacklistTorrentByGuidQuery,
)
from app.application.blacklist_torrent.use_cases import (
    AddTorrentToBlacklistUseCase,
    AddTorrentToBlacklistByHashUseCase,
    RemoveTorrentFromBlacklistUseCase,
)
from app.factories.torrentDownload import create_get_torrent_download_by_uid_query


def _get_repo(session: AsyncSession) -> BlacklistTorrentRepository:
    return BlacklistTorrentRepository(session)


def create_is_blacklisted_by_guid_prowlarr_query(
    session: AsyncSession = Depends(get_db)
) -> IsBlacklistedByGuidProwlarrQuery:
    """Factory for IsBlacklistedByGuidProwlarrQuery (do not send to Deluge if blacklisted)."""
    return IsBlacklistedByGuidProwlarrQuery(_get_repo(session))


def create_add_torrent_to_blacklist_use_case(
    session: AsyncSession = Depends(get_db)
) -> AddTorrentToBlacklistUseCase:
    """Factory for AddTorrentToBlacklistUseCase (add with reason: infected, unhealthy, etc.)."""
    return AddTorrentToBlacklistUseCase(_get_repo(session))


def create_list_blacklist_torrents_query(
    session: AsyncSession = Depends(get_db)
) -> ListBlacklistTorrentsQuery:
    """Factory for ListBlacklistTorrentsQuery (list all blacklist entries)."""
    return ListBlacklistTorrentsQuery(_get_repo(session))


def create_get_blacklist_torrent_by_guid_query(
    session: AsyncSession = Depends(get_db)
) -> GetBlacklistTorrentByGuidQuery:
    """Factory for GetBlacklistTorrentByGuidQuery (get one entry by GUID)."""
    return GetBlacklistTorrentByGuidQuery(_get_repo(session))


def create_remove_torrent_from_blacklist_use_case(
    session: AsyncSession = Depends(get_db)
) -> RemoveTorrentFromBlacklistUseCase:
    """Factory for RemoveTorrentFromBlacklistUseCase (remove entry by GUID)."""
    return RemoveTorrentFromBlacklistUseCase(_get_repo(session))


def create_add_torrent_to_blacklist_by_hash_use_case(
    session: AsyncSession = Depends(get_db)
) -> AddTorrentToBlacklistByHashUseCase:
    """Factory for AddTorrentToBlacklistByHashUseCase (add by torrent hash/uid)."""
    get_torrent = create_get_torrent_download_by_uid_query(session)
    add_use_case = AddTorrentToBlacklistUseCase(_get_repo(session))
    return AddTorrentToBlacklistByHashUseCase(get_torrent, add_use_case)
