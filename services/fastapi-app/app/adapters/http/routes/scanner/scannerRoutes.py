"""Scanner routes for antivirus scanning."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.application.antivirus.useCases.scanAndMoveFiles import ScanAndMoveFilesUseCase
from app.factories.antivirus.antivirusFactory import create_scan_and_move_files_use_case

scannerRoutes = APIRouter(prefix="/scanner", tags=["scanner"])


class ScanRequest(BaseModel):
    """Request model for scanning a torrent."""
    torrent_hash: str


@scannerRoutes.post("/scan")
async def scan_torrent(
    request: ScanRequest,
    use_case: ScanAndMoveFilesUseCase = Depends(create_scan_and_move_files_use_case)
):
    """
    Scan a torrent's files with ClamAV and YARA rules.
    If clean, move files to appropriate media directory.
    If infected, move to quarantine.
    """
    try:
        result = await use_case.execute(request.torrent_hash)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error scanning torrent: {str(e)}")

