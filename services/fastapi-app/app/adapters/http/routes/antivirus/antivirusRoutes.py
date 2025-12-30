"""Antivirus routes for direct file/directory scanning."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.domain.ports.external.antivirus.clamavProvider import ClamAVProvider
from app.factories.antivirus.antivirusFactory import create_clamav_provider

antivirusRoutes = APIRouter(prefix="/antivirus", tags=["antivirus"])


class ScanPathRequest(BaseModel):
    """Request model for scanning a file or directory path."""
    path: str


@antivirusRoutes.post("/scan")
async def scan_path(
    request: ScanPathRequest,
    clamav_provider: ClamAVProvider = Depends(create_clamav_provider)
):
    """
    Scan a file or directory with ClamAV and YARA rules.
    
    **IMPORTANT:** This endpoint scans files that are ALREADY on disk.
    Files are NOT uploaded - you provide the path to existing files.
    
    The service automatically detects if the path is a file or directory
    and scans accordingly. This endpoint only scans - it does NOT move files.
    
    **Shared paths between FastAPI and ClamAV:**
    - `/downloads/` - Downloads folder (read-only in ClamAV)
    - `/media/` - Media folder (read-only in ClamAV)
    - `/media/quarantine/` - Quarantine folder (shared, read-write)
    
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
        scan_result = clamav_provider.scan(request.path)
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error scanning path: {str(e)}")


@antivirusRoutes.get("/health")
async def health_check(
    clamav_provider: ClamAVProvider = Depends(create_clamav_provider)
):
    """
    Check ClamAV service health and connection status.
    
    **Returns:**
    - `connected`: Boolean indicating if ClamAV daemon is reachable
    - `status`: "healthy" or "unhealthy"
    """
    try:
        is_connected = clamav_provider.test_connection()
        return {
            "service": "clamav",
            "connected": is_connected,
            "status": "healthy" if is_connected else "unhealthy"
        }
    except Exception as e:
        return {
            "service": "clamav",
            "connected": False,
            "status": "unhealthy",
            "error": str(e)
        }

