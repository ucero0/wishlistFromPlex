"""Scanner module API routes."""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import get_api_key
from app.modules.scanner.service import ScannerService
from app.modules.scanner.schemas import (
    ScanRequest,
    ScanResponse,
    ScanResultResponse,
    ScanStatsResponse,
    ScanStatusEnum,
    ScannerResult,
)
from app.modules.scanner.models import ScanStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scanner", tags=["scanner"])


@router.post("/scan", response_model=ScanResponse, dependencies=[Depends(get_api_key)])
async def scan_torrent(request: ScanRequest, db: Session = Depends(get_db)):
    """
    Scan a completed torrent for viruses and organize files.
    
    This endpoint is typically called by Deluge's Execute plugin when a torrent completes.
    
    Pipeline:
    1. ClamAV antivirus scan
    2. YARA pattern-based malware detection
    3. If clean: organize into movies/tvshows folders
    4. If infected: move to quarantine
    """
    service = ScannerService(db)
    
    try:
        result = await service.scan_torrent(request.torrent_hash)
        
        scanners = []
        
        # Add ClamAV result
        if result.clamav_result:
            scanners.append(ScannerResult(
                scanner="ClamAV",
                status=result.clamav_result.get("status", "unknown"),
                details=result.clamav_result
            ))
        
        # Add YARA result
        if result.yara_result:
            scanners.append(ScannerResult(
                scanner="YARA",
                status=result.yara_result.get("status", "unknown"),
                details=result.yara_result
            ))
        
        # Map status
        status_map = {
            ScanStatus.PENDING: ScanStatusEnum.PENDING,
            ScanStatus.SCANNING: ScanStatusEnum.SCANNING,
            ScanStatus.CLEAN: ScanStatusEnum.CLEAN,
            ScanStatus.INFECTED: ScanStatusEnum.INFECTED,
            ScanStatus.ERROR: ScanStatusEnum.ERROR,
        }
        
        message = "Scan completed successfully"
        if result.status == ScanStatus.CLEAN:
            message = f"File is clean. Moved to: {result.destination_path}"
        elif result.status == ScanStatus.INFECTED:
            message = f"Threat detected: {result.threat_name}. File quarantined."
        elif result.status == ScanStatus.ERROR:
            message = f"Scan error: {result.clamav_result.get('error', 'Unknown error') if result.clamav_result else 'Unknown error'}"
        
        return ScanResponse(
            torrent_hash=request.torrent_hash,
            status=status_map.get(result.status, ScanStatusEnum.ERROR),
            scanners=scanners,
            threat_name=result.threat_name,
            original_path=result.original_path,
            destination_path=result.destination_path,
            message=message
        )
        
    except Exception as e:
        logger.exception(f"Error scanning torrent {request.torrent_hash}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scan failed: {str(e)}"
        )


@router.get("/result/{torrent_hash}", response_model=ScanResultResponse, dependencies=[Depends(get_api_key)])
async def get_scan_result(torrent_hash: str, db: Session = Depends(get_db)):
    """Get the scan result for a specific torrent."""
    service = ScannerService(db)
    result = service.get_scan_result(torrent_hash)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No scan result found for torrent: {torrent_hash}"
        )
    
    return result


@router.get("/stats", response_model=ScanStatsResponse, dependencies=[Depends(get_api_key)])
async def get_scan_stats(db: Session = Depends(get_db)):
    """Get scanner statistics."""
    service = ScannerService(db)
    stats = service.get_scan_stats()
    
    return ScanStatsResponse(**stats)

