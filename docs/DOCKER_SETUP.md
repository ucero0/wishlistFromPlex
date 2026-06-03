# Docker setup — first-time initialization

Step-by-step guide for configuring and running the stack locally.  
Use this before your first `docker compose up`.

**See also:** [Documentation index](README.md) · [Using the app](USAGE.md) · [Antivirus](ANTIVIRUS.md)

---

## What you are running

| Service | Role | Host access |
|---------|------|-------------|
| **plex-orchestrator** | API, orchestration, Plex sync | http://localhost:8000 |
| **postgres** | PostgreSQL (`plex_orchestrator` DB) | internal only |
| **gluetun** | VPN tunnel (NordVPN) | — |
| **deluge** | Torrent client (via VPN) | http://localhost:8112 |
| **prowlarr** | Indexer search (via VPN) | http://localhost:9696 |
| **flaresolverr** | Cloudflare bypass (off VPN, docker-internal) | internal |
| **plex** | Media server (**optional** — see [Plex: two ways to run](#plex-two-ways-to-run)) | http://localhost:32400 |
| **antivirus** | ClamAV + scan API | internal |

Default stack: **Deluge** and **Prowlarr** share Gluetun’s network (`network_mode: service:gluetun`). **FlareSolverr** stays on the Docker bridge so it is not exposed as an open HTTP proxy on the VPN namespace. Prowlarr reaches it at `http://flaresolverr:8191` (Gluetun uses `DNS_ADDRESS=127.0.0.11` for Docker name resolution). FastAPI reaches Deluge/Prowlarr using **`DELUGE_HOST`** / **`PROWLARR_HOST`** from `.env` (typically `gluetun` on the VPN stack).

For local work without VPN, use the standalone [docker-compose.no-vpn.yml](../docker-compose.no-vpn.yml).

---

## Compose files (base / dev / no-vpn)

| File | Purpose |
|------|---------|
| **`docker-compose.yml`** | Full stack with **Gluetun VPN** + production FastAPI |
| **`docker-compose.dev.yml`** | Development overlay — hot reload + bind-mount `app/` and `main.py` |
| **`docker-compose.no-vpn.yml`** | **Standalone** stack without Gluetun (Deluge/Prowlarr on `plex-orchestrator-network`) |

| Goal | Command |
|------|---------|
| **Production + VPN** (default) | `docker compose up -d --build` |
| **Development + VPN** | `docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build` |
| **Development, no VPN** | `docker compose -f docker-compose.no-vpn.yml -f docker-compose.dev.yml up -d --build` |
| **Production, no VPN** | `docker compose -f docker-compose.no-vpn.yml up -d --build` |

**No-VPN file:** use `DELUGE_HOST=deluge` and `PROWLARR_HOST=prowlarr` in `.env`. NordVPN variables are not required.

**Do not** run dev without `-f docker-compose.dev.yml` when you want hot reload. Base alone is production-style FastAPI.

After code changes in **production** mode: `docker compose build plex-orchestrator && docker compose up -d plex-orchestrator`.

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
cd path\to\automatic_plexMediaSever
copy .env.example .env
```

Never commit `.env` (secrets).

**Plex:** choose one mode before editing `.env` — see [Plex: two ways to run](#plex-two-ways-to-run). Defaults in `.env.example` use **host Plex**; switch `PLEX_SERVER_URL` and compose profile for Docker Plex.

---

## Plex: two ways to run

The stack always runs **FastAPI in Docker**. Plex can run **on your PC** or **inside Docker** — pick one.

| | **Host Plex** (default) | **Docker Plex** (optional profile) |
|--|-------------------------|-------------------------------------|
| Where Plex runs | Windows/macOS/Linux Plex app | `linuxserver/plex` container |
| Plex UI in browser | http://localhost:32400 | http://localhost:32400 |
| `PLEX_SERVER_URL` in `.env` | `http://host.docker.internal:32400` | `http://plex:32400` |
| Start Plex with compose? | **No** | **Yes** (`--profile plex-docker`) |
| `PLEX_CLAIM` | Not used (claim in desktop app) | One-time token from https://plex.tv/claim (fresh install only) |
| Library bind mounts | **`plex-orchestrator` only** in `docker-compose.yml` | **`plex` + `plex-orchestrator`** in `docker-compose.yml` |

**Important:** FastAPI never uses `localhost` to reach Plex. Inside the container, `localhost` is FastAPI itself. Use `host.docker.internal` for a PC-installed Plex, or `plex` when the Plex container is running.

### Start commands

**Host Plex** (no Plex container) — development:

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

**Docker Plex** (includes Plex container) — development:

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml --profile plex-docker up -d
```

Plain `docker compose up -d` runs **production-style** FastAPI and **does not** start Plex unless you pass `--profile plex-docker`.

### Verify Plex mode

```powershell
# Is the Plex container running? (only for Docker Plex mode)
docker compose ps plex

# From your PC — works in both modes if Plex is running
curl http://localhost:32400/identity

# From FastAPI's point of view
curl http://localhost:8000/plex/test-connection
```

If `.env` has `PLEX_SERVER_URL=http://plex:32400` but you did not use `--profile plex-docker`, `/plex/test-connection` will fail (no container named `plex`).

---

## Step 2 — Edit `.env` (required values)

Open `.env` and set each section. **No spaces around `=`** (use `KEY=value`, not `KEY = value`).

### 2.1 API & database (required)

| Variable | What to set | Example |
|----------|-------------|---------|
| `API_KEY` | Secret for FastAPI routes that require auth | long random string |
| `POSTGRES_USER` | DB user | `plex_orchestrator_user` |
| `POSTGRES_PASSWORD` | DB password | strong password |
| `POSTGRES_DB` | DB name | `plex_orchestrator` |

`DATABASE_URL` in `.env.example` should match the three `POSTGRES_*` values.

Schema is managed with **Alembic** (`services/plex-orchestrator/alembic/`). On first install or after wiping `infra/postgres-data`, the orchestrator applies revision `0001_initial_schema` automatically.

### 2.2 NordVPN / Gluetun (required for default `docker-compose.yml`)

| Variable | What to set |
|----------|-------------|
| `NORDVPN_USER` | NordVPN OpenVPN username |
| `NORDVPN_PASSWORD` | NordVPN OpenVPN password |
| `SERVER_COUNTRIES` | Comma-separated P2P-friendly countries | e.g. `Netherlands,Switzerland,Sweden` |
| `SERVER_CATEGORIES` | NordVPN server category filter | `P2P` (limits Gluetun to P2P-capable servers) |

Without valid VPN credentials on the default stack, Gluetun stays unhealthy and Deluge/Prowlarr will not work reliably. Skip this section when using `docker-compose.no-vpn.yml`.

### 2.3 Deluge RPC (required for downloads)

| Variable | What to set | Notes |
|----------|-------------|--------|
| `DELUGE_HOST` | `gluetun` (VPN stack) or `deluge` (no-vpn overlay) | Hostname FastAPI uses for RPC |
| `DELUGE_PORT` | `58846` | Daemon RPC port |
| `DELUGE_USERNAME` | e.g. `deluge` | RPC user; applied to `config/auth` on start |
| `DELUGE_PASSWORD` | **strong random value** | Set before first start; replaces default `deluge:deluge` |
| `DELUGE_WEB_PASSWORD` | optional | Web UI password (default: `DELUGE_PASSWORD`); login user is `admin` |
| `CONTAINER_DELUGE_QUARANTINE_PATH` | `/downloads/quarantine` | Keep unless you change volumes |

### 2.4 Prowlarr (required for search)

| Variable | What to set |
|----------|-------------|
| `PROWLARR_HOST` | `gluetun` (VPN stack) or `prowlarr` (no-vpn overlay) |
| `PROWLARR_PORT` | `9696` |
| `PROWLARR_API_KEY` | Long random string — written to Prowlarr `config.xml` on start; used by FastAPI and bootstrap |

Indexers, Deluge download client, and FlareSolverr are created by **bootstrap scripts** on container start (see [infra/prowlarr/README.md](../infra/prowlarr/README.md)). Deluge password is synced from `DELUGE_PASSWORD` in `.env` every time Prowlarr starts.

### 2.5 Plex (required for library / watchlist)

Set variables according to the mode you chose above.

**Host Plex** (Plex app on your PC):

| Variable | What to set |
|----------|-------------|
| `PLEX_SERVER_URL` | `http://host.docker.internal:32400` |
| `PLEX_SERVER_ADMIN_TOKEN` | Server owner X-Plex-Token (or set later via API) |
| `PLEX_CLAIM` | Leave empty |

**Docker Plex** (Plex container):

| Variable | What to set |
|----------|-------------|
| `PLEX_SERVER_URL` | `http://plex:32400` |
| `PLEX_SERVER_ADMIN_TOKEN` | Server owner X-Plex-Token (or set later via API) |
| `PLEX_CLAIM` | Optional one-time token from https://plex.tv/claim (fresh install only) |

Library folders are **not** set in `.env`. Add them in the Plex UI, then bind-mount host paths in `docker-compose.yml` (see Step 3b).

**No spaces around `=`** — use `PLEX_SERVER_URL=http://host.docker.internal:32400`, not `PLEX_SERVER_URL= http://...`.

### 2.6 Paths & optional services

| Variable | What to set |
|----------|-------------|
| `DELUGE_QUARANTINE_VOLUME_PATH` | Host folder for quarantine downloads, e.g. `./infra/deluge/downloads/quarantine` |
| `TMDB_API_KEY` | Optional; leave empty to disable TMDB |
| `SCANFORVIRUS_API_URL` | Usually `http://plex-orchestrator:8000/...` — see `.env.example` |
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

Paths must exist **inside the FastAPI container** at the same paths Plex uses (for ingest moves and disk-usage checks).

#### Host Plex (Plex on your PC)

1. Install and run Plex on your PC. Open http://localhost:32400 and add libraries (e.g. `D:\Media\Movies`).
2. Run library path sync (Step 5.4b) and check what paths Plex returns:
   ```powershell
   curl http://localhost:8000/plex/servers/library/locations-by-media -H "X-API-Key: YOUR_API_KEY"
   ```
3. Edit `docker-compose.yml` — mount each host folder on **`plex-orchestrator`** so the **container path matches** what Plex reports (often `/movies`, `/tv` if you use those in Docker-style library paths, or map host paths accordingly):

```yaml
  plex-orchestrator:
    volumes:
      # ... existing app + quarantine mounts ...
      - D:/Media/Movies:/movies
      - D:/Media/TV:/tv
```

4. Recreate FastAPI after changing mounts: `docker compose up -d --force-recreate plex-orchestrator`

#### Docker Plex (`--profile plex-docker`)

1. Open http://localhost:32400, add libraries using **container paths** you will mount (e.g. `/movies`, `/tv`).
2. Edit `docker-compose.yml` — add the **same** bind mounts under **both** `plex` and `plex-orchestrator`:

```yaml
  plex:
    volumes:
      - ./infra/plex/config:/config
      - D:/Media/Movies:/movies
      - D:/Media/TV:/tv

  plex-orchestrator:
    volumes:
      # ... existing app + quarantine mounts ...
      - D:/Media/Movies:/movies
      - D:/Media/TV:/tv
```

3. After libraries exist, sync paths to the API database (Step 5.4b).

Ingest and disk-usage use the paths Plex returns; they must exist inside the FastAPI container at those paths.
---

## Step 4 — First start

Pick **development** or **production** (see [Compose files](#compose-files-base--dev)).

### Development (recommended while coding)

Hot reload and live source mounts:

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml build
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

With Docker Plex:

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml --profile plex-docker up -d
```

### Production (stable runtime image)

Code is copied into the image at build time — rebuild after changes:

```powershell
docker compose -f docker-compose.yml build plex-orchestrator
docker compose -f docker-compose.yml up -d
```

First boot can take several minutes (antivirus ClamAV definitions, VPN connect; Docker Plex also pulls/starts Plex on first profile run).

Check containers:

```powershell
docker compose ps
# Docker Plex only:
docker compose --profile plex-docker ps plex
```
---

## Step 5 — Post-start configuration (per service)

### 5.1 Gluetun (VPN stack only)

1. Wait until `gluetun` is **healthy**: `docker compose ps`
2. Logs: `docker compose logs gluetun --tail 50`

Skip this section when using `docker-compose.no-vpn.yml`.

### 5.2 Deluge

**Before the first start**, set strong credentials in `.env`:

```env
DELUGE_USERNAME=deluge
DELUGE_PASSWORD=your-long-random-password
# optional — Web UI only (defaults to DELUGE_PASSWORD); login user is always "admin"
# DELUGE_WEB_PASSWORD=
```

On first container start, `custom-cont-init.d/` scripts:

- Set `allow_remote: true`, quarantine download path, Execute plugin, and torrent-complete hook (`98-configure-deluge-downloads.sh`)
- Remove the well-known default RPC user `deluge:deluge`
- Write your `DELUGE_USERNAME` / `DELUGE_PASSWORD` into `infra/deluge/config/auth`
- Set the Web UI password from `DELUGE_WEB_PASSWORD` (or `DELUGE_PASSWORD`)

1. Web UI: http://localhost:8112 — login **`admin`** + password from `.env`
2. RPC remote access and quarantine path are applied automatically on start (no manual `core.conf` edit required).
3. After changing `.env` passwords later, restart Deluge (RPC syncs automatically; Web UI only re-applies if you set `DELUGE_FORCE_WEB_PASSWORD=true` or delete `infra/deluge/config/.deluge-web-password-configured`):
   ```powershell
   docker compose restart deluge
   ```

4. API check:
   ```powershell
   curl http://localhost:8000/deluge/test-connection
   ```

Details: [infra/deluge/README.md](../infra/deluge/README.md)

### 5.3 Prowlarr

Bootstrap runs on every Prowlarr start: API key from `.env`, Deluge/FlareSolverr clients from compose env, indexers from `bootstrap/seed.json` on first start only.

1. Set in `.env`:
   ```env
   PROWLARR_API_KEY=your-long-random-key
   DELUGE_PASSWORD=your-deluge-password
   ```
2. Start Prowlarr (and dependencies):
   ```powershell
   docker compose up -d gluetun deluge flaresolverr prowlarr
   ```
   No-VPN: `docker compose -f docker-compose.no-vpn.yml up -d deluge flaresolverr prowlarr`
3. Check bootstrap:
   ```powershell
   docker compose logs prowlarr --tail 30
   ```
4. API check:
   ```powershell
   curl http://localhost:8000/prowlarr/test-connection
   curl http://localhost:8000/prowlarr/indexers/count
   ```

After changing `DELUGE_PASSWORD` in `.env`, restart Prowlarr only — bootstrap updates the download client:

```powershell
docker compose restart prowlarr
```

Optional UI: http://localhost:9696 (add indexers in UI — stored in local `prowlarr.db`, not committed).

Details: [infra/prowlarr/README.md](../infra/prowlarr/README.md)

### 5.4 Plex

**Host Plex:** ensure the Plex desktop app (or Windows service) is running before testing API connectivity.

**Docker Plex:** ensure you started with `--profile plex-docker` and `PLEX_SERVER_URL=http://plex:32400`.

1. Open http://localhost:32400 and sign in.
   - **Docker Plex, fresh install:** optional `PLEX_CLAIM` in `.env` before first start, or claim manually in the browser.
   - **Host Plex:** claim/sign in via the desktop app or browser as usual.
2. Create libraries pointing at your media folders (Step 3b).
3. Set the **server admin token** — either in `.env` or via API (DB value overrides env):
   ```env
   PLEX_SERVER_ADMIN_TOKEN=your_server_admin_x_plex_token
   ```

   Or after the server is up:

   ```powershell
   curl -X POST http://localhost:8000/plex/servers/admin-token `
     -H "Content-Type: application/json" `
     -H "X-API-Key: YOUR_API_KEY" `
     -d '{"admin_token":"YOUR_SERVER_ADMIN_TOKEN"}'
   ```

   Update later with `PUT /plex/servers/admin-token`. Check status: `GET /plex/servers/admin-token`.

4. Register Plex users in the API (watchlist sync only), e.g.:

   ```powershell
   curl -X POST http://localhost:8000/plex/users/ `
     -H "Content-Type: application/json" `
     -H "X-API-Key: YOUR_API_KEY" `
     -d '{"name":"me","plex_token":"YOUR_PLEX_USER_TOKEN"}'
   ```

   Invalid user tokens return **401** with `error_type: "user_auth"`.

5. Check connectivity:

   ```powershell
   curl http://localhost:8000/plex/test-connection
   curl http://localhost:8000/plex/test-admin-token
   ```

### 5.4b Plex library paths (database, for ingest)

Server API calls use the **server admin token** (DB or `PLEX_SERVER_ADMIN_TOKEN`), not per-user tokens.

| Endpoint | Purpose |
|----------|---------|
| `GET /plex/servers/library/locations-by-media` | Live paths from Plex (read-only) |
| `POST /plex/servers/library/locations-by-media/sync` | Same data → saved to DB |
| `GET /plex/library-paths` | Flat paths from DB (+ optional refresh) |
| `GET /plex/library-paths/disk-usage` | DB paths with disk usage by section |
| `GET /plex/library-paths/media-devices` | HDD volumes aggregated from DB |

1. After Plex libraries are configured:

   ```powershell
   curl -X POST http://localhost:8000/plex/servers/library/locations-by-media/sync `
     -H "X-API-Key: YOUR_API_KEY"
   ```

   Missing admin token → **503** (`error_type: "configuration"`). Invalid admin token → **401** (`error_type: "server_auth"`).

2. Read synced paths and disk space:

   ```powershell
   curl http://localhost:8000/plex/library-paths -H "X-API-Key: YOUR_API_KEY"
   curl http://localhost:8000/plex/library-paths/media-devices -H "X-API-Key: YOUR_API_KEY"
   ```

3. Re-run **sync** when you add or change library folders in Plex (optional — also runs automatically).

**Automatic DB updates** (Plex server API via admin token):

- **Scheduled** on an interval from DB (`GET /scheduler/settings`, default 360 minutes)
- **Before ingest** when moving a clean torrent
- **Before** `GET /plex/library-paths*` reads (best-effort refresh)

Media types: `movie`, `tvshow`, `other`.

**Important:** Paths returned by Plex must match bind mounts on the `plex-orchestrator` service (Step 3b). There is no `PLEX_MEDIA_*` variable in `.env`.

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

## Step 6 — Production deploy

Base compose is production-oriented (`runtime` image, no dev bind mounts). Rebuild FastAPI when code changes:

```powershell
docker compose -f docker-compose.yml build plex-orchestrator
docker compose -f docker-compose.yml up -d
```

With Docker Plex:

```powershell
docker compose -f docker-compose.yml --profile plex-docker up -d --build
```
---

## Step 7 — Verify the full chain

Run these after configuration:

```powershell
curl http://localhost:8000/health
curl http://localhost:8000/deluge/test-connection
curl http://localhost:8000/prowlarr/test-connection
curl http://localhost:8000/plex/test-connection
curl http://localhost:8000/plex/library-paths -H "X-API-Key: YOUR_API_KEY"
curl http://localhost:8000/antivirus/health
curl http://localhost:8000/tmdb/test-connection
```

| Endpoint | Healthy when |
|----------|----------------|
| `/deluge/test-connection` | `connected: true`, `vpn_healthy: true` (Gluetun :9999); `torrent_connectivity` is informational only |
| `/prowlarr/test-connection` | API key valid |
| `/plex/test-connection` | Plex server reachable |
| `/antivirus/health` | ClamAV + scan service up |

---

## Important operational rules

### Recreate VPN-side services together (VPN stack only)

Deluge, Prowlarr, and FlareSolverr use `network_mode: service:gluetun`. If Gluetun gets a **new container ID**, dependents must be recreated or FlareSolverr/indexers break.

The **`vpn-stack-sync`** service (see [infra/gluetun/README.md](../infra/gluetun/README.md)) watches Gluetun start events and reconciles dependents automatically after autoheal, the in-container health monitor, or a manual Gluetun recreate.

Manual full recreate (always safe):

```powershell
docker compose up -d --force-recreate gluetun deluge prowlarr flaresolverr
docker compose restart plex-orchestrator
```

One-shot sync without recreating Gluetun:

```powershell
docker compose run --rm --entrypoint sync-vpn-dependents vpn-stack-sync once
```

### Prowlarr clients on no-vpn overlay

When using `docker-compose.no-vpn.yml`, set in Prowlarr UI if `prowlarr.db` still has `127.0.0.1`:

| Client | Host |
|--------|------|
| Deluge Web UI | `deluge` port `8112` |
| FlareSolverr | `http://flaresolverr:8191` |

### Do not change these without updating docs/config

| Setting | VPN stack | No-VPN overlay |
|---------|-----------|----------------|
| `DELUGE_HOST` | `gluetun` | `deluge` |
| `PROWLARR_HOST` | `gluetun` | `prowlarr` |
| `DELUGE_PORT` | `58846` | `58846` |

### Windows: no `make` required

```powershell
# Tests (dev image)
docker compose -f docker-compose.yml -f docker-compose.dev.yml run --rm --no-deps plex-orchestrator pytest -q

# Logs
docker compose logs -f plex-orchestrator

# Stop everything
docker compose down
```

---

## Troubleshooting

| Symptom | Likely cause | What to do |
|---------|--------------|------------|
| Deluge `connection refused` | Wrong `DELUGE_HOST` or Gluetun/Deluge not up | VPN: `gluetun` + recreate deluge; no-vpn: `deluge` |
| Gluetun unhealthy | Bad NordVPN creds or country | Fix `.env`, check `docker compose logs gluetun` |
| Deluge `Username does not exist` | Missing line in `config/auth` | Add `user:pass:10`, restart deluge |
| Deluge `Password does not match` | Wrong password in `.env` vs `auth` | Align both; plain text in `auth` |
| Prowlarr auth / Deluge grab fails | Wrong `PROWLARR_API_KEY` or Deluge password mismatch | Set `PROWLARR_API_KEY` and `DELUGE_PASSWORD` in `.env`, then `docker compose restart prowlarr` |
| `/plex/test-connection` unhealthy, `error_type: connection` | Wrong `PLEX_SERVER_URL` vs mode, or Plex not running | Host Plex: app running + `http://host.docker.internal:32400`. Docker Plex: `--profile plex-docker` + `http://plex:32400` |
| Plex container not listed in `docker compose ps` | Expected for host Plex | Use `--profile plex-docker` only if you want Plex in Docker |
| Plex paths empty / ingest cannot move files | Library not in Plex or mounts missing on `plex-orchestrator` | Add libraries in Plex UI, add matching bind mounts on `plex-orchestrator` (and `plex` if Docker Plex), run sync, recreate containers |
| Antivirus slow start | First-time ClamAV download | Wait 2–5 min, check logs |
| `gluetun` / `antivirus` exit code 2, logs show `: not found` or `syntax error` in `.sh` files | Windows checked out shell scripts with CRLF line endings | Pull latest (`.gitattributes` enforces LF), then run `git add --renormalize infra/ && git checkout -- infra/` and recreate containers |
| `plex-orchestrator`: `exec /docker-entrypoint.sh: no such file or directory` | CRLF in `docker-entrypoint.sh` baked into image at build time on Windows | Pull latest, run `git add --renormalize services/plex-orchestrator/docker-entrypoint.sh && git checkout -- services/plex-orchestrator/docker-entrypoint.sh`, then `docker compose build --no-cache plex-orchestrator && docker compose up -d plex-orchestrator` |
| Alembic / DB connection errors after pull | Old Postgres volume vs new schema | `docker compose down`, delete `infra/postgres-data`, `up -d --build` (see [USAGE.md](USAGE.md)) |

---

## Related docs

- [infra/deluge/README.md](../infra/deluge/README.md) — Deluge auth & RPC
- [services/plex-orchestrator/ARCHITECTURE_FOLDER_GUIDE.md](../services/plex-orchestrator/ARCHITECTURE_FOLDER_GUIDE.md) — FastAPI code layout
- [docs/README.md](README.md) — Antivirus documentation index
