# How to Use Antivirus Service from FastAPI

## Overview

The antivirus service provides ClamAV and YARA scanning capabilities. **YARA scanning is handled entirely in the ClamAV container** - FastAPI just calls the service via HTTP. Files are scanned on disk (no uploads needed).

## Architecture

```
FastAPI Container              ClamAV Container
┌─────────────────┐           ┌──────────────────┐
│  ClamAVClient   │  HTTP     │  HTTP Scan        │
│                 │──────────▶│  Service (3311)   │
│  (No YARA)      │  Request  │                   │
│                 │           │  - ClamAV scan    │
│                 │◀──────────│  - YARA scan      │
│                 │  JSON     │  - YARA rules     │
└─────────────────┘  Response │  at /yara-rules   │
                              └──────────────────┘
```

**Key Points:**
- ✅ YARA rules are in ClamAV container (updated daily from GitHub)
- ✅ YARA scanning happens in ClamAV container
- ✅ FastAPI has no YARA dependencies
- ✅ Files are scanned on disk (no uploads)

## Quick Start

### 1. API Endpoint (Easiest)

**Scan a file or directory:**
```bash
POST /antivirus/scan
Content-Type: application/json

{
  "path": "/downloads/movie.mkv"
}
```

**Check health:**
```bash
GET /antivirus/health
```

### 2. In Your Code (Recommended)

```python
from fastapi import Depends
from app.domain.ports.external.clamav.clamavProvider import ClamAVProvider
from app.factories.antivirus.antivirusFactory import create_clamav_provider

@router.post("/check-file")
async def check_file(
    file_path: str,
    clamav: ClamAVProvider = Depends(create_clamav_provider)
):
    """Scan a file that's already on disk."""
    result = clamav.scan(file_path)
    
    if result.is_infected:
        return {
            "error": "File is infected",
            "virus": result.virus_name,
            "yara_matches": result.yara_matches
        }
    
    return {"status": "clean"}
```

## Available Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/antivirus/scan` | POST | Scan file/directory (scan only) |
| `/antivirus/health` | GET | Check ClamAV service health |
| `/scanner/scan` | POST | Scan torrent & auto-move files |

## Complete Examples

### Example 1: Scan Downloaded File

```python
from fastapi import APIRouter, Depends, HTTPException
from app.domain.ports.external.clamav.clamavProvider import ClamAVProvider
from app.factories.antivirus.antivirusFactory import create_clamav_provider
import os

router = APIRouter(prefix="/files", tags=["files"])

@router.post("/scan-downloaded")
async def scan_downloaded_file(
    file_path: str,  # Path to file already on disk
    clamav: ClamAVProvider = Depends(create_clamav_provider)
):
    """Scan a file that's already downloaded (no upload needed)."""
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
    
    # Scan the file (YARA scanning happens in ClamAV container)
    result = clamav.scan(file_path)
    
    if result.is_infected:
        # Move to quarantine (shared folder)
        from app.core.config import settings
        quarantine_path = os.path.join(
            settings.media_quarantine_path,
            os.path.basename(file_path)
        )
        os.rename(file_path, quarantine_path)
        
        return {
            "error": "File is infected",
            "virus": result.virus_name,
            "yara_matches": result.yara_matches,
            "quarantined_to": quarantine_path
        }
    
    return {"status": "clean", "file": file_path}
```

### Example 2: Background Scanning

```python
from fastapi import BackgroundTasks, Depends
from app.domain.ports.external.clamav.clamavProvider import ClamAVProvider
from app.factories.antivirus.antivirusFactory import create_clamav_provider

async def scan_in_background(
    path: str,
    clamav: ClamAVProvider
):
    """Scan a file in the background."""
    result = clamav.scan(path)
    if result.is_infected:
        print(f"ALERT: Infected file: {path}")
        print(f"Virus: {result.virus_name}")
        print(f"YARA matches: {result.yara_matches}")

@router.post("/upload")
async def upload_file(
    file_path: str,
    background_tasks: BackgroundTasks,
    clamav: ClamAVProvider = Depends(create_clamav_provider)
):
    """Process a file and scan it in background."""
    background_tasks.add_task(scan_in_background, file_path, clamav)
    return {"message": "File processing started, scanning in background"}
```

## Scan Result Model

```python
class ScanResult(BaseModel):
    is_infected: bool                    # True if any file is infected
    virus_name: Optional[str]            # Name of the first virus found
    yara_matches: List[str]               # List of YARA rule names that matched
    scanned_files: List[str]              # All files that were scanned
    infected_files: List[str]             # Files that were infected
```

## Shared Folders

Both FastAPI and ClamAV containers share these folders:

| Host Path | FastAPI Container | ClamAV Container | Access |
|-----------|-------------------|------------------|--------|
| `./infra/deluge/downloads` | `/downloads` | `/scan/downloads` | Read-only in ClamAV |
| `./media` | `/media` | `/scan/media` | Read-only in ClamAV |
| `./media/quarantine` | `/media/quarantine` | `/scan/quarantine` | Read-write (shared) |

**Always use FastAPI container paths in your API calls!**

## Path Mapping

When you call `scan("/downloads/file.mkv")`:
1. FastAPI receives: `/downloads/file.mkv`
2. FastAPI maps to ClamAV: `/scan/downloads/file.mkv`
3. ClamAV scans the file (both ClamAV and YARA)
4. Results returned to FastAPI

## Configuration

The service is configured via environment variables:

- `CLAMAV_HOST`: Antivirus container host (default: `antivirus`)
- `CLAMAV_PORT`: ClamAV daemon port (default: `3310`)
- Scan service runs on port `3311` in ClamAV container

## How It Works

1. **FastAPI calls** `clamav_provider.scan(path)`
2. **ClamAVClient** calls HTTP service at `http://antivirus:3311/scan`
3. **ClamAV container** scans with:
   - ClamAV daemon (via `clamdscan`)
   - YARA rules (from `/yara-rules` directory)
4. **Results returned** as JSON to FastAPI
5. **FastAPI returns** `ScanResult` model

## Daily Updates

- **ClamAV definitions**: Updated daily at 2 AM via `freshclam`
- **YARA rules**: Updated daily at 2 AM from GitHub (Yara-Rules/rules)

See `docs/CLAMAV_UPDATES.md` for details.

## Troubleshooting

### Scan Service Not Responding

```bash
# Check if HTTP service is running
docker exec antivirus ps aux | grep http_scan_server

# Check logs
docker exec antivirus tail -f /var/log/scan-service.log

# Test service directly
curl -X POST http://localhost:3311/scan \
  -H "Content-Type: application/json" \
  -d '{"path": "/scan/downloads/test.mkv"}'
```

### YARA Rules Not Working

```bash
# Check YARA installation in antivirus container
docker exec antivirus which yara

# Check YARA rules
docker exec antivirus find /yara-rules -name "*.yar" | head -10

# Check update logs
docker exec antivirus tail -f /var/log/clamav-updates.log
```

### Connection Errors

```bash
# Test ClamAV daemon
docker exec antivirus clamdcheck.sh

# Test HTTP scan service
curl http://localhost:3311/health
```

## Best Practices

1. **Scan before processing** user-accessible files
2. **Use dependency injection** for testability
3. **Handle errors gracefully** - service might be temporarily unavailable
4. **Log scan results** for security auditing
5. **Use background tasks** for non-blocking scans

## Summary

- ✅ **Simple**: Just call `scan(path)` - works with files or directories
- ✅ **No YARA in FastAPI**: All YARA scanning in ClamAV container
- ✅ **No uploads**: Files are scanned on disk
- ✅ **Automatic updates**: ClamAV and YARA rules update daily
- ✅ **Shared quarantine**: Both containers can access quarantine folder

**See also:**
- `docs/QUICK_START_ANTIVIRUS.md` - Quick reference
- `docs/SCANNING_FILES_ON_DISK.md` - Details on scanning without uploads
- `docs/YARA_IN_CLAMAV_CONTAINER.md` - Architecture details
- `docs/CLAMAV_UPDATES.md` - Update configuration
