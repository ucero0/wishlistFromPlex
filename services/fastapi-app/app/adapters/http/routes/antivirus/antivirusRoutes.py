"""Antivirus routes for direct file/directory scanning and torrent scanning."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
import httpx
from app.domain.ports.external.antivirus.antivirusProvider import AntivirusProvider
from app.factories.antivirus.antivirusFactory import create_antivirus_provider, create_scan_and_move_files_use_case
from app.application.antivirus.useCases.scanAndMoveFiles import ScanAndMoveFilesUseCase

antivirusRoutes = APIRouter(prefix="/antivirus", tags=["antivirus"])


class ScanPathRequest(BaseModel):
    """Request model for scanning a file or directory path."""
    path: str


@antivirusRoutes.post("/scan")
async def scan_path(
    request: ScanPathRequest,
    antivirus_provider: AntivirusProvider = Depends(create_antivirus_provider)
):
    """
    Scan a file or directory with antivirus and YARA rules.
    
    **IMPORTANT:** This endpoint scans files that are ALREADY on disk.
    Files are NOT uploaded - you provide the path to existing files.
    
    The service automatically detects if the path is a file or directory
    and scans accordingly. This endpoint only scans - it does NOT move files.
    
    **Shared paths between FastAPI and antivirus:**

    - `/downloads/quarantine/` - Quarantine folder (shared, read-write)
    
    **Example paths (from FastAPI container perspective):**
    - `/downloads/movie.mkv` - Scan a single file
    - `/downloads/torrent-folder/` - Scan entire directory
    - `/media/movies/movie.mkv` - Scan a file in media folder
    - `/media/quarantine/suspicious-file.exe` - Scan quarantined file
    
    **Returns:**
    - `infected`: Boolean indicating if any files are infected
    - `virus_name`: Name of the virus if found
    - `yara_matches`: List of YARA rule names that matched
    - `scanned_files`: All files that were scanned
    - `infected_files`: Files that were infected
    """
    try:
        scan_result = antivirus_provider.scan(request.path)
        return {
            "status": "infected" if scan_result.is_infected else "clean",
            "infected": scan_result.is_infected,
            "virus_name": scan_result.virus_name,
            "yara_matches": scan_result.yara_matches,
            "scanned_files": scan_result.scanned_files,
            "infected_files": scan_result.infected_files,
            "summary": {
                "total_scanned": len(scan_result.scanned_files),
                "total_infected": len(scan_result.infected_files)
            }
        }
    except httpx.HTTPStatusError as e:
        # Preserve the status code from the scan service
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Scan service error: {e.response.text[:200]}"
        )
    except httpx.RequestError as e:
        # Connection/timeout errors
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Unable to connect to scan service: {str(e)}"
        )
    except Exception as e:
        # Other unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error scanning path: {str(e)}"
        )


@antivirusRoutes.get("/health")
async def health_check(
    antivirus_provider: AntivirusProvider = Depends(create_antivirus_provider)
):
    """
    Check antivirus service health and connection status.
    
    **Returns:**
    - `connected`: Boolean indicating if antivirus daemon is reachable
    - `status`: "healthy" or "unhealthy"
    """
    try:
        is_connected = antivirus_provider.test_connection()
        return {
            "service": "antivirus",
            "connected": is_connected,
            "status": "healthy" if is_connected else "unhealthy"
        }
    except Exception as e:
        return {
            "service": "antivirus",
            "connected": False,
            "status": "unhealthy",
            "error": str(e)
        }


class ScanTorrentRequest(BaseModel):
    """Request model for scanning a torrent."""
    torrent_hash: str


@antivirusRoutes.post("/scan/torrent")
async def scan_torrent(
    request: ScanTorrentRequest,
    use_case: ScanAndMoveFilesUseCase = Depends(create_scan_and_move_files_use_case)
):
    """
    Scan a torrent's files with antivirus and YARA rules.
    If clean, move files to appropriate media directory.
    If infected, delete the files/directory.
    
    This endpoint:
    1. Gets the torrent download by hash from the database
    2. Scans files from the quarantine path using the torrent's fileName
    3. If clean: moves to containerPlexPath/movies or tvshow based on type
    4. If infected: deletes the files/directory
    
    **Returns:**
    - `status`: "clean", "infected", or "error"
    - `infected`: Boolean indicating if files are infected
    - `moved`: Boolean indicating if files were moved (if clean)
    - `deleted`: Boolean indicating if files were deleted (if infected)
    - `destination_path`: Path where files were moved (if clean and moved)
    """
    try:
        result = await use_case.execute(request.torrent_hash)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error scanning torrent: {str(e)}")

