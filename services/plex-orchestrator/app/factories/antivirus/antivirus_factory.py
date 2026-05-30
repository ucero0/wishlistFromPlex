"""Factory for Antivirus queries and use cases."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.external.antivirus.adapter import AntivirusAdapter
from app.application.antivirus.queries import (
    CheckInfectedByGuidProwlarrQuery,
    GetAllAntivirusScansQuery,
    GetAntivirusScanByFilePathQuery,
    GetAntivirusScanByIdQuery,
    GetAntivirusScansByGuidProwlarrQuery,
    GetCleanItemsQuery,
    GetInfectedItemsQuery,
)
from app.application.antivirus.use_cases import (
    CreateAntivirusScanUseCase,
    DeleteAntivirusScanByIdUseCase,
    DeleteAntivirusScanUseCase,
    DeleteAntivirusScansByGuidProwlarrUseCase,
    UpdateAntivirusScanUseCase,
)
from app.composition.antivirus import (
    build_antivirus_provider,
    build_check_infected_by_guid_prowlarr_query,
    build_create_antivirus_scan_use_case,
    build_delete_antivirus_scan_by_id_use_case,
    build_delete_antivirus_scan_use_case,
    build_delete_antivirus_scans_by_guid_prowlarr_use_case,
    build_get_all_antivirus_scans_query,
    build_get_antivirus_scan_by_file_path_query,
    build_get_antivirus_scan_by_id_query,
    build_get_antivirus_scans_by_guid_prowlarr_query,
    build_get_clean_items_query,
    build_get_infected_items_query,
    build_update_antivirus_scan_use_case,
)
from app.infrastructure.persistence.database import get_db


def create_check_infected_by_guid_prowlarr_query(
    session: AsyncSession = Depends(get_db),
) -> CheckInfectedByGuidProwlarrQuery:
    return build_check_infected_by_guid_prowlarr_query(session)


def create_get_antivirus_scan_by_id_query(
    session: AsyncSession = Depends(get_db),
) -> GetAntivirusScanByIdQuery:
    return build_get_antivirus_scan_by_id_query(session)


def create_get_antivirus_scans_by_guid_prowlarr_query(
    session: AsyncSession = Depends(get_db),
) -> GetAntivirusScansByGuidProwlarrQuery:
    return build_get_antivirus_scans_by_guid_prowlarr_query(session)


def create_get_antivirus_scan_by_file_path_query(
    session: AsyncSession = Depends(get_db),
) -> GetAntivirusScanByFilePathQuery:
    return build_get_antivirus_scan_by_file_path_query(session)


def create_get_infected_items_query(
    session: AsyncSession = Depends(get_db),
) -> GetInfectedItemsQuery:
    return build_get_infected_items_query(session)


def create_get_clean_items_query(
    session: AsyncSession = Depends(get_db),
) -> GetCleanItemsQuery:
    return build_get_clean_items_query(session)


def create_get_all_antivirus_scans_query(
    session: AsyncSession = Depends(get_db),
) -> GetAllAntivirusScansQuery:
    return build_get_all_antivirus_scans_query(session)


def create_create_antivirus_scan_use_case(
    session: AsyncSession = Depends(get_db),
) -> CreateAntivirusScanUseCase:
    return build_create_antivirus_scan_use_case(session)


def create_update_antivirus_scan_use_case(
    session: AsyncSession = Depends(get_db),
) -> UpdateAntivirusScanUseCase:
    return build_update_antivirus_scan_use_case(session)


def create_delete_antivirus_scan_use_case(
    session: AsyncSession = Depends(get_db),
) -> DeleteAntivirusScanUseCase:
    return build_delete_antivirus_scan_use_case(session)


def create_delete_antivirus_scan_by_id_use_case(
    session: AsyncSession = Depends(get_db),
) -> DeleteAntivirusScanByIdUseCase:
    return build_delete_antivirus_scan_by_id_use_case(session)


def create_delete_antivirus_scans_by_guid_prowlarr_use_case(
    session: AsyncSession = Depends(get_db),
) -> DeleteAntivirusScansByGuidProwlarrUseCase:
    return build_delete_antivirus_scans_by_guid_prowlarr_use_case(session)


def create_antivirus_provider() -> AntivirusAdapter:
    return build_antivirus_provider()
