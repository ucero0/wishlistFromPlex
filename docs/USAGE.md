# Using the application

How to operate **automatic_plexMediaSever** after [Docker setup](DOCKER_SETUP.md) is complete.

## Authentication

Most routes require:

```http
X-API-Key: your-api-key-from-env
```

Public examples (no key): `GET /health`, some Deluge read-only routes — see http://localhost:8000/docs.

## End-to-end workflow

### 1. Configure Plex

1. **Reachability:** `GET /plex/test-connection` → should return `200` with `"connected": true`.
2. **Admin token** (library API, sync, ingest):
   - Set `PLEX_SERVER_ADMIN_TOKEN` in `.env`, **or**
   - `POST /plex/servers/admin-token` with body `{"admin_token":"..."}`  
   - Check: `GET /plex/servers/admin-token`, `GET /plex/test-admin-token`
3. **Users** (watchlist only — per-user Plex tokens):
   ```powershell
   curl -X POST http://localhost:8000/plex/users/ `
     -H "Content-Type: application/json" `
     -H "X-API-Key: YOUR_API_KEY" `
     -d '{"name":"me","plex_token":"YOUR_PLEX_USER_TOKEN"}'
   ```
4. **Library paths** — add libraries in Plex, mount folders on the `plex-orchestrator` container, then sync:
   ```powershell
   curl -X POST http://localhost:8000/plex/servers/library/locations-by-media/sync `
     -H "X-API-Key: YOUR_API_KEY"
   ```

### 2. Configure download stack

| Step | Endpoint | Notes |
|------|----------|--------|
| Deluge | `GET /deluge/test-connection` | RPC reachable; `torrent_connectivity: good` or `idle` when swarm is healthy |
| Prowlarr | `GET /prowlarr/test-connection` | set `PROWLARR_API_KEY` in `.env` |

### 3. Run the pipeline

**Automatic (scheduler):**

- Watchlist → search → Deluge: runs on an interval (see scheduler in app startup logs).
- Library path sync: interval from DB (`GET /scheduler/settings`, default 360 min). Also refreshes HDD free space into the database.
- Deferred downloads: every `DEFERRED_DOWNLOAD_PROCESS_INTERVAL_MINUTES` (default 15).
- Deluge ingest + health: interval from DB (default 5 min). Ingest completed torrents → sync tracking → remove unhealthy torrents. **Policies in DB:** `GET`/`PUT /scheduler/settings`, `GET`/`PUT /deluge/torrent-health`. **VPN check first:** Gluetun `http://gluetun:9999/`. Per-torrent: `unfinishable`, `no_complete_copy`, `stalled`, `error`.

**Manual triggers:**

```powershell
# Process watchlists → Prowlarr → Deluge
curl -X POST http://localhost:8000/pipelines/watchlist/process-downloads `
  -H "X-API-Key: YOUR_API_KEY"

# Reconcile DB active downloads with Deluge
curl -X POST http://localhost:8000/pipelines/watchlist/reconcile-deluge `
  -H "X-API-Key: YOUR_API_KEY"
```

**Search and add one torrent (Prowlarr):**

```powershell
curl -X POST http://localhost:8000/prowlarr/search/by-query `
  -H "Content-Type: application/json" `
  -H "X-API-Key: YOUR_API_KEY" `
  -d '{"query":"Movie Title 2024","media_type":"movie","auto_add_to_deluge":true}'
```

### 4. Scan and ingest

Completed torrents are picked up automatically by the **Deluge Ingest and Torrent Health** scheduler job. You can also trigger it manually:

```powershell
curl -X POST http://localhost:8000/scheduler/jobs/process_deluge_torrents/run `
  -H "X-API-Key: YOUR_API_KEY"
```

Or ingest a single torrent by hash:

```powershell
# Scan only
curl -X POST http://localhost:8000/pipelines/ingest/scan-torrent `
  -H "Content-Type: application/json" `
  -H "X-API-Key: YOUR_API_KEY" `
  -d '{"torrent_hash":"YOUR_HASH"}'

# Scan + move to library + Plex partial scan (full ingest)
curl -X POST http://localhost:8000/pipelines/ingest/scan-and-ingest `
  -H "Content-Type: application/json" `
  -H "X-API-Key: YOUR_API_KEY" `
  -d '{"torrent_hash":"YOUR_HASH"}'
```

If infected: torrent is removed and the item can be re-queued on the watchlist. See [ANTIVIRUS.md](ANTIVIRUS.md).

---

## API reference by area

### Plex (`/plex`)

| Route | Purpose |
|-------|---------|
| `GET /plex/test-connection` | Server reachable (no token) |
| `GET /plex/test-admin-token` | Admin token valid |
| `GET/POST /plex/servers/admin-token` | Manage admin token in DB |
| `GET/POST /plex/users/` | Plex users for watchlist |
| `GET /plex/watchlist/items` | List watchlist items |
| `GET /plex/servers/items/in-library` | Check if media exists in library |
| `GET /plex/library-paths` | Library paths from DB |
| `GET /plex/library-paths/disk-usage` | Disk usage per path |
| `GET /plex/library-paths/media-devices` | HDD volumes summary |
| `POST /plex/servers/library/locations-by-media/sync` | Sync paths from Plex → DB |

### Pipelines (`/pipelines`)

| Route | Purpose |
|-------|---------|
| `POST /pipelines/watchlist/process-downloads` | Watchlist download pipeline |
| `POST /pipelines/watchlist/reconcile-deluge` | Sync active downloads with Deluge |
| `POST /pipelines/ingest/scan-torrent` | Antivirus scan only |
| `POST /pipelines/ingest/scan-and-ingest` | Scan, move to library, Plex scan |

### Deluge (`/deluge`)

| Route | Purpose |
|-------|---------|
| `GET /deluge/test-connection` | RPC + VPN health; `torrent_connectivity` is informational |
| `GET /deluge/torrent-health` | Current unhealthy-removal policy (DB; requires `X-API-Key`) |
| `PUT /deluge/torrent-health` | Update policy (partial JSON body; next maintenance poll applies) |
| `GET /deluge/torrents` | List torrents |
| `GET /deluge/torrents/completed` | Completed torrents |
| `GET /deluge/torrents/downloading` | Active downloads |

### Scheduler (`/scheduler`)

| Route | Purpose |
|-------|---------|
| `GET /scheduler/settings` | Job intervals, download buffers, TV ahead buffer (DB; `X-API-Key`) |
| `PUT /scheduler/settings` | Update policy; **intervals reschedule immediately** (no restart) |
| `GET /scheduler/jobs` | List jobs and next run time |
| `POST /scheduler/jobs/{job_id}/run` | Run a job now |
| `POST /scheduler/watchlist-downloads/run` | Shortcut for watchlist download job |

### Prowlarr (`/prowlarr`)

| Route | Purpose |
|-------|---------|
| `GET /prowlarr/test-connection` | API health + version |
| `POST /prowlarr/search/by-query` | Search and optionally send to Deluge |
| `GET /prowlarr/indexers/count` | Indexer count |

### Antivirus (`/antivirus`)

| Route | Purpose |
|-------|---------|
| `GET /antivirus/health` | Scan service health |
| `POST /antivirus/scan` | Scan path on disk |

Details: [ANTIVIRUS.md](ANTIVIRUS.md).

### Other

| Prefix | Purpose |
|--------|---------|
| `/tracking` | Active / deferred download tracking |
| `/blacklist-torrents` | Block bad Prowlarr GUIDs |
| `/tmdb` | TMDB connectivity and title lookup |

---

## HTTP errors from external services

Domain errors map to structured JSON and proper status codes:

| `error_type` | Typical HTTP | Meaning |
|--------------|--------------|---------|
| `connection` | 503 | Service unreachable |
| `server_auth` | 401 | Invalid Plex admin token |
| `user_auth` | 401 | Invalid Plex user token |
| `configuration` | 503 | Missing token or config |
| `operation` | 502 | Upstream API error |

Health endpoints (`/plex/test-connection`, `/prowlarr/test-connection`, etc.) use the same mapping instead of always returning 200.

Example error body:

```json
{
  "service": "plex",
  "error_type": "connection",
  "detail": "Cannot connect to http://host.docker.internal:32400: ..."
}
```

---

## Common tasks

**Reset database** (wipes all app data; schema is recreated by Alembic on next start):

```powershell
docker compose down
Remove-Item -Recurse -Force infra/postgres-data
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
```

Migrations run automatically (`alembic upgrade head` in the orchestrator entrypoint). Current baseline: revision `0001_initial_schema`.

**Run migrations manually** (if needed):

```powershell
docker compose exec plex-orchestrator alembic upgrade head
docker compose exec plex-orchestrator alembic current
```

**Recreate VPN-side containers** (VPN stack only):

```powershell
docker compose up -d --force-recreate gluetun deluge prowlarr flaresolverr
docker compose restart plex-orchestrator
```

**No-VPN stack:** see `docker-compose.no-vpn.yml`.

**Rebuild FastAPI after code changes (production):**

```powershell
docker compose build plex-orchestrator
docker compose up -d plex-orchestrator
```
