# Prowlarr config (bootstrap from `.env`)

Prowlarr is configured on container start by bootstrap scripts — **not** from a committed `prowlarr.db`.

| When | What runs |
|------|-----------|
| **Every start** | Sync API key → `config.xml`; update Deluge + FlareSolverr clients from `.env` |
| **First start only** | Create indexers from `bootstrap/seed.json` (marker: `config/.prowlarr-bootstrap-v1.done`) |

## In Git

| Path | Purpose |
|------|---------|
| `bootstrap/seed.json` | Indexer list (names, definitions, FlareSolverr flag) |
| `scripts/bootstrap_prowlarr.sh` | Prowlarr API bootstrap |
| `custom-cont-init.d/99-ensure-api-key.sh` | Writes `PROWLARR_API_KEY` to `config.xml` |
| `custom-services.d/bootstrap` | Runs bootstrap after Prowlarr starts |
| `config/.gitkeep` | Empty config mount point |

## Not in Git (runtime)

| Path | Created by |
|------|------------|
| `config/config.xml` | Init script from `PROWLARR_API_KEY` |
| `config/prowlarr.db` | Prowlarr + bootstrap |
| `config/.prowlarr-bootstrap-v1.done` | Bootstrap after first indexer sync |

## `.env` (required)

| Variable | Purpose |
|----------|---------|
| `PROWLARR_API_KEY` | Prowlarr API key (source of truth — written to `config.xml` on start) |
| `PROWLARR_HOST` | `gluetun` (VPN stack) or `prowlarr` (no-vpn) — for **FastAPI** only |
| `DELUGE_PASSWORD` | Deluge Web UI password — synced to Prowlarr download client every start |
| `DELUGE_WEB_PASSWORD` | Optional; defaults to `DELUGE_PASSWORD` for Prowlarr → Deluge |

Deluge/FlareSolverr **host URLs** for Prowlarr are set in `docker-compose.yml` (VPN: `127.0.0.1`) or `docker-compose.no-vpn.yml` (`deluge`, `flaresolverr`).

## First start

1. Set in `.env`:
   ```env
   PROWLARR_API_KEY=your-long-random-key
   DELUGE_PASSWORD=your-deluge-password
   ```
2. Start stack:
   ```powershell
   docker compose up -d gluetun deluge flaresolverr prowlarr
   ```
3. Check bootstrap logs:
   ```powershell
   docker compose logs prowlarr --tail 50
   ```
4. Verify:
   ```powershell
   curl http://localhost:8000/prowlarr/test-connection
   curl http://localhost:8000/prowlarr/indexers/count
   ```

## After changing Deluge password

Update `DELUGE_PASSWORD` in `.env` and restart Prowlarr — bootstrap updates the download client automatically:

```powershell
docker compose restart prowlarr
```

## Re-run indexer bootstrap

To recreate indexers from `seed.json` (e.g. after editing the seed file):

```powershell
docker compose stop prowlarr
Remove-Item infra\prowlarr\config\.prowlarr-bootstrap-v1.done -ErrorAction SilentlyContinue
docker compose up -d prowlarr
```

Or set `PROWLARR_BOOTSTRAP_FORCE=true` in compose env for one start.

## Add indexers

Edit `bootstrap/seed.json`, remove the marker file, restart Prowlarr — or add indexers in the UI (persisted in local `prowlarr.db`, not committed).
