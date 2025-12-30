"""Factory for Antivirus queries and use cases."""
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from app.infrastructure.persistence.database import get_db
from app.infrastructure.persistence.antivirus.repo.antivirus_repository import AntivirusRepository
from app.infrastructure.externalApis.antivirus.client import AntivirusClient
from app.adapters.external.antivirus.adapter import AntivirusAdapter
from app.domain.services.filesystem_service import FilesystemServiceImpl
from app.application.antivirus.queries import (
    CheckInfectedByGuidProwlarrQuery,
    GetAntivirusScanByIdQuery,
    GetAntivirusScansByGuidProwlarrQuery,
    GetAntivirusScanByFilePathQuery,
    GetInfectedItemsQuery,
    GetCleanItemsQuery,
    GetAllAntivirusScansQuery,
)
from app.application.antivirus.useCases import (
    CreateAntivirusScanUseCase,
    UpdateAntivirusScanUseCase,
    DeleteAntivirusScanUseCase,
    DeleteAntivirusScanByIdUseCase,
    DeleteAntivirusScansByGuidProwlarrUseCase,
)
from app.application.antivirus.useCases.scanAndMoveFiles import ScanAndMoveFilesUseCase
from app.factories.torrentDownload.torrentDownloadFactory import create_get_torrent_download_by_uid_query
from app.infrastructure.externalApis.deluge.client import DelugeClient
from app.adapters.external.deluge.adapter import DelugeAdapter


def _get_repo(session: AsyncSession) -> AntivirusRepository:
    """Helper function to create repository instance."""
    return AntivirusRepository(session)


# Query Factories
def create_check_infected_by_guid_prowlarr_query(
    session: AsyncSession = Depends(get_db)
) -> CheckInfectedByGuidProwlarrQuery:
    """Factory function to create CheckInfectedByGuidProwlarrQuery."""
    return CheckInfectedByGuidProwlarrQuery(_get_repo(session))


def create_get_antivirus_scan_by_id_query(
    session: AsyncSession = Depends(get_db)
) -> GetAntivirusScanByIdQuery:
    """Factory function to create GetAntivirusScanByIdQuery."""
    return GetAntivirusScanByIdQuery(_get_repo(session))


def create_get_antivirus_scans_by_guid_prowlarr_query(
    session: AsyncSession = Depends(get_db)
) -> GetAntivirusScansByGuidProwlarrQuery:
    """Factory function to create GetAntivirusScansByGuidProwlarrQuery."""
    return GetAntivirusScansByGuidProwlarrQuery(_get_repo(session))


def create_get_antivirus_scan_by_file_path_query(
    session: AsyncSession = Depends(get_db)
) -> GetAntivirusScanByFilePathQuery:
    """Factory function to create GetAntivirusScanByFilePathQuery."""
    return GetAntivirusScanByFilePathQuery(_get_repo(session))


def create_get_infected_items_query(
    session: AsyncSession = Depends(get_db)
) -> GetInfectedItemsQuery:
    """Factory function to create GetInfectedItemsQuery."""
    return GetInfectedItemsQuery(_get_repo(session))


def create_get_clean_items_query(
    session: AsyncSession = Depends(get_db)
) -> GetCleanItemsQuery:
    """Factory function to create GetCleanItemsQuery."""
    return GetCleanItemsQuery(_get_repo(session))


def create_get_all_antivirus_scans_query(
    session: AsyncSession = Depends(get_db)
) -> GetAllAntivirusScansQuery:
    """Factory function to create GetAllAntivirusScansQuery."""
    return GetAllAntivirusScansQuery(_get_repo(session))


# Use Case Factories
def create_create_antivirus_scan_use_case(
    session: AsyncSession = Depends(get_db)
) -> CreateAntivirusScanUseCase:
    """Factory function to create CreateAntivirusScanUseCase."""
    return CreateAntivirusScanUseCase(_get_repo(session))


def create_update_antivirus_scan_use_case(
    session: AsyncSession = Depends(get_db)
) -> UpdateAntivirusScanUseCase:
    """Factory function to create UpdateAntivirusScanUseCase."""
    return UpdateAntivirusScanUseCase(_get_repo(session))


def create_delete_antivirus_scan_use_case(
    session: AsyncSession = Depends(get_db)
) -> DeleteAntivirusScanUseCase:
    """Factory function to create DeleteAntivirusScanUseCase."""
    return DeleteAntivirusScanUseCase(_get_repo(session))


def create_delete_antivirus_scan_by_id_use_case(
    session: AsyncSession = Depends(get_db)
) -> DeleteAntivirusScanByIdUseCase:
    """Factory function to create DeleteAntivirusScanByIdUseCase."""
    return DeleteAntivirusScanByIdUseCase(_get_repo(session))


def create_delete_antivirus_scans_by_guid_prowlarr_use_case(
    session: AsyncSession = Depends(get_db)
) -> DeleteAntivirusScansByGuidProwlarrUseCase:
    """Factory function to create DeleteAntivirusScansByGuidProwlarrUseCase."""
    return DeleteAntivirusScansByGuidProwlarrUseCase(_get_repo(session))


def create_scan_and_move_files_use_case(
    session: AsyncSession = Depends(get_db)
) -> ScanAndMoveFilesUseCase:
    """Factory function to create ScanAndMoveFilesUseCase with all dependencies."""
    # Antivirus setup
    antivirus_client = AntivirusClient()
    antivirus_adapter = AntivirusAdapter(antivirus_client)
    
    # Filesystem service
    filesystem_service = FilesystemServiceImpl()
    
    # Antivirus repository
    antivirus_repo = _get_repo(session)
    
    # Torrent download query
    get_torrent_download_query = create_get_torrent_download_by_uid_query(session)
    
    # Deluge provider
    deluge_client = DelugeClient()
    deluge_adapter = DelugeAdapter(deluge_client)
    
    return ScanAndMoveFilesUseCase(
        antivirus_provider=antivirus_adapter,
        filesystem_service=filesystem_service,
        antivirus_repo=antivirus_repo,
        get_torrent_download_query=get_torrent_download_query,
        deluge_provider=deluge_adapter
    )


def create_antivirus_provider() -> AntivirusAdapter:
    """Factory function to create AntivirusProvider for direct scanning."""
    client = AntivirusClient()
    return AntivirusAdapter(client)

