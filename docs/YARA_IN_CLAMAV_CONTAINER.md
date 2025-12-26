# YARA Rules in ClamAV Container

## Architecture

YARA scanning is handled **entirely in the ClamAV container**, not in FastAPI. This provides better separation of concerns and keeps all scanning logic in one place.

**Key Benefits:**
- ✅ Separation of concerns: All scanning logic in ClamAV container
- ✅ No YARA dependencies in FastAPI: Removed `yara-python` package
- ✅ Centralized updates: YARA rules updated in one place
- ✅ Reusable service: HTTP API can be called from anywhere
- ✅ Better resource management: YARA only loaded in ClamAV container

## How It Works

1. **ClamAV Container**:
   - Has YARA rules at `/yara-rules` (updated daily from GitHub)
   - Runs an HTTP scanning service on port `3311`
   - This service handles both ClamAV and YARA scanning

2. **FastAPI Container**:
   - Calls the HTTP scanning service in ClamAV container
   - No YARA dependencies needed in FastAPI
   - Just sends HTTP requests with file paths

## Components

### ClamAV Container

**HTTP Scanning Service** (`/scan-service/http_scan_server.py`):
- Listens on port `3311`
- Handles `POST /scan` requests
- Scans files with both ClamAV (`clamdscan`) and YARA (`yara` command)
- Returns JSON results

**YARA Rules**:
- Located at `/yara-rules` in ClamAV container
- Updated daily from GitHub (Yara-Rules/rules repository)
- Automatically loaded by the scanning service

### FastAPI Container

**ClamAV Client** (`app/infrastructure/externalApis/clamav/client.py`):
- Calls HTTP service at `http://antivirus:3311/scan`
- Maps FastAPI paths to ClamAV container paths
- No YARA dependencies - removed `yara-python` package

## Path Mapping

| FastAPI Container | ClamAV Container |
|-------------------|-----------------|
| `/downloads/file.mkv` | `/scan/downloads/file.mkv` |
| `/media/movies/file.mkv` | `/scan/media/movies/file.mkv` |
| `/media/quarantine/file.exe` | `/scan/quarantine/file.exe` |

The client automatically maps paths when calling the scan service.

## API Endpoints

### ClamAV Container HTTP Service

**Scan File/Directory:**
```bash
POST http://antivirus:3311/scan
Content-Type: application/json

{
  "path": "/scan/downloads/movie.mkv"
}
```

**Health Check:**
```bash
GET http://antivirus:3311/health
```

### FastAPI Endpoints (Unchanged)

**Scan File/Directory:**
```bash
POST /antivirus/scan
{
  "path": "/downloads/movie.mkv"
}
```

FastAPI automatically calls the ClamAV container service internally.

## Benefits

✅ **Separation of Concerns**: All scanning logic in ClamAV container  
✅ **No YARA in FastAPI**: Removed `yara-python` dependency  
✅ **Centralized Updates**: YARA rules updated in one place  
✅ **Reusable Service**: Other services can call the HTTP API  
✅ **Better Resource Management**: YARA only loaded in ClamAV container

## Configuration

### ClamAV Container
- **YARA Rules Path**: `/yara-rules` (mapped from `./yara-rules` on host)
- **HTTP Service Port**: `3311`
- **ClamAV Daemon Port**: `3310` (for ClamAV daemon only)

### FastAPI Container
- **Scan Service URL**: `http://antivirus:3311/scan`
- **No YARA dependencies**: Removed from `requirements.txt`

## Troubleshooting

### Check if HTTP Service is Running

```bash
# Check if service is running
docker exec antivirus ps aux | grep http_scan_server

# Check logs
docker exec antivirus tail -f /var/log/scan-service.log

# Test the service directly
curl -X POST http://localhost:3311/scan \
  -H "Content-Type: application/json" \
  -d '{"path": "/scan/downloads/test.mkv"}'
```

### Check YARA Installation

```bash
# Check if YARA is installed in antivirus container
docker exec antivirus which yara

# Check YARA version
docker exec antivirus yara --version

# List YARA rules
docker exec antivirus find /yara-rules -name "*.yar" -o -name "*.yara" | head -10
```

### Check Python 3

```bash
# Check if Python 3 is available
docker exec antivirus python3 --version

# If not installed, it will be installed automatically on container start
```

## Manual Testing

### Test from FastAPI Container

```bash
# From FastAPI container
docker exec plex-wishlist-api curl -X POST http://antivirus:3311/scan \
  -H "Content-Type: application/json" \
  -d '{"path": "/scan/downloads/test.mkv"}'
```

### Test from Host

```bash
# From host (if port is exposed)
curl -X POST http://localhost:3311/scan \
  -H "Content-Type: application/json" \
  -d '{"path": "/scan/downloads/test.mkv"}'
```

## Summary

- ✅ YARA rules are in ClamAV container at `/yara-rules`
- ✅ YARA scanning happens in ClamAV container via HTTP service
- ✅ FastAPI calls the HTTP service - no YARA dependencies
- ✅ All scanning (ClamAV + YARA) is centralized in ClamAV container
- ✅ Service runs on port `3311` in ClamAV container

The architecture is now cleaner with proper separation of concerns!

