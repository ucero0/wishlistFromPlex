# Documentation

Guides for **Wishlist from Plex** — setup, daily use, and development.

## Start here

| If you want to… | Read |
|-----------------|------|
| Install and configure Docker for the first time | [DOCKER_SETUP.md](DOCKER_SETUP.md) |
| Use the API (watchlist, downloads, ingest) | [USAGE.md](USAGE.md) |
| Understand virus scanning | [ANTIVIRUS.md](ANTIVIRUS.md) |
| Fix Deluge RPC / VPN connectivity | [../infra/deluge/README.md](../infra/deluge/README.md) |
| Prowlarr indexers & apps (in Git) | [../infra/prowlarr/README.md](../infra/prowlarr/README.md) |
| FlareSolverr (env-only) | [../infra/flaresolverr/README.md](../infra/flaresolverr/README.md) |
| Navigate the FastAPI codebase | [../services/fastapi-app/ARCHITECTURE_FOLDER_GUIDE.md](../services/fastapi-app/ARCHITECTURE_FOLDER_GUIDE.md) |

## Stack overview

| Service | Role | URL (host) |
|---------|------|------------|
| **fastapi** | API and orchestration | http://localhost:8000 |
| **db** | PostgreSQL | internal |
| **gluetun** | NordVPN tunnel | — |
| **deluge** | Torrent client (via VPN) | http://localhost:8112 |
| **prowlarr** | Indexer search (via VPN) | http://localhost:9696 |
| **antivirus** | ClamAV + YARA HTTP scan | internal |
| **plex** | Media server (optional Docker profile) | http://localhost:32400 |

FastAPI talks to Deluge and Prowlarr at hostname **`gluetun`**, not `deluge` or `prowlarr`.

## Compose commands

| Mode | Command |
|------|---------|
| Development | `docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build` |
| Production | `docker compose -f docker-compose.yml up -d --build` |
| Docker Plex | add `--profile plex-docker` |

See [DOCKER_SETUP.md](DOCKER_SETUP.md) for Plex on your PC vs Plex in Docker.

## API entry points

- Interactive docs: http://localhost:8000/docs
- Health: http://localhost:8000/health
- Authentication: `X-API-Key` header (value from `.env` → `API_KEY`)
