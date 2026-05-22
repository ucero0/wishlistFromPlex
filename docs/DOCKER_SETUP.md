# Docker setup — first-time initialization

Step-by-step guide for configuring and running the stack locally.  
Use this before your first `docker compose up`.

---

## What you are running

| Service | Role | Host access |
|---------|------|-------------|
| **fastapi** | API, orchestration, Plex sync | http://localhost:8000 |
| **db** | PostgreSQL | internal only |
| **gluetun** | VPN tunnel (NordVPN) | — |
| **deluge** | Torrent client (via VPN) | http://localhost:8112 (Web UI) |
| **prowlarr** | Indexer search (via VPN) | http://localhost:9696 |
| **flaresolverr** | Cloudflare bypass (via VPN) | internal |
| **plex** | Media server | http://localhost:32400 |
| **antivirus** | ClamAV + scan API | internal |

Deluge, Prowlarr, and FlareSolverr share Gluetun’s network (`network_mode: service:gluetun`). FastAPI talks to them at hostname **`gluetun`**, not `deluge` or `prowlarr`.

---

## Prerequisites

1. [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows/macOS) or Docker Engine + Compose v2 (Linux).
2. **NordVPN** account with OpenVPN credentials ([NordVPN service credentials](https://my.nordaccount.com/dashboard/nordvpn/manual-configuration/) — not your login email/password for the website unless you use those as OpenVPN user/pass).
3. Optional: [TMDB API key](https://www.themoviedb.org/settings/api) for original-title lookup.
4. Host folders for Plex libraries (you mount them in `docker-compose.yml`) and for Deluge quarantine (`.env`).

---

## Step 1 — Copy environment file

From the repository root:

```powershell
cd path\to\wishlistFromPlex
copy .env.example .env
```

Never commit `.env` (secrets).

---

## Step 2 — Edit `.env` (required values)

Open `.env` and set each section. **No spaces around `=`** (use `KEY=value`, not `KEY = value`).

### 2.1 API & database (required)

| Variable | What to set | Example |
|----------|-------------|---------|
| `API_KEY` | Secret for FastAPI routes that require auth | long random string |
| `POSTGRES_USER` | DB user | `plex_wishlist_user` |
| `POSTGRES_PASSWORD` | DB password | strong password |
| `POSTGRES_DB` | DB name | `plex_wishlist` |

`DATABASE_URL` in `.env.example` should match the three `POSTGRES_*` values.

### 2.2 NordVPN / Gluetun (required for torrent stack)

| Variable | What to set |
|----------|-------------|
| `NORDVPN_USER` | NordVPN OpenVPN username |
| `NORDVPN_PASSWORD` | NordVPN OpenVPN password |
| `SERVER_COUNTRIES` | Comma-separated countries | e.g. `Switzerland,Spain` |

Without valid VPN credentials, Gluetun stays unhealthy and Deluge/Prowlarr will not work reliably.

### 2.3 Deluge RPC (required for downloads)

| Variable | What to set | Notes |
|----------|-------------|--------|
| `DELUGE_HOST` | `gluetun` | Do not use `deluge` |
| `DELUGE_PORT` | `58846` | Daemon RPC port |
| `DELUGE_USERNAME` | e.g. `deluge` | Must exist in `infra/deluge/config/auth` |
| `DELUGE_PASSWORD` | same as in `auth` | **Plain text** in auth file |
| `CONTAINER_DELUGE_QUARANTINE_PATH` | `/downloads/quarantine` | Keep unless you change volumes |

### 2.4 Prowlarr (required for search)

| Variable | What to set |
|----------|-------------|
| `PROWLARR_HOST` | `gluetun` |
| `PROWLARR_PORT` | `9696` |
| `PROWLARR_API_KEY` | From Prowlarr UI → Settings → General |

### 2.5 Plex (required for library / watchlist)

| Variable | What to set |
|----------|-------------|
| `PLEX_SERVER_URL` | `http://plex:32400` (inside Docker network) |
| `PLEX_CLAIM` | Optional one-time claim token from https://plex.tv/claim |

Library folders are **not** set in `.env`. Add them in the Plex web UI, then bind-mount the same host paths in `docker-compose.yml` under `plex` and `fastapi` (see Step 3b).

### 2.6 Paths & optional services

| Variable | What to set |
|----------|-------------|
| `DELUGE_QUARANTINE_VOLUME_PATH` | Host folder for quarantine downloads, e.g. `./infra/deluge/downloads/quarantine` |
| `TMDB_API_KEY` | Optional; leave empty to disable TMDB |
| `SCANFORVIRUS_API_URL` | Usually `http://fastapi:8000/...` — see `.env.example` |
| `LOG_LEVEL` | `INFO` or `DEBUG` |

---

## Step 3 — Create host folders

Create the Deluge quarantine directory (if it does not exist):

```powershell
mkdir -Force infra\deluge\downloads\quarantine
```

On Linux/macOS:

```bash
mkdir -p infra/deluge/downloads/quarantine
```

Ensure Docker can read/write `DELUGE_QUARANTINE_VOLUME_PATH`.

### 3b — Plex library bind mounts (docker-compose, not `.env`)

1. In Plex (http://localhost:32400), add libraries and choose **container paths** you will mount (e.g. `/movies`, `/tv`).
2. Edit `docker-compose.yml` and add matching bind mounts under **both** `plex` and `fastapi` `volumes:` (same left host path, same right container path):

```yaml
  plex:
    volumes:
      - ./infra/plex/config:/config
      - D:/Media/Movies:/movies
      - D:/Media/TV:/tv

  fastapi:
    volumes:
      # ... existing app + quarantine mounts ...
      - D:/Media/Movies:/movies
      - D:/Media/TV:/tv
```

3. After libraries exist, sync paths to the API database (Step 5.4b).

Ingest and disk-usage use the paths Plex returns; they must exist inside the FastAPI container at the same paths.

---

## Step 4 — First start (development)

Development uses hot-reload for FastAPI:

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml build
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

First boot can take several minutes (antivirus ClamAV definitions, VPN connect, Plex).

Check containers:

```powershell
docker compose ps
```

---

## Step 5 — Post-start configuration (per service)

### 5.1 Gluetun (VPN)

1. Wait until `gluetun` is **healthy**: `docker compose ps`
2. API check: `curl http://localhost:8000/gluetun/health`  
   - `connected: true` → VPN tunnel OK  
   - `error` field → read message (auth, timeout, etc.)

Logs:

```powershell
docker compose logs gluetun --tail 50
```

### 5.2 Deluge

1. Web UI: http://localhost:8112 (default password often `deluge` on first login — change it in the UI).
2. Confirm remote RPC in `infra/deluge/config/core.conf`:
   ```json
   "allow_remote": true,
   ```
3. Confirm API user in `infra/deluge/config/auth` (plain password):
   ```
   deluge:your_password:10
   ```
   Must match `DELUGE_USERNAME` / `DELUGE_PASSWORD` in `.env`.

   On **first** start, `custom-cont-init.d/99-configure-api-user.sh` can add the user from env if missing.

4. Restart after editing auth:
   ```powershell
   docker compose restart deluge
   ```

5. API check:
   ```powershell
   curl http://localhost:8000/deluge/test-connection
   ```
   Response includes `vpn` (Gluetun) and `deluge` status.

Details: [infra/deluge/README.md](../infra/deluge/README.md)

### 5.3 Prowlarr

1. Open http://localhost:9696
2. Complete wizard; add indexers as needed.
3. **Settings → General** → copy **API Key** into `.env` as `PROWLARR_API_KEY`.
4. Restart FastAPI so it picks up the key:
   ```powershell
   docker compose restart fastapi
   ```
5. Check: `curl http://localhost:8000/prowlarr/test-connection`

### 5.4 Plex

1. Open http://localhost:32400 and sign in / claim server (`PLEX_CLAIM` in `.env` if fresh install).
2. Create libraries pointing at the folders you mounted in `docker-compose.yml` (Step 3b).
3. Register Plex users in the API (watchlist sync), e.g.:
   ```powershell
   curl -X POST http://localhost:8000/plex/users/ `
     -H "Content-Type: application/json" `
     -H "X-API-Key: YOUR_API_KEY" `
     -d '{"name":"me","plex_token":"YOUR_PLEX_TOKEN"}'
   ```
   Plex tokens: https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/

4. Check: `curl http://localhost:8000/plex/test-connection`

### 5.4b Plex library paths (database, for ingest)

Uses the same **locations-by-media** API you already have; sync only persists it for ingest.

| Endpoint | Purpose |
|----------|---------|
| `GET /plex/servers/library/locations-by-media` | Live paths from Plex (read-only) |
| `POST /plex/servers/library/locations-by-media/sync` | Same data → saved to DB |
| `GET /plex/servers/library/locations-by-media/stored` | Paths from DB (same JSON shape) |
| `GET /plex/servers/library/locations-by-media/disk-usage` | Paths + free space on this host |

1. After Plex libraries are configured:

   ```powershell
   curl -X POST http://localhost:8000/plex/servers/library/locations-by-media/sync `
     -H "X-Plex-Token: YOUR_PLEX_TOKEN"
   ```

2. Optional — compare live vs stored:

   ```powershell
   curl http://localhost:8000/plex/servers/library/locations-by-media -H "X-Plex-Token: YOUR_TOKEN"
   curl http://localhost:8000/plex/servers/library/locations-by-media/stored
   ```

3. Re-run **sync** when you add or change library folders in Plex (optional — also runs automatically).

**Automatic DB updates** (same Plex `locations-by-media` API):

- **Scheduled** every `PLEX_LIBRARY_PATHS_SYNC_INTERVAL_HOURS` (default `6`) for all active Plex users in the DB
- **Before ingest** when moving a clean torrent (uses that download’s Plex user token)
- Paths **removed** in Plex → `is_active=false` in DB; **new** folders → inserted or reactivated

Media types: `movie`, `tvshow`, `other`.

**Important:** Paths returned by Plex must match bind mounts on the `fastapi` service (Step 3b). There is no `PLEX_MEDIA_*` variable in `.env`.

### 5.5 Antivirus

ClamAV needs a few minutes on first run. Check:

```powershell
curl http://localhost:8000/antivirus/health
docker compose logs antivirus --tail 30
```

### 5.6 FastAPI

- Docs: http://localhost:8000/docs  
- Health: http://localhost:8000/health  
- Most routes need header: `X-API-Key: <API_KEY from .env>`

---

## Step 6 — Production compose (optional)

No source bind-mounts; image runs baked code:

```powershell
docker compose -f docker-compose.yml -f docker-compose.prod.yml build fastapi
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

---

## Step 7 — Verify the full chain

Run these after configuration:

```powershell
curl http://localhost:8000/health
curl http://localhost:8000/gluetun/health
curl http://localhost:8000/deluge/test-connection
curl http://localhost:8000/prowlarr/test-connection
curl http://localhost:8000/plex/test-connection
curl http://localhost:8000/plex/servers/library/locations-by-media/stored
curl http://localhost:8000/antivirus/health
curl http://localhost:8000/tmdb/test-connection
```

| Endpoint | Healthy when |
|----------|----------------|
| `/gluetun/health` | VPN up |
| `/deluge/test-connection` | `connected: true` and `vpn.connected: true` |
| `/prowlarr/test-connection` | API key valid |
| `/plex/test-connection` | Plex server reachable |
| `/antivirus/health` | ClamAV + scan service up |

---

## Important operational rules

### Recreate VPN-side services together

If you recreate **only** Gluetun, Deluge/Prowlarr/FlareSolverr can lose the shared network until recreated:

```powershell
docker compose up -d --force-recreate gluetun deluge prowlarr flaresolverr
```

Then restart FastAPI if needed:

```powershell
docker compose restart fastapi
```

### Do not change these without updating docs/config

| Setting | Keep as |
|---------|---------|
| `DELUGE_HOST` / `PROWLARR_HOST` | `gluetun` |
| `DELUGE_PORT` | `58846` |
| Gluetun `FIREWALL_INPUT_PORTS` | Must include `58846`, `8112`, `${PROWLARR_PORT}`, `8191`, `9999` |

### Windows: no `make` required

```powershell
# Tests (dev image)
docker compose -f docker-compose.yml -f docker-compose.dev.yml run --rm --no-deps fastapi pytest -q

# Logs
docker compose logs -f fastapi

# Stop everything
docker compose down
```

---

## Troubleshooting

| Symptom | Likely cause | What to do |
|---------|--------------|------------|
| Deluge `connection refused` | Gluetun recreated without Deluge | Recreate `deluge` (see above) |
| Deluge `Username does not exist` | Missing line in `config/auth` | Add `user:pass:10`, restart deluge |
| Deluge `Password does not match` | Wrong password in `.env` vs `auth` | Align both; plain text in `auth` |
| Prowlarr unhealthy | Missing/wrong `PROWLARR_API_KEY` | Set in UI + `.env`, restart fastapi |
| Gluetun unhealthy | Bad NordVPN creds or country | Fix `.env`, check `docker compose logs gluetun` |
| Plex paths empty / ingest cannot move files | Library not in Plex or mounts missing on `fastapi` | Add libraries in Plex UI, add matching bind mounts in `docker-compose.yml`, run sync, recreate containers |
| Antivirus slow start | First-time ClamAV download | Wait 2–5 min, check logs |

---

## Related docs

- [infra/deluge/README.md](../infra/deluge/README.md) — Deluge auth & RPC
- [services/fastapi-app/ARCHITECTURE_FOLDER_GUIDE.md](../services/fastapi-app/ARCHITECTURE_FOLDER_GUIDE.md) — FastAPI code layout
- [docs/README.md](README.md) — Antivirus documentation index
