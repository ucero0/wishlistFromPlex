# Debug Fix: FastAPI Antivirus Scan Endpoint

## Problem

The `/antivirus/scan` endpoint was failing with error:
```
"Unable to connect to scan service: Server disconnected without sending a response."
```

## Root Cause

**Port Mismatch:**
- `docker-compose.yml` was setting `CLAMAV_PORT: 3310` (ClamAV daemon port)
- But the HTTP scan service runs on port **3311**
- The Settings class expects `ANTIVIRUS_PORT` environment variable (not `CLAMAV_PORT`)
- Without `ANTIVIRUS_PORT` set, the service was trying to connect to port 3310 instead of 3311

## Solution

Updated `docker-compose.yml` to include both environment variables:

```yaml
# Scanner configuration
# CLAMAV_HOST and CLAMAV_PORT are for the ClamAV daemon (port 3310)
# ANTIVIRUS_HOST and ANTIVIRUS_PORT are for the HTTP scan service (port 3311)
CLAMAV_HOST: antivirus
CLAMAV_PORT: 3310
ANTIVIRUS_HOST: antivirus
ANTIVIRUS_PORT: 3311
```

## Ports Explained

| Service | Port | Purpose |
|---------|------|---------|
| ClamAV Daemon | 3310 | Direct ClamAV daemon connection (for pyclamd) |
| HTTP Scan Service | 3311 | HTTP API for scanning with ClamAV + YARA |

## Verification

After the fix, the endpoint now works correctly:

```bash
curl -X POST http://localhost:8000/antivirus/scan \
  -H "Content-Type: application/json" \
  -d '{"path": "/downloads/quarantine/malicious_subtitle.srt"}'
```

**Response:**
```json
{
  "status": "infected",
  "infected": true,
  "virus_name": null,
  "yara_matches": [
    "contains_base64",
    "domain",
    "Misc_Suspicious_Strings",
    "url"
  ],
  "scanned_files": ["/downloads/quarantine/malicious_subtitle.srt"],
  "infected_files": ["/downloads/quarantine/malicious_subtitle.srt"],
  "summary": {
    "total_scanned": 1,
    "total_infected": 1
  }
}
```

## Files Changed

1. `docker-compose.yml` - Added `ANTIVIRUS_HOST` and `ANTIVIRUS_PORT` environment variables

## Next Steps

After updating `docker-compose.yml`, restart the FastAPI container:
```bash
docker-compose restart fastapi
```

Or if using docker directly:
```bash
docker restart plex-wishlist-api
```

