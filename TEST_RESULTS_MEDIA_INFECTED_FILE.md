# Test Results: Media-Related Infected File Detection

## Test File Created

**File:** `infra/deluge/downloads/quarantine/malicious_subtitle.srt`

This is a malicious subtitle file (.srt format) that contains:
- Script injection attempts: `<script>`, `javascript:`, `onerror=`
- Suspicious URLs with malicious domains: `.tk`, `.xyz`, `.ga`
- Executable file references: `.exe`, `.bat`, `.ps1`

## YARA Detection Results

### Direct YARA Test
```bash
docker exec antivirus yara -s /scan-service/yara-rules-custom/subtitle_detection.yar /downloads/quarantine/malicious_subtitle.srt
```

**Results:**
- ✅ **Suspicious_Subtitle_Content** - Detected (multiple matches):
  - Script tags: `<script>`, `javascript:`, `onerror=`
  - Suspicious domains: `malicious-site.tk`, `phishing-site.xyz`, `fake-update.ga`
  - HTTP URLs: Multiple malicious URLs detected
  - Executable references: `.exe`, `.bat`, `.ps1` files referenced

- ✅ **Subtitle_File_Format** - Detected (SRT format recognized)

### Antivirus Scan Service Test
```bash
docker exec antivirus python3 -c "import urllib.request, json; data = json.dumps({'path': '/downloads/quarantine/malicious_subtitle.srt'}).encode(); req = urllib.request.Request('http://localhost:3311/scan', data=data, headers={'Content-Type': 'application/json'}); response = urllib.request.urlopen(req); result = json.loads(response.read().decode()); print(json.dumps(result, indent=2))"
```

**Results:**
```json
{
  "is_infected": true,
  "virus_name": null,
  "yara_matches": [
    "contains_base64",
    "domain",
    "Misc_Suspicious_Strings",
    "url"
  ],
  "scanned_files": [
    "/downloads/quarantine/malicious_subtitle.srt"
  ],
  "infected_files": [
    "/downloads/quarantine/malicious_subtitle.srt"
  ]
}
```

## Summary

✅ **File Successfully Detected as Infected**

The malicious subtitle file is correctly identified by the antivirus system:
- The custom `Suspicious_Subtitle_Content` YARA rule detects multiple malicious patterns
- The file is flagged as infected by the scan service
- Multiple YARA rules match (generic rules for domains, URLs, suspicious strings)
- The file would be quarantined/deleted in a real scenario

## Test Files Available

1. **test_xmrig_miner.txt** - Contains "stratum+tcp" string (triggers XMRIG_Miner rule)
2. **malicious_subtitle.srt** - Malicious subtitle file with script injection and suspicious URLs

Both files are located in: `/downloads/quarantine/` (shared between containers)

## How to Test

### Via Direct Scan Service
```bash
docker exec antivirus python3 -c "import urllib.request, json; data = json.dumps({'path': '/downloads/quarantine/malicious_subtitle.srt'}).encode(); req = urllib.request.Request('http://localhost:3311/scan', data=data, headers={'Content-Type': 'application/json'}); response = urllib.request.urlopen(req); print(response.read().decode())"
```

### Via FastAPI Endpoint
```bash
POST http://localhost:8000/antivirus/scan
Content-Type: application/json

{
  "path": "/downloads/quarantine/malicious_subtitle.srt"
}
```

## Custom YARA Rules

The custom subtitle detection rule is located at:
- `/scan-service/yara-rules-custom/subtitle_detection.yar` (in antivirus container)
- `infra/antivirus/scan-service/yara-rules-custom/subtitle_detection.yar` (on host)

This rule specifically detects:
- Script injection in subtitles
- Suspicious domains and URLs
- Executable content in subtitle files
- Binary content in text files

