# Wishlist from Plex

Automated media pipeline: sync Plex watchlists, search torrents (Prowlarr), download via Deluge (VPN through Gluetun by default), scan (ClamAV + YARA), and ingest clean files into your Plex libraries.

## What it does

```text
Plex watchlist  →  Prowlarr search  →  Deluge (VPN)  →  quarantine scan  →  Plex library
```

The **FastAPI** service orchestrates everything. Scheduled jobs also run watchlist processing, library-path sync, and deferred downloads when disk space is low.

## Quick start

1. Copy and edit environment:
   ```powershell
   copy .env.example .env
   ```
2. Follow **[docs/DOCKER_SETUP.md](docs/DOCKER_SETUP.md)** — VPN, Deluge, Prowlarr, Plex, library mounts.
3. Start the stack:

   **Development** (code hot-reload):
   ```powershell
   docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
   ```

   **Production** (stable image):
   ```powershell
   docker compose -f docker-compose.yml up -d --build
   ```

4. Open **http://localhost:8000/docs** — use header `X-API-Key: <API_KEY from .env>` on protected routes.

## Documentation

| Document | Description |
|----------|-------------|
| [docs/README.md](docs/README.md) | Documentation index |
| [docs/DOCKER_SETUP.md](docs/DOCKER_SETUP.md) | First-time Docker and `.env` setup |
| [docs/USAGE.md](docs/USAGE.md) | How to use the API and workflows |
| [docs/ANTIVIRUS.md](docs/ANTIVIRUS.md) | Virus scanning and quarantine |
| [infra/deluge/README.md](infra/deluge/README.md) | Deluge RPC auth and VPN networking |
| [services/fastapi-app/ARCHITECTURE_FOLDER_GUIDE.md](services/fastapi-app/ARCHITECTURE_FOLDER_GUIDE.md) | Code layout (hexagonal architecture) |

## Health checks

```powershell
curl http://localhost:8000/health
curl http://localhost:8000/deluge/test-connection
curl http://localhost:8000/prowlarr/test-connection
curl http://localhost:8000/plex/test-connection
curl http://localhost:8000/antivirus/health
```

Unhealthy service checks return non-200 status codes with an `error_type` field (see [docs/USAGE.md](docs/USAGE.md)).

## Make shortcuts

```powershell
make dev      # development stack
make prod     # production stack
make test     # run pytest in dev container
```
