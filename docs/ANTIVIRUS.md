# Antivirus scanning

Completed torrents are scanned in **quarantine** before files move into Plex library folders. The stack uses a dedicated **antivirus** container (ClamAV + YARA) with an HTTP API consumed by FastAPI.

## Flow

```text
Deluge completes  →  files in /downloads (quarantine mount)
                 →  POST /pipelines/ingest/scan-torrent  or  scan-and-ingest
                 →  antivirus service scans each file
                 →  clean: move to library + optional Plex partial scan
                 →  infected: remove torrent, re-queue watchlist item
```

Quarantine and library paths are configured in `docker-compose.yml` and `.env` (see [DOCKER_SETUP.md](DOCKER_SETUP.md)).

## API

### Health

```powershell
curl http://localhost:8000/antivirus/health
```

Returns ClamAV/YARA readiness. Non-200 if the scan service is down or misconfigured.

### Scan a path (low level)

```powershell
curl -X POST http://localhost:8000/antivirus/scan `
  -H "Content-Type: application/json" `
  -H "X-API-Key: YOUR_API_KEY" `
  -d '{"path":"/downloads/movie-folder"}'
```

Paths are **inside the FastAPI container** (usually the shared quarantine volume). Prefer pipeline endpoints for torrent-based workflows.

### Pipeline (recommended)

```powershell
# Scan only — updates tracking, no library move
curl -X POST http://localhost:8000/pipelines/ingest/scan-torrent `
  -H "Content-Type: application/json" `
  -H "X-API-Key: YOUR_API_KEY" `
  -d '{"torrent_hash":"abc123..."}'

# Full ingest
curl -X POST http://localhost:8000/pipelines/ingest/scan-and-ingest `
  -H "Content-Type: application/json" `
  -H "X-API-Key: YOUR_API_KEY" `
  -d '{"torrent_hash":"abc123..."}'
```

## YARA rules

**Custom rules (in Git):** `infra/antivirus/scan-service/yara-rules-custom/` — mounted into the container and always applied.

**Community rules (runtime):** `infra/antivirus/yara-rules/` — cloned from GitHub on first container start by `init-yara-rules.sh`; not committed (too large). See [infra/antivirus/README.md](../infra/antivirus/README.md).

After editing rules:

```powershell
docker compose restart antivirus
```

## ClamAV signature updates

The antivirus image updates virus definitions on its own schedule inside the container. If scans fail with “database outdated” or similar:

```powershell
docker compose restart antivirus
docker logs antivirus --tail 50
```

For persistent issues, rebuild the antivirus service:

```powershell
docker compose up -d --build antivirus
```

## Troubleshooting

| Symptom | What to check |
|---------|----------------|
| `503` on `/antivirus/health` | `docker ps` — is `antivirus` running? `docker logs antivirus` |
| Scan timeout on large files | Increase scan timeout in app config if exposed; check disk I/O on quarantine volume |
| False positive | Adjust YARA rules; temporarily quarantine file manually before ingest |
| Infected handling | Torrent removed from Deluge; item returns to watchlist for a new search |

**Verify quarantine mount:** from the FastAPI container, the completed download path must exist and match what Deluge wrote.

```powershell
docker compose exec plex-orchestrator ls /downloads
```

## Security notes

- Infected files should **not** be moved to library paths until scan passes.
- Keep YARA rules under version control; review changes before deploy.
- Quarantine volume should not be exposed as a Plex library root.
