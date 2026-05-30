# Prowlarr bootstrap

Prowlarr is configured **automatically on first start** from repo seed files and **secrets in `.env`**. Runtime data under `config/` is **not** committed.

## In Git

| Path | Purpose |
|------|---------|
| `bootstrap/seed.json` | Indexer list only (names, definitions, FlareSolverr tag flags) |
| `scripts/bootstrap_prowlarr.sh` | Applies config via Prowlarr API (`curl` + `jq`) |
| `custom-cont-init.d/99-ensure-api-key.sh` | Writes `PROWLARR_API_KEY` into `config.xml` before start |
| `custom-services.d/bootstrap` | Runs bootstrap on every container start |

## In `.env` (secrets)

| Variable | Purpose |
|----------|---------|
| `PROWLARR_API_KEY` | Prowlarr API + FastAPI |
| `DELUGE_PASSWORD` / `DELUGE_WEB_PASSWORD` | Deluge **Web UI** password for Prowlarr download client |

## In `docker-compose.yml` (connection defaults)

Prowlarr shares Gluetun’s network with Deluge and FlareSolverr, so host/port differ from FastAPI’s `DELUGE_HOST` / `DELUGE_PORT` (RPC via `gluetun:58846`):

| Compose env (prowlarr service) | Value | Purpose |
|-------------------------------|-------|---------|
| `PROWLARR_DELUGE_HOST` | `127.0.0.1` | Deluge Web UI |
| `PROWLARR_DELUGE_WEB_PORT` | `8112` | Deluge Web UI (not RPC `58846`) |
| `FLARESOLVERR_URL` | `http://127.0.0.1:8191` | FlareSolverr proxy |
| `PROWLARR_DELUGE_CATEGORY` | `prowlarr` | Torrent category |
| `PROWLARR_FLARESOLVERR_TAG` | `flaresolverr` | Indexer tag |

Edit `docker-compose.yml` to override these — they are **not** in `.env` by default.

## Bootstrap behaviour

| Resource | When updated |
|----------|----------------|
| FlareSolverr proxy | **Every start** — from compose |
| Deluge download client | **Every start** — compose host/port + `.env` password |
| Indexers | **First start only** — from `seed.json` (set `PROWLARR_BOOTSTRAP_FORCE=true` in compose to re-run) |

## First start

1. Set in `.env`:
   ```env
   PROWLARR_API_KEY=your-long-random-key
   DELUGE_PASSWORD=your-strong-deluge-web-password
   ```
2. Start stack:
   ```powershell
   docker compose up -d gluetun deluge flaresolverr prowlarr
   ```
3. Verify:
   ```powershell
   docker logs prowlarr 2>&1 | Select-String prowlarr-bootstrap
   curl http://localhost:8000/prowlarr/test-connection
   ```

## After password change

Update `DELUGE_PASSWORD` in `.env`, then:

```powershell
docker compose restart deluge prowlarr
```

## Customize indexers

Edit `bootstrap/seed.json`, set `PROWLARR_BOOTSTRAP_FORCE=true` in `docker-compose.yml` for one restart, then set back to `false`.

## Security

Do **not** commit `infra/prowlarr/config/`. Secrets stay in `.env` only.
