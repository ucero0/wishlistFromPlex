# Rename ClamAV to Antivirus

## Summary

Updated all user-facing references from "ClamAV" to "antivirus" for consistency throughout the codebase.

## Changes Made

### 1. Function Names
- `scan_with_clamav()` → `scan_with_antivirus()` in `http_scan_server.py`

### 2. Comments and Documentation
- Updated all comments to use "antivirus" instead of "ClamAV"
- Updated docstrings to use "antivirus engine" terminology
- Updated log messages from `[CLAMAV]` to `[ANTIVIRUS]`

### 3. Configuration
- Updated `docker-compose.yml` environment variables:
  - `CLAMAV_HOST` → `ANTIVIRUS_DAEMON_HOST` (for daemon connection, if needed)
  - `CLAMAV_PORT` → `ANTIVIRUS_DAEMON_PORT` (for daemon connection, if needed)
  - Kept `ANTIVIRUS_HOST` and `ANTIVIRUS_PORT` for HTTP scan service

### 4. Client Code
- Removed unused `pyclamd` import and `ClamdNetworkSocket` connection
- Updated `test_connection()` to test HTTP service instead of daemon
- Updated all comments to use "antivirus" terminology

### 5. Files Updated
- `infra/antivirus/scan-service/http_scan_server.py`
- `services/fastapi-app/app/infrastructure/externalApis/antivirus/client.py`
- `services/fastapi-app/app/core/config.py`
- `services/fastapi-app/app/application/antivirus/useCases/scanAndMoveFiles.py`
- `docker-compose.yml`

## What Stayed the Same

The following were kept as-is because they are technical/product names:
- Docker image: `clamav/clamav:latest` (actual product name)
- Environment variables in antivirus container: `CLAMAV_NO_FRESHCLAMD`, `CLAMAV_NO_CLAMD` (ClamAV-specific)
- Volume path: `/var/lib/clamav` (ClamAV's standard data directory)
- Command: `clamdscan` (actual ClamAV command name)

## Testing

After changes, verified:
- ✅ Configuration loads correctly
- ✅ HTTP scan service works
- ✅ Health check works
- ✅ File scanning works

## Benefits

1. **Consistency**: All user-facing code uses "antivirus" terminology
2. **Clarity**: Makes it clear this is a generic antivirus service, not ClamAV-specific
3. **Maintainability**: Easier to understand and maintain
4. **Future-proof**: If we switch antivirus engines, the naming is already generic

