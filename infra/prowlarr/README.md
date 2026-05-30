# Prowlarr config (in Git)

Prowlarr is pre-configured from files committed under `config/`. On `docker compose up`, the container mounts that directory as `/config` — no bootstrap scripts or manual UI setup required for indexers, Deluge, or FlareSolverr.

## In Git

| Path | Purpose |
|------|---------|
| `config/config.xml` | API key, port, auth settings |
| `config/prowlarr.db` | Indexers, download clients, FlareSolverr proxy, apps |
| `config/Definitions/` | Indexer definition YAMLs (bundled with the DB snapshot) |

## Not in Git (runtime)

| Path | Why ignored |
|------|-------------|
| `config/logs/` | Log output |
| `config/Backups/` | Scheduled backups |
| `config/asp/` | ASP.NET data protection keys |
| `config/Sentry/` | Crash telemetry |
| `config/*.pid`, `config/logs.db*` | Process / log DB artifacts |

## `.env` (FastAPI only)

| Variable | Purpose |
|----------|---------|
| `PROWLARR_HOST` | `gluetun` (FastAPI reaches Prowlarr via Gluetun) |
| `PROWLARR_PORT` | `9696` |
| `PROWLARR_API_KEY` | Must match `<ApiKey>` in `config/config.xml` |

Deluge Web UI credentials for the Prowlarr → Deluge client are stored **inside** `prowlarr.db`. Use the same `DELUGE_PASSWORD` / `DELUGE_WEB_PASSWORD` as when the DB was created, or update the Deluge client once in the Prowlarr UI (http://localhost:9696).

## First start

1. Set in `.env`:
   ```env
   PROWLARR_API_KEY=<same value as config/config.xml ApiKey>
   ```
2. Start stack:
   ```powershell
   docker compose up -d gluetun deluge flaresolverr prowlarr
   ```
3. Verify:
   ```powershell
   curl http://localhost:8000/prowlarr/test-connection
   curl http://localhost:8000/prowlarr/indexers/count
   ```

## Updating the committed config

After changing indexers or download clients in the Prowlarr UI:

1. Stop Prowlarr so the DB is not locked:
   ```powershell
   docker compose stop prowlarr
   ```
2. Commit updated `config/prowlarr.db` and `config/config.xml` if the API key changed.
3. Do **not** commit `logs/`, `Backups/`, or `asp/`.

## Security

This is a private homelab setup. `config.xml` and `prowlarr.db` contain the API key and may contain Deluge credentials. Do not publish the repo publicly without rotating secrets.
