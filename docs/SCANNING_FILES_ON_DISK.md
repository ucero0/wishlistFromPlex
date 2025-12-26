# Scanning Files on Disk (No Upload Required)

## Overview

The antivirus service scans files that are **already on disk**. You don't upload files - you provide the path to existing files that are accessible to both FastAPI and ClamAV containers.

**Important:** YARA scanning is handled in the ClamAV container, not in FastAPI.

## Shared Folders

Both FastAPI and ClamAV containers share the following folders:

| Host Path | FastAPI Container | ClamAV Container | Access |
|-----------|-------------------|------------------|--------|
| `./infra/deluge/downloads` | `/downloads` | `/scan/downloads` | Read-only in ClamAV |
| `./media` | `/media` | `/scan/media` | Read-only in ClamAV |
| `./media/quarantine` | `/media/quarantine` | `/scan/quarantine` | Read-write (shared) |

## How to Use

### Scan Files Already Downloaded

Files downloaded by Deluge are automatically available for scanning:

```bash
# Scan a file in downloads folder
POST /antivirus/scan
{
  "path": "/downloads/movie.mkv"
}

# Scan entire torrent folder
POST /antivirus/scan
{
  "path": "/downloads/torrent-folder-name/"
}
```

### Scan Files in Media Folders

```bash
# Scan a movie file
POST /antivirus/scan
{
  "path": "/media/movies/movie.mkv"
}

# Scan a TV show folder
POST /antivirus/scan
{
  "path": "/media/tvshows/ShowName/Season 01/"
}
```

## Complete Example

```python
from fastapi import APIRouter, Depends, HTTPException
from app.domain.ports.external.clamav.clamavProvider import ClamAVProvider
from app.factories.antivirus.antivirusFactory import create_clamav_provider
import os

router = APIRouter(prefix="/process", tags=["process"])

@router.post("/file")
async def process_file(
    file_path: str,  # Path to file already on disk
    clamav: ClamAVProvider = Depends(create_clamav_provider)
):
    """Process a file that's already on disk. First scans it."""
    # Check if file exists
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
    
    # Scan the file (no upload needed - it's already on disk)
    # YARA scanning happens in ClamAV container
    scan_result = clamav.scan(file_path)
    
    if scan_result.is_infected:
        # Move to quarantine (shared folder)
        from app.core.config import settings
        quarantine_path = os.path.join(
            settings.media_quarantine_path,
            os.path.basename(file_path)
        )
        os.rename(file_path, quarantine_path)
        
        return {
            "error": "File is infected",
            "virus": scan_result.virus_name,
            "yara_matches": scan_result.yara_matches,
            "quarantined_to": quarantine_path
        }
    
    # File is clean, proceed with processing
    return {
        "status": "processed",
        "file": file_path,
        "scan_status": "clean"
    }
```

## Path Mapping

When calling the API, use paths from the **FastAPI container perspective**:

| What You Want | FastAPI Path | ClamAV Path (internal) |
|---------------|--------------|------------------------|
| Downloads folder | `/downloads/` | `/scan/downloads/` |
| Media movies | `/media/movies/` | `/scan/media/movies/` |
| Media TV shows | `/media/tvshows/` | `/scan/media/tvshows/` |
| Quarantine | `/media/quarantine/` | `/scan/quarantine/` |

**Always use FastAPI paths in your API calls!** The client automatically maps them.

## Workflow Example

1. **File is downloaded by Deluge** → Goes to `/downloads/` (FastAPI) = `/scan/downloads/` (ClamAV)

2. **Scan the file:**
   ```bash
   POST /antivirus/scan
   {"path": "/downloads/movie.mkv"}
   ```
   - FastAPI calls ClamAV HTTP service
   - ClamAV scans with both ClamAV and YARA
   - Results returned to FastAPI

3. **If clean, move to media:**
   ```python
   os.rename("/downloads/movie.mkv", "/media/movies/movie.mkv")
   ```

4. **If infected, move to quarantine:**
   ```python
   os.rename("/downloads/movie.mkv", "/media/quarantine/movie.mkv")
   ```

## Benefits

✅ **No file size limits** - Files stay on disk, not in memory  
✅ **Fast** - No upload/download overhead  
✅ **Efficient** - Direct file access  
✅ **Shared storage** - Both containers see the same files  
✅ **Quarantine support** - Shared quarantine folder for infected files  
✅ **YARA in ClamAV** - All scanning logic in one place

## Important Notes

1. **Use FastAPI container paths** when calling the API
2. **Files must exist** before scanning (they're already on disk)
3. **Quarantine folder is shared** - both containers can read/write
4. **Large files are fine** - no upload size limits
5. **YARA scanning** happens in ClamAV container automatically

## Troubleshooting

### File Not Found

```python
# Check if file exists
import os
file_path = "/downloads/movie.mkv"
if not os.path.exists(file_path):
    print(f"File not found: {file_path}")
```

### Permission Issues

Make sure the quarantine folder has write permissions:
```bash
# On host
chmod 755 ./media/quarantine
```

### Path Issues

Always use absolute paths from container perspective:
- ✅ `/downloads/file.mkv`
- ❌ `downloads/file.mkv` (relative)
- ❌ `./downloads/file.mkv` (relative)

## Summary

- ✅ **No uploads** - Files are already on disk
- ✅ **Use FastAPI paths** - `/downloads/`, `/media/`, etc.
- ✅ **Shared folders** - Both containers see the same files
- ✅ **Quarantine shared** - Both can read/write quarantine
- ✅ **No size limits** - Files stay on disk
- ✅ **YARA in ClamAV** - All scanning in ClamAV container

The service is designed for scanning files that are already downloaded and available on disk!
