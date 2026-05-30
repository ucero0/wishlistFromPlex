"""Composition root for antivirus queries and use cases."""
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
from app.composition.persistence import build_antivirus_repository
from app.infrastructure.external_apis.antivirus.client import AntivirusClient


def build_check_infected_by_guid_prowlarr_query(
    session: AsyncSession,
) -> CheckInfectedByGuidProwlarrQuery:
    return CheckInfectedByGuidProwlarrQuery(build_antivirus_repository(session))


def build_get_antivirus_scan_by_id_query(
    session: AsyncSession,
) -> GetAntivirusScanByIdQuery:
    return GetAntivirusScanByIdQuery(build_antivirus_repository(session))


def build_get_antivirus_scans_by_guid_prowlarr_query(
    session: AsyncSession,
) -> GetAntivirusScansByGuidProwlarrQuery:
    return GetAntivirusScansByGuidProwlarrQuery(build_antivirus_repository(session))


def build_get_antivirus_scan_by_file_path_query(
    session: AsyncSession,
) -> GetAntivirusScanByFilePathQuery:
    return GetAntivirusScanByFilePathQuery(build_antivirus_repository(session))


def build_get_infected_items_query(session: AsyncSession) -> GetInfectedItemsQuery:
    return GetInfectedItemsQuery(build_antivirus_repository(session))


def build_get_clean_items_query(session: AsyncSession) -> GetCleanItemsQuery:
    return GetCleanItemsQuery(build_antivirus_repository(session))


def build_get_all_antivirus_scans_query(
    session: AsyncSession,
) -> GetAllAntivirusScansQuery:
    return GetAllAntivirusScansQuery(build_antivirus_repository(session))


def build_create_antivirus_scan_use_case(
    session: AsyncSession,
) -> CreateAntivirusScanUseCase:
    return CreateAntivirusScanUseCase(build_antivirus_repository(session))


def build_update_antivirus_scan_use_case(
    session: AsyncSession,
) -> UpdateAntivirusScanUseCase:
    return UpdateAntivirusScanUseCase(build_antivirus_repository(session))


def build_delete_antivirus_scan_use_case(
    session: AsyncSession,
) -> DeleteAntivirusScanUseCase:
    return DeleteAntivirusScanUseCase(build_antivirus_repository(session))


def build_delete_antivirus_scan_by_id_use_case(
    session: AsyncSession,
) -> DeleteAntivirusScanByIdUseCase:
    return DeleteAntivirusScanByIdUseCase(build_antivirus_repository(session))


def build_delete_antivirus_scans_by_guid_prowlarr_use_case(
    session: AsyncSession,
) -> DeleteAntivirusScansByGuidProwlarrUseCase:
    return DeleteAntivirusScansByGuidProwlarrUseCase(build_antivirus_repository(session))


def build_antivirus_provider() -> AntivirusAdapter:
    return AntivirusAdapter(AntivirusClient())
