"""Antivirus routes: scan path by path, health. Torrent scan/ingest are under /orchestrator."""
from fastapi import APIRouter, Depends

from app.adapters.http.schemas.antivirus.antivirusSchemas import (
    HealthCheckResponse,
    ScanPathRequest,
    ScanPathResponse,
    ScanSummary,
)
from app.domain.ports.external.antivirus.antivirusProvider import AntivirusProvider
from app.factories.antivirus.antivirusFactory import create_antivirus_provider

antivirusRoutes = APIRouter(prefix="/antivirus", tags=["antivirus"])


@antivirusRoutes.post("/scan", response_model=ScanPathResponse)
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


@antivirusRoutes.get("/health", response_model=HealthCheckResponse)
async def health_check(
    antivirus_provider: AntivirusProvider = Depends(create_antivirus_provider),
):
    status = antivirus_provider.test_connection()
    return HealthCheckResponse(
        service=status.service,
        connected=status.connected,
        status="healthy" if status.is_healthy else "unhealthy",
        error=status.error,
    )
