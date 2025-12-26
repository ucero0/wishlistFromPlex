# Antivirus Service Documentation

Complete documentation for the ClamAV and YARA antivirus scanning service.

## 📚 Documentation Index

### Quick Start
- **[QUICK_START_ANTIVIRUS.md](QUICK_START_ANTIVIRUS.md)** - Quick reference guide for using the service

### Usage Guides
- **[FASTAPI_ANTIVIRUS_USAGE.md](FASTAPI_ANTIVIRUS_USAGE.md)** - Complete guide on how to use the antivirus service from FastAPI
- **[SCANNING_FILES_ON_DISK.md](SCANNING_FILES_ON_DISK.md)** - Guide for scanning files that are already on disk (no uploads)

### Architecture & Configuration
- **[YARA_IN_CLAMAV_CONTAINER.md](YARA_IN_CLAMAV_CONTAINER.md)** - Architecture details: YARA scanning in ClamAV container
- **[CLAMAV_UPDATES.md](CLAMAV_UPDATES.md)** - Configuration for daily ClamAV and YARA rule updates

## 🚀 Quick Start

```python
from fastapi import Depends
from app.domain.ports.external.clamav.clamavProvider import ClamAVProvider
from app.factories.antivirus.antivirusFactory import create_clamav_provider

@router.post("/scan")
async def scan_file(
    file_path: str,
    clamav: ClamAVProvider = Depends(create_clamav_provider)
):
    result = clamav.scan(file_path)
    return {"infected": result.is_infected}
```

## 📋 Key Features

- ✅ **YARA in ClamAV Container** - All YARA scanning handled in ClamAV container
- ✅ **No Uploads** - Files are scanned on disk (no file size limits)
- ✅ **Automatic Updates** - ClamAV and YARA rules update daily at 2 AM
- ✅ **Shared Quarantine** - Both containers can access quarantine folder
- ✅ **Simple Interface** - Just call `scan(path)` - works with files or directories

## 🔗 API Endpoints

- `POST /antivirus/scan` - Scan file/directory
- `GET /antivirus/health` - Check service health
- `POST /scanner/scan` - Scan torrent & auto-move files

## 📖 Documentation by Topic

### For Developers
1. Start with [QUICK_START_ANTIVIRUS.md](QUICK_START_ANTIVIRUS.md)
2. Read [FASTAPI_ANTIVIRUS_USAGE.md](FASTAPI_ANTIVIRUS_USAGE.md) for complete examples
3. Check [SCANNING_FILES_ON_DISK.md](SCANNING_FILES_ON_DISK.md) for file scanning details

### For System Administrators
1. Read [CLAMAV_UPDATES.md](CLAMAV_UPDATES.md) for update configuration
2. Check [YARA_IN_CLAMAV_CONTAINER.md](YARA_IN_CLAMAV_CONTAINER.md) for architecture

## 🏗️ Architecture Summary

```
┌─────────────────┐           ┌──────────────────┐
│  FastAPI        │  HTTP     │  ClamAV Container │
│  Container      │──────────▶│                   │
│                 │  :3311    │  - ClamAV daemon  │
│  - No YARA      │           │  - YARA rules     │
│  - HTTP client  │◀──────────│  - HTTP service   │
└─────────────────┘  JSON     └──────────────────┘
```

- **FastAPI**: Calls HTTP service, no YARA dependencies
- **ClamAV Container**: Handles both ClamAV and YARA scanning
- **YARA Rules**: Updated daily from GitHub (Yara-Rules/rules)

## 📝 Notes

- Files are scanned on disk - no uploads needed
- YARA scanning happens in ClamAV container automatically
- All scanning logic is centralized in ClamAV container
- Shared folders allow both containers to access the same files

