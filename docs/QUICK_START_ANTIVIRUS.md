# Quick Start: Antivirus Service

## 🚀 How to Use

### 1. API Endpoint (Simplest)

**Scan files that are ALREADY on disk:**
```bash
POST /antivirus/scan
Body: {"path": "/downloads/movie.mkv"}
```

**Check health:**
```bash
GET /antivirus/health
```

### 2. In Your Code

```python
from fastapi import Depends
from app.domain.ports.external.clamav.clamavProvider import ClamAVProvider
from app.factories.antivirus.antivirusFactory import create_clamav_provider

@router.post("/check-file")
async def check_file(
    file_path: str,
    clamav: ClamAVProvider = Depends(create_clamav_provider)
):
    result = clamav.scan(file_path)
    
    if result.is_infected:
        return {"error": "Infected!", "virus": result.virus_name}
    
    return {"status": "clean"}
```

### 3. Scan Torrent (Auto-move)

```bash
POST /scanner/scan
Body: {"torrent_hash": "abc123..."}
```

## 📋 Endpoints

| Endpoint | What It Does |
|----------|-------------|
| `POST /antivirus/scan` | Scan file/directory |
| `GET /antivirus/health` | Check service health |
| `POST /scanner/scan` | Scan torrent & move files |

## 💡 Example

```python
# File is already on disk - no upload needed
result = clamav.scan("/downloads/movie.mkv")

if result.is_infected:
    print(f"Virus: {result.virus_name}")
    print(f"YARA: {result.yara_matches}")
else:
    print("Clean!")
```

## 📦 Response

```python
{
    "status": "clean" | "infected",
    "infected": bool,
    "virus_name": str | null,
    "yara_matches": ["rule1", "rule2"],
    "scanned_files": ["/path/file1"],
    "infected_files": ["/path/infected"]
}
```

## ✅ Key Points

- ✅ **YARA in ClamAV container** - Not in FastAPI
- ✅ **No uploads** - Files scanned on disk
- ✅ **Shared folders** - Both containers see same files
- ✅ **Auto-updates** - ClamAV & YARA update daily
- ✅ **Simple interface** - Just call `scan(path)`

## 📁 Shared Folders

- `/downloads/` - Downloaded files
- `/media/` - Media files  
- `/media/quarantine/` - Quarantine (shared read-write)

**See `docs/FASTAPI_ANTIVIRUS_USAGE.md` for complete guide!**
