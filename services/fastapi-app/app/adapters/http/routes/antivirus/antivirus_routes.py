"""Antivirus routes: scan path by path, health. Torrent scan/ingest are under /pipelines."""
from fastapi import APIRouter, Depends

from app.adapters.http.mappers.external_service_http_mapper import (
    external_connection_to_json_response,
)
from app.adapters.http.schemas.antivirus.antivirus_schemas import (
    HealthCheckResponse,
    ScanPathRequest,
    ScanPathResponse,
    ScanSummary,
)
from app.domain.ports.external.antivirus.antivirus_provider import AntivirusProvider
from app.factories.antivirus.antivirus_factory import create_antivirus_provider

antivirus_routes = APIRouter(prefix="/antivirus", tags=["antivirus"])


@antivirus_routes.post("/scan", response_model=ScanPathResponse)
async def scan_path(
    request: ScanPathRequest,
    antivirus_provider: AntivirusProvider = Depends(create_antivirus_provider),
):
    scan_result = antivirus_provider.scan(request.path)
    return ScanPathResponse(
        status="infected" if scan_result.is_infected else "clean",
        infected=scan_result.is_infected,
        virus_name=scan_result.virus_name,
        yara_matches=scan_result.yara_matches,
        scanned_files=scan_result.scanned_files,
        infected_files=scan_result.infected_files,
        summary=ScanSummary(
            total_scanned=len(scan_result.scanned_files),
            total_infected=len(scan_result.infected_files),
        ),
    )


@antivirus_routes.get("/health", response_model=HealthCheckResponse)
async def health_check(
    antivirus_provider: AntivirusProvider = Depends(create_antivirus_provider),
):
    status = antivirus_provider.test_connection()
    return external_connection_to_json_response(status)
