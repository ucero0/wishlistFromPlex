# Using the application

How to operate **Wishlist from Plex** after [Docker setup](DOCKER_SETUP.md) is complete.

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
4. **Library paths** — add libraries in Plex, mount folders on the `fastapi` container, then sync:
   ```powershell
   curl -X POST http://localhost:8000/plex/servers/library/locations-by-media/sync `
     -H "X-API-Key: YOUR_API_KEY"
   ```

### 2. Configure download stack

| Step | Endpoint | Notes |
|------|----------|--------|
| VPN | `GET /gluetun/health` | `connected: true` required |
| Deluge | `GET /deluge/test-connection` | includes `vpn` status |
| Prowlarr | `GET /prowlarr/test-connection` | set `PROWLARR_API_KEY` in `.env` |

### 3. Run the pipeline

**Automatic (scheduler):**

- Watchlist → search → Deluge: runs on an interval (see scheduler in app startup logs).
- Library path sync: every `PLEX_LIBRARY_PATHS_SYNC_INTERVAL_HOURS` (default 6).
- Deferred downloads: every `DEFERRED_DOWNLOAD_PROCESS_INTERVAL_MINUTES` (default 15).

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

After a torrent completes (files in quarantine):

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
| `GET /deluge/test-connection` | RPC + VPN health |
| `GET /deluge/torrents` | List torrents |
| `GET /deluge/torrents/completed` | Completed torrents |
| `GET /deluge/torrents/downloading` | Active downloads |

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
| `/gluetun` | VPN health |

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

**Reset database** (destroys all app data):

```powershell
docker compose down
Remove-Item -Recurse -Force infra/postgres-data
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
```

Tables are recreated on FastAPI startup.

**Recreate VPN-side containers** (if Deluge loses network after Gluetun restart):

```powershell
docker compose up -d --force-recreate gluetun deluge prowlarr flaresolverr
docker compose restart fastapi
```

**Rebuild FastAPI after code changes (production):**

```powershell
docker compose build fastapi
docker compose up -d fastapi
```
